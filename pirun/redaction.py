from __future__ import annotations

import re


SECRET_KEY_VALUE_PATTERN = re.compile(
    r"(?i)(?P<prefix>[\"']?\b(?:password|token|secret|api[_-]?key)[\"']?\s*[:=]\s*[\"']?)"
    r"(?P<secret>[^\"',\s}\]]+)"
    r"(?P<suffix>[\"']?)"
)
PASSWORD_ASSIGNMENT_PATTERN = re.compile(r"(?i)\bpassword\s*=\s*[^,\s]+")
AUTHORIZATION_BEARER_PATTERN = re.compile(
    r"(?i)(?P<prefix>\bauthorization\s*[:=]\s*bearer\s+)(?P<secret>[A-Za-z0-9._~+/-]+)"
)
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL)
RAW_SECRET_VALUE_PATTERN = re.compile(r"raw-secret-value")

SCAN_PATTERNS = [
    ("password_assignment", PASSWORD_ASSIGNMENT_PATTERN),
    ("secret_key_value", SECRET_KEY_VALUE_PATTERN),
    ("authorization_bearer", AUTHORIZATION_BEARER_PATTERN),
    ("private_key", PRIVATE_KEY_PATTERN),
    ("raw_secret_value", RAW_SECRET_VALUE_PATTERN),
]


def redact_text(text: str) -> str:
    redacted = PRIVATE_KEY_PATTERN.sub("[REDACTED_PRIVATE_KEY]", text)
    redacted = AUTHORIZATION_BEARER_PATTERN.sub(r"\g<prefix>[REDACTED]", redacted)
    redacted = SECRET_KEY_VALUE_PATTERN.sub(r"\g<prefix>[REDACTED]\g<suffix>", redacted)
    redacted = RAW_SECRET_VALUE_PATTERN.sub("[REDACTED]", redacted)
    return redacted
