package com.marketmind.exception;

public class InvalidStatusTransitionException extends RuntimeException {

    public InvalidStatusTransitionException(String currentStatus, String targetStatus) {
        super("Transición de estado inválida: '" + currentStatus + "' → '" + targetStatus + "'.");
    }
}
