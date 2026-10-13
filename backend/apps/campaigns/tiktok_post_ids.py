"""Normalize only IDs from authenticated Content Posting responses/events."""
import re


def public_post_id(value):
    if type(value) is int and 0 < value <= 2**63 - 1:
        return str(value)
    if isinstance(value, str) and re.fullmatch(r'[0-9]{1,19}', value) and 0 < int(value) <= 2**63 - 1:
        return value
    return None
