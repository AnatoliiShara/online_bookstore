from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from bookstore.errors import ValidationError


@dataclass(frozen=True)
class Sale:
    """Іммутабельна транзакція продажу книги.
    Поля:
    - sale_id: UUID цього продажу
    - book_id: UUID книги (зв'язок з Book.id)
    - isbn: нормалізований
    - qty: кількість проданих примірників
    - unit_price_cents: ціна за одиницю
    - currency: валюта
    - timestamp: час продажу
    """

    sale_id: str
    book_id: str
    isbn: str
    qty: int
    unit_price_cents: int
    currency: str
    timestamp: datetime

    _ISBN_RE = re.compile(r"^[0-9]{9}[0-9X]$|^[0-9]{13}$")

    @classmethod
    def create(
        cls,
        *,
        book_id: str,
        isbn: str,
        qty: int,
        unit_price_cents: int,
        currency: str,
        timestamp: datetime | None = None,
    ) -> "Sale":
        cls._validate_non_empty("book_id", book_id)
        cls._validate_positive_int("qty", qty)
        cls._validate_non_negative_int("unit_price_cents", unit_price_cents)

        norm_isbn = cls._normalize_isbn(isbn)
        norm_currency = cls._normalize_currency(currency)

        return cls(
            sale_id=str(uuid.uuid4()),
            book_id=book_id.strip(),
            isbn=norm_isbn,
            qty=qty,
            unit_price_cents=unit_price_cents,
            currency=norm_currency,
            timestamp=timestamp or datetime.now(),
        )

    @property
    def unit_price(self) -> Decimal:
        return Decimal(self.unit_price_cents) / Decimal(100)

    @property
    def total_cents(self) -> int:
        return self.unit_price_cents * self.qty

    @property
    def total(self) -> Decimal:
        return Decimal(self.total_cents) / Decimal(100)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sale_id": self.sale_id,
            "book_id": self.book_id,
            "isbn": self.isbn,
            "qty": self.qty,
            "unit_price_cents": self.unit_price_cents,
            "currency": self.currency,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sale":
        ts = datetime.fromisoformat(data["timestamp"])
        return cls(
            sale_id=data["sale_id"],
            book_id=data["book_id"],
            isbn=data["isbn"],
            qty=int(data["qty"]),
            unit_price_cents=int(data["unit_price_cents"]),
            currency=data.get("currency", "USD"),
            timestamp=ts,
        )

    def __repr__(self) -> str:
        return (
            f"Sale(sale_id={self.sale_id!r}, book_id={self.book_id!r}, "
            f"isbn={self.isbn!r}, qty={self.qty!r}, "
            f"unit_price={self.unit_price!r}, currency={self.currency!r}, "
            f"total={self.total!r}, timestamp={self.timestamp.isoformat()})"
        )

    @staticmethod
    def _normalize_isbn(raw: str) -> str:
        if not isinstance(raw, str):
            raise ValidationError("isbn", "Must be a string")
        cleaned = re.sub(r"[-\s]", "", raw).upper()
        if not Sale._ISBN_RE.match(cleaned):
            raise ValidationError("isbn", "Must be 10 or 13 digits")
        return cleaned

    @staticmethod
    def _normalize_currency(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("currency", "Must be a non-empty string")
        return value.strip().upper()

    @staticmethod
    def _validate_non_empty(field: str, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(field, "Must be a non-empty string")

    @staticmethod
    def _validate_positive_int(field: str, value: int) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValidationError(field, "Must be a positive integer")
        return value

    @staticmethod
    def _validate_non_negative_int(field: str, value: int) -> int:
        if not isinstance(value, int) or value < 0:
            raise ValidationError(field, "Must be a non-negative integer")
        return value
