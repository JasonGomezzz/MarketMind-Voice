"""Static checks only: exported graph integrity and common embedded credentials.

No nodes, expressions or JavaScript are executed. Findings never include values.
This is not an n8n runtime validator or a complete repository secret scanner.
"""
import json
from pathlib import Path
import re
import sys

KNOWN_SECRETS = [
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"\bre_[0-9A-Za-z_]{20,}\b"),
    re.compile(r"\bsk-(?:proj-)?[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9+/_.=-]{20,}", re.IGNORECASE),
    re.compile(r"[?&](?:key|api_key|access_token)=[A-Za-z0-9_-]{20,}", re.IGNORECASE),
]
SENSITIVE_FIELDS = {"apikey", "password", "secret", "accesstoken", "refreshtoken", "authorization", "xgoogapikey"}


def configured_reference(value):
    """Accept n8n expressions or conspicuous placeholders, not literal credentials."""
    return (not value or value.startswith("={{") and value.endswith("}}")
            or value.startswith("${") and value.endswith("}")
            or value.startswith("<") and value.endswith(">")
            or value.upper() in {"REDACTED", "CHANGEME", "PLACEHOLDER"})


def inspect_secrets(value, location, issues):
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in KNOWN_SECRETS):
            issues.append(f"{location}: possible embedded credential (value redacted)")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            inspect_secrets(item, f"{location}[{i}]", issues)
    elif isinstance(value, dict):
        for key, item in value.items():
            child = f"{location}.{key}"
            normalized = re.sub(r"[^a-z]", "", key.lower())
            if normalized in SENSITIVE_FIELDS and isinstance(item, str) and not configured_reference(item):
                issues.append(f"{child}: literal credential field (value redacted)")
            inspect_secrets(item, child, issues)
        # n8n HTTP headers use name/value pairs instead of named JSON fields.
        name = value.get("name")
        header_value = value.get("value")
        if (isinstance(name, str) and re.sub(r"[^a-z]", "", name.lower()) in SENSITIVE_FIELDS
                and isinstance(header_value, str) and not configured_reference(header_value)):
            issues.append(f"{location}.value: literal credential header (value redacted)")


def validate_workflow(document):
    issues = []
    inspect_secrets(document, "$", issues)
    if not isinstance(document, dict):
        return issues + ["$: workflow must be an object"]
    nodes = document.get("nodes")
    connections = document.get("connections")
    if not isinstance(nodes, list) or not nodes:
        return issues + ["$.nodes: nonempty node list required"]
    if not isinstance(connections, dict):
        return issues + ["$.connections: object required"]
    names, ids = set(), set()
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            issues.append(f"$.nodes[{i}]: object required")
            continue
        for field, seen in [("name", names), ("id", ids)]:
            value = node.get(field)
            if not isinstance(value, str) or not value or value in seen:
                issues.append(f"$.nodes[{i}].{field}: unique nonempty string required")
            else:
                seen.add(value)
        if not isinstance(node.get("type"), str) or not node["type"]:
            issues.append(f"$.nodes[{i}].type: nonempty string required")
        if not isinstance(node.get("parameters"), dict):
            issues.append(f"$.nodes[{i}].parameters: object required")
    for source, outputs in connections.items():
        if source not in names or not isinstance(outputs, dict):
            issues.append("$.connections: unknown source or invalid outputs")
            continue
        for groups in outputs.values():
            if not isinstance(groups, list):
                issues.append("$.connections: output groups must be a list")
                continue
            for group in groups:
                if not isinstance(group, list):
                    issues.append("$.connections: output edges must be a list")
                    continue
                for edge in group:
                    if (not isinstance(edge, dict) or not isinstance(edge.get("node"), str)
                            or edge["node"] not in names
                            or not isinstance(edge.get("type"), str)
                            or type(edge.get("index")) is not int or edge["index"] < 0):
                        issues.append("$.connections: malformed edge or unknown destination")
    return issues


def check_file(path):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate object key")
            result[key] = value
        return result

    try:
        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (OSError, ValueError) as error:
        # Never print source snippets or duplicate keys, which could hold credentials.
        return [f"unable to read valid JSON ({type(error).__name__})"]
    return validate_workflow(document)


def main():
    root = Path(__file__).resolve().parents[2]
    files = sorted((root / "n8n").glob("*.json"))
    if not files:
        print("ERROR: no n8n JSON exports found", file=sys.stderr)
        return 1
    failed = False
    for path in files:
        issues = check_file(path)
        for issue in issues:
            print(f"ERROR {path.relative_to(root)}: {issue}", file=sys.stderr)
        failed |= bool(issues)
        if not issues:
            print(f"OK {path.relative_to(root)}: JSON, graph references and credential patterns")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
