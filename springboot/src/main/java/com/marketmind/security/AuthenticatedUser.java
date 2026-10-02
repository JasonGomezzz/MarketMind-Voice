package com.marketmind.security;

import org.springframework.lang.NonNull;

/**
 * Claims extraídos del JWT de Django tras validación exitosa.
 * tokenVersion viaja en el payload (HU18): se compara contra la BD en el
 * filtro para invalidar tokens de usuarios suspendidos/reactivados.
 */
public record AuthenticatedUser(@NonNull Long userId, String role, String nombre, Integer tokenVersion) {}
