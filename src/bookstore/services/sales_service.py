from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from bookstore.errors import BookNotFoundError, OutOfStockError, ValidationError
from bookstore.models.book import Book
from bookstore.models.sale import Sale
from bookstore.repository.book_repository import BookRepository
from bookstore.storage.json_store import JSONStore


class SalesService:
    """
    Сервіс продажів:
      - sell: списує товар, створює транзакцію Sale, зберігає її у JSONStore
      - list_sales: повертає транзакції з опційною фільтрацією за ISBN
      - sales_total: підсумовує виручку за всіма/обраним ISBN
    """

    def __init__(self, repo: BookRepository, store: JSONStore) -> None:
        self._repo = repo
        self._store = store

    # ───────────────────────────────────────────────────────────────
    # Команди (mutations)

    def sell(self, *, isbn: str, qty: int) -> Sale:
        """
        Продає 'qty' примірників книги з заданим ISBN.
        Перевіряє:
          - qty > 0
          - книга існує, не архівна
          - достатня кількість на складі
        Оновлює книгу та додає транзакцію у журнал.
        Повертає створений Sale.
        """
        if not isinstance(qty, int) or qty <= 0:
            raise ValidationError("qty", "Must be an integer > 0.")

        # 1) Знайти книгу
        book = self._repo.get_by_isbn(isbn)  # може кинути BookNotFoundError

        # 2) Валідації стану
        if book.archived:
            raise ValidationError("book", "Cannot sell an archived book.")
        if book.quantity < qty:
            raise OutOfStockError(book.isbn, requested_qty=qty, available_qty=book.quantity)

        # 3) Створити транзакцію (фіксуємо історичну ціну/валюту на момент продажу)
        sale = Sale.create(
            book_id=book.id,
            isbn=book.isbn,
            qty=qty,
            unit_price_cents=book.price_cents,
            currency=book.currency,
        )

        # 4) Списати залишок і зберегти книгу
        book.decrease_stock(qty)
        self._repo.update(book)

        # 5) Записати транзакцію у журнал продажів (JSONStore)
        data = self._store.load()
        sales = data.get("sales", [])
        sales.append(sale.to_dict())
        data["sales"] = sales
        self._store.save(data)

        return sale

    # ───────────────────────────────────────────────────────────────
    # Запити (queries)

    def list_sales(self, *, isbn: Optional[str] = None, limit: int = 100) -> List[Sale]:
        """
        Повертає список транзакцій продажів.
        Опційно фільтрує за ISBN. Останні транзакції — наприкінці (за часом).
        """
        data = self._store.load()
        raw = data.get("sales", [])
        sales: List[Sale] = [Sale.from_dict(d) for d in raw]

        if isbn and isbn.strip():
            # Тут ми використовуємо нормалізацію, яка має бути в моделі Sale,
            # щоб не залежати від BookRepository.
            norm_isbn = Sale._normalize_isbn(isbn) 
            sales = [s for s in sales if s.isbn == norm_isbn]

        # Сортуємо за часом для стабільності від старих до нових
        sales.sort(key=lambda s: s.timestamp)
        if limit is not None and limit > 0:
            sales = sales[-limit:]
        return sales

    def sales_total(self, *, isbn: Optional[str] = None) -> Decimal:
        """
        Повертає сумарну виручку як Decimal.
        Якщо задано ISBN — агрегує лише по ньому.
        """
        total_cents = 0
        sales = self.list_sales(isbn=isbn, limit=None)
        for s in sales:
            total_cents += s.total_cents
        return Decimal(total_cents) / Decimal(100)