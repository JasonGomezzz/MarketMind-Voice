package com.marketmind.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Optional;

/**
 * Valida JWT emitidos por Django simplejwt.
 * Algoritmo: HS256. Clave: SECRET_KEY bytes (igual que Django).
 * sub = PK entero del usuario como string (simplejwt default).
 * claim "role" = valor del campo 'rol' del User (minúsculas).
 * Spring Boot NUNCA emite tokens — solo valida.
 */
@Component
public class JwtTokenValidator {

    private final SecretKey signingKey;

    public JwtTokenValidator(@Value("${app.jwt.secret}") String secretKey) {
        this.signingKey = Keys.hmacShaKeyFor(secretKey.getBytes(StandardCharsets.UTF_8));
    }

    public Optional<AuthenticatedUser> validateAndExtract(String token) {
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(signingKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();

            Long userId = Long.parseLong(claims.getSubject());
            String role = claims.get("role", String.class);
            String nombre = claims.get("nombre", String.class);

            return Optional.of(new AuthenticatedUser(userId, role, nombre));

        } catch (JwtException | IllegalArgumentException e) {
            return Optional.empty();
        }
    }
}
