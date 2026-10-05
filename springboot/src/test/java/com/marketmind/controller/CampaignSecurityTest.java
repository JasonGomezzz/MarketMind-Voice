package com.marketmind.controller;

import com.marketmind.config.SecurityConfig;
import com.marketmind.entity.UserEntity;
import com.marketmind.repository.UserRepository;
import com.marketmind.security.AuthenticatedUser;
import com.marketmind.security.JwtAuthenticationFilter;
import com.marketmind.security.JwtTokenValidator;
import com.marketmind.service.CampaignService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;
import java.util.Optional;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(CampaignController.class)
@Import({SecurityConfig.class, JwtAuthenticationFilter.class})
class CampaignSecurityTest {
    @Autowired MockMvc mvc;
    @MockBean CampaignService campaigns;
    @MockBean JwtTokenValidator validator;
    @MockBean UserRepository users;
    UserEntity user;

    @BeforeEach void setup() {
        user = new UserEntity();
        ReflectionTestUtils.setField(user, "isActive", true);
        ReflectionTestUtils.setField(user, "tokenVersion", 2);
        when(users.findById(1L)).thenReturn(Optional.of(user));
        when(validator.validateAndExtract("client")).thenReturn(Optional.of(new AuthenticatedUser(1L, "cliente", "Cliente", 2)));
        when(validator.validateAndExtract("marketer")).thenReturn(Optional.of(new AuthenticatedUser(1L, "marketero", "Marketero", 2)));
        when(validator.validateAndExtract("expired-version")).thenReturn(Optional.of(new AuthenticatedUser(1L, "cliente", "Cliente", 1)));
        when(validator.validateAndExtract("invalid")).thenReturn(Optional.empty());
        when(campaigns.getSummary(any())).thenReturn(Map.of("pendientes", 1L));
    }
    @Test void anonymousCannotReadClientSummary() throws Exception {
        mvc.perform(get("/api/v1/campaigns/summary")).andExpect(status().isForbidden());
        verifyNoInteractions(campaigns);
    }
    @Test void clientCanReadSummary() throws Exception {
        mvc.perform(get("/api/v1/campaigns/summary").header("Authorization", "Bearer client"))
            .andExpect(status().isOk()).andExpect(jsonPath("$.data.pendientes").value(1));
    }
    @Test void marketerCannotReadClientSummary() throws Exception {
        mvc.perform(get("/api/v1/campaigns/summary").header("Authorization", "Bearer marketer")).andExpect(status().isForbidden());
        verifyNoInteractions(campaigns);
    }
    @Test void suspendedUserCannotReadSummary() throws Exception {
        ReflectionTestUtils.setField(user, "isActive", false);
        mvc.perform(get("/api/v1/campaigns/summary").header("Authorization", "Bearer client")).andExpect(status().isForbidden());
        verifyNoInteractions(campaigns);
    }
    @Test void revokedTokenCannotReadSummary() throws Exception {
        mvc.perform(get("/api/v1/campaigns/summary").header("Authorization", "Bearer expired-version")).andExpect(status().isForbidden());
        verifyNoInteractions(campaigns);
    }
    @Test void invalidTokenCannotReadSummary() throws Exception {
        mvc.perform(get("/api/v1/campaigns/summary").header("Authorization", "Bearer invalid")).andExpect(status().isForbidden());
        verifyNoInteractions(campaigns);
    }
}
