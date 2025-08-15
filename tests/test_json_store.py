from pathlib import Path
from bookstore.storage.json_store import JSONStore


def test_json_store_init_load_save(tmp_path):
    """Тестує ініціалізацію, завантаження та збереження даних."""
    db_path = tmp_path / "db.json"
    store = JSONStore(db_path)

    # Завантаження щойно створеного пустого файлу
    data = store.load()
    assert "books" in data and "sales" in data
    assert isinstance(data["books"], list)
    assert isinstance(data["sales"], list)

    # Проста модифікація і збереження
    data["books"].append({"id": "1", "title": "X"})
    store.save(data)

    # Повторне завантаження, щоб перевірити збережені дані
    data2 = store.load()
    assert len(data2["books"]) == 1
    assert data2["books"][0]["id"] == "1"
    assert data2["books"][0]["title"] == "X"
