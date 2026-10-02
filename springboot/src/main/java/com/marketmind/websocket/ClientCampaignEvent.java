package com.marketmind.websocket;

/** Notification only; clients retrieve campaign contents from the authenticated API. */
public record ClientCampaignEvent(String type, Long campaignId, String recipientEmail) {}
