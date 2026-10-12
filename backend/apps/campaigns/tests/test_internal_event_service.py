from unittest.mock import patch
from django.test import override_settings
from services.internal_event_service import notify_campaign_submitted


@override_settings(INTERNAL_EVENT_TOKEN='')
def test_internal_events_require_private_configuration():
    with patch('services.internal_event_service.requests.post') as send:
        notify_campaign_submitted(1)
        send.assert_not_called()
