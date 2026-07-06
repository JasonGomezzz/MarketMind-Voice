package com.marketmind.controller;

import com.marketmind.dto.ApiResponse;
import com.marketmind.dto.CampaignResponseDTO;
import com.marketmind.dto.StatusUpdateRequest;
import com.marketmind.security.AuthenticatedUser;
import com.marketmind.service.CampaignService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/campaigns")
@RequiredArgsConstructor
public class CampaignController {

    private final CampaignService campaignService;

    /**
     * HU12 — Lista campañas pendientes de aprobación.
     * Acceso: solo rol CLIENTE.
     */
    @GetMapping("/pending")
    @PreAuthorize("hasRole('CLIENTE')")
    public ResponseEntity<ApiResponse<Page<CampaignResponseDTO>>> getPending(
            Pageable pageable,
            @AuthenticationPrincipal AuthenticatedUser user) {
        Page<CampaignResponseDTO> page = campaignService.findPending(user, pageable);
        return ResponseEntity.ok(ApiResponse.ok("Campañas pendientes de aprobación.", page));
    }

    @GetMapping("/mine")
    @PreAuthorize("hasRole('CLIENTE')")
    public ResponseEntity<ApiResponse<Page<CampaignResponseDTO>>> getMine(
            Pageable pageable,
            @AuthenticationPrincipal AuthenticatedUser user,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String estado,
            @RequestParam(required = false) String industria,
            @RequestParam(required = false) String plataforma,
            @RequestParam(required = false) Integer valoracion) {
        Page<CampaignResponseDTO> page = campaignService.findMine(
                user, q, estado, industria, plataforma, valoracion, pageable);
        return ResponseEntity.ok(ApiResponse.ok("Campañas del cliente.", page));
    }

    /**
     * Dashboard cliente — conteos de campañas por estado (pendientes/aprobadas/rechazadas).
     * Acceso: solo rol CLIENTE.
     */
    @GetMapping("/summary")
    @PreAuthorize("hasRole('CLIENTE')")
    public ResponseEntity<ApiResponse<java.util.Map<String, Long>>> getSummary(
            @AuthenticationPrincipal AuthenticatedUser user) {
        return ResponseEntity.ok(ApiResponse.ok("Resumen de campañas.", campaignService.getSummary(user)));
    }

    /**
     * HU13 — Detalle de campaña.
     * Acceso: cualquier usuario autenticado.
     */
    @GetMapping("/{id}")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<ApiResponse<CampaignResponseDTO>> getById(
            @PathVariable Long id,
            @AuthenticationPrincipal AuthenticatedUser user) {
        return ResponseEntity.ok(ApiResponse.ok("Campaña obtenida.", campaignService.findById(id, user)));
    }

    /**
     * HU14 — Aprobar o rechazar campaña.
     * Acceso: CLIENTE o SUPERADMIN.
     * El campo version del request es usado por JPA @Version para detectar conflictos.
     */
    @PatchMapping("/{id}/status")
    @PreAuthorize("hasAnyRole('CLIENTE', 'SUPERADMIN')")
    public ResponseEntity<ApiResponse<CampaignResponseDTO>> updateStatus(
            @PathVariable Long id,
            @RequestBody @Valid StatusUpdateRequest request,
            @AuthenticationPrincipal AuthenticatedUser user) {

        CampaignResponseDTO dto = campaignService.updateStatus(
                id,
                request.getEstado(),
                request.getFeedback(),
                request.getValoracion(),
                request.getVersion(),
                user);
        return ResponseEntity.ok(ApiResponse.ok("Estado de campaña actualizado.", dto));
    }
}
