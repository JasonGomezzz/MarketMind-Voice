package com.marketmind.repository;

import com.marketmind.entity.CampaignEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Set;

public interface CampaignRepository extends JpaRepository<CampaignEntity, Long> {

    /** HU12 — campañas pendientes de aprobación filtradas por cliente. */
    @Query("""
            select c
            from CampaignEntity c
            where c.estado = :estado
              and lower(c.clienteEmail) = lower(:clienteEmail)
            order by coalesce(c.enviadoClienteAt, c.fechaActualizacion, c.fechaCreacion) desc
            """)
    Page<CampaignEntity> findPendingOrdered(
            @Param("estado") String estado,
            @Param("clienteEmail") String clienteEmail,
            Pageable pageable);

    @Query("""
            select c
            from CampaignEntity c
            where lower(c.clienteEmail) = lower(:clienteEmail)
              and (:estado is null or c.estado = :estado)
              and (:industria is null or c.industria = :industria)
              and (:plataforma is null or c.plataforma = :plataforma)
              and (:valoracion is null or c.clienteValoracion = :valoracion)
              and (
                :hasQ = false
                or lower(c.titulo) like concat('%', :q, '%')
                or lower(c.textoGenerado) like concat('%', :q, '%')
                or lower(c.industria) like concat('%', :q, '%')
                or lower(c.plataforma) like concat('%', :q, '%')
                or (:hasMarketeroIds = true and c.marketeroId in :marketeroIds)
              )
            order by coalesce(c.enviadoClienteAt, c.fechaActualizacion, c.fechaCreacion) desc
            """)
    Page<CampaignEntity> findMine(
            @Param("clienteEmail") String clienteEmail,
            @Param("q") String q,
            @Param("hasQ") boolean hasQ,
            @Param("estado") String estado,
            @Param("industria") String industria,
            @Param("plataforma") String plataforma,
            @Param("valoracion") Short valoracion,
            @Param("hasMarketeroIds") boolean hasMarketeroIds,
            @Param("marketeroIds") Set<Long> marketeroIds,
            Pageable pageable);

    /** Dashboard cliente — conteo de campañas por estado. */
    long countByEstadoAndClienteEmailIgnoreCase(String estado, String clienteEmail);
}
