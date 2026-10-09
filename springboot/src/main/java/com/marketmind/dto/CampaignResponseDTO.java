package com.marketmind.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

/**
 * DTO de respuesta para campañas.
 * Excluye campos internos: n8nCallbackToken, iaErrorMessage, password.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CampaignResponseDTO {

    private Long id;
    private String titulo;
    private String clienteNombre;
    private String clienteEmail;
    private String industria;
    private String tono;
    private String plataforma;
    private String prompt;
    private String textoGenerado;
    private java.util.Map<String, String> textosPorPlataforma;
    private String imagenUrl;
    private String imagenB64;
    private Integer tokensConsumidos;
    private Integer intentosGeneracion;
    private String estado;
    private String feedbackRechazo;
    private Integer clienteValoracion;
    private OffsetDateTime clienteValoracionAt;
    private Integer rechazosClienteCount;
    private Long marketeroId;
    private String marketeroNombre;
    private OffsetDateTime fechaCreacion;
    private OffsetDateTime fechaActualizacion;
    private OffsetDateTime enviadoClienteAt;
    private Integer version;
}
