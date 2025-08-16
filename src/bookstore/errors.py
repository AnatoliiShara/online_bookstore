from __future__ import annotations


class DomainError(Exception):
    """Базовий клас для всіх домених помилок у книжковому магазині"""


class ValidationError(DomainError):
    """ "Невалідні дані домену (наприклад, від'ємна кількість, поганий ISBN)"""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Invalid value for '{field}': {message}")


class BookNotFoundError(DomainError):
    """Книгу не знайдено за ідентифікатором"""

    def __init__(self, *, book_id: str | None = None, isbn: str | None = None):
        self.book_id = book_id
        self.isbn = isbn
        ident = f"id={book_id}" if book_id is not None else f"ISBN={isbn}"
        super().__init__(f"Book not found ({ident})")


class DuplicateISBNError(DomainError):
    """Спроба додати книгу з ISBN, який вже існує в каталозі"""

    def __init__(self, isbn: str):
        self.isbn = isbn
        super().__init__(f"Book with ISBN={isbn} already exists")


class OutOfStockError(DomainError):
    """Недостатньо примірників для продажу"""

    def __init__(self, isbn: str, requested_qty: int, available_qty: int):
        self.isbn = isbn
        self.requested_qty = requested_qty
        self.available_qty = available_qty
        super().__init__(
            f"Not enough stock for ISBN={isbn}: requested {requested_qty},available {available_qty}"
        )


class StorageError(DomainError):
    """Помилка доступу до сховища (файл JSON, etc)"""

    def __init__(self, message: str, *, cause: Exception | None = None):
        super().__init__(message)


__all__ = [
    "DomainError",
    "ValidationError",
    "BookNotFoundError",
    "DuplicateISBNError",
    "OutOfStockError",
    "StorageError",
]
