package com.marketmind.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.marketmind.dto.CampaignResponseDTO;
import com.marketmind.entity.CampaignEntity;
import com.marketmind.entity.UserEntity;
import com.marketmind.exception.CampaignNotFoundException;
import com.marketmind.exception.InvalidStatusTransitionException;
import com.marketmind.repository.CampaignRepository;
import com.marketmind.repository.UserRepository;
import com.marketmind.security.AuthenticatedUser;
import com.marketmind.websocket.ClientCampaignWebSocketHandler;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
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
    private final ClientCampaignWebSocketHandler webSocketHandler;
    private final ObjectMapper objectMapper;

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
        return campaignRepository.findById(id)
                .map(this::toDTOConNombre)
                .orElseThrow(() -> new CampaignNotFoundException(id));
    }

    /** HU13 — detalle de campaña por id con control de acceso para usuarios finales. */
    public CampaignResponseDTO findById(Long id, AuthenticatedUser user) {
        CampaignEntity campaign = campaignRepository.findById(id)
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
        CampaignEntity campaign = campaignRepository.findById(id)
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

        // Dashboard de cliente en vivo — mismo canal WS que ya usa
        // InternalCampaignEventController para "campaign_submitted".
        // Fire-and-forget, misma convención que n8nEmailClient.notify() abajo.
        broadcastStatusChanged(saved);

        // HU17 — notificar al marketero vía n8n + Resend.
        // Fire-and-forget interno (N8nEmailClient absorbe excepciones);
        // si el HTTP demora, agregamos hasta N8N_WEBHOOK_TIMEOUT a la respuesta.
        n8nEmailClient.notify(saved, finalStatus);

        return toDTOConNombre(saved);
    }

    private void broadcastStatusChanged(CampaignEntity saved) {
        try {
            String payload = objectMapper.writeValueAsString(Map.of(
                    "type", "campaign_status_changed",
                    "campaign", toDTOConNombre(saved)
            ));
            webSocketHandler.sendToClient(saved.getClienteEmail(), payload);
        } catch (JsonProcessingException e) {
            log.warn("No se pudo serializar el evento campaign_status_changed para campaña {}", saved.getId(), e);
        }
    }

    private Page<CampaignResponseDTO> withMarketerNames(Page<CampaignEntity> page) {
        Map<Long, String> nombres = nombresPorId(
                page.getContent().stream()
                        .map(CampaignEntity::getMarketeroId)
                        .filter(Objects::nonNull)
                        .collect(Collectors.toSet()));
        return page.map(e -> toDTO(e, nombres.get(e.getMarketeroId())));
    }

    private String authenticatedEmail(AuthenticatedUser user) {
        return userRepository.findById(user.userId())
                .map(UserEntity::getEmail)
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
                .map(UserEntity::getId)
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
                .collect(Collectors.toMap(UserEntity::getId, UserEntity::getNombre));
    }

    /** Variante para flujos de UNA campaña (detalle, updateStatus). */
    private CampaignResponseDTO toDTOConNombre(CampaignEntity e) {
        String nombre = e.getMarketeroId() == null
                ? null
                : userRepository.findById(e.getMarketeroId())
                        .map(UserEntity::getNombre)
                        .orElse(null);
        return toDTO(e, nombre);
    }

    private CampaignResponseDTO toDTO(CampaignEntity e, String marketeroNombre) {
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
                .textosPorPlataforma(e.getTextosPorPlataforma())
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
                .build();
    }
}
