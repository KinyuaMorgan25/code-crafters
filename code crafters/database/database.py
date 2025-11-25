"""
Low-level database helpers built on top of mysql-connector.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import mysql.connector
from mysql.connector import Error, pooling

from config import get_mysql_config

logger = logging.getLogger(__name__)

_pool: Optional[pooling.MySQLConnectionPool] = None


def _ensure_pool() -> pooling.MySQLConnectionPool:
    """Create a global connection pool reused across the app."""
    global _pool
    if _pool is None:
        config = get_mysql_config()
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="library_pool",
                pool_size=5,
                pool_reset_session=True,
                **config,
            )
        except Error as exc:
            logger.error("Unable to create connection pool: %s", exc)
            raise
    return _pool


@contextmanager
def get_db_connection():
    """Context manager yielding a pooled connection."""
    pool = _ensure_pool()
    conn = pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()


def run_query(
    query: str,
    params: Optional[Union[Tuple[Any, ...], List[Any]]] = None,
    *,
    fetch: str = "all",
    dictionary: bool = True,
) -> Union[List[Dict[str, Any]], Dict[str, Any], int, None]:
    """
    Execute a single query and optionally fetch rows.

    fetch: "all" (default), "one", or "none". When "none", the affected-row
    count is returned.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            cursor.execute(query, params or ())
            if fetch == "all":
                return cursor.fetchall()
            if fetch == "one":
                return cursor.fetchone()
            conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()


def run_transaction(queries: Iterable[Tuple[str, Tuple[Any, ...]]]) -> None:
    """
    Execute multiple queries atomically.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            for query, params in queries:
                cursor.execute(query, params)
            conn.commit()
        except Error as exc:
            conn.rollback()
            logger.error("Transaction failed: %s", exc)
            raise
        finally:
            cursor.close()

