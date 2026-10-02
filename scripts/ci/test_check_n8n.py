import copy
from pathlib import Path
import tempfile
import unittest

from check_n8n import check_file, validate_workflow


class WorkflowGuardTests(unittest.TestCase):
    def setUp(self):
        self.workflow = {
            "nodes": [
                {"id": "1", "name": "Input", "type": "n8n-nodes-base.webhook", "parameters": {}},
                {"id": "2", "name": "Request", "type": "n8n-nodes-base.httpRequest", "parameters": {}},
            ],
            "connections": {"Input": {"main": [[{"node": "Request", "type": "main", "index": 0}]]}},
        }

    def test_environment_expression_and_credential_reference_are_allowed(self):
        self.workflow["nodes"][1]["parameters"]["headers"] = [
            {"name": "x-goog-api-key", "value": "={{ $env.GEMINI_API_KEY }}"}]
        self.workflow["nodes"][1]["credentials"] = {"httpHeaderAuth": {"id": "ref-1", "name": "server-key"}}
        self.assertEqual(validate_workflow(self.workflow), [])

    def test_known_key_in_code_is_detected_without_disclosing_it(self):
        key = "AIza" + "X" * 35
        self.workflow["nodes"][1]["parameters"]["jsCode"] = f"const key = '{key}';"
        issues = validate_workflow(self.workflow)
        self.assertTrue(issues)
        self.assertNotIn(key, str(issues))

    def test_literal_auth_header_is_rejected(self):
        self.workflow["nodes"][1]["parameters"]["headers"] = [
            {"name": "Authorization", "value": "a-private-value"}]
        self.assertTrue(validate_workflow(self.workflow))

    def test_unknown_destination_and_duplicate_identity_are_rejected(self):
        dangling = copy.deepcopy(self.workflow)
        dangling["connections"]["Input"]["main"][0][0]["node"] = "Missing"
        self.assertTrue(validate_workflow(dangling))
        self.workflow["nodes"][1]["id"] = "1"
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


if __name__ == "__main__":
    unittest.main()
