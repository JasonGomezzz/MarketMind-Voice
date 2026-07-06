package com.marketmind.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import lombok.NoArgsConstructor;

/** Body para PATCH /api/v1/campaigns/{id}/status */
@Data
@NoArgsConstructor
public class StatusUpdateRequest {

    @NotBlank(message = "El estado es obligatorio.")
    private String estado;

    @NotNull(message = "La versión es obligatoria para prevenir conflictos concurrentes.")
    private Integer version;

    @NotNull(message = "La valoración es obligatoria.")
    private Integer valoracion;

    // Sin @NotBlank — validación cross-field en el service (solo requerido cuando estado="rechazado")
    private String feedback;
}
