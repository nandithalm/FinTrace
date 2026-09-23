"""Refuse PIN, OTP, password, transfer, and other-customer requests before NLU."""

from __future__ import annotations

import re

# Checked before Gemini. Intent stays unsafe_refusal so the trace is honest.
_UNSAFE = re.compile(
    r"\b(pin|otp|password|passwd)\b"
    r"|send money"
    r"|\btransfer\b"
    r"|another customer"
    r"|\brahul\b"
    r"|पिन|ओटीपी|पासवर्ड",
    re.IGNORECASE,
)


def is_unsafe(message: str) -> bool:
    return bool(_UNSAFE.search(message or ""))
