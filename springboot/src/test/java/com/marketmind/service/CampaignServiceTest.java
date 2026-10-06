package com.marketmind.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.marketmind.entity.CampaignEntity;
import com.marketmind.entity.UserEntity;
import com.marketmind.exception.InvalidStatusTransitionException;
import com.marketmind.repository.CampaignRepository;
import com.marketmind.repository.UserRepository;
import com.marketmind.security.AuthenticatedUser;
import com.marketmind.websocket.ClientCampaignWebSocketHandler;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.test.util.ReflectionTestUtils;
import java.util.Optional;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CampaignServiceTest {
    @Mock CampaignRepository campaigns;
    @Mock UserRepository users;
    @Mock N8nEmailClient email;
    @Mock ClientCampaignWebSocketHandler websocket;
    CampaignService service;
    CampaignEntity campaign;
    AuthenticatedUser client = new AuthenticatedUser(1L, "cliente", "Cliente", 0);

    @BeforeEach void setup() {
        service = new CampaignService(campaigns, users, email, websocket, new ObjectMapper().findAndRegisterModules());
        campaign = new CampaignEntity();
        ReflectionTestUtils.setField(campaign, "id", 10L);
        ReflectionTestUtils.setField(campaign, "clienteEmail", "client@example.com");
        ReflectionTestUtils.setField(campaign, "estado", "pendiente_aprobacion");
        ReflectionTestUtils.setField(campaign, "version", 3);
        UserEntity user = new UserEntity();
        ReflectionTestUtils.setField(user, "email", "client@example.com");
        when(campaigns.findById(10L)).thenReturn(Optional.of(campaign));
        when(users.findById(1L)).thenReturn(Optional.of(user));
    }
    @Test void unrelatedClientCannotReadCampaign() {
        ReflectionTestUtils.setField(campaign, "clienteEmail", "other@example.com");
        assertThrows(AccessDeniedException.class, () -> service.findById(10L, client));
    }
    @Test void unrelatedClientCannotApproveCampaign() {
        ReflectionTestUtils.setField(campaign, "clienteEmail", "other@example.com");
        assertThrows(AccessDeniedException.class, () -> service.updateStatus(10L, "aprobado", null, 5, 3, client));
        verify(campaigns, never()).save(any());
    }
    @Test void staleVersionCannotOverwriteDecision() {
        assertThrows(IllegalArgumentException.class, () -> service.updateStatus(10L, "aprobado", null, 5, 2, client));
        verify(campaigns, never()).save(any());
    }
    @Test void approvalRequiresValidRating() {
        assertThrows(IllegalArgumentException.class, () -> service.updateStatus(10L, "aprobado", null, 6, 3, client));
        verify(campaigns, never()).save(any());
    }
    @Test void finalStateCannotBeApprovedAgain() {
        ReflectionTestUtils.setField(campaign, "estado", "aprobado");
        assertThrows(InvalidStatusTransitionException.class, () -> service.updateStatus(10L, "aprobado", null, 5, 3, client));
        verify(campaigns, never()).save(any());
    }
    @Test void rejectionRequiresFeedback() {
        assertThrows(IllegalArgumentException.class, () -> service.updateStatus(10L, "rechazado", "corto", 2, 3, client));
        verify(campaigns, never()).save(any());
    }
    @Test void approvalPersistsRatingAndNotifiesMarketer() {
        when(campaigns.save(campaign)).thenReturn(campaign);
        var result = service.updateStatus(10L, "aprobado", null, 5, 3, client);
        assertEquals("aprobado", result.getEstado());
        assertEquals(5, result.getClienteValoracion());
        verify(email).notify(campaign, "aprobado");
        verify(websocket).sendToClient(eq(campaign.getClienteEmail()), any());
    }
    @Test void secondRejectionEndsCampaignAsFailure() {
        ReflectionTestUtils.setField(campaign, "rechazosClienteCount", (short) 1);
        when(campaigns.save(campaign)).thenReturn(campaign);
        var result = service.updateStatus(10L, "rechazado", "El mensaje requiere cambios.", 2, 3, client);
        assertEquals("fracaso", result.getEstado());
        assertEquals(2, result.getRechazosClienteCount());
        verify(email).notify(campaign, "fracaso");
    }
}
