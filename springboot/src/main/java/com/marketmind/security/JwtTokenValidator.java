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
import java.time.Instant;
import java.util.Set;

/**
 * Valida JWT emitidos por Django simplejwt.
 * Algoritmo: HS256. Clave: SECRET_KEY bytes (igual que Django).
 * claim "user_id" = PK del usuario (simplejwt default; NO usa 'sub').
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
        return validateAccessToken(token).map(ValidatedAccessToken::user);
    }

    public record ValidatedAccessToken(AuthenticatedUser user, Instant expiresAt) {}

    public Optional<ValidatedAccessToken> validateAccessToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(signingKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
            if (!"access".equals(claims.get("token_type", String.class))
                    || claims.getExpiration() == null) return Optional.empty();

            // simplejwt no usa 'sub'; el id va en el claim 'user_id'.
            // Number (no Long) porque JJWT/Jackson puede deserializar como Integer.
            Number userIdClaim = claims.get("user_id", Number.class);
            if (userIdClaim == null) return Optional.empty();
            Long userId = userIdClaim.longValue();
            String role = claims.get("role", String.class);
            if (role == null || !Set.of("cliente", "marketero", "superadmin").contains(role)) return Optional.empty();
            String nombre = claims.get("nombre", String.class);
            Number tokenVersionClaim = claims.get("token_version", Number.class);
            Integer tokenVersion = tokenVersionClaim == null ? null : tokenVersionClaim.intValue();

            return Optional.of(new ValidatedAccessToken(
                    new AuthenticatedUser(userId, role, nombre, tokenVersion), claims.getExpiration().toInstant()));

        } catch (JwtException | IllegalArgumentException e) {
            return Optional.empty();
        }
    }
}
