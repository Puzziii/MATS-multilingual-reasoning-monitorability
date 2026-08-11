from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from typing import Any, Protocol

from ..models import ConditionCall


class RetryableProviderError(RuntimeError):
    """A transport or rate-limit failure that may be retried."""


class Provider(Protocol):
    name: str

    def generate(self, call: ConditionCall) -> Mapping[str, Any]:
        """Return adapter-normalized text fields without logging secrets."""


def redact_for_log(value: Any) -> Any:
    """Redact common credential-shaped fields before structured logging."""
    secret_keys = {
        "api_key",
        "apikey",
        "api-subscription-key",
        "api_subscription_key",
        "authorization",
        "access_token",
        "secret",
        "token",
    }
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if str(key).lower() in secret_keys else redact_for_log(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_for_log(item) for item in value]
    return value


def redact_secret_value(value: Any, secret: str) -> Any:
    """Remove an exact in-memory secret value from data before it is returned."""
    if not secret:
        return value
    if isinstance(value, Mapping):
        return {
            "[REDACTED]" if str(key) == secret else str(key): redact_secret_value(item, secret)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secret_value(item, secret) for item in value]
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]")
    return value


def sanitize_error(exc: BaseException) -> dict[str, str]:
    """Keep retry evidence useful without persisting credential-like values."""
    message = str(exc)
    message = re.sub(
        r"(?i)(bearer\s+)[^\s,;]+",
        lambda match: f"{match.group(1)}[REDACTED]",
        message,
    )
    message = re.sub(
        r"(?i)((?:api(?:[_ -]?(?:subscription[_ -]?)?)?key|authorization|access[_ -]?token|secret|token)\s*[:=]\s*)[^\s,;]+",
        lambda match: f"{match.group(1)}[REDACTED]",
        message,
    )
    return {"error_type": type(exc).__name__, "error_message": message[:500]}


def safe_log(logger: logging.Logger, event: str, **fields: Any) -> None:
    logger.info("%s", json.dumps(redact_for_log({"event": event, **fields}), sort_keys=True))
