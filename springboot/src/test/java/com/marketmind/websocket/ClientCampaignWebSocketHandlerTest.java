package com.marketmind.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.marketmind.controller.InternalCampaignEventController;
import com.marketmind.dto.CampaignSubmittedEventRequest;
import com.marketmind.entity.CampaignEntity;
import com.marketmind.entity.UserEntity;
import com.marketmind.repository.CampaignRepository;
import com.marketmind.repository.UserRepository;
import com.marketmind.security.AuthenticatedUser;
import com.marketmind.security.CurrentUserVerifier;
import com.marketmind.security.CurrentUserSnapshot;
import com.marketmind.security.JwtTokenValidator;
import com.marketmind.repository.PublicationViewRepository;
import com.marketmind.service.CampaignService;
import com.marketmind.service.DjangoEventClient;
import com.marketmind.service.N8nEmailClient;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.lang.NonNull;
import org.mockito.ArgumentMatcher;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.support.AbstractPlatformTransactionManager;
import org.springframework.transaction.support.DefaultTransactionStatus;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.WebSocketMessage;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Optional;
import java.util.Objects;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class ClientCampaignWebSocketHandlerTest {
    private static final String SECRET = "socket-test-secret-at-least-thirty-two-bytes";
    private UserRepository users;
    private ClientCampaignWebSocketHandler handler;
    private List<Runnable> deadlines;
    private AnnotationConfigApplicationContext context;
    private UserEntity alice;

    @BeforeEach
    void setUp() {
        users = mock(UserRepository.class);
        alice = user(1L, "alice@example.com");
        when(users.findById(1L)).thenReturn(Optional.of(alice));
        when(users.findById(2L)).thenReturn(Optional.of(user(2L, "bob@example.com")));
        when(users.findCurrentSnapshotById(anyLong())).thenAnswer(invocation -> {
            Long id = Objects.requireNonNull(invocation.getArgument(0));
            return users.findById(id).map(entity -> new CurrentUserSnapshot(
                    entity.getEmail(), entity.getRol(), entity.getIsActive(), entity.getTokenVersion()));
        });
        deadlines = new ArrayList<>();
        TaskScheduler scheduler = mock(TaskScheduler.class);
        doAnswer(invocation -> {
            deadlines.add(invocation.getArgument(0));
            return mock(ScheduledFuture.class);
        }).when(scheduler).schedule(matched(any(Runnable.class), () -> {}),
                matched(any(Instant.class), Objects.requireNonNull(Instant.EPOCH)));
        handler = new ClientCampaignWebSocketHandler(new JwtTokenValidator(SECRET),
                new CurrentUserVerifier(users), new ObjectMapper(), scheduler);
        context = new AnnotationConfigApplicationContext();
        context.register(EventConfig.class);
        context.registerBean(ClientCampaignWebSocketHandler.class, () -> handler);
        context.refresh();
    }

    @AfterEach
    void closeContext() { context.close(); }

    @Configuration
    @EnableTransactionManagement
    static class EventConfig {}

    @Test
    void anonymousNeverReceivesEventsAndClosesAtDeadline() throws Exception {
        WebSocketSession anonymous = connect("anonymous");
        handler.deliver(event());
        verify(anonymous, never()).sendMessage(anyMessage());
        deadlines.getFirst().run();
        verify(anonymous).close(closeCode(4401));
    }

    @ParameterizedTest
    @ValueSource(strings = {"malformed", "expired", "refresh", "unsigned", "missing-exp"})
    void rejectsInvalidCredentials(String kind) throws Exception {
        WebSocketSession session = connect("invalid");
        var builder = Jwts.builder().claim("user_id", 1).claim("role", "cliente")
                .claim("token_version", 0).claim("token_type", "refresh".equals(kind) ? "refresh" : "access");
        if (!"missing-exp".equals(kind)) builder.expiration(Date.from(Instant.now().plusSeconds("expired".equals(kind) ? -60 : 300)));
        String token = "malformed".equals(kind) ? "invalid" : "unsigned".equals(kind)
                ? builder.compact() : builder.signWith(Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8))).compact();
        authenticate(session, token);
        handler.deliver(event());
        verify(session).close(closeCode(4401));
        verify(session, never()).sendMessage(anyMessage());
    }

    @Test
    void rejectsNonClientAndSuspendedAndUnknownUsers() throws Exception {
        WebSocketSession marketer = connect("marketer");
        authenticate(marketer, token(1L, "marketero", 0));
        verify(marketer).close(closeCode(4403));
        ReflectionTestUtils.setField(Objects.requireNonNull(alice), "isActive", false);
        WebSocketSession suspended = connect("suspended");
        authenticate(suspended, token(1L, "cliente", 0));
        verify(suspended).close(closeCode(4403));
        WebSocketSession unknown = connect("unknown");
        authenticate(unknown, token(99L, "cliente", 0));
        verify(unknown).close(closeCode(4403));
    }

    @Test
    void sendsOnlyToRecipientAcrossAllAuthenticatedTabsWithoutCampaignContents() throws Exception {
        WebSocketSession aliceOne = authenticated("alice1", 1L);
        WebSocketSession aliceTwo = authenticated("alice2", 1L);
        WebSocketSession bob = authenticated("bob", 2L);
        WebSocketSession anonymous = connect("anonymous");
        handler.deliver(new ClientCampaignEvent("campaign_submitted", 10L, "ALICE@example.com"));
        for (WebSocketSession session : List.of(aliceOne, aliceTwo)) {
            verify(session).sendMessage(messageMatching(message -> message.getPayload().equals("{\"type\":\"authenticated\"}")));
            verify(session).sendMessage(messageMatching(message -> {
                String payload = message.getPayload().toString();
                return payload.contains("\"campaignId\":10") && !payload.contains("email") && !payload.contains("campaign\":");
            }));
        }
        verify(bob, times(1)).sendMessage(anyMessage()); // Authentication acknowledgment only.
        verify(anonymous, never()).sendMessage(anyMessage());
    }

    @ParameterizedTest
    @ValueSource(strings = {"suspended", "version", "role", "deleted"})
    void closesWhenSessionIsRevokedAfterConnection(String change) throws Exception {
        WebSocketSession session = authenticated("alice", 1L);
        switch (change) {
            case "suspended" -> ReflectionTestUtils.setField(Objects.requireNonNull(alice), "isActive", false);
            case "version" -> ReflectionTestUtils.setField(Objects.requireNonNull(alice), "tokenVersion", 1);
            case "role" -> ReflectionTestUtils.setField(Objects.requireNonNull(alice), "rol", "marketero");
            case "deleted" -> when(users.findById(1L)).thenReturn(Optional.empty());
        }
        handler.deliver(event());
        verify(session, times(1)).sendMessage(anyMessage());
        verify(session).close(closeCode(4403));
    }

    @Test
    void recipientUsesCurrentDatabaseEmailAndFailsClosedWhenDatabaseUnavailable() throws Exception {
        WebSocketSession session = authenticated("alice", 1L);
        ReflectionTestUtils.setField(Objects.requireNonNull(alice), "email", "changed@example.com");
        handler.deliver(event());
        verify(session, times(1)).sendMessage(anyMessage());
        when(users.findById(1L)).thenThrow(new IllegalStateException("database unavailable"));
        handler.deliver(event());
        verify(session).close(Objects.requireNonNull(CloseStatus.SERVER_ERROR));
        verify(session, times(1)).sendMessage(anyMessage());
    }

    @Test
    void expiryClosesConnectionAndCannotReceiveLaterNotifications() throws Exception {
        WebSocketSession session = authenticated("alice", 1L);
        deadlines.getLast().run();
        verify(session).close(closeCode(4408));
        handler.deliver(event());
        verify(session, times(1)).sendMessage(anyMessage());
    }

    @Test
    void rolledBackStatusUpdatesNeverNotifyButCommittedUpdatesDo() throws Exception {
        WebSocketSession session = authenticated("alice", 1L);
        CampaignRepository campaigns = mock(CampaignRepository.class);
        CampaignEntity campaign = new CampaignEntity();
        ReflectionTestUtils.setField(campaign, "id", 10L);
        ReflectionTestUtils.setField(campaign, "clienteEmail", "alice@example.com");
        ReflectionTestUtils.setField(campaign, "estado", "pendiente_aprobacion");
        ReflectionTestUtils.setField(campaign, "version", 0);
        when(campaigns.findById(10L)).thenReturn(Optional.of(campaign));
        when(campaigns.save(matched(any(), new CampaignEntity()))).thenReturn(campaign);
        N8nEmailClient emailClient = mock(N8nEmailClient.class);
        DjangoEventClient djangoEvents = mock(DjangoEventClient.class);
        CampaignService service = new CampaignService(
                campaigns, users, emailClient, context, djangoEvents, mock(PublicationViewRepository.class));
        var transaction = new TransactionTemplate(new LocalTransactionManager());
        AuthenticatedUser principal = new AuthenticatedUser(1L, "cliente", "Alice", 0);
        transaction.executeWithoutResult(status -> {
            service.updateStatus(10L, "aprobado", null, 5, 0, principal);
            assertDoesNotThrow(() -> verify(session, times(1)).sendMessage(anyMessage()));
            verifyNoInteractions(emailClient);
            status.setRollbackOnly();
        });
        verify(session, times(1)).sendMessage(anyMessage());
        verifyNoInteractions(emailClient);
        verifyNoInteractions(djangoEvents);
        ReflectionTestUtils.setField(campaign, "estado", "pendiente_aprobacion");
        transaction.executeWithoutResult(status -> {
            service.updateStatus(10L, "aprobado", null, 5, 0, principal);
            try { verify(session, times(1)).sendMessage(anyMessage()); }
            catch (Exception ex) { throw new AssertionError(ex); }
            verifyNoInteractions(emailClient);
        });
        verify(session, times(2)).sendMessage(anyMessage());
        verify(emailClient).notify(campaign, "aprobado");
        verify(djangoEvents).notifyApprovedAsync(10L);
    }

    @Test
    void internalSubmitUsesServerRecipientAndRejectsWrongInternalSecret() throws Exception {
        WebSocketSession session = authenticated("alice", 1L);
        WebSocketSession bob = authenticated("bob", 2L);
        CampaignService service = mock(CampaignService.class);
        when(service.findById(10L)).thenReturn(com.marketmind.dto.CampaignResponseDTO.builder()
                .id(10L).clienteEmail("alice@example.com").build());
        var controller = new InternalCampaignEventController(service, context);
        ReflectionTestUtils.setField(controller, "eventToken", "test-internal");
        CampaignSubmittedEventRequest request = new CampaignSubmittedEventRequest();
        request.setCampaignId(10L);
        assertEquals(403, controller.submitted("wrong", request).getStatusCode().value());
        verify(service, never()).findById(any());
        assertEquals(200, controller.submitted("test-internal", request).getStatusCode().value());
        verify(session, times(2)).sendMessage(anyMessage());
        verify(bob, times(1)).sendMessage(anyMessage());
    }

    @NonNull
    private WebSocketSession connect(String id) {
        WebSocketSession session = mock(WebSocketSession.class);
        when(session.getId()).thenReturn(id);
        AtomicBoolean open = new AtomicBoolean(true);
        when(session.isOpen()).thenAnswer(invocation -> open.get());
        try { doAnswer(invocation -> { open.set(false); return null; }).when(session).close(anyCloseStatus()); }
        catch (Exception ex) { throw new AssertionError(ex); }
        handler.afterConnectionEstablished(session);
        return session;
    }

    @NonNull
    private WebSocketSession authenticated(String id, Long userId) {
        WebSocketSession session = connect(id);
        authenticate(session, token(userId, "cliente", 0));
        return session;
    }

    private void authenticate(@NonNull WebSocketSession session, String token) {
        handler.handleTextMessage(session, new TextMessage("{\"type\":\"authenticate\",\"accessToken\":\"" + token + "\"}"));
    }

    private String token(Long id, String role, int version) {
        return Jwts.builder().claim("user_id", id).claim("role", role).claim("token_version", version)
                .claim("token_type", "access").expiration(Date.from(Instant.now().plusSeconds(300)))
                .signWith(Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8))).compact();
    }

    private UserEntity user(Long id, String email) {
        UserEntity entity = new UserEntity();
        ReflectionTestUtils.setField(entity, "id", id);
        ReflectionTestUtils.setField(entity, "email", email);
        ReflectionTestUtils.setField(entity, "rol", "cliente");
        ReflectionTestUtils.setField(entity, "isActive", true);
        ReflectionTestUtils.setField(entity, "tokenVersion", 0);
        return entity;
    }

    private ClientCampaignEvent event() { return new ClientCampaignEvent("campaign_submitted", 10L, "alice@example.com"); }

    // Mockito records each matcher on its stack; these placeholders satisfy Spring's
    // non-null signature without evaluating the matcher's intentional null return.
    @NonNull
    private static <T> T matched(T ignored, @NonNull T placeholder) {
        return placeholder;
    }

    @NonNull
    private static TextMessage anyMessage() {
        any();
        return new TextMessage("");
    }

    @NonNull
    private static WebSocketMessage<?> messageMatching(ArgumentMatcher<WebSocketMessage<?>> matcher) {
        argThat(matcher);
        return new TextMessage("");
    }

    @NonNull
    private static CloseStatus closeCode(int code) {
        argThat((CloseStatus status) -> status != null && status.getCode() == code);
        return new CloseStatus(code);
    }

    @NonNull
    private static CloseStatus anyCloseStatus() {
        any();
        return new CloseStatus(1000);
    }

    // Tests Spring's real event/commit/rollback callbacks; no database or network is used.
    static class LocalTransactionManager extends AbstractPlatformTransactionManager {
        @Override @NonNull protected Object doGetTransaction() { return new Object(); }
        @Override protected void doBegin(@NonNull Object transaction, @NonNull TransactionDefinition definition) {}
        @Override protected void doCommit(@NonNull DefaultTransactionStatus status) {}
        @Override protected void doRollback(@NonNull DefaultTransactionStatus status) {}
    }
}
