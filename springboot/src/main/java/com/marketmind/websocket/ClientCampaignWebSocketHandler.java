package com.marketmind.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.marketmind.security.CurrentUserVerifier;
import com.marketmind.security.JwtTokenValidator;
import com.marketmind.security.JwtTokenValidator.ValidatedAccessToken;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.lang.NonNull;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ScheduledFuture;

/** Authenticates a browser's first frame; an unauthenticated connection is never subscribed. */
@Slf4j
@Component
@RequiredArgsConstructor
public class ClientCampaignWebSocketHandler extends TextWebSocketHandler {
    private static final CloseStatus UNAUTHORIZED = new CloseStatus(4401, "Authentication required");
    private static final CloseStatus FORBIDDEN = new CloseStatus(4403, "Session revoked or role denied");
    private static final CloseStatus EXPIRED = new CloseStatus(4408, "Access token expired");
    private final JwtTokenValidator tokenValidator;
    private final CurrentUserVerifier currentUserVerifier;
    private final ObjectMapper objectMapper;
    private final TaskScheduler clientCampaignSocketScheduler;
    private final Map<String, Connection> connections = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(@NonNull WebSocketSession session) {
        session.setTextMessageSizeLimit(8192);
        Connection connection = new Connection(session);
        synchronized (connection) {
            connections.put(session.getId(), connection);
            connection.deadline = clientCampaignSocketScheduler.schedule(
                    () -> close(connection, UNAUTHORIZED), Objects.requireNonNull(Instant.now().plusSeconds(5)));
        }
    }

    @Override
    protected void handleTextMessage(@NonNull WebSocketSession session, @NonNull TextMessage message) {
        Connection connection = connections.get(session.getId());
        if (connection == null) return;
        synchronized (connection) {
            // Only one authentication frame is supported; renewing means a new connection.
            if (connection.authentication != null) {
                close(connection, CloseStatus.POLICY_VIOLATION);
                return;
            }
            try {
                JsonNode frame = objectMapper.readTree(message.getPayload());
                if (frame == null || !"authenticate".equals(frame.path("type").asText())
                        || !frame.path("accessToken").isTextual()) {
                    close(connection, UNAUTHORIZED);
                    return;
                }
                var authentication = tokenValidator.validateAccessToken(frame.path("accessToken").asText());
                if (authentication.isEmpty()) {
                    close(connection, UNAUTHORIZED);
                    return;
                }
                var access = authentication.get();
                if (!"cliente".equals(access.user().role())
                        || currentUserVerifier.findCurrent(access.user()).isEmpty()) {
                    close(connection, FORBIDDEN);
                    return;
                }
                if (connection.deadline != null) connection.deadline.cancel(false);
                connection.authentication = access;
                connection.deadline = clientCampaignSocketScheduler.schedule(
                        () -> close(connection, EXPIRED), Objects.requireNonNull(access.expiresAt()));
                session.sendMessage(new TextMessage("{\"type\":\"authenticated\"}"));
            } catch (IOException | IllegalArgumentException ex) {
                close(connection, UNAUTHORIZED);
            } catch (RuntimeException ex) {
                // Database failure must fail closed, without logging the incoming credential.
                close(connection, CloseStatus.SERVER_ERROR);
            }
        }
    }

    @Override
    public void afterConnectionClosed(@NonNull WebSocketSession session, @NonNull CloseStatus status) {
        Connection connection = connections.remove(session.getId());
        if (connection != null) {
            synchronized (connection) {
                if (connection.deadline != null) connection.deadline.cancel(false);
            }
        }
    }

    @Override
    public void handleTransportError(@NonNull WebSocketSession session, @NonNull Throwable exception) {
        Connection connection = connections.get(session.getId());
        if (connection != null) close(connection, CloseStatus.SERVER_ERROR);
    }

    // HTTP internal events have no active transaction; status updates publish within one.
    // AFTER_COMMIT suppresses rolled-back updates. The REST API remains the source of truth.
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT, fallbackExecution = true)
    public void deliver(ClientCampaignEvent event) {
        if (event.recipientEmail() == null || event.recipientEmail().isBlank()) return;
        final TextMessage message;
        try {
            message = new TextMessage(Objects.requireNonNull(objectMapper.writeValueAsString(Map.of(
                    "type", event.type(), "campaignId", event.campaignId()))));
        } catch (IOException ex) {
            log.warn("No se pudo serializar la notificación de campaña {}", event.campaignId());
            return;
        }
        for (Connection connection : connections.values()) {
            synchronized (connection) {
                if (!connection.session.isOpen()) {
                    close(connection, CloseStatus.NORMAL);
                    continue;
                }
                var access = connection.authentication;
                if (access == null) continue;
                if (!access.expiresAt().isAfter(Instant.now())) {
                    close(connection, EXPIRED);
                    continue;
                }
                try {
                    // Re-read before EVERY delivery: suspension, role, version and email can change.
                    var currentUser = currentUserVerifier.findCurrent(access.user());
                    if (currentUser.isEmpty()) {
                        close(connection, FORBIDDEN);
                    } else if (!access.expiresAt().isAfter(Instant.now())) {
                        close(connection, EXPIRED);
                    } else if (event.recipientEmail().equalsIgnoreCase(currentUser.get().email())) {
                        connection.session.sendMessage(message);
                    }
                } catch (IOException | RuntimeException ex) {
                    close(connection, CloseStatus.SERVER_ERROR);
                }
            }
        }
    }

    private void close(Connection connection, CloseStatus status) {
        synchronized (connection) {
            connections.remove(connection.session.getId(), connection);
            if (connection.deadline != null) connection.deadline.cancel(false);
            try {
                if (connection.session.isOpen()) connection.session.close(Objects.requireNonNull(status));
            } catch (IOException ex) {
                log.debug("No se pudo cerrar una conexión WebSocket.");
            }
        }
    }

    private static final class Connection {
        private final WebSocketSession session;
        private ValidatedAccessToken authentication;
        private ScheduledFuture<?> deadline;

        private Connection(WebSocketSession session) {
            this.session = session;
        }
    }
}
