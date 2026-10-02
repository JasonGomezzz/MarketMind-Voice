package com.marketmind.exception;

import com.marketmind.dto.ApiResponse;
import com.marketmind.dto.StatusUpdateRequest;
import org.junit.jupiter.api.Test;
import org.springframework.core.MethodParameter;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.validation.BeanPropertyBindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;

import java.util.Map;
import java.util.Objects;

import static org.junit.jupiter.api.Assertions.*;

class ExceptionHandlerTest {

    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    @Test
    void handlesCampaignNotFoundAsNotFound() {
        ResponseEntity<ApiResponse<Void>> response = handler.handleNotFound(new CampaignNotFoundException(9L));

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        ApiResponse<Void> body = requireBody(response);
        assertEquals("Campaña no encontrada con id: 9", body.getMessage());
        assertFalse(body.isSuccess());
    }

    @Test
    void handlesInvalidTransitionAsConflict() {
        ResponseEntity<ApiResponse<Void>> response = handler.handleInvalidTransition(
                new InvalidStatusTransitionException("pendiente", "aprobada"));

        assertEquals(HttpStatus.CONFLICT, response.getStatusCode());
        assertEquals("Transición de estado inválida: 'pendiente' → 'aprobada'.",
            requireBody(response).getMessage());
    }

    @Test
    void handlesOptimisticLockAsConflictWithStableMessage() {
        ResponseEntity<ApiResponse<Void>> response = handler.handleOptimisticLock(
                new OptimisticLockingFailureException("stale"));

        assertEquals(HttpStatus.CONFLICT, response.getStatusCode());
        assertEquals("La campaña fue modificada por otro proceso. Recarga e intenta de nuevo.",
            requireBody(response).getMessage());
    }

    @Test
    void handlesIllegalArgumentAsBadRequest() {
        ResponseEntity<ApiResponse<Void>> response = handler.handleIllegalArg(new IllegalArgumentException("dato inválido"));

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertEquals("dato inválido", requireBody(response).getMessage());
    }

    @Test
    void handlesAccessDeniedAsForbidden() {
        ResponseEntity<ApiResponse<Void>> response = handler.handleAccessDenied(new AccessDeniedException("denied"));

        assertEquals(HttpStatus.FORBIDDEN, response.getStatusCode());
        assertEquals("No tienes permisos para realizar esta acción.", requireBody(response).getMessage());
    }

    @Test
    void handlesUnexpectedExceptionAsInternalServerError() {
        ResponseEntity<ApiResponse<Void>> response = handler.handleGeneric(new RuntimeException("boom"));

        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertEquals("Error interno del servidor.", requireBody(response).getMessage());
    }

    @Test
    void handlesValidationWithoutDefaultMessageAndKeepsFirstErrorPerField() throws NoSuchMethodException {
        BeanPropertyBindingResult bindingResult = new BeanPropertyBindingResult(
                new StatusUpdateRequest(), "request");
        bindingResult.addError(new FieldError("request", "estado", null, false, null, null, null));
        bindingResult.addError(new FieldError("request", "estado", "Segundo error"));
        MethodParameter parameter = new MethodParameter(
                Objects.requireNonNull(ExceptionHandlerTest.class.getDeclaredMethod(
                        "validationTarget", StatusUpdateRequest.class)), 0);

        ResponseEntity<ApiResponse<Map<String, String>>> response = handler.handleValidation(
                new MethodArgumentNotValidException(parameter, bindingResult));

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        ApiResponse<Map<String, String>> body = requireBody(response);
        assertFalse(body.isSuccess());
        assertEquals(Map.of("estado", "Valor inválido."), body.getData());
    }

    static void validationTarget(StatusUpdateRequest request) {
        // Supplies the controller parameter metadata required by Spring's exception.
    }

    private static <T> T requireBody(ResponseEntity<T> response) {
        T body = response.getBody();
        if (body == null) {
            return fail("La respuesta debe incluir un cuerpo.");
        }
        return body;
    }
}
