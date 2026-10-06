package com.marketmind.service;

import com.marketmind.dto.CampaignResponseDTO;
import com.marketmind.dto.DestinoDTO;
import com.marketmind.entity.CampaignEntity;
import com.marketmind.entity.UserEntity;
import com.marketmind.exception.CampaignNotFoundException;
import com.marketmind.exception.InvalidStatusTransitionException;
import com.marketmind.repository.CampaignRepository;
import com.marketmind.repository.PublicationViewRepository;
import com.marketmind.repository.UserRepository;
import com.marketmind.security.AuthenticatedUser;
import com.marketmind.websocket.ClientCampaignEvent;
import org.springframework.context.ApplicationEventPublisher;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.OffsetDateTime;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Lógica de negocio del bloque usuario (Spring Boot).
 * Solo permite las transiciones de estado que le corresponden:
 * pendiente_aprobacion → aprobado | rechazado.
 */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
@Slf4j
public class CampaignService {

    private static final Map<String, Set<String>> ALLOWED_TRANSITIONS = Map.of(
            "pendiente_aprobacion", Set.of("aprobado", "rechazado")
    );

    private final CampaignRepository campaignRepository;
    private final UserRepository userRepository;
    private final N8nEmailClient n8nEmailClient;
    private final ApplicationEventPublisher eventPublisher;
    private final DjangoEventClient djangoEventClient;
    private final PublicationViewRepository publicationViewRepository;

    /** HU12 — lista campañas pendientes de aprobación del cliente autenticado. */
    public Page<CampaignResponseDTO> findPending(AuthenticatedUser user, Pageable pageable) {
        String clienteEmail = authenticatedEmail(user);
        Page<CampaignEntity> page = campaignRepository
                .findPendingOrdered("pendiente_aprobacion", clienteEmail, pageable);
        return withMarketerNames(page);
    }

    public Page<CampaignResponseDTO> findMine(
            AuthenticatedUser user,
            String q,
            String estado,
            String industria,
            String plataforma,
            Integer valoracion,
            Pageable pageable) {
        String clienteEmail = authenticatedEmail(user);
        String cleanQ = cleanLower(q);
        Set<Long> marketeroIds = marketeroIdsForQuery(cleanQ);
        Page<CampaignEntity> page = campaignRepository.findMine(
                clienteEmail,
                cleanQ == null ? "" : cleanQ,
                cleanQ != null,
                clean(estado),
                clean(industria),
                clean(plataforma),
                valoracion == null ? null : valoracion.shortValue(),
                !marketeroIds.isEmpty(),
                marketeroIds.isEmpty() ? Set.of(-1L) : marketeroIds,
                pageable);
        return withMarketerNames(page);
    }

    /**
     * Dashboard cliente — conteos por estado para las stat cards.
     * Solo lectura (COUNT), respeta la regla políglota: Spring nunca escribe
     * más allá del campo estado.
     */
    public Map<String, Long> getSummary(AuthenticatedUser user) {
        String clienteEmail = authenticatedEmail(user);
        return Map.of(
                "pendientes", campaignRepository.countByEstadoAndClienteEmailIgnoreCase("pendiente_aprobacion", clienteEmail),
                "aprobadas", campaignRepository.countByEstadoAndClienteEmailIgnoreCase("aprobado", clienteEmail),
                "rechazadas", campaignRepository.countByEstadoAndClienteEmailIgnoreCase("rechazado", clienteEmail)
        );
    }

    /** HU13 — detalle de campaña por id. */
    public CampaignResponseDTO findById(Long id) {
        return campaignRepository.findById(Objects.requireNonNull(id, "id"))
                .map(this::toDTOConNombre)
                .orElseThrow(() -> new CampaignNotFoundException(id));
    }

    /** HU13 — detalle de campaña por id con control de acceso para usuarios finales. */
    public CampaignResponseDTO findById(Long id, AuthenticatedUser user) {
        CampaignEntity campaign = campaignRepository.findById(Objects.requireNonNull(id, "id"))
                .orElseThrow(() -> new CampaignNotFoundException(id));
        assertCanRead(campaign, user);
        return toDTOConNombre(campaign);
    }

    /**
     * HU14/HU15 — aprobar o rechazar una campaña.
     * Al rechazar, feedback es obligatorio (10-500 chars).
     * JPA lanza ObjectOptimisticLockingFailureException si la versión no coincide.
     */
    @Transactional
    public CampaignResponseDTO updateStatus(
            Long id,
            String newStatus,
            String feedback,
            Integer valoracion,
            Integer requestVersion,
            AuthenticatedUser user) {
        CampaignEntity campaign = campaignRepository.findById(Objects.requireNonNull(id, "id"))
                .orElseThrow(() -> new CampaignNotFoundException(id));
        assertClientOwns(campaign, user);

        if (!Objects.equals(campaign.getVersion(), requestVersion)) {
            throw new IllegalArgumentException("La campaña cambió desde que la abriste. Recarga e intenta nuevamente.");
        }

        if (valoracion == null || valoracion < 1 || valoracion > 5) {
            throw new IllegalArgumentException("La valoración es obligatoria y debe estar entre 1 y 5.");
        }

        Set<String> allowed = ALLOWED_TRANSITIONS.getOrDefault(campaign.getEstado(), Set.of());
        if (!allowed.contains(newStatus)) {
            throw new InvalidStatusTransitionException(campaign.getEstado(), newStatus);
        }

        String finalStatus = newStatus;
        if ("rechazado".equals(newStatus)) {
            if (feedback == null || feedback.isBlank()
                    || feedback.strip().length() < 10 || feedback.strip().length() > 500) {
                throw new IllegalArgumentException(
                        "El feedback de rechazo es obligatorio (entre 10 y 500 caracteres)."
                );
            }
            campaign.setFeedbackRechazo(feedback.strip());
            int rechazos = campaign.getRechazosClienteCount() == null
                    ? 1
                    : campaign.getRechazosClienteCount() + 1;
            campaign.setRechazosClienteCount((short) rechazos);
            if (rechazos >= 2) {
                finalStatus = "fracaso";
            }
        }

        campaign.setEstado(finalStatus);
        campaign.setClienteValoracion(valoracion.shortValue());
        campaign.setClienteValoracionAt(OffsetDateTime.now());
        CampaignEntity saved = campaignRepository.save(campaign);

        // Delivered after transaction commit; rolled-back changes never reach sockets.
        eventPublisher.publishEvent(new ClientCampaignEvent(
                "campaign_status_changed", saved.getId(), saved.getClienteEmail()));

        // Email must follow the same committed decision as the socket notification.
        // No notification is issued if JPA flush/optimistic locking rolls back.
        String committedStatus = finalStatus;
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                try {
                    n8nEmailClient.notify(saved, committedStatus);
                } catch (RuntimeException ex) {
                    log.warn("No se pudo notificar la decisión confirmada de campaña {}", saved.getId());
                }
                // Aprobada: Django publica en las cuentas que eligió el marketero.
                if ("aprobado".equals(committedStatus)) {
                    djangoEventClient.notifyApprovedAsync(saved.getId());
                }
            }
        });

        return toDTOConNombre(saved);
    }

    private Page<CampaignResponseDTO> withMarketerNames(Page<CampaignEntity> page) {
        Map<Long, String> nombres = nombresPorId(
                page.getContent().stream()
                        .map(campaign -> campaign.getMarketeroId())
                        .filter(Objects::nonNull)
                        .collect(Collectors.toSet()));
        Map<Long, List<DestinoDTO>> destinos = destinosPorCampana(
                page.getContent().stream().map(campaign -> campaign.getId()).collect(Collectors.toSet()));
        return page.map(e -> toDTO(e, nombres.get(e.getMarketeroId()), destinos.getOrDefault(e.getId(), List.of())));
    }

    private String authenticatedEmail(AuthenticatedUser user) {
        return userRepository.findById(user.userId())
                .map(entity -> entity.getEmail())
                .orElseThrow(() -> new AccessDeniedException("Usuario autenticado no encontrado."));
    }

    private void assertCanRead(CampaignEntity campaign, AuthenticatedUser user) {
        if ("cliente".equals(user.role())) {
            assertClientOwns(campaign, user);
        }
    }

    private void assertClientOwns(CampaignEntity campaign, AuthenticatedUser user) {
        String email = authenticatedEmail(user);
        if (campaign.getClienteEmail() == null
                || !campaign.getClienteEmail().equalsIgnoreCase(email)) {
            throw new AccessDeniedException("No tienes acceso a esta campaña.");
        }
    }

    private String clean(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.strip();
    }

    private String cleanLower(String value) {
        String cleaned = clean(value);
        return cleaned == null ? null : cleaned.toLowerCase();
    }

    private Set<Long> marketeroIdsForQuery(String q) {
        if (q == null) {
            return Set.of();
        }
        return userRepository.findByNombreContainingIgnoreCase(q).stream()
                .map(entity -> entity.getId())
                .collect(Collectors.toSet());
    }

    /**
     * Resuelve los nombres de marketero para un conjunto de ids en un solo
     * query (findAllById). Lectura pura sobre la tabla users de Django.
     */
    private Map<Long, String> nombresPorId(Set<Long> ids) {
        if (ids.isEmpty()) {
            return Map.of();
        }
        List<UserEntity> users = userRepository.findAllById(ids);
        return users.stream()
                .collect(Collectors.toMap(entity -> entity.getId(), entity -> entity.getNombre()));
    }

    /** Variante para flujos de UNA campaña (detalle, updateStatus). */
    private CampaignResponseDTO toDTOConNombre(CampaignEntity e) {
        Long marketeroId = e.getMarketeroId();
        String nombre = marketeroId == null
                ? null
                : userRepository.findById(marketeroId)
                        .map(entity -> entity.getNombre())
                        .orElse(null);
        List<DestinoDTO> destinos = destinosPorCampana(Set.of(e.getId())).getOrDefault(e.getId(), List.of());
        return toDTO(e, nombre, destinos);
    }

    /** Destinos de publicación de varias campañas en un solo query (lectura de tabla de Django). */
    private Map<Long, List<DestinoDTO>> destinosPorCampana(Collection<Long> campaignIds) {
        if (campaignIds.isEmpty()) {
            return Map.of();
        }
        return publicationViewRepository.findByCampaignIdIn(campaignIds).stream()
                .collect(Collectors.groupingBy(
                        publication -> publication.getCampaignId(),
                        Collectors.mapping(publication -> DestinoDTO.builder()
                                .red(publication.getRed())
                                .cuentaNombre(publication.getCuentaNombre())
                                .estado(publication.getEstado())
                                .permalink(publication.getPermalink())
                                .build(), Collectors.toList())));
    }

    private CampaignResponseDTO toDTO(CampaignEntity e, String marketeroNombre, List<DestinoDTO> destinos) {
        return CampaignResponseDTO.builder()
                .id(e.getId())
                .titulo(e.getTitulo())
                .clienteNombre(e.getClienteNombre())
                .clienteEmail(e.getClienteEmail())
                .industria(e.getIndustria())
                .tono(e.getTono())
                .plataforma(e.getPlataforma())
                .prompt(e.getPrompt())
                .textoGenerado(e.getTextoGenerado())
                .imagenUrl(e.getImagenUrl())
                .imagenB64(e.getImagenB64())
                .tokensConsumidos(e.getTokensConsumidos())
                .intentosGeneracion(e.getIntentosGeneracion())
                .estado(e.getEstado())
                .feedbackRechazo(e.getFeedbackRechazo())
                .clienteValoracion(e.getClienteValoracion() == null ? null : e.getClienteValoracion().intValue())
                .clienteValoracionAt(e.getClienteValoracionAt())
                .rechazosClienteCount(e.getRechazosClienteCount() == null ? null : e.getRechazosClienteCount().intValue())
                .marketeroId(e.getMarketeroId())
                .marketeroNombre(marketeroNombre)
                .fechaCreacion(e.getFechaCreacion())
                .fechaActualizacion(e.getFechaActualizacion())
                .enviadoClienteAt(e.getEnviadoClienteAt())
                .version(e.getVersion())
                .destinos(destinos)
                .build();
    }
}
