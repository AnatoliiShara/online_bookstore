from __future__ import annotations

from decimal import Decimal
from typing import List

from bookstore.errors import BookNotFoundError, ValidationError
from bookstore.models.book import Book
from bookstore.repository.book_repository import BookRepository


class InventoryService:
    """
    Бізнес-логіка каталогу/складу:
      - Додає книгу або збільшує залишок, якщо ISBN уже існує
      - Оновлює ціну/залишок
      - Архівує книгу, коли qty == 0
      - Пошук/перелік книг для UI
    """

    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    # ────────────────────────────────────────────────────────────────
    # Команди (mutations)

    def add_book(
        self,
        *,
        title: str,
        author: str,
        isbn: str,
        price: Decimal | float | str,
        currency: str = "USD",
        quantity: int = 1,
        update_price_if_changed: bool = True,
    ) -> Book:
        """
        Додає нову книгу. Якщо книга з таким ISBN уже є — збільшує її залишок.
        За бажанням оновлює ціну під поточну (update_price_if_changed=True).
        Повертає актуальний об'єкт Book.
        """
        if quantity <= 0:
            raise ValidationError("quantity", "Must be > 0.")

        try:
            existing = self._repo.get_by_isbn(isbn)
        except BookNotFoundError:
            # Створюємо нову книгу (Book валідовує title/author/isbn/price/quantity)
            book = Book(
                title=title,
                author=author,
                isbn=isbn,
                price=price,
                currency=currency,
                quantity=quantity,
            )
            self._repo.add(book)
            return book

        # Якщо вже існує — збільшуємо сток, опційно підганяємо ціну
        existing.increase_stock(quantity)
        if update_price_if_changed:
            existing.price = price  # property сам переведе у cents і провалідовує
        self._repo.update(existing)
        return existing

    def set_price(self, *, isbn: str, new_price: Decimal | float | str) -> Book:
        """Жорстко встановити нову ціну для книги за ISBN."""
        book = self._repo.get_by_isbn(isbn)
        book.price = new_price
        self._repo.update(book)
        return book

    def set_quantity(self, *, isbn: str, new_qty: int) -> Book:
        """Жорстко встановити кількість (>=0). Для ручних корекцій інвентаря."""
        if not isinstance(new_qty, int) or new_qty < 0:
            raise ValidationError("quantity", "Must be an integer >= 0.")
        book = self._repo.get_by_isbn(isbn)
        book.quantity = new_qty
        self._repo.update(book)
        return book

    def increase_stock(self, *, isbn: str, by: int) -> Book:
        """Збільшити залишок на 'by' (>0)."""
        book = self._repo.get_by_isbn(isbn)
        book.increase_stock(by)
        self._repo.update(book)
        return book

    def decrease_stock(self, *, isbn: str, by: int) -> Book:
        """
        Зменшити залишок на 'by' (>0). Не дозволяє піти нижче 0.
        Якщо потрібно забезпечувати іншу помилку для продажів (OutOfStock),
        цим займеться SalesService. Тут — базова валідація через Book.
        """
        book = self._repo.get_by_isbn(isbn)
        book.decrease_stock(by)
        self._repo.update(book)
        return book

    def archive_if_empty(self, *, isbn: str) -> Book:
        """
        Архівує книгу, якщо кількість == 0. Якщо qty > 0 — підкаже помилку.
        """
        book = self._repo.get_by_isbn(isbn)
        if book.quantity != 0:
            raise ValidationError("quantity", "Can archive only when quantity == 0.")
        self._repo.archive_by_isbn(isbn)
        # У репозиторії ми вже викликали `book.mark_archived()`
        # тому можна просто повернути об'єкт, який вже був оновлений в пам'яті.
        # Не потрібно перечитувати з репозиторію.
        return book

    # ────────────────────────────────────────────────────────────────
    # Запити (queries)

    def list_all(self, *, include_archived: bool = True) -> List[Book]:
        """Увесь каталог (за замовчуванням із архівними)."""
        return self._repo.list_all(include_archived=include_archived)

    def search_books(self, query: str, *, include_archived: bool = False, limit: int = 50) -> List[Book]:
        """Пошук за назвою/автором/ISBN (case-insensitive)."""
        return self._repo.search(query, include_archived=include_archived, limit=limit)