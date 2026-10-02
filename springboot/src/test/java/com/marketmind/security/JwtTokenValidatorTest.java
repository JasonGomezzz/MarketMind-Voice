package com.marketmind.security;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.JwtBuilder;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

class JwtTokenValidatorTest {

    private static final String SECRET = "test-secret-key-with-at-least-32-bytes";
    private JwtTokenValidator validator;
    private SecretKey signingKey;

    @BeforeEach
    void setUp() {
        validator = new JwtTokenValidator(SECRET);
        signingKey = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));
    }

    @Test
    void extractsAuthenticatedUserFromValidToken() {
        String token = accessToken()
                .claim("user_id", 42)
                .claim("role", "cliente")
                .claim("nombre", "Ada")
                .claim("token_version", 3)
                .signWith(signingKey)
                .compact();

        Optional<AuthenticatedUser> result = validator.validateAndExtract(token);

        assertTrue(result.isPresent());
        assertEquals(new AuthenticatedUser(42L, "cliente", "Ada", 3), result.get());
    }

    @Test
    void acceptsTokenWithoutOptionalClaims() {
        String token = accessToken()
                .claim("user_id", 7)
                .signWith(signingKey)
                .compact();

        Optional<AuthenticatedUser> result = validator.validateAndExtract(token);

        assertEquals(Optional.of(new AuthenticatedUser(7L, "cliente", null, null)), result);
    }

    @Test
    void rejectsTokenWithoutUserId() {
        String token = accessToken()
                .claim("user_id", null)
                .claim("role", "cliente")
                .signWith(signingKey)
                .compact();

        assertTrue(validator.validateAndExtract(token).isEmpty());
    }

    @Test
    void rejectsMalformedToken() {
        assertTrue(validator.validateAndExtract("not-a-jwt").isEmpty());
    }

    @Test
    void rejectsTokenSignedWithAnotherKey() {
        SecretKey otherKey = Keys.hmacShaKeyFor("another-secret-key-with-at-least-32-bytes".getBytes(StandardCharsets.UTF_8));
        String token = accessToken()
                .claim("user_id", 42)
                .signWith(otherKey)
                .compact();

        assertTrue(validator.validateAndExtract(token).isEmpty());
    }

    @Test
    void rejectsRefreshTokenAsBearerCredential() {
        String token = accessToken()
                .claim("token_type", "refresh")
                .signWith(signingKey)
                .compact();

        assertTrue(validator.validateAndExtract(token).isEmpty());
    }

    @Test
    void rejectsTokenWithoutType() {
        String token = accessToken()
                .claim("token_type", null)
                .signWith(signingKey)
                .compact();

        assertTrue(validator.validateAndExtract(token).isEmpty());
    }

    @ParameterizedTest
    @NullAndEmptySource
    @ValueSource(strings = {" ", "admin", "CLIENTE"})
    void rejectsMissingOrInvalidRole(String role) {
        String token = accessToken()
                .claim("role", role)
                .signWith(signingKey)
                .compact();

        assertTrue(validator.validateAndExtract(token).isEmpty());
    }

    @ParameterizedTest
    @ValueSource(strings = {"superadmin", "marketero", "cliente"})
    void acceptsEachDjangoRole(String role) {
        String token = accessToken()
                .claim("role", role)
                .signWith(signingKey)
                .compact();

        assertEquals(role, validator.validateAndExtract(token).orElseThrow().role());
    }

    @ParameterizedTest
    @ValueSource(longs = {0, -1})
    void rejectsNonPositiveUserId(long userId) {
        String token = accessToken()
                .claim("user_id", userId)
                .signWith(signingKey)
                .compact();

        assertTrue(validator.validateAndExtract(token).isEmpty());
    }

    @Test
    void rejectsFractionalUserId() {
        String token = accessToken()
                .claim("user_id", 42.5)
                .signWith(signingKey)
                .compact();

        assertTrue(validator.validateAndExtract(token).isEmpty());
    }

    @Test
    void rejectsExpiredAccessToken() {
        String token = accessToken()
                .expiration(Date.from(Instant.now().minusSeconds(60)))
                .signWith(signingKey)
                .compact();

        assertTrue(validator.validateAndExtract(token).isEmpty());
    }

    private JwtBuilder accessToken() {
        return Jwts.builder()
                .claim("user_id", 42)
                .claim("role", "cliente")
                .claim("token_type", "access")
                .expiration(Date.from(Instant.now().plusSeconds(300)));
    }
}
