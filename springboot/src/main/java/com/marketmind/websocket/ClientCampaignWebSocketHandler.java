package com.marketmind.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.marketmind.entity.UserEntity;
import com.marketmind.repository.UserRepository;
import com.marketmind.security.AuthenticatedUser;
import com.marketmind.security.JwtTokenValidator;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;
import org.springframework.web.socket.handler.ConcurrentWebSocketSessionDecorator;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

@RequiredArgsConstructor
@Component
public class ClientCampaignWebSocketHandler extends TextWebSocketHandler {

    private final JwtTokenValidator validator;
    private final UserRepository users;
    private final ObjectMapper mapper;
    private final ConcurrentHashMap<WebSocketSession, Connection> connections = new ConcurrentHashMap<>();
    private final ScheduledExecutorService timers = Executors.newSingleThreadScheduledExecutor(task -> {
        Thread thread = new Thread(task, "client-socket-expiry");
        thread.setDaemon(true);
        return thread;
    });

    private static class Connection {
        final WebSocketSession session;
        AuthenticatedUser user;
        String email;
        Instant expiresAt;
        ScheduledFuture<?> timeout;
        Connection(WebSocketSession session) {
            this.session = new ConcurrentWebSocketSessionDecorator(session, 5000, 4 * 1024 * 1024);
        }
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        session.setTextMessageSizeLimit(8192);
        Connection connection = new Connection(session);
        connections.put(session, connection);
        connection.timeout = timers.schedule(() -> disconnect(session, CloseStatus.POLICY_VIOLATION), 5, TimeUnit.SECONDS);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        disconnect(session, status);
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) {
        Connection connection = connections.get(session);
        if (connection == null) return;
        synchronized (connection) {
            if (connection.user != null || message.getPayloadLength() > 8192) {
                disconnect(session, CloseStatus.POLICY_VIOLATION);
                return;
            }
            try {
                JsonNode frame = mapper.readTree(message.getPayload());
                if (frame == null || !"authenticate".equals(frame.path("type").asText()) || !frame.path("token").isTextual()) {
                    disconnect(session, CloseStatus.POLICY_VIOLATION);
                    return;
                }
                var token = validator.validateAccessToken(frame.path("token").asText()).orElse(null);
                if (token == null || !token.expiresAt().isAfter(Instant.now())) {
                    disconnect(session, CloseStatus.POLICY_VIOLATION);
                    return;
                }
                UserEntity user = users.findById(token.user().userId()).orElse(null);
                if (!isCurrentClient(token.user(), user) || user.getEmail() == null || user.getEmail().isBlank()) {
                    disconnect(session, CloseStatus.POLICY_VIOLATION);
                    return;
                }
                connection.user = token.user();
                connection.email = user.getEmail();
                connection.expiresAt = token.expiresAt();
                connection.timeout.cancel(false);
                connection.timeout = timers.schedule(() -> disconnect(session, CloseStatus.POLICY_VIOLATION),
                        Math.max(1, Duration.between(Instant.now(), token.expiresAt()).toMillis()), TimeUnit.MILLISECONDS);
                connection.session.sendMessage(new TextMessage("{\"type\":\"authenticated\"}"));
            } catch (Exception error) {
                // Never log frames, JWTs, email addresses or parser errors.
                disconnect(session, CloseStatus.POLICY_VIOLATION);
            }
        }
    }

    private boolean isCurrentClient(AuthenticatedUser claims, UserEntity user) {
        int version = claims.tokenVersion() == null ? 0 : claims.tokenVersion();
        int stored = user == null || user.getTokenVersion() == null ? 0 : user.getTokenVersion();
        return user != null && Boolean.TRUE.equals(user.getIsActive())
                && "cliente".equals(claims.role()) && "cliente".equals(user.getRol()) && version == stored;
    }

    public void sendToClient(String clienteEmail, String payload) {
        if (clienteEmail == null || clienteEmail.isBlank()) return;
        connections.forEach((original, connection) -> {
            synchronized (connection) {
                if (connection.user == null) return;
                try {
                    UserEntity user = users.findById(connection.user.userId()).orElse(null);
                    if (!original.isOpen() || !connection.expiresAt.isAfter(Instant.now())
                            || !isCurrentClient(connection.user, user) || !Objects.equals(connection.email, user.getEmail())) {
                        disconnect(original, CloseStatus.POLICY_VIOLATION);
                        return;
                    }
                    if (clienteEmail.strip().equalsIgnoreCase(connection.email)) {
                        connection.session.sendMessage(new TextMessage(payload));
                    }
                } catch (Exception error) {
                    disconnect(original, CloseStatus.SERVER_ERROR);
                }
            }
        });
    }

    private void disconnect(WebSocketSession session, CloseStatus status) {
        Connection connection = connections.get(session);
        if (connection == null) return;
        synchronized (connection) {
            if (!connections.remove(session, connection)) return;
            if (connection.timeout != null) connection.timeout.cancel(false);
            try { session.close(status); } catch (IOException ignored) { /* already closed */ }
        }
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable error) {
        disconnect(session, CloseStatus.SERVER_ERROR);
    }

    @PreDestroy
    public void shutdown() {
        connections.keySet().forEach(session -> disconnect(session, CloseStatus.GOING_AWAY));
        timers.shutdownNow();
    }
}
