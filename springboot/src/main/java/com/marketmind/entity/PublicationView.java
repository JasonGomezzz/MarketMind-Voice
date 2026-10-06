package com.marketmind.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Immutable;

/**
 * Lectura de social_publications (tabla de Django). Spring nunca la escribe:
 * solo la usa para mostrar al cliente en qué cuentas se publicará lo que aprueba.
 */
@Entity
@Immutable
@Table(name = "social_publications")
@Getter
@NoArgsConstructor
public class PublicationView {

    @Id
    @Column(name = "id")
    private Long id;

    @Column(name = "campaign_id")
    private Long campaignId;

    @Column(name = "red")
    private String red;

    @Column(name = "cuenta_nombre")
    private String cuentaNombre;

    @Column(name = "estado")
    private String estado;

    @Column(name = "permalink")
    private String permalink;
}
