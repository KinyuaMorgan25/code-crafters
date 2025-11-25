"""
Utilities to add optional seed data for local testing.
"""

from __future__ import annotations

from typing import List, Tuple

from database.database import run_transaction


def seed_categories() -> None:
    categories: List[Tuple[str, str]] = [
        ("Technology", "Books covering software engineering and hardware."),
        ("Fiction", "Novels and short stories."),
        ("Business", "Finance, leadership, and entrepreneurship."),
    ]
    queries = [
        (
            "INSERT INTO categories (name, description) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE description = VALUES(description)",
            (name, desc),
        )
        for name, desc in categories
    ]
    run_transaction(queries)


def seed_authors() -> None:
    authors: List[Tuple[str, str]] = [
        ("Andy", "Weir"),
        ("Haruki", "Murakami"),
        ("Sheryl", "Sandberg"),
    ]
    queries = [
        (
            "INSERT INTO authors (first_name, last_name) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE last_name = last_name",
            (first, last),
        )
        for first, last in authors
    ]
    run_transaction(queries)


def seed_books() -> None:
    books: List[Tuple[str, str, str]] = [
        ("Project Hail Mary", "9780593135204", "Technology"),
        ("Kafka on the Shore", "9781400079278", "Fiction"),
        ("Lean In", "9780385349949", "Business"),
    ]
    queries = []
    for title, isbn, category in books:
        queries.append(
            (
                """
                INSERT INTO books (title, isbn, description, category_id)
                VALUES (
                    %s,
                    %s,
                    %s,
                    (SELECT category_id FROM categories WHERE name = %s LIMIT 1)
                )
                ON DUPLICATE KEY UPDATE description = VALUES(description)
                """,
                (title, isbn, f"Sample description for {title}.", category),
            )
        )
    run_transaction(queries)

