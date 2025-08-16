from decimal import Decimal

import pytest

from bookstore.errors import OutOfStockError
from bookstore.repository.book_repository import BookRepository
from bookstore.services.inventory_service import InventoryService
from bookstore.services.sales_service import SalesService
from bookstore.storage.json_store import JSONStore


def make_services(tmp_path):
    """Допоміжна функція для створення всіх необхідних сервісів."""
    store = JSONStore(tmp_path / "db.json")
    repo = BookRepository(store)
    inv = InventoryService(repo)
    sales = SalesService(repo, store)
    return inv, sales, repo


def test_sell_and_totals(tmp_path):
    """
    Тестує:
    - продаж книги
    - оновлення кількості на складі
    - перевірку загальної виручки
    - підрахунок транзакцій
    """
    inv, sales, repo = make_services(tmp_path)

    inv.add_book(
        title="Clean Code", author="Uncle Bob", isbn="978-0132350884", price="10.00", quantity=5
    )

    sale = sales.sell(isbn="978-0132350884", qty=2)
    assert sale.total == Decimal("20.00")

    book = repo.get_by_isbn("978-0132350884")
    assert book.quantity == 3  # 5 - 2

    assert sales.sales_total() == Decimal("20.00")
    assert len(sales.list_sales()) == 1


def test_out_of_stock(tmp_path):
    """
    Тестує поведінку системи при спробі продати більше книг, ніж є на складі.
    Очікує виняток OutOfStockError.
    """
    inv, sales, _ = make_services(tmp_path)
    inv.add_book(title="DDD", author="Evans", isbn="978-0321125217", price="15.00", quantity=1)

    with pytest.raises(OutOfStockError):
        sales.sell(isbn="978-0321125217", qty=5)
