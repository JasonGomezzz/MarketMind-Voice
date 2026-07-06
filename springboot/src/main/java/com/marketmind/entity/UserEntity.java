package com.marketmind.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

/**
 * Mapeo de solo lectura del modelo User de Django.
 * Tabla: users (db_table definido en Django).
 * Spring Boot NUNCA escribe filas en esta tabla.
 */
@Entity
@Table(name = "users")
@Getter
@NoArgsConstructor
public class UserEntity {

    @Id
    @Column(name = "id", updatable = false, nullable = false)
    private Long id;

    @Column(name = "email", updatable = false, nullable = false)
    private String email;

    @Column(name = "nombre", updatable = false, nullable = false)
    private String nombre;

    @Column(name = "rol", updatable = false, nullable = false)
    private String rol;

    @Column(name = "is_active", updatable = false)
    private Boolean isActive;

    @Column(name = "is_staff", updatable = false)
    private Boolean isStaff;

    @Column(name = "tokens_disponibles", updatable = false)
    private Integer tokensDisponibles;

    @Column(name = "token_version", updatable = false)
    private Integer tokenVersion;

    @Column(name = "fecha_creacion", updatable = false)
    private OffsetDateTime fechaCreacion;

    @Column(name = "fecha_actualizacion", updatable = false)
    private OffsetDateTime fechaActualizacion;
}
