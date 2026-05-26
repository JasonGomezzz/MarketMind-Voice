package com.marketmind.security;

/** Claims extraídos del JWT de Django tras validación exitosa. */
public record AuthenticatedUser(Long userId, String role, String nombre) {}
