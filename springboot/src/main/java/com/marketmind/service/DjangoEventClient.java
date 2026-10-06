package com.marketmind.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.Map;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

/**
 * Avisa a Django que el cliente aprobó una campaña, para que publique en las
 * cuentas elegidas. Espejo del aviso Django → Spring de "campaña enviada".
 *
 * Se llama después del commit y en segundo plano: publicar en Meta tarda
 * varios segundos y no debe demorar la respuesta al cliente. Si el aviso se
 * pierde, el marketero tiene "Publicar ahora" como respaldo.
 */
@Component
public class DjangoEventClient {

    private static final Logger log = LoggerFactory.getLogger(DjangoEventClient.class);

    private final RestTemplate restTemplate;
    private final Executor executor;
    private final String baseUrl;
    private final String eventToken;

    @Autowired
    public DjangoEventClient(
            @Value("${app.django.internal-url:http://host.docker.internal:8000}") String baseUrl,
            @Value("${app.internal.event-token:dev-internal-event-token}") String eventToken) {
        this(baseUrl, eventToken, defaultRestTemplate(), Executors.newVirtualThreadPerTaskExecutor());
    }

    DjangoEventClient(String baseUrl, String eventToken, RestTemplate restTemplate, Executor executor) {
        this.baseUrl = baseUrl.replaceAll("/+$", "");
        this.eventToken = eventToken;
        this.restTemplate = restTemplate;
        this.executor = executor;
    }

    private static RestTemplate defaultRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(3000);
        // Django publica en Meta dentro de esta llamada (contenedor + espera + publicación).
        factory.setReadTimeout(90000);
        return new RestTemplate(factory);
    }

    public void notifyApprovedAsync(Long campaignId) {
        executor.execute(() -> notifyApproved(campaignId));
    }

    void notifyApproved(Long campaignId) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-Internal-Event-Token", eventToken);
        try {
            restTemplate.postForEntity(
                    baseUrl + "/api/internal/campaign-events/approved",
                    new HttpEntity<>(Map.of("campaignId", campaignId), headers),
                    String.class);
        } catch (RestClientException ex) {
            log.warn("No se pudo avisar a Django la aprobación de la campaña {}: {}", campaignId, ex.getMessage());
        }
    }
}
