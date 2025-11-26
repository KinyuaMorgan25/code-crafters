"""
Utility helpers to bootstrap a lightweight SQLite database for local usage.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Tuple

from werkzeug.security import generate_password_hash

SCHEMA_STATEMENTS: Tuple[str, ...] = (
    """
    PRAGMA foreign_keys = ON;
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL DEFAULT 'user',
        password_hash TEXT NOT NULL,
        total_fines REAL NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS authors (
        author_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        biography TEXT,
        UNIQUE(first_name, last_name)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        isbn TEXT NOT NULL UNIQUE,
        description TEXT,
        publisher TEXT,
        publication_year INTEGER,
        category_id INTEGER,
        FOREIGN KEY(category_id) REFERENCES categories(category_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS book_authors (
        book_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        PRIMARY KEY (book_id, author_id),
        FOREIGN KEY(book_id) REFERENCES books(book_id) ON DELETE CASCADE,
        FOREIGN KEY(author_id) REFERENCES authors(author_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS book_copies (
        copy_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'available',
        location TEXT,
        FOREIGN KEY(book_id) REFERENCES books(book_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS borrow_transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        copy_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        borrow_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT 'borrowed',
        fine_amount REAL NOT NULL DEFAULT 0,
        FOREIGN KEY(copy_id) REFERENCES book_copies(copy_id),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(book_id) REFERENCES books(book_id),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
)


def _exec_many(cursor, statements: Iterable[str]) -> None:
    for stmt in statements:
        cursor.execute(stmt)


def _seed_categories(cursor) -> None:
    categories = [
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
    for name, desc in categories:
        cursor.execute(
            """
            INSERT OR IGNORE INTO categories (name, description)
            VALUES (?, ?)
            """,
            (name, desc),
        )


def _seed_authors(cursor) -> None:
    authors = [
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
    for first, last in authors:
        cursor.execute(
            """
            INSERT OR IGNORE INTO authors (first_name, last_name)
            VALUES (?, ?)
            """,
            (first, last),
        )


def _seed_books(cursor) -> None:
    books = [
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
    for title, isbn, category_name in books:
        cursor.execute(
            """
            INSERT OR IGNORE INTO books (title, isbn, description, category_id)
            VALUES (
                ?,
                ?,
                ?,
                (SELECT category_id FROM categories WHERE name = ? LIMIT 1)
            )
            """,
            (title, isbn, f"Sample description for {title}.", category_name),
        )


def _seed_book_authors(cursor) -> None:
    mapping = [
        ("Project Hail Mary", "Andy", "Weir"),
        ("Kafka on the Shore", "Haruki", "Murakami"),
        ("Lean In", "Sheryl", "Sandberg"),
        ("Sapiens", "Yuval", "Harari"),
        ("Educated", "Tara", "Westover"),
        ("Becoming", "Michelle", "Obama"),
        ("The Night Circus", "Amor", "Towles"),
        ("The Martian", "Andy", "Weir"),
        ("Good Omens", "Neil", "Gaiman"),
        ("Good Omens", "Terry", "Pratchett"),
        ("Outliers", "Malcolm", "Gladwell"),
        ("Atomic Habits", "James", "Clear"),
        ("Dune", "Frank", "Herbert"),
        ("Where the Crawdads Sing", "Delia", "Owens"),
        ("The Alchemist", "Paulo", "Coelho"),
        ("The Art of Travel", "Alain", "de Botton"),
        ("Creative Confidence", "Tom", "Kelley"),
        ("Creative Confidence", "Brene", "Brown"),
        ("The Ocean at the End of the Lane", "Neil", "Gaiman"),
    ]
    for title, first, last in mapping:
        cursor.execute(
            """
            INSERT OR IGNORE INTO book_authors (book_id, author_id)
            VALUES (
                (SELECT book_id FROM books WHERE title = ? LIMIT 1),
                (SELECT author_id FROM authors WHERE first_name = ? AND last_name = ? LIMIT 1)
            )
            """,
            (title, first, last),
        )


def _seed_book_copies(cursor) -> None:
    cursor.execute("SELECT COUNT(*) FROM book_copies")
    if cursor.fetchone()[0]:
        return
    copies = [
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
    for title, location in copies:
        cursor.execute(
            """
            INSERT INTO book_copies (book_id, location, status)
            VALUES (
                (SELECT book_id FROM books WHERE title = ? LIMIT 1),
                ?,
                'available'
            )
            """,
            (title, location),
        )


def _seed_users(cursor) -> None:
    admin_email = "kinyuamorgan90@gmail.com"
    admin_password = "admin123"
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (full_name, email, role, password_hash, total_fines)
        VALUES (?, ?, 'admin', ?, 0)
        """,
        (
            "Library Admin",
            admin_email,
            generate_password_hash(admin_password, method="scrypt"),
        ),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (full_name, email, role, password_hash, total_fines)
        VALUES (?, ?, 'user', ?, 0)
        """,
        (
            "Sample Patron",
            "patron@example.com",
            generate_password_hash("patron123", method="scrypt"),
        ),
    )


def _seed_transactions(cursor) -> None:
    # Only add demo data if table is empty.
    cursor.execute("SELECT COUNT(*) FROM borrow_transactions")
    if cursor.fetchone()[0]:
        return
    cursor.execute(
        """
        SELECT copy_id FROM book_copies
        WHERE book_id = (SELECT book_id FROM books WHERE title = 'Project Hail Mary' LIMIT 1)
        LIMIT 1
        """
    )
    copy_row = cursor.fetchone()
    if not copy_row:
        return
    copy_id = copy_row[0]
    cursor.execute(
        "SELECT user_id FROM users WHERE email = 'patron@example.com' LIMIT 1"
    )
    user_row = cursor.fetchone()
    if not user_row:
        return
    user_id = user_row[0]
    borrow_date = datetime.utcnow().date()
    due_date = borrow_date + timedelta(days=14)
    cursor.execute(
        """
        INSERT INTO borrow_transactions
        (copy_id, user_id, borrow_date, due_date, status, fine_amount)
        VALUES (?, ?, ?, ?, 'borrowed', 0)
        """,
        (copy_id, user_id, str(borrow_date), str(due_date)),
    )
    cursor.execute(
        "UPDATE book_copies SET status = 'borrowed' WHERE copy_id = ?", (copy_id,)
    )


def bootstrap_sqlite(conn) -> None:
    """
    Ensure schema and sample data exist for SQLite deployments.
    """
    cursor = conn.cursor()
    _exec_many(cursor, SCHEMA_STATEMENTS)
    _seed_categories(cursor)
    _seed_authors(cursor)
    _seed_books(cursor)
    _seed_book_authors(cursor)
    _seed_users(cursor)
    _seed_book_copies(cursor)
    _seed_transactions(cursor)
    conn.commit()

