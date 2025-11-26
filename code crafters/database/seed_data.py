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
        ("History", "World history, civilizations, and events."),
        ("Science", "Physics, chemistry, and general science reads."),
        ("Biography", "Stories about influential people."),
        ("Children", "Middle-grade and young-reader selections."),
        ("Mystery", "Detective and thriller fiction."),
        ("Art", "Design, art theory, and creativity."),
        ("Travel", "Exploration, adventure, and travel writing."),
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
        ("Yuval", "Harari"),
        ("Michelle", "Obama"),
        ("Walter", "Isaacson"),
        ("Neil", "Gaiman"),
        ("Terry", "Pratchett"),
        ("Malcolm", "Gladwell"),
        ("Amor", "Towles"),
        ("James", "Clear"),
        ("Brene", "Brown"),
        ("Trevor", "Noah"),
        ("Tara", "Westover"),
        ("Delia", "Owens"),
        ("Paulo", "Coelho"),
        ("Alain", "de Botton"),
        ("Tom", "Kelley"),
        ("Frank", "Herbert"),
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
        ("Sapiens", "9780062316097", "History"),
        ("Educated", "9780399590504", "Biography"),
        ("Becoming", "9781524763138", "Biography"),
        ("The Night Circus", "9780307744432", "Fiction"),
        ("The Martian", "9780553418026", "Technology"),
        ("Good Omens", "9780060853983", "Mystery"),
        ("Outliers", "9780316017930", "Science"),
        ("Atomic Habits", "9780735211292", "Business"),
        ("Dune", "9780441172719", "Science"),
        ("Where the Crawdads Sing", "9780735219106", "Fiction"),
        ("The Alchemist", "9780062315008", "Travel"),
        ("The Art of Travel", "9780375725341", "Travel"),
        ("Creative Confidence", "9780385349360", "Art"),
        ("The Ocean at the End of the Lane", "9780062255656", "Children"),
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


def seed_book_copies() -> None:
    copies: List[Tuple[str, str]] = [
        ("Project Hail Mary", "Main Branch"),
        ("Project Hail Mary", "Tech Wing"),
        ("Kafka on the Shore", "Downtown"),
        ("Lean In", "Main Branch"),
        ("Sapiens", "History Corner"),
        ("Educated", "Biography Nook"),
        ("Becoming", "Biography Nook"),
        ("The Night Circus", "Fiction Aisle"),
        ("The Martian", "Tech Wing"),
        ("Good Omens", "Mystery Shelf"),
        ("Outliers", "Science Stack"),
        ("Atomic Habits", "Business Hub"),
        ("Dune", "Science Stack"),
        ("Where the Crawdads Sing", "Fiction Aisle"),
        ("The Alchemist", "Travel Loft"),
        ("The Art of Travel", "Travel Loft"),
        ("Creative Confidence", "Art Studio"),
        ("The Ocean at the End of the Lane", "Children's Section"),
    ]
    queries = [
        (
            """
            INSERT INTO book_copies (book_id, status, location)
            VALUES (
                (SELECT book_id FROM books WHERE title = %s LIMIT 1),
                'available',
                %s
            )
            """,
            (title, location),
        )
        for title, location in copies
    ]
    run_transaction(queries)

