# src/bookstore/bookstore.py
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from bookstore.models.book import Book
from bookstore.models.sale import Sale
from bookstore.repository.book_repository import BookRepository
from bookstore.services.inventory_service import InventoryService
from bookstore.services.sales_service import SalesService
from bookstore.storage.json_store import JSONStore


@dataclass(frozen=True)
class BookstoreStats:
    """Простий агрегат для відображення статистики у UI/тестах."""

    total_titles: int
    active_titles: int
    archived_titles: int
    total_quantity: int
    sales_count: int
    revenue: Decimal


class Bookstore:
    """
    Фасад книжкового магазину.
    Єдина точка входу для UI: інкапсулює репозиторій, сервіси та сховище.
    """

    def __init__(self, db_path: str | Path = "data/bookstore.json") -> None:
        """
        Args:
            db_path: шлях до JSON-файлу “БД”.
        """
        self._store = JSONStore(db_path)
        self._repo = BookRepository(self._store)
        self._inventory = InventoryService(self._repo)
        self._sales = SalesService(self._repo, self._store)

    # ──────────────────────────────────────────────────────────────
    # Інвентар / Каталог

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
        Додає книгу або збільшує залишок, якщо ISBN уже існує.
        За потреби оновлює ціну до переданої.
        """
        return self._inventory.add_book(
            title=title,
            author=author,
            isbn=isbn,
            price=price,
            currency=currency,
            quantity=quantity,
            update_price_if_changed=update_price_if_changed,
        )

    def set_price(self, *, isbn: str, new_price: Decimal | float | str) -> Book:
        return self._inventory.set_price(isbn=isbn, new_price=new_price)

    def set_quantity(self, *, isbn: str, new_qty: int) -> Book:
        return self._inventory.set_quantity(isbn=isbn, new_qty=new_qty)

    def increase_stock(self, *, isbn: str, by: int) -> Book:
        return self._inventory.increase_stock(isbn=isbn, by=by)

    def decrease_stock(self, *, isbn: str, by: int) -> Book:
        return self._inventory.decrease_stock(isbn=isbn, by=by)

    def archive_if_empty(self, *, isbn: str) -> Book:
        return self._inventory.archive_if_empty(isbn=isbn)

    def get_book_by_isbn(self, *, isbn: str) -> Book:
        return self._repo.get_by_isbn(isbn)

    def get_book_by_id(self, *, book_id: str) -> Book:
        return self._repo.get_by_id(book_id)

    def list_all(self, *, include_archived: bool = True) -> List[Book]:
        return self._inventory.list_all(include_archived=include_archived)

    def search(self, query: str, *, include_archived: bool = False, limit: int = 50) -> List[Book]:
        return self._inventory.search_books(query, include_archived=include_archived, limit=limit)

    # ──────────────────────────────────────────────────────────────
    # Продажі

    def sell(self, *, isbn: str, qty: int) -> Sale:
        """
        Продає книгу у кількості qty:
          - перевіряє залишок та стан (не архівна),
          - списує зі складу,
          - фіксує транзакцію у журналі.
        """
        return self._sales.sell(isbn=isbn, qty=qty)

    def list_sales(self, *, isbn: Optional[str] = None, limit: int = 100) -> List[Sale]:
        return self._sales.list_sales(isbn=isbn, limit=limit)

    def sales_total(self, *, isbn: Optional[str] = None) -> Decimal:
        return self._sales.sales_total(isbn=isbn)

    # ──────────────────────────────────────────────────────────────
    # Агрегована статистика для UI

    def stats(self) -> BookstoreStats:
        """
        Повертає просту агреговану статистику для виводу у UI:
          - кількість унікальних тайтлів
          - скільки активних/архівних
          - загальний залишок примірників
          - кількість транзакцій продажів
          - сумарна виручка
        """
        books = self._repo.list_all(include_archived=True)
        total_titles = len(books)
        active_titles = sum(1 for b in books if not b.archived)
        archived_titles = total_titles - active_titles
        total_quantity = sum(b.quantity for b in books)

        sales = self._sales.list_sales(limit=None)
        sales_count = len(sales)
        revenue = self._sales.sales_total()

        return BookstoreStats(
            total_titles=total_titles,
            active_titles=active_titles,
            archived_titles=archived_titles,
            total_quantity=total_quantity,
            sales_count=sales_count,
            revenue=revenue,
        )

    # ──────────────────────────────────────────────────────────────
    # Технічне

    @property
    def db_path(self) -> Path:
        """Шлях до JSON-файлу з даними (для діагностики/тестів)."""
        return self._store.path
