from __future__ import annotations
import re 
from typing import Iterable, List, Optional
from bookstore.errors import BookNotFoundError, DuplicateISBNError, ValidationError
from bookstore.models.book import Book
from bookstore.storage.json_store import JSONStore

class BookRepository:
    """Репозиторій для доступу книг у JSONStore
    Відповідальності:
    - тримати унікальність ISBN
    - надавати CRUD та пошук
    - працювати з моделями (Book) а не з сирими словниками
    """

    _ISBN_CLEAN = re.compile(r"[- ]")
    
    def __init__(self, store: JSONStore):
        self._store = store 

    def list_all(self, *, include_archived: bool = True) -> List[Book]:
        books = self._load_books()
        if include_archived:
            return books
        return [b for b in books if not b.archived]
    
    def search(self, query: str, *, include_archived: bool = True, limit: int = 50) -> List[Book]:
        q = query.strip().lower()
        if not q:
            return []
        books = self.list_all(include_archived=include_archived)
        results = []
        for b in books:
            if (
                q in b.title.lower()
                or q in b.author.lower()
                or q in b.isbn.lower()
            ):
                results.append(b)
                if len(results) >= limit:
                    break
        results.sort(key=lambda x: (x.title.lower(), x.author.lower()))
        return results
    
    def get_by_id(self, book_id: str) -> Book:
        books = self._load_books()
        for b in books:
            if b.id == book_id:
                return b 
        raise BookNotFoundError(book_id=book_id)
    
    def get_by_isbn(self, isbn: str) -> Book:
        norm = self._normalize_isbn(isbn)
        books = self._load_books()
        for b in books:
            if b.isbn == norm:
                return b 
        raise BookNotFoundError(isbn=norm)
    
    def add(self, book: Book):
        books = self._load_books()
        if any(b.isbn == book.isbn for b in books):
            raise DuplicateISBNError(book.isbn)
        books.append(book)
        self._save_books(books)

    def update(self, book: Book):
        books = self._load_books()
        idx = self._find_index_by_id(books, book.id)
        if idx is None:
            raise BookNotFoundError(book_id=book.id)
        for i, b in enumerate(books):
            if i != idx and b.isbn == book.isbn:
                raise DuplicateISBNErrror(book.isbn)
        books[idx] = book
        self._save_books(books)

    def remove(self, book_id: str):
        books = self._load_books()
        idx = self._find_index_by_id(books, book_id)
        if idx is None:
            raise BookNotFoundError(book_id=book_id)
        del books[idx]
        self._save_books(books)

    def archive_by_isbn(self, isbn: str):
        books = self._load_books()
        norm = self._normalize_isbn(isbn)
        idx = self._find_index_by_isbn(books, norm)
        if idx is None:
            raise BookNotFoundError(isbn=norm)
        
        book = books[idx]
        book.mark_archived()
        books[idx] = book 
        self._save_books(books)

    def _load_books(self) -> List[Book]:
        data = self._store.load()
        raw_books = data.get("books", [])
        books = []
        for item in raw_books:
            try:
                books.append(Book.from_dict(item))
            except ValidationError:
                continue
        return books
    
    def _save_books(self, books: Iterable[Book]):
        data = self._store.load()
        data["books"] = [b.to_dict() for b in books]
        self._store.save(data)

    @staticmethod
    def _normalize_isbn(raw: str) -> str:
        if not isinstance(raw, str):
            raise ValidationError("isbn", "Must be a string")
        return BookRepository._ISBN_CLEAN.sub("", raw).upper()
    
    @staticmethod
    def _find_index_by_id(books: List[Book], book_id: str) -> Optional[int]:
        for index, book in enumerate(books):
            if book.id == book_id:
                return index
        return None
    
    @staticmethod
    def _find_index_by_isbn(books: List[Book], isbn: str) -> Optional[int]:
        for index, book in enumerate(books):
            if book.isbn == isbn:
                return index
        return None