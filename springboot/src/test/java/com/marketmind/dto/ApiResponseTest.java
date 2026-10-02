package com.marketmind.dto;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ApiResponseTest {

    @Test
    void createsSuccessfulResponse() {
        ApiResponse<String> response = ApiResponse.ok("Creado", "data");

        assertTrue(response.isSuccess());
        assertEquals("Creado", response.getMessage());
        assertEquals("data", response.getData());
    }

    @Test
    void createsErrorResponse() {
        ApiResponse<Void> response = ApiResponse.error("Falló", null);

        assertFalse(response.isSuccess());
        assertEquals("Falló", response.getMessage());
        assertNull(response.getData());
    }
}
