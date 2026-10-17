package com.marketmind.service;

import com.marketmind.entity.CampaignEntity;
import com.marketmind.entity.UserEntity;
import com.marketmind.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.jsonPath;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class N8nEmailClientTest {

    private static final UUID CALLBACK_TOKEN = UUID.fromString("11111111-2222-3333-4444-555555555555");

    private CampaignEntity campaniaRechazada() {
        CampaignEntity campaign = mock(CampaignEntity.class);
        when(campaign.getId()).thenReturn(42L);
        when(campaign.getMarketeroId()).thenReturn(7L);
        when(campaign.getTitulo()).thenReturn("Promo café");
        when(campaign.getFeedbackRechazo()).thenReturn("Cambiar la foto");
        when(campaign.getTextoGenerado()).thenReturn("Copy de prueba");
        when(campaign.getN8nCallbackToken()).thenReturn(CALLBACK_TOKEN);
        return campaign;
    }

    private UserRepository repositorioConMarketero() {
        UserEntity marketero = mock(UserEntity.class);
        when(marketero.getEmail()).thenReturn("marketero@test.com");
        when(marketero.getNombre()).thenReturn("Marketero");
        UserRepository users = mock(UserRepository.class);
        when(users.findById(7L)).thenReturn(Optional.of(marketero));
        return users;
    }

    @Test
    void decisionEmailIsSentToN8nWithTheSharedSecret() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();
        N8nEmailClient client = new N8nEmailClient(
                repositorioConMarketero(), restTemplate, "http://n8n:5678/", "secreto-compartido");

        server.expect(requestTo("http://n8n:5678/webhook/marketmind-email"))
                .andExpect(method(Objects.requireNonNull(HttpMethod.POST)))
                .andExpect(header(N8nEmailClient.TOKEN_HEADER, "secreto-compartido"))
                .andExpect(jsonPath("$.event_type").value("rechazado"))
                .andExpect(jsonPath("$.marketero_email").value("marketero@test.com"))
                .andExpect(jsonPath("$.n8n_callback_token").value(CALLBACK_TOKEN.toString()))
                .andRespond(withSuccess());

        client.notify(campaniaRechazada(), "rechazado");
        server.verify();
    }

    @Test
    void aRejectedSecretNeverBreaksTheDecision() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();
        N8nEmailClient client = new N8nEmailClient(
                repositorioConMarketero(), restTemplate, "http://n8n:5678", "otro-secreto");
        server.expect(requestTo("http://n8n:5678/webhook/marketmind-email"))
                .andRespond(withStatus(Objects.requireNonNull(org.springframework.http.HttpStatus.FORBIDDEN)));

        assertDoesNotThrow(() -> client.notify(campaniaRechazada(), "rechazado"));
        server.verify();
    }
}
