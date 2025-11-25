"""
Input validation helpers.
"""

from __future__ import annotations

import re
from typing import Tuple

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(value: str) -> bool:
    return bool(value and EMAIL_REGEX.match(value))


def validate_password_strength(value: str) -> Tuple[bool, str]:
    if len(value) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", value):
        return False, "Include at least one uppercase letter."
    if not re.search(r"[a-z]", value):
        return False, "Include at least one lowercase letter."
    if not re.search(r"\d", value):
        return False, "Include at least one number."
    return True, ""

