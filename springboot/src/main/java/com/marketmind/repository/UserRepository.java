package com.marketmind.repository;

import com.marketmind.entity.UserEntity;
import com.marketmind.security.CurrentUserSnapshot;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

/**
 * Repositorio de solo lectura para UserEntity.
 * Usado por N8nEmailClient (HU17) para obtener email + nombre del marketero
 * a partir de campaign.marketero_id antes de notificar a n8n.
 */
public interface UserRepository extends JpaRepository<UserEntity, Long> {
    @Query("select new com.marketmind.security.CurrentUserSnapshot(u.email, u.rol, u.isActive, u.tokenVersion) "
            + "from UserEntity u where u.id = :id")
    Optional<CurrentUserSnapshot> findCurrentSnapshotById(@Param("id") Long id);

    Optional<UserEntity> findByEmail(String email);

    List<UserEntity> findByNombreContainingIgnoreCase(String nombre);
}
