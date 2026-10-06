package com.marketmind.service;

import org.junit.jupiter.api.Test;
import org.springframework.lang.NonNull;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import java.util.Objects;
import java.util.concurrent.Executor;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class DjangoEventClientTest {

    /** Ejecuta en el mismo hilo para que la prueba vea la llamada sin esperar. */
    private static final Executor INMEDIATO = new Executor() {
        @Override
        public void execute(@NonNull Runnable command) {
            command.run();
        }
    };

    @Test
    void approvalIsSentToDjangoWithTheInternalToken() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();
        DjangoEventClient client = new DjangoEventClient("http://django:8000/", "secreto-interno", restTemplate, INMEDIATO);

        server.expect(requestTo("http://django:8000/api/internal/campaign-events/approved"))
                .andExpect(method(Objects.requireNonNull(HttpMethod.POST)))
                .andExpect(header("X-Internal-Event-Token", "secreto-interno"))
                .andExpect(content().json("{\"campaignId\": 42}"))
                .andRespond(withSuccess("{}", MediaType.APPLICATION_JSON));

        client.notifyApprovedAsync(42L);
        server.verify();
    }

    @Test
    void aDjangoFailureNeverBreaksTheApproval() {
        RestTemplate restTemplate = new RestTemplate();
        MockRestServiceServer server = MockRestServiceServer.bindTo(restTemplate).build();
        DjangoEventClient client = new DjangoEventClient("http://django:8000", "t", restTemplate, INMEDIATO);
        server.expect(requestTo("http://django:8000/api/internal/campaign-events/approved"))
                .andRespond(withServerError());

        assertDoesNotThrow(() -> client.notifyApprovedAsync(7L));
        server.verify();
    }
}
