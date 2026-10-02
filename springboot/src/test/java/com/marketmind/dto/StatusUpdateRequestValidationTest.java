package com.marketmind.dto;

import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class StatusUpdateRequestValidationTest {

    private static ValidatorFactory validatorFactory;
    private static Validator validator;

    @BeforeAll
    static void setUpValidator() {
        validatorFactory = Validation.buildDefaultValidatorFactory();
        validator = validatorFactory.getValidator();
    }

    @AfterAll
    static void closeValidator() {
        validatorFactory.close();
    }

    @Test
    void acceptsCompleteRequest() {
        StatusUpdateRequest request = new StatusUpdateRequest();
        request.setEstado("aprobada");
        request.setVersion(4);
        request.setValoracion(5);

        assertTrue(validator.validate(request).isEmpty());
    }

    @Test
    void rejectsMissingRequiredFields() {
        Set<?> violations = validator.validate(new StatusUpdateRequest());

        assertEquals(3, violations.size());
    }

    @Test
    void rejectsBlankStatus() {
        StatusUpdateRequest request = new StatusUpdateRequest();
        request.setEstado(" ");
        request.setVersion(1);
        request.setValoracion(3);

        assertEquals(1, validator.validate(request).size());
    }
}
