package com.marketmind.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Version;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

/**
 * Mapeo de la tabla campaigns (db_table de Django).
 * Spring Boot solo escribe el campo 'estado' (aprobar/rechazar).
 * El campo 'version' es gestionado por JPA @Version para optimistic locking.
 * Django es dueño de todas las demás columnas.
 */
@Entity
@Table(name = "campaigns")
@Getter
@NoArgsConstructor
public class CampaignEntity {

    @Id
    @Column(name = "id", updatable = false, nullable = false)
    private Long id;

    @Column(name = "titulo", updatable = false, nullable = false)
    private String titulo;

    @Column(name = "cliente_nombre", updatable = false, nullable = false)
    private String clienteNombre;

    @Column(name = "cliente_email", updatable = false)
    private String clienteEmail;

    @Column(name = "industria", updatable = false, nullable = false)
    private String industria;

    @Column(name = "tono", updatable = false)
    private String tono;

    @Column(name = "plataforma", updatable = false)
    private String plataforma;

    @Column(name = "prompt", updatable = false)
    private String prompt;

    @Column(name = "texto_generado", updatable = false)
    private String textoGenerado;

    @org.hibernate.annotations.JdbcTypeCode(org.hibernate.type.SqlTypes.JSON)
    @Column(name = "textos_por_plataforma", updatable = false, columnDefinition = "jsonb")
    private java.util.Map<String, String> textosPorPlataforma;

    @Column(name = "imagen_url", updatable = false)
    private String imagenUrl;

    @Column(name = "imagen_b64", updatable = false)
    private String imagenB64;

    @Column(name = "n8n_callback_token", columnDefinition = "uuid", updatable = false)
    private java.util.UUID n8nCallbackToken;

    @Column(name = "tokens_consumidos", updatable = false)
    private Integer tokensConsumidos;

    @Column(name = "intentos_generacion", updatable = false)
    private Integer intentosGeneracion;

    @Column(name = "ia_error_message", updatable = false)
    private String iaErrorMessage;

    @Column(name = "feedback_rechazo")
    private String feedbackRechazo;

    @Column(name = "cliente_valoracion")
    private Short clienteValoracion;

    @Column(name = "cliente_valoracion_at")
    private OffsetDateTime clienteValoracionAt;

    // Short porque Django creó la columna como PositiveSmallIntegerField
    // (smallint) — con Integer, Hibernate falla validando el esquema.
    @Column(name = "rechazos_cliente_count")
    private Short rechazosClienteCount;

    // Campos que Spring Boot puede escribir (estado + feedbackRechazo al rechazar)
    @Column(name = "estado", nullable = false)
    private String estado;

    @Column(name = "marketero_id", updatable = false, nullable = false)
    private Long marketeroId;

    @Column(name = "fecha_creacion", updatable = false)
    private OffsetDateTime fechaCreacion;

    @Column(name = "fecha_actualizacion", updatable = false)
    private OffsetDateTime fechaActualizacion;

    @Column(name = "enviado_cliente_at", updatable = false)
    private OffsetDateTime enviadoClienteAt;

    // @Version: JPA emite UPDATE ... SET estado=?, version=version+1 WHERE id=? AND version=?
    // Si la versión no coincide → ObjectOptimisticLockingFailureException
    @Version
    @Column(name = "version", nullable = false)
    private Integer version;

    public void setEstado(String estado) {
        this.estado = estado;
    }

    public void setFeedbackRechazo(String feedbackRechazo) {
        this.feedbackRechazo = feedbackRechazo;
    }

    public void setClienteValoracion(Short clienteValoracion) {
        this.clienteValoracion = clienteValoracion;
    }

    public void setClienteValoracionAt(OffsetDateTime clienteValoracionAt) {
        this.clienteValoracionAt = clienteValoracionAt;
    }

    public void setRechazosClienteCount(Short rechazosClienteCount) {
        this.rechazosClienteCount = rechazosClienteCount;
    }
}
