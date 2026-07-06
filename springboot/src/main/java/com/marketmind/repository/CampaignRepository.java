package com.marketmind.repository;

import com.marketmind.entity.CampaignEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface CampaignRepository extends JpaRepository<CampaignEntity, Long> {

    /** HU12 — campañas pendientes de aprobación (todas, sin filtro por usuario). */
    @Query("""
            select c
            from CampaignEntity c
            where c.estado = :estado
            order by coalesce(c.enviadoClienteAt, c.fechaActualizacion, c.fechaCreacion) desc
            """)
    Page<CampaignEntity> findPendingOrdered(@Param("estado") String estado, Pageable pageable);

    /** Dashboard cliente — conteo de campañas por estado. */
    long countByEstado(String estado);
}
