package com.marketmind.service;

import com.marketmind.entity.CampaignEntity;
import com.marketmind.entity.UserEntity;
import com.marketmind.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

/**
 * HU17 — Cliente HTTP que dispara el webhook de email de n8n cuando una
 * campaña pasa a aprobado o rechazado. Spring Boot es dueño de esta transición
 * (escribe directo en la BD compartida) por lo que también dispara el email
 * sin pasar por Django.
 *
 * Patrón fire-and-forget: si el webhook falla, se loguea pero NO se rolea la
 * transición. n8n se encarga de los 3 reintentos a Resend.
 *
 * El webhook exige el secreto compartido N8N_WEBHOOK_TOKEN en el encabezado
 * X-NexoMark-Token (el mismo que envía Django); sin él n8n responde 401/403.
 */
@Component
public class N8nEmailClient {

    private static final Logger log = LoggerFactory.getLogger(N8nEmailClient.class);

    static final String TOKEN_HEADER = "X-NexoMark-Token";

    private final UserRepository userRepository;
    private final RestTemplate restTemplate;
    private final String n8nBaseUrl;
    private final String webhookToken;

    @Autowired
    public N8nEmailClient(
            UserRepository userRepository,
            @Value("${n8n.webhook-url:http://host.docker.internal:5678}") String n8nBaseUrl,
            @Value("${n8n.webhook-token:dev-n8n-webhook-token}") String webhookToken) {
        this(userRepository, defaultRestTemplate(), n8nBaseUrl, webhookToken);
    }

    N8nEmailClient(UserRepository userRepository, RestTemplate restTemplate, String n8nBaseUrl, String webhookToken) {
        this.userRepository = userRepository;
        this.restTemplate = restTemplate;
        this.n8nBaseUrl = n8nBaseUrl.replaceAll("/+$", "");
        this.webhookToken = webhookToken;
    }

    private static RestTemplate defaultRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(2000);
        factory.setReadTimeout(3000);
        return new RestTemplate(factory);
    }

    /**
     * Dispara el webhook de email al marketero. Resuelve el destinatario
     * leyendo UserEntity por marketero_id.
     *
     * @param campaign  campaña recién guardada con el nuevo estado
     * @param newEstado "aprobado" o "rechazado"
     */
    public void notify(CampaignEntity campaign, String newEstado) {
        Long marketeroId = campaign.getMarketeroId();
        if (marketeroId == null) {
            log.warn("HU17: campaña {} sin marketero asignado", campaign.getId());
            return;
        }
        UserEntity marketero = userRepository.findById(marketeroId).orElse(null);
        if (marketero == null) {
            log.warn("HU17: marketero {} no encontrado para campaña {}",
                    campaign.getMarketeroId(), campaign.getId());
            return;
        }

        Map<String, Object> payload = new HashMap<>();
        payload.put("event_type", newEstado);
        payload.put("campaign_id", campaign.getId());
        payload.put("campaign_titulo", campaign.getTitulo());
        payload.put("marketero_email", marketero.getEmail());
        payload.put("marketero_nombre", marketero.getNombre());
        payload.put("feedback", campaign.getFeedbackRechazo() == null ? "" : campaign.getFeedbackRechazo());
        payload.put("copy_preview", truncarPalabras(campaign.getTextoGenerado(), 80));
        payload.put("n8n_callback_token",
                campaign.getN8nCallbackToken() == null ? "" : campaign.getN8nCallbackToken().toString());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set(TOKEN_HEADER, webhookToken);
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);

        String url = n8nBaseUrl + "/webhook/marketmind-email";
        try {
            restTemplate.postForLocation(url, request);
            log.info("HU17 notify email disparado para campaña {} → {}", campaign.getId(), newEstado);
        } catch (Exception e) {
            log.warn("HU17 notify email falló para campaña {}: {}", campaign.getId(), e.getMessage());
        }
    }

    private static String truncarPalabras(String texto, int n) {
        if (texto == null || texto.isBlank()) {
            return "";
        }
        String[] palabras = texto.trim().split("\\s+");
        if (palabras.length <= n) {
            return texto.trim();
        }
        return String.join(" ", Arrays.copyOfRange(palabras, 0, n)) + "…";
    }
}
