from __future__ import annotations
import re
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict
from bookstore.errors import ValidationError

class Book:
    """
    Доменна сутність книги
    Інваріанти: 
    - title/author: непорожні рядки
    - isbn: нормалізований (без дефісів)
    - price_cents: int >= 0
    -  quantity: int >= 0
    """
    _ISBN_RE = re.compile(r'^[0-9]{9}[0-9X]$|^[0-9]{13}$')

    def __init__(self, title: str, author: str, isbn: str, 
                 price: Decimal | float | str,
                 currency: str="USD", quantity: int=0, *,
                 book_id: str | None=None, 
                 archived: bool=False, created_at: datetime | None=None):
        self.id: str = book_id or str(uuid.uuid4())
        self.created_at: datetime = created_at or datetime.now()
        self.title = self._validate_non_empty("title", title)
        self.author = self._validate_non_empty("author", author)
        self.isbn: str = self._normalize_isbn(isbn)
        if not self._ISBN_RE.match(self.isbn):
            raise ValidationError("isbn", "Must be 10 or 13 digits")
        self.currency: str = self._validate_currency(currency)
        self._price_cents: int = self._to_cents(price)
        self.quantity:int = self._validate_non_negative_int("quantity", quantity)
        self.archived: bool = archived

    @property
    def price(self) -> Decimal:
        return Decimal(self._price_cents) / Decimal(100)
    
    @price.setter
    def price(self, value: Decimal | float | str):
        self._price_cents = self._to_cents(value)

    @property
    def price_cents(self) -> int:
        return self._price_cents
    
    def increase_stock(self, n: int):
        inc = self._validate_positive_int("n", n)
        self.quantity += inc 
    
    def decrease_stock(self, n: int):
        dec = self._validate_positive_int("n", n)
        if dec > self.quantity:
            raise ValidationError("quantity", f"Cannot decrease by {dec}: only {self.quantity} in stock.")
        self.quantity -= dec 

    def mark_archived(self):
        self.archived = True

    def is_available(self) -> bool:
        return (not self.archived) and (self.quantity > 0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "price_cents": self._price_cents,
            "currency": self.currency,
            "quantity": self.quantity,
            "archived": self.archived,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Book":
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else None
        price = Decimal(int(data["price_cents"])) / Decimal(100)
        return cls(
            title=data["title"],
            author=data["author"],
            isbn=data["isbn"],
            price=price,
            currency=data.get("currency", "USD"),
            quantity=int(data.get("quantity", 0)),
            book_id=data.get("id"),
            archived=bool(data.get("archived", False)),
            created_at=created_at
        )
    
    def __repr__(self):
        return (
                f"Book(id={self.id!r}, title={self.title!r}, author={self.author!r}, "
                f"isbn={self.isbn!r}, price={self.price!r}, currency={self.currency!r}, "
                f"qty={self.quantity!r}, archived={self.archived!r})"
                )
    
    def __eq__(self, other):
        if not isinstance(other, Book):
            return NotImplemented
        return self.id == other.id 
    
    @staticmethod
    def _validate_non_empty(field: str, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(field, "Must be a non-empty string")
        return value.strip()

    @staticmethod
    def _validate_non_negative_int(field: str, value: int) -> int:
        if not isinstance(value, int) or value < 0:
            raise ValidationError(field, "Must be a non-negative integer")
        return value

    @staticmethod
    def _validate_positive_int(field: str, value: int) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValidationError(field, "Must be a positive integer")
        return value

    @staticmethod
    def _validate_currency(value: str) -> str:
        if not isinstance(value, str) or not value.strip(): 
            raise ValidationError("currency", "Must be a non-empty string")
        return value.strip().upper()
    
    @staticmethod
    def _normalize_isbn(raw: str) -> str:
        if not isinstance(raw, str):
            raise ValidationError("isbn", "ISBN must be a string")
        cleaned = re.sub(r"[- ]", "", raw).upper()
        return cleaned
    
    @staticmethod
    def _to_cents(amount: Decimal | float | str) -> int:
        try:
            dec = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            raise ValidationError("price", "Invalid numeric amount")
        if dec < 0:
            raise ValidationError("price", "Must be >= 0")
        cents = int((dec * 100).quantize(Decimal("1")))
        return cents