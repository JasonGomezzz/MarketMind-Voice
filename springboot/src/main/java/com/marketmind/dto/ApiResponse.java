package com.marketmind.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

/** Envelope estándar {success, message, data} — espeja el formato Django. */
@Data
@AllArgsConstructor
public class ApiResponse<T> {

    private boolean success;
    private String message;
    private T data;

    public static <T> ApiResponse<T> ok(String message, T data) {
        return new ApiResponse<>(true, message, data);
    }

    public static <T> ApiResponse<T> error(String message, T data) {
        return new ApiResponse<>(false, message, data);
    }
}
