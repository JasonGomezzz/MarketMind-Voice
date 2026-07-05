package com.marketmind.repository;

import com.marketmind.entity.CampaignEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CampaignRepository extends JpaRepository<CampaignEntity, Long> {

    /** HU12 — campañas pendientes de aprobación (todas, sin filtro por usuario). */
    Page<CampaignEntity> findByEstado(String estado, Pageable pageable);

    /** Dashboard cliente — conteo de campañas por estado. */
    long countByEstado(String estado);
}
