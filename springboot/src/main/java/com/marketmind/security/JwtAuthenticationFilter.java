package com.marketmind.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

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
    private final CurrentUserVerifier currentUserVerifier;

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain) throws ServletException, IOException {

        String authHeader = request.getHeader("Authorization");

        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            jwtTokenValidator.validateAndExtract(token)
                    .filter(user -> currentUserVerifier.findCurrent(user).isPresent())
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

}
