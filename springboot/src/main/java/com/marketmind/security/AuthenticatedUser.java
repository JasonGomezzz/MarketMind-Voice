package com.marketmind.security;

/**
 * Claims extraídos del JWT de Django tras validación exitosa.
 * tokenVersion viaja en el payload (HU18): se compara contra la BD en el
 * filtro para invalidar tokens de usuarios suspendidos/reactivados.
 */
public record AuthenticatedUser(Long userId, String role, String nombre, Integer tokenVersion) {}
