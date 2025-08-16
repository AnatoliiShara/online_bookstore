from decimal import Decimal

from bookstore.bookstore import Bookstore


def test_facade_e2e(tmp_path):
    """
    Тестує роботу всього фасаду Bookstore:
    - додавання книги,
    - продаж книги,
    - перевірку агрегованої статистики.
    """
    bs = Bookstore(db_path=tmp_path / "db.json")

    # Додаємо книгу
    bs.add_book(
        title="Refactoring", author="Fowler", isbn="978-0201485677", price="11.00", quantity=2
    )

    # Продаємо один примірник
    bs.sell(isbn="978-0201485677", qty=1)

    # Перевіряємо, чи всі показники вірні
    stats = bs.stats()
    assert stats.total_titles == 1
    assert stats.active_titles == 1
    assert stats.total_quantity == 1
    assert stats.sales_count == 1
    assert stats.revenue == Decimal("11.00")
