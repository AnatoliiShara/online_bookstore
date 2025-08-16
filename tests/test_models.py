from decimal import Decimal

import pytest

from bookstore.errors import ValidationError
from bookstore.models.book import Book
from bookstore.models.sale import Sale


def test_book_create_and_stock_ops():
    b = Book(
        title="Clean Code",
        author="Robert C. Martin",
        isbn="978-0132350884",
        price="12.34",
        currency="USD",
        quantity=5,
    )

    assert b.price == Decimal("12.34")
    assert b.quantity == 5
    assert b.is_available() is True

    b.increase_stock(2)
    assert b.quantity == 7

    b.decrease_stock(3)
    assert b.quantity == 4


def test_book_invalid_quantity_raises():
    with pytest.raises(ValidationError):
        Book(title="X", author="Y", isbn="0132350882", price="1.00", quantity=-1)


def test_sale_create_and_totals():
    s = Sale.create(
        book_id="abc123", isbn="978-0132350884", qty=2, unit_price_cents=1234, currency="USD"
    )
    assert s.unit_price == Decimal("12.34")
    assert s.total_cents == 2468
    assert s.total == Decimal("24.68")
