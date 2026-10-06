package com.marketmind.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.marketmind.entity.UserEntity;
import com.marketmind.repository.UserRepository;
import com.marketmind.security.AuthenticatedUser;
import com.marketmind.security.JwtTokenValidator;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import java.time.Instant;
import java.util.Optional;
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;

class ClientCampaignWebSocketHandlerTest {
    JwtTokenValidator validator = mock(JwtTokenValidator.class);
    UserRepository users = mock(UserRepository.class);
    ClientCampaignWebSocketHandler handler;

    @BeforeEach void setup() { handler = new ClientCampaignWebSocketHandler(validator, users, new ObjectMapper()); }
    @AfterEach void teardown() { handler.shutdown(); }
    UserEntity user(long id, String email) {
        UserEntity user = new UserEntity();
        ReflectionTestUtils.setField(user, "id", id);
        ReflectionTestUtils.setField(user, "email", email);
        ReflectionTestUtils.setField(user, "rol", "cliente");
        ReflectionTestUtils.setField(user, "isActive", true);
        ReflectionTestUtils.setField(user, "tokenVersion", 2);
        when(users.findById(id)).thenReturn(Optional.of(user));
        when(validator.validateAccessToken("token" + id)).thenReturn(Optional.of(new JwtTokenValidator.ValidatedAccessToken(new AuthenticatedUser(id, "cliente", "Cliente", 2), Instant.now().plusSeconds(60))));
        return user;
    }
    WebSocketSession socket(String id) {
        WebSocketSession session = mock(WebSocketSession.class);
        when(session.isOpen()).thenReturn(true);
        handler.afterConnectionEstablished(session);
        return session;
    }
    void authenticate(WebSocketSession session, long id) { handler.handleTextMessage(session, new TextMessage("{\"type\":\"authenticate\",\"token\":\"token" + id + "\"}")); }

    @Test void anonymousReceivesNoCampaigns() throws Exception {
        var session = socket("anonymous");
        handler.sendToClient("a@test.com", "secret");
        verify(session, never()).sendMessage(any());
    }
    @Test void authenticatedClientsOnlyReceiveTheirOwnEvents() throws Exception {
        user(1L, "a@test.com"); user(2L, "b@test.com");
        var a = socket("a"); var b = socket("b");
        authenticate(a, 1); authenticate(b, 2);
        clearInvocations(a, b);
        handler.sendToClient("A@test.com", "secret-for-a");
        verify(a).sendMessage(argThat(message -> "secret-for-a".equals(message.getPayload())));
        verify(b, never()).sendMessage(any());
    }
    @Test void invalidTokenAndMalformedFrameAreClosed() throws Exception {
        var invalid = socket("invalid"); authenticate(invalid, 99);
        verify(invalid).close(CloseStatus.POLICY_VIOLATION);
        var malformed = socket("malformed"); handler.handleTextMessage(malformed, new TextMessage("invalid-json"));
        verify(malformed).close(CloseStatus.POLICY_VIOLATION);
    }
    @Test void suspendedAndRevokedAccountsCannotAuthenticate() throws Exception {
        UserEntity suspended = user(1L, "a@test.com");
        ReflectionTestUtils.setField(suspended, "isActive", false);
        var a = socket("a"); authenticate(a, 1);
        verify(a).close(CloseStatus.POLICY_VIOLATION);
        UserEntity revoked = user(2L, "b@test.com");
        ReflectionTestUtils.setField(revoked, "tokenVersion", 3);
        var b = socket("b"); authenticate(b, 2);
        verify(b).close(CloseStatus.POLICY_VIOLATION);
    }
    @Test void roleAndExpiryAreEnforced() throws Exception {
        UserEntity admin = user(1L, "a@test.com");
        ReflectionTestUtils.setField(admin, "rol", "superadmin");
        var a = socket("a"); authenticate(a, 1);
        verify(a).close(CloseStatus.POLICY_VIOLATION);
        user(2L, "b@test.com");
        when(validator.validateAccessToken("token2")).thenReturn(Optional.of(new JwtTokenValidator.ValidatedAccessToken(new AuthenticatedUser(2L, "cliente", "Cliente", 2), Instant.now().minusSeconds(1))));
        var b = socket("b"); authenticate(b, 2);
        verify(b).close(CloseStatus.POLICY_VIOLATION);
    }
    @Test void revocationAfterAuthenticationBlocksDelivery() throws Exception {
        UserEntity user = user(1L, "a@test.com");
        var a = socket("a"); authenticate(a, 1); clearInvocations(a);
        ReflectionTestUtils.setField(user, "tokenVersion", 3);
        handler.sendToClient("a@test.com", "secret");
        verify(a, never()).sendMessage(any());
        verify(a).close(CloseStatus.POLICY_VIOLATION);
    }
    @Test void unknownRecipientDoesNotBroadcastAndReauthenticationIsRejected() throws Exception {
        user(1L, "a@test.com"); var a = socket("a"); authenticate(a, 1); clearInvocations(a);
        handler.sendToClient(null, "secret"); handler.sendToClient("b@test.com", "secret");
        verify(a, never()).sendMessage(any());
        authenticate(a, 1);
        verify(a).close(CloseStatus.POLICY_VIOLATION);
    }
}
