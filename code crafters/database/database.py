"""
Low-level database helpers built on top of mysql-connector.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import mysql.connector
from mysql.connector import Error, pooling
import sqlite3

from config import get_db_backend, get_mysql_config, get_sqlite_path
from database.sqlite_bootstrap import bootstrap_sqlite

logger = logging.getLogger(__name__)

_pool: Optional[pooling.MySQLConnectionPool] = None
_sqlite_conn: Optional[sqlite3.Connection] = None
_sqlite_bootstrapped = False
_DB_BACKEND = get_db_backend()


def _prepare_sql(query: str) -> str:
    if _DB_BACKEND == "sqlite":
        return query.replace("%s", "?")
    return query


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


def _ensure_sqlite_conn() -> sqlite3.Connection:
    """Create a singleton SQLite connection."""
    global _sqlite_conn, _sqlite_bootstrapped
    if _sqlite_conn is None:
        db_path = get_sqlite_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        bootstrap_sqlite(conn)
        _sqlite_conn = conn
        _sqlite_bootstrapped = True
    elif not _sqlite_bootstrapped:
        conn = _sqlite_conn
        conn.execute("PRAGMA foreign_keys = ON;")
        bootstrap_sqlite(conn)
        _sqlite_bootstrapped = True
    return _sqlite_conn


@contextmanager
def get_db_connection():
    """Context manager yielding a connection for the configured backend."""
    if _DB_BACKEND == "sqlite":
        conn = _ensure_sqlite_conn()
        try:
            yield conn
        finally:
            # SQLite connection is reused globally; do not close here.
            pass
    else:
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
        sql = _prepare_sql(query)
        if _DB_BACKEND == "sqlite":
            cursor = conn.cursor()
        else:
            cursor = conn.cursor(dictionary=dictionary)
        try:
            cursor.execute(sql, params or ())
            if fetch == "all":
                rows = cursor.fetchall()
                if _DB_BACKEND == "sqlite" and dictionary:
                    return [dict(row) for row in rows]
                return rows
            if fetch == "one":
                row = cursor.fetchone()
                if _DB_BACKEND == "sqlite" and dictionary and row is not None:
                    return dict(row)
                return row
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
                cursor.execute(_prepare_sql(query), params)
            conn.commit()
        except Exception as exc:  # sqlite3 and mysql share similar handling
            conn.rollback()
            logger.error("Transaction failed: %s", exc)
            raise
        finally:
            cursor.close()

