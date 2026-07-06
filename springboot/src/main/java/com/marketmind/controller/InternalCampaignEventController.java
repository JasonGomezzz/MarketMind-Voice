package com.marketmind.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.marketmind.dto.ApiResponse;
import com.marketmind.dto.CampaignResponseDTO;
import com.marketmind.dto.CampaignSubmittedEventRequest;
import com.marketmind.service.CampaignService;
import com.marketmind.websocket.ClientCampaignWebSocketHandler;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/internal/campaign-events")
@RequiredArgsConstructor
public class InternalCampaignEventController {

    private final CampaignService campaignService;
    private final ClientCampaignWebSocketHandler webSocketHandler;
    private final ObjectMapper objectMapper;

    @Value("${app.internal.event-token:dev-internal-event-token}")
    private String eventToken;

    @PostMapping("/submitted")
    public ResponseEntity<ApiResponse<Map<String, Object>>> submitted(
            @RequestHeader(value = "X-Internal-Event-Token", required = false) String token,
            @RequestBody CampaignSubmittedEventRequest request) throws JsonProcessingException {

        if (!eventToken.equals(token)) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(ApiResponse.error("Token interno inválido.", Map.of()));
        }

        CampaignResponseDTO campaign = campaignService.findById(request.getCampaignId());
        String payload = objectMapper.writeValueAsString(Map.of(
                "type", "campaign_submitted",
                "campaign", campaign
        ));
        webSocketHandler.broadcast(payload);

        return ResponseEntity.ok(ApiResponse.ok("Evento emitido.", Map.of("campaignId", request.getCampaignId())));
    }
}
