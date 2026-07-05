package com.marketmind.service;

import com.marketmind.dto.CampaignResponseDTO;
import com.marketmind.entity.CampaignEntity;
import com.marketmind.entity.UserEntity;
import com.marketmind.exception.CampaignNotFoundException;
import com.marketmind.exception.InvalidStatusTransitionException;
import com.marketmind.repository.CampaignRepository;
import com.marketmind.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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
public class CampaignService {

    private static final Map<String, Set<String>> ALLOWED_TRANSITIONS = Map.of(
            "pendiente_aprobacion", Set.of("aprobado", "rechazado")
    );

    private final CampaignRepository campaignRepository;
    private final UserRepository userRepository;
    private final N8nEmailClient n8nEmailClient;

    /** HU12 — lista todas las campañas pendientes de aprobación. */
    public Page<CampaignResponseDTO> findPending(Pageable pageable) {
        Page<CampaignEntity> page = campaignRepository
                .findByEstado("pendiente_aprobacion", pageable);
        // Nombres de marketero resueltos en UN solo query (sin N+1 por fila)
        Map<Long, String> nombres = nombresPorId(
                page.getContent().stream()
                        .map(CampaignEntity::getMarketeroId)
                        .filter(Objects::nonNull)
                        .collect(Collectors.toSet()));
        return page.map(e -> toDTO(e, nombres.get(e.getMarketeroId())));
    }

    /**
     * Dashboard cliente — conteos por estado para las stat cards.
     * Solo lectura (COUNT), respeta la regla políglota: Spring nunca escribe
     * más allá del campo estado.
     */
    public Map<String, Long> getSummary() {
        return Map.of(
                "pendientes", campaignRepository.countByEstado("pendiente_aprobacion"),
                "aprobadas", campaignRepository.countByEstado("aprobado"),
                "rechazadas", campaignRepository.countByEstado("rechazado")
        );
    }

    /** HU13 — detalle de campaña por id. */
    public CampaignResponseDTO findById(Long id) {
        return campaignRepository.findById(id)
                .map(this::toDTOConNombre)
                .orElseThrow(() -> new CampaignNotFoundException(id));
    }

    /**
     * HU14/HU15 — aprobar o rechazar una campaña.
     * Al rechazar, feedback es obligatorio (10-500 chars).
     * JPA lanza ObjectOptimisticLockingFailureException si la versión no coincide.
     */
    @Transactional
    public CampaignResponseDTO updateStatus(Long id, String newStatus, String feedback) {
        CampaignEntity campaign = campaignRepository.findById(id)
                .orElseThrow(() -> new CampaignNotFoundException(id));

        Set<String> allowed = ALLOWED_TRANSITIONS.getOrDefault(campaign.getEstado(), Set.of());
        if (!allowed.contains(newStatus)) {
            throw new InvalidStatusTransitionException(campaign.getEstado(), newStatus);
        }

        if ("rechazado".equals(newStatus)) {
            if (feedback == null || feedback.isBlank()
                    || feedback.strip().length() < 10 || feedback.strip().length() > 500) {
                throw new IllegalArgumentException(
                        "El feedback de rechazo es obligatorio (entre 10 y 500 caracteres)."
                );
            }
            campaign.setFeedbackRechazo(feedback.strip());
        }

        campaign.setEstado(newStatus);
        CampaignEntity saved = campaignRepository.save(campaign);

        // HU17 — notificar al marketero vía n8n + Resend.
        // Fire-and-forget interno (N8nEmailClient absorbe excepciones);
        // si el HTTP demora, agregamos hasta N8N_WEBHOOK_TIMEOUT a la respuesta.
        n8nEmailClient.notify(saved, newStatus);

        return toDTOConNombre(saved);
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
                .marketeroId(e.getMarketeroId())
                .marketeroNombre(marketeroNombre)
                .fechaCreacion(e.getFechaCreacion())
                .fechaActualizacion(e.getFechaActualizacion())
                .version(e.getVersion())
                .build();
    }
}
