"""
Dataclasses mirroring the MySQL schema. Useful for type hints.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class User:
    user_id: int
    full_name: str
    email: str
    role: str
    password_hash: str
    total_fines: float
    created_at: datetime
    updated_at: datetime


@dataclass
class Category:
    category_id: int
    name: str
    description: Optional[str]


@dataclass
class Author:
    author_id: int
    first_name: str
    last_name: str
    biography: Optional[str]


@dataclass
class Book:
    book_id: int
    title: str
    isbn: str
    description: Optional[str]
    publisher: Optional[str]
    publication_year: Optional[int]
    category_id: Optional[int]


@dataclass
class BookCopy:
    copy_id: int
    book_id: int
    status: str
    location: Optional[str]


@dataclass
class BorrowTransaction:
    transaction_id: int
    copy_id: int
    user_id: int
    borrow_date: date
    due_date: date
    return_date: Optional[date]
    status: str
    fine_amount: float


@dataclass
class Reservation:
    reservation_id: int
    book_id: int
    user_id: int
    status: str
    created_at: datetime

