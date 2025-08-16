from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from bookstore.errors import StorageError


class JSONStore:
    """Просте файлове сховище на базі JSON з атомарним записом"""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._atomic_write(self._default_data())

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Dict[str, Any]:
        try:
            with self._path.open("r", encoding="UTF-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = self._default_data()
            self._atomic_write(data)
        except json.JSONDecodeError as e:
            raise StorageError(f"Corrupted JSON at {self._path}: {e}", cause=e)

        return self._validate_and_normalize(data)

    def save(self, data: Dict[str, Any]):
        data = self._validate_and_normalize(data, allow_missing=False)
        self._atomic_write(data)

    @staticmethod
    def _default_data() -> Dict[str, Any]:
        return {"books": [], "sales": []}

    def _validate_and_normalize(
        self, data: Dict[str, Any], *, allow_missing: bool = True
    ) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise StorageError("Root JSON must be an object {  ...  }")
        books = data.get("books")
        sales = data.get("sales")

        if books is None or sales is None:
            if allow_missing:
                if books is None:
                    books = []
                if sales is None:
                    sales = []
            else:
                raise StorageError("JSON must contain: 'books' and 'sales'")
        if not isinstance(books, list) or not isinstance(sales, list):
            raise StorageError("'books' and 'sales' must be arrays")
        return {"books": books, "sales": sales}

    def _atomic_write(self, data: Dict[str, Any]):
        """Атомарний запис у файлах.
        1) пишемо у тимчасовий файл у тій же директорії
        2) os.replace() замінює оригінал
        """
        tmp_dir = str(self._path.parent)
        tmp_name = ""  # Ініціалізуємо змінну
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="UTF-8",
                dir=tmp_dir,
                prefix=self._path.name + ".",
                suffix=".tmp",
                delete=False,
            ) as tf:
                json.dump(data, tf, ensure_ascii=False, indent=2)
                tf.write("\n")
                tmp_name = tf.name
            os.replace(tmp_name, self._path)
        except Exception as e:
            try:
                if tmp_name and os.path.exists(tmp_name):
                    os.remove(tmp_name)
            except OSError:
                pass
            raise StorageError(f"Failed to write JSON to {self._path}: {e}", cause=e)
