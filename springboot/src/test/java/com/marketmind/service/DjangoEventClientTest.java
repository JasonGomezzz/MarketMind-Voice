package com.marketmind.service;

import org.junit.jupiter.api.Test;
import org.springframework.lang.NonNull;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import com.sun.net.httpserver.HttpServer;

import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
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

    /**
     * Django (WSGI) lee vacío un cuerpo enviado en chunked: el cliente real debe
     * mandar Content-Length. Se prueba contra un servidor HTTP de verdad.
     */
    @Test
    void theRealClientSendsContentLengthSoDjangoCanReadTheBody() throws Exception {
        AtomicReference<String> contentLength = new AtomicReference<>();
        AtomicReference<String> transferEncoding = new AtomicReference<>();
        AtomicReference<String> body = new AtomicReference<>();
        HttpServer django = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        django.createContext("/api/internal/campaign-events/approved", exchange -> {
            contentLength.set(exchange.getRequestHeaders().getFirst("Content-Length"));
            transferEncoding.set(exchange.getRequestHeaders().getFirst("Transfer-Encoding"));
            body.set(new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
            byte[] respuesta = "{}".getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, respuesta.length);
            exchange.getResponseBody().write(respuesta);
            exchange.close();
        });
        django.start();
        try {
            String url = "http://127.0.0.1:" + django.getAddress().getPort();
            new DjangoEventClient(url, "t", DjangoEventClient.defaultRestTemplate(), INMEDIATO).notifyApprovedAsync(47L);
        } finally {
            django.stop(0);
        }
        assertEquals("{\"campaignId\":47}", body.get());
        assertEquals(String.valueOf(body.get().getBytes(StandardCharsets.UTF_8).length), contentLength.get());
        assertNull(transferEncoding.get());
    }
}
