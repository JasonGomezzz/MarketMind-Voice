package com.marketmind.exception;

public class CampaignNotFoundException extends RuntimeException {

    public CampaignNotFoundException(Long id) {
        super("Campaña no encontrada con id: " + id);
    }
}
