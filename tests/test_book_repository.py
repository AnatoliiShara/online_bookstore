import pytest
from bookstore.models.book import Book
from bookstore.repository.book_repository import BookRepository
from bookstore.storage.json_store import JSONStore
from bookstore.errors import DuplicateISBNError, BookNotFoundError


def make_repo(tmp_path) -> BookRepository:
    """Допоміжна функція для створення репозиторію з тимчасовою JSON-базою."""
    store = JSONStore(tmp_path / "db.json")
    return BookRepository(store)


def test_add_get_search_and_duplicate(tmp_path):
    """
    Тестує:
    - додавання нової книги
    - отримання книги за ISBN
    - пошук за ключовим словом
    - обробку помилки при спробі додати книгу з дублікатом ISBN
    """
    repo = make_repo(tmp_path)
    b = Book(title="Clean Code", author="Uncle Bob",
             isbn="9780132350884", price="10.00", quantity=2)
    repo.add(b)

    fetched = repo.get_by_isbn("9780132350884")
    assert fetched.title == "Clean Code"

    results = repo.search("uncle")
    assert len(results) == 1
    assert results[0].isbn == "9780132350884"

    # Спроба додати з тим самим ISBN
    with pytest.raises(DuplicateISBNError):
        repo.add(Book(title="Another", author="Bob",
                      isbn="9780132350884", price="9.99"))


def test_archive_and_remove(tmp_path):
    """
    Тестує:
    - архівацію книги
    - видалення книги за її ID
    """
    repo = make_repo(tmp_path)
    b = Book(title="DDD", author="Evans",
             isbn="9780321125217", price="15.00", quantity=0)
    repo.add(b)

    # Спочатку перевіряємо, що книга не архівована
    assert repo.get_by_isbn("9780321125217").archived is False

    # Архівуємо
    repo.archive_by_isbn("9780321125217")
    archived_book = repo.get_by_isbn("9780321125217")
    assert archived_book.archived is True

    # Додаємо другу книжку і видаляємо
    b2 = Book(title="Refactoring", author="Fowler",
              isbn="9780201485677", price="11.00")
    repo.add(b2)
    repo.remove(b2.id)

    with pytest.raises(BookNotFoundError):
        repo.get_by_id(b2.id)