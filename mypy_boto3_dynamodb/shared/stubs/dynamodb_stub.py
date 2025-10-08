"""Simple in-memory DynamoDB stub for tests."""
from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class _InMemoryTable:
    name: str
    _items: dict[str, dict[str, Any]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def scan(self, *_: Any, **__: Any) -> dict[str, list[dict[str, Any]]]:
        with self._lock:
            return {"Items": list(self._items.values())}

    def get_item(self, Key: dict[str, Any], *_: Any, **__: Any) -> dict[str, Any]:  # noqa: N803
        key = self._key(Key)
        with self._lock:
            item = self._items.get(key)
            return {"Item": item} if item else {}

    def put_item(self, Item: dict[str, Any], *_: Any, **__: Any) -> dict[str, Any]:  # noqa: N803
        key = self._key(Item)
        with self._lock:
            self._items[key] = dict(Item)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def update_item(self, Key: dict[str, Any], *_: Any, **__: Any) -> dict[str, Any]:  # noqa: N803
        key = self._key(Key)
        with self._lock:
            existing = self._items.setdefault(key, dict(Key))
            existing.update({k: v for k, v in Key.items() if k not in existing})
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def delete_item(self, Key: dict[str, Any], *_: Any, **__: Any) -> dict[str, Any]:  # noqa: N803
        key = self._key(Key)
        with self._lock:
            self._items.pop(key, None)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def query(self, *_: Any, **__: Any) -> dict[str, list[dict[str, Any]]]:
        return {"Items": []}

    def transact_write_items(self, *_: Any, **__: Any) -> dict[str, Any]:
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def batch_writer(self, *_: Any, **__: Any) -> _BatchWriter:
        return _BatchWriter(self)

    def _key(self, key_dict: dict[str, Any]) -> str:
        return "|".join(f"{k}:{key_dict[k]}" for k in sorted(key_dict))


class _BatchWriter:
    def __init__(self, table: _InMemoryTable) -> None:
        self._table = table

    def __enter__(self) -> _BatchWriter:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        return False

    def put_item(self, Item: dict[str, Any]) -> None:  # noqa: N803
        self._table.put_item(Item=Item)


class DynamoStub:
    """Minimal DynamoDB resource stub that returns in-memory tables."""

    def __init__(self) -> None:
        self._tables: dict[str, _InMemoryTable] = defaultdict(lambda: _InMemoryTable(name=""))

    def Table(self, name: str) -> _InMemoryTable:  # noqa: N802
        table = self._tables.get(name)
        if table is None or not table.name:
            table = _InMemoryTable(name)
            self._tables[name] = table
        return table


_singleton = DynamoStub()


def resource(_service: str, *_: Any, **__: Any) -> DynamoStub:
    return _singleton


def client(_service: str, *_: Any, **__: Any) -> DynamoStub:
    return _singleton
