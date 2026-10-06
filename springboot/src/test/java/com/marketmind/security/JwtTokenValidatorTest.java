package com.marketmind.security;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.Test;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import static org.junit.jupiter.api.Assertions.*;

class JwtTokenValidatorTest {
    String secret = "test-signing-key-with-more-than-thirty-two-bytes";
    JwtTokenValidator validator = new JwtTokenValidator(secret);
    String token(String type, Instant expiry) {
        return Jwts.builder().claim("user_id", 1).claim("role", "cliente").claim("token_version", 2)
                .claim("token_type", type).expiration(Date.from(expiry))
                .signWith(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8))).compact();
    }
    @Test void acceptsAccessButNotRefreshOrExpiredToken() {
        assertTrue(validator.validateAndExtract(token("access", Instant.now().plusSeconds(60))).isPresent());
        assertTrue(validator.validateAndExtract(token("refresh", Instant.now().plusSeconds(60))).isEmpty());
        assertTrue(validator.validateAndExtract(token("access", Instant.now().minusSeconds(10))).isEmpty());
        assertTrue(validator.validateAndExtract("invalid").isEmpty());
    }
}
