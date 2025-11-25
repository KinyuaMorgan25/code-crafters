"""
High level helpers wrapping database operations.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from config import DEFAULT_LOAN_DAYS, FINE_PER_DAY, MAX_ACTIVE_LOANS, MAX_FINE_BEFORE_BLOCK, Pagination
from database.database import run_query, run_transaction


def fetch_book_catalog(
    *,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    pagination: Optional[Pagination] = None,
) -> List[Dict]:
    pagination = pagination or Pagination()
    filters = []
    params: List = []
    if search:
        filters.append("(b.title LIKE %s OR b.isbn LIKE %s)")
        pattern = f"%{search}%"
        params.extend([pattern, pattern])
    if category_id:
        filters.append("b.category_id = %s")
        params.append(category_id)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT
            b.book_id,
            b.title,
            b.isbn,
            c.name AS category_name,
            COUNT(CASE WHEN bc.status = 'available' THEN 1 END) AS available_copies
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN book_copies bc ON bc.book_id = b.book_id
        {where_clause}
        GROUP BY b.book_id
        ORDER BY b.title ASC
        LIMIT %s OFFSET %s
    """
    params.extend([pagination.page_size, pagination.offset])
    return run_query(query, tuple(params)) or []


def fetch_book_details(book_id: int) -> Optional[Dict]:
    query = """
        SELECT
            b.*,
            c.name AS category_name,
            GROUP_CONCAT(CONCAT(a.first_name, ' ', a.last_name) SEPARATOR ', ') AS authors
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN book_authors ba ON ba.book_id = b.book_id
        LEFT JOIN authors a ON a.author_id = ba.author_id
        WHERE b.book_id = %s
        GROUP BY b.book_id
    """
    return run_query(query, (book_id,), fetch="one")


def fetch_active_loans(user_id: int) -> List[Dict]:
    query = """
        SELECT
            bt.transaction_id,
            bt.borrow_date,
            bt.due_date,
            bt.status,
            bt.fine_amount,
            b.title
        FROM borrow_transactions bt
        JOIN book_copies bc ON bc.copy_id = bt.copy_id
        JOIN books b ON b.book_id = bc.book_id
        WHERE bt.user_id = %s AND bt.status IN ('borrowed', 'overdue')
        ORDER BY bt.due_date ASC
    """
    return run_query(query, (user_id,)) or []


def fetch_user_transactions(user_id: int) -> List[Dict]:
    query = """
        SELECT
            bt.*,
            b.title
        FROM borrow_transactions bt
        JOIN book_copies bc ON bc.copy_id = bt.copy_id
        JOIN books b ON b.book_id = bc.book_id
        WHERE bt.user_id = %s
        ORDER BY bt.borrow_date DESC
        LIMIT 100
    """
    return run_query(query, (user_id,)) or []


def _compute_fine(due_date: date, return_date: date) -> float:
    overdue_days = (return_date - due_date).days
    if overdue_days <= 0:
        return 0.0
    return round(overdue_days * FINE_PER_DAY, 2)


def borrow_book(user_id: int, book_id: int) -> Tuple[bool, str]:
    """Borrow the first available copy of the book."""
    if not book_id:
        return False, "Invalid book selection."
    fines = run_query(
        "SELECT total_fines FROM users WHERE user_id = %s",
        (user_id,),
        fetch="one",
    ) or {"total_fines": 0.0}
    if fines["total_fines"] > MAX_FINE_BEFORE_BLOCK:
        return False, "You have outstanding fines above the allowed limit."

    active_loans = run_query(
        """
        SELECT COUNT(*) AS count
        FROM borrow_transactions
        WHERE user_id = %s AND status IN ('borrowed', 'overdue')
        """,
        (user_id,),
        fetch="one",
    )
    if active_loans and active_loans["count"] >= MAX_ACTIVE_LOANS:
        return False, "Maximum active loans reached."

    copy = run_query(
        """
        SELECT copy_id FROM book_copies
        WHERE book_id = %s AND status = 'available'
        LIMIT 1
        """,
        (book_id,),
        fetch="one",
    )
    if not copy:
        return False, "No available copies at the moment."

    copy_id = copy["copy_id"]
    borrow_date = datetime.utcnow().date()
    due_date = borrow_date + timedelta(days=DEFAULT_LOAN_DAYS)

    queries = [
        (
            """
            INSERT INTO borrow_transactions
            (copy_id, user_id, borrow_date, due_date, status, fine_amount)
            VALUES (%s, %s, %s, %s, 'borrowed', 0.00)
            """,
            (copy_id, user_id, borrow_date, due_date),
        ),
        (
            "UPDATE book_copies SET status = 'borrowed' WHERE copy_id = %s",
            (copy_id,),
        ),
    ]
    run_transaction(queries)
    return True, "Book borrowed successfully."


def return_book(transaction_id: int) -> Tuple[bool, str]:
    transaction = run_query(
        """
        SELECT bt.*, bc.book_id
        FROM borrow_transactions bt
        JOIN book_copies bc ON bc.copy_id = bt.copy_id
        WHERE bt.transaction_id = %s
        """,
        (transaction_id,),
        fetch="one",
    )
    if not transaction:
        return False, "Transaction not found."

    if transaction["status"] == "returned":
        return False, "Book already returned."

    return_date = datetime.utcnow().date()
    fine = _compute_fine(transaction["due_date"], return_date)

    queries = [
        (
            """
            UPDATE borrow_transactions
            SET return_date = %s, status = 'returned', fine_amount = %s
            WHERE transaction_id = %s
            """,
            (return_date, fine, transaction_id),
        ),
        (
            "UPDATE book_copies SET status = 'available' WHERE copy_id = %s",
            (transaction["copy_id"],),
        ),
        (
            "UPDATE users SET total_fines = total_fines + %s WHERE user_id = %s",
            (fine, transaction["user_id"]),
        ),
    ]
    run_transaction(queries)
    return True, "Book returned successfully."


def create_reservation(user_id: int, book_id: int) -> Tuple[bool, str]:
    existing = run_query(
        """
        SELECT reservation_id FROM reservations
        WHERE user_id = %s AND book_id = %s AND status = 'pending'
        """,
        (user_id, book_id),
        fetch="one",
    )
    if existing:
        return False, "You already have an active reservation for this book."

    run_query(
        """
        INSERT INTO reservations (book_id, user_id, status)
        VALUES (%s, %s, 'pending')
        """,
        (book_id, user_id),
        fetch="none",
    )
    return True, "Reservation created. We will notify you when it's available."


def update_fine_totals() -> None:
    """
    Update overdue transactions and fines. This can be called manually
    from the admin dashboard.
    """
    overdue_transactions = run_query(
        """
        SELECT transaction_id, due_date
        FROM borrow_transactions
        WHERE status = 'borrowed' AND due_date < CURRENT_DATE()
        """
    )
    if not overdue_transactions:
        return

    queries = []
    today = datetime.utcnow().date()
    for tx in overdue_transactions:
        fine = _compute_fine(tx["due_date"], today)
        queries.append(
            (
                """
                UPDATE borrow_transactions
                SET status = 'overdue', fine_amount = %s
                WHERE transaction_id = %s
                """,
                (fine, tx["transaction_id"]),
            )
        )
    run_transaction(queries)


def fetch_dashboard_metrics() -> Dict[str, float]:
    metrics = {
        "active_loans": 0,
        "overdue": 0,
        "reservations": 0,
        "fines": 0.0,
    }
    rows = run_query(
        """
        SELECT
            (SELECT COUNT(*) FROM borrow_transactions WHERE status IN ('borrowed','overdue')) AS active_loans,
            (SELECT COUNT(*) FROM borrow_transactions WHERE status = 'overdue') AS overdue,
            (SELECT COUNT(*) FROM reservations WHERE status = 'pending') AS reservations,
            (SELECT SUM(fine_amount) FROM borrow_transactions) AS fines
        """,
        fetch="one",
    )
    if rows:
        metrics.update(
            {
                "active_loans": rows.get("active_loans", 0),
                "overdue": rows.get("overdue", 0),
                "reservations": rows.get("reservations", 0),
                "fines": rows.get("fines", 0.0) or 0.0,
            }
        )
    return metrics

