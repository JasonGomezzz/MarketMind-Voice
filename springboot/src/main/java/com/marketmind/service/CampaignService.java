package com.marketmind.service;

import com.marketmind.dto.CampaignResponseDTO;
import com.marketmind.entity.CampaignEntity;
import com.marketmind.exception.CampaignNotFoundException;
import com.marketmind.exception.InvalidStatusTransitionException;
import com.marketmind.repository.CampaignRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.Set;

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

    /** HU12 — lista todas las campañas pendientes de aprobación. */
    public Page<CampaignResponseDTO> findPending(Pageable pageable) {
        return campaignRepository
                .findByEstado("pendiente_aprobacion", pageable)
                .map(this::toDTO);
    }

    /** HU13 — detalle de campaña por id. */
    public CampaignResponseDTO findById(Long id) {
        return campaignRepository.findById(id)
                .map(this::toDTO)
                .orElseThrow(() -> new CampaignNotFoundException(id));
    }

    /**
     * HU14 — aprobar o rechazar una campaña.
     * JPA lanza ObjectOptimisticLockingFailureException si la versión no coincide.
     */
    @Transactional
    public CampaignResponseDTO updateStatus(Long id, String newStatus) {
        CampaignEntity campaign = campaignRepository.findById(id)
                .orElseThrow(() -> new CampaignNotFoundException(id));

        Set<String> allowed = ALLOWED_TRANSITIONS.getOrDefault(campaign.getEstado(), Set.of());
        if (!allowed.contains(newStatus)) {
            throw new InvalidStatusTransitionException(campaign.getEstado(), newStatus);
        }

        campaign.setEstado(newStatus);
        return toDTO(campaignRepository.save(campaign));
    }

    private CampaignResponseDTO toDTO(CampaignEntity e) {
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
                .tokensConsumidos(e.getTokensConsumidos())
                .intentosGeneracion(e.getIntentosGeneracion())
                .estado(e.getEstado())
                .marketeroId(e.getMarketeroId())
                .fechaCreacion(e.getFechaCreacion())
                .fechaActualizacion(e.getFechaActualizacion())
                .version(e.getVersion())
                .build();
    }
}
