"""Logging filters loaded before Django's application registry is initialized."""
import logging


class RedactOAuthQueryFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.args, tuple) and record.args and isinstance(record.args[0], str):
            line = record.args[0]
            if '/settings?' in line or '/api/auth/facebook/callback/?' in line:
                prefix, _, suffix = line.partition('?')
                protocol = suffix.rsplit(' ', 1)[-1]
                record.args = (prefix + '?[redacted] ' + protocol, *record.args[1:])
        return True
