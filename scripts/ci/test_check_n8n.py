import copy
from pathlib import Path
import tempfile
import unittest

from check_n8n import check_file, validate_workflow


class WorkflowGuardTests(unittest.TestCase):
    def setUp(self):
        guard = "const t = $input.first().json.headers['x-nexomark-token']; const e = $env.N8N_WEBHOOK_TOKEN;"
        self.workflow = {
            "nodes": [
                {"id": "1", "name": "Input", "type": "n8n-nodes-base.webhook",
                 "parameters": {"responseMode": "responseNode"}},
                {"id": "3", "name": "Guard", "type": "n8n-nodes-base.code", "parameters": {"jsCode": guard}},
                {"id": "2", "name": "Request", "type": "n8n-nodes-base.httpRequest", "parameters": {}},
            ],
            "connections": {
                "Input": {"main": [[{"node": "Guard", "type": "main", "index": 0}]]},
                "Guard": {"main": [[{"node": "Request", "type": "main", "index": 0}]]},
            },
        }

    def test_environment_expression_and_credential_reference_are_allowed(self):
        self.workflow["nodes"][2]["parameters"]["headers"] = [
            {"name": "x-goog-api-key", "value": "={{ $env.GEMINI_API_KEY }}"}]
        self.workflow["nodes"][2]["credentials"] = {"httpHeaderAuth": {"id": "ref-1", "name": "server-key"}}
        self.assertEqual(validate_workflow(self.workflow), [])

    def test_known_key_in_code_is_detected_without_disclosing_it(self):
        key = "AIza" + "X" * 35
        self.workflow["nodes"][2]["parameters"]["jsCode"] = f"const key = '{key}';"
        issues = validate_workflow(self.workflow)
        self.assertTrue(issues)
        self.assertNotIn(key, str(issues))

    def test_literal_auth_header_is_rejected(self):
        self.workflow["nodes"][2]["parameters"]["headers"] = [
            {"name": "Authorization", "value": "a-private-value"}]
        self.assertTrue(validate_workflow(self.workflow))

    def test_unknown_destination_and_duplicate_identity_are_rejected(self):
        dangling = copy.deepcopy(self.workflow)
        dangling["connections"]["Guard"]["main"][0][0]["node"] = "Missing"
        self.assertTrue(validate_workflow(dangling))
        self.workflow["nodes"][2]["id"] = "1"
        self.assertTrue(validate_workflow(self.workflow))

    def test_invalid_json_fails_without_source_dump(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text('{"secret": "private-input",')
            issues = check_file(path)
            self.assertTrue(issues)
            self.assertNotIn("private-input", str(issues))

    def test_missing_or_malformed_graph_fails(self):
        for bad in [[], {}, {"nodes": [None], "connections": {}},
                    {"nodes": self.workflow["nodes"], "connections": {"Input": {"main": [None]}}}]:
            with self.subTest(document=bad):
                self.assertTrue(validate_workflow(bad))

    def test_duplicate_json_fields_cannot_hide_an_embedded_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"secret": "private-input", "secret": "REDACTED"}')
            issues = check_file(path)
            self.assertTrue(issues)
            self.assertNotIn("private-input", str(issues))

    def test_webhook_that_answers_before_the_token_check_is_rejected(self):
        self.workflow["nodes"][0]["parameters"]["responseMode"] = "onReceived"
        self.assertTrue(validate_workflow(self.workflow))

    def test_webhook_without_a_token_guard_first_is_rejected(self):
        self.workflow["connections"]["Input"]["main"][0][0]["node"] = "Request"
        self.assertTrue(validate_workflow(self.workflow))
        self.workflow["connections"]["Input"]["main"][0][0]["node"] = "Guard"
        self.workflow["nodes"][1]["parameters"]["jsCode"] = "return $input.all();"
        self.assertTrue(validate_workflow(self.workflow))

    def test_callback_url_from_payload_is_rejected(self):
        self.workflow["nodes"][2]["parameters"]["url"] = "={{ $json.body.callback_url }}"
        self.assertTrue(validate_workflow(self.workflow))

    def test_django_callback_needs_the_shared_secret_header(self):
        params = self.workflow["nodes"][2]["parameters"]
        params["url"] = "={{ $env.DJANGO_CALLBACK_BASE_URL }}/api/campaigns/webhook/ia-result/"
        self.assertTrue(validate_workflow(self.workflow))
        params["sendHeaders"] = True
        params["headerParameters"] = {"parameters": [
            {"name": "X-NexoMark-Token", "value": "={{ $env.N8N_WEBHOOK_TOKEN }}"}]}
        self.assertEqual(validate_workflow(self.workflow), [])

    def test_literal_shared_secret_header_is_rejected(self):
        params = self.workflow["nodes"][2]["parameters"]
        params["headerParameters"] = {"parameters": [{"name": "X-NexoMark-Token", "value": "a-private-value"}]}
        issues = validate_workflow(self.workflow)
        self.assertTrue(issues)
        self.assertNotIn("a-private-value", str(issues))


if __name__ == "__main__":
    unittest.main()
