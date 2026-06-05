package com.marketmind.repository;

import com.marketmind.entity.UserEntity;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * Repositorio de solo lectura para UserEntity.
 * Usado por N8nEmailClient (HU17) para obtener email + nombre del marketero
 * a partir de campaign.marketero_id antes de notificar a n8n.
 */
public interface UserRepository extends JpaRepository<UserEntity, Long> {
}
