package com.marketmind.security;

import com.marketmind.entity.UserEntity;
import com.marketmind.repository.UserRepository;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;
import java.util.Objects;

/**
 * Lee el JWT del header Authorization, lo valida y puebla el SecurityContext.
 * Roles Django (minúsculas) → Spring Security ROLE_<MAYÚSCULAS>.
 *
 * Además de la firma, verifica contra la BD (HU18 — misma garantía que Django):
 * el usuario debe existir, estar activo y su token_version debe coincidir con
 * el claim. Sin esto, un usuario suspendido seguiría operando en :8080 hasta
 * que su token expirara.
 */
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenValidator jwtTokenValidator;
    private final UserRepository userRepository;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        String authHeader = request.getHeader("Authorization");

        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            jwtTokenValidator.validateAndExtract(token)
                    .filter(this::isVigenteEnBd)
                    .ifPresent(user -> {
                        var authority = new SimpleGrantedAuthority("ROLE_" + user.role().toUpperCase());
                        var authentication = new UsernamePasswordAuthenticationToken(
                                user, null, List.of(authority)
                        );
                        authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                        SecurityContextHolder.getContext().setAuthentication(authentication);
                    });
        }

        filterChain.doFilter(request, response);
    }

    /**
     * Verificación HU18 contra la tabla users (solo lectura):
     * usuario existente + activo + token_version del JWT vigente.
     */
    private boolean isVigenteEnBd(AuthenticatedUser user) {
        return userRepository.findById(user.userId())
                .map(entity -> Boolean.TRUE.equals(entity.getIsActive())
                        && tokenVersionVigente(user, entity))
                .orElse(false);
    }

    private boolean tokenVersionVigente(AuthenticatedUser user, UserEntity entity) {
        // Tokens antiguos sin el claim se rechazan solo si la BD ya versionó (>0).
        Integer enBd = entity.getTokenVersion();
        Integer enJwt = user.tokenVersion();
        if (enJwt == null) {
            return enBd == null || enBd == 0;
        }
        return Objects.equals(enBd, enJwt);
    }
}
