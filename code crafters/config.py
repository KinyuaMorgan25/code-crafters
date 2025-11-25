"""
Global configuration settings for the Library Management System.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_LOAN_DAYS = 14
MAX_ACTIVE_LOANS = 5
MAX_FINE_BEFORE_BLOCK = 10.0
FINE_PER_DAY = 0.50


def _from_streamlit_secrets(key: str) -> Optional[Any]:
    """Return values stored in Streamlit secrets if present."""
    if hasattr(st, "secrets") and "mysql" in st.secrets:
        return st.secrets["mysql"].get(key)
    return None


def get_mysql_config() -> Dict[str, Any]:
    """
    Read database credentials from Streamlit secrets or env vars.

    Environment variable fallbacks use the MYSQL_* convention.
    """
    keys = ("host", "user", "password", "database", "port")
    config: Dict[str, Any] = {}
    for key in keys:
        secret_value = _from_streamlit_secrets(key)
        env_value = os.getenv(f"MYSQL_{key.upper()}")
        if secret_value is not None:
            config[key] = secret_value
        elif env_value is not None:
            config[key] = env_value

    config.setdefault("host", "localhost")
    config.setdefault("user", "root")
    config.setdefault("password", "")
    config.setdefault("database", "library_system")
    config["port"] = int(config.get("port", 3306))
    return config


@dataclass
class Pagination:
    """Helper dataclass for pagination metadata."""

    page: int = 1
    page_size: int = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

