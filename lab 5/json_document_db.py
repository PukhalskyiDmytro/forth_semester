from __future__ import annotations

import copy
import json
import operator
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from typing import Any, Dict, List, Optional


class DatabaseError(Exception):
    pass
class DocumentNotFoundError(DatabaseError):
    pass
class FieldNotFoundError(DatabaseError):
    pass
class InvalidJsonError(DatabaseError):
    pass
class AggregationError(DatabaseError):
    pass
class DuplicateIdError(DatabaseError):
    pass


NO_DEFAULT = object()
MISSING = object()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_json_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def split_path(path: str) -> List[str]:
    if not path:
        raise ValueError("Шлях поля не може бути порожнім")
    return path.split(".")


def get_nested_value(document: Dict[str, Any], path: str, default: Any = NO_DEFAULT) -> Any:
    current: Any = document
    for part in split_path(path):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            if 0 <= index < len(current):
                current = current[index]
            else:
                if default is NO_DEFAULT:
                    raise FieldNotFoundError(f"Індекс '{part}' відсутній у списку для поля '{path}'")
                return default
        else:
            if default is NO_DEFAULT:
                raise FieldNotFoundError(f"Поле '{path}' не знайдено")
            return default
    return current


def set_nested_value(document: Dict[str, Any], path: str, value: Any) -> None:
    parts = split_path(path)
    current = document

    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value


def has_nested_field(document: Dict[str, Any], path: str) -> bool:
    return get_nested_value(document, path, default=MISSING) is not MISSING


def normalize_for_index(value: Any) -> Any:
    try:
        hash(value)
        return value
    except TypeError:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)


@dataclass
class Document:
    data: Dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.data, dict):
            raise InvalidJsonError("Документ має бути JSON-об'єктом")
        if "id" not in self.data:
            raise InvalidJsonError("Документ повинен мати поле 'id'")

    @property
    def id(self) -> Any:
        return self.data["id"]

    def copy(self) -> Dict[str, Any]:
        return copy.deepcopy(self.data)


class Query:
    OPERATORS = {
        "==": operator.eq,
        "=": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
    }

    @staticmethod
    def match(document: Dict[str, Any], condition: Optional[Dict[str, Any]]) -> bool:
        if condition is None:
            return True

        if "and" in condition:
            return all(Query.match(document, subcondition) for subcondition in condition["and"])

        if "or" in condition:
            return any(Query.match(document, subcondition) for subcondition in condition["or"])

        if "not" in condition:
            return not Query.match(document, condition["not"])

        field = condition.get("field")
        op = condition.get("op", "==")
        expected = condition.get("value")

        if not field:
            raise ValueError("Умова повинна містити поле 'field'")

        if op == "exists":
            should_exist = True if expected is None else bool(expected)
            return has_nested_field(document, field) == should_exist

        actual = get_nested_value(document, field, default=MISSING)
        if actual is MISSING:
            return False

        if op == "contains":
            if isinstance(actual, list):
                return expected in actual
            if isinstance(actual, str):
                return str(expected) in actual
            return False

        if op not in Query.OPERATORS:
            raise ValueError(f"Непідтримуваний оператор: {op}")

        try:
            return bool(Query.OPERATORS[op](actual, expected))
        except TypeError:
            return False

    @staticmethod
    def from_cli(field: str, op: str, value: Optional[Any] = None) -> Dict[str, Any]:
        return {"field": field, "op": op, "value": value}


@dataclass
class Collection:
    name: str
    _documents: Dict[Any, Document] = dataclass_field(default_factory=dict)
    _indexes: Dict[str, Dict[Any, set]] = dataclass_field(default_factory=dict)
    history: List[Dict[str, Any]] = dataclass_field(default_factory=list)

    def _add_history(self, action: str, document_id: Any, details: Optional[Dict[str, Any]] = None) -> None:
        self.history.append({
            "time": now_iso(),
            "action": action,
            "document_id": document_id,
            "details": details or {},
        })

    def _rebuild_indexes(self) -> None:
        fields = list(self._indexes.keys())
        self._indexes = {}
        for field in fields:
            self.create_index(field)

    def add(self, document_data: Dict[str, Any]) -> Document:
        document = Document(copy.deepcopy(document_data))

        if document.id in self._documents:
            raise DuplicateIdError(f"Документ з id={document.id!r} вже існує")

        self._documents[document.id] = document
        self._add_history("add", document.id, {"document": document.copy()})
        self._rebuild_indexes()
        return document

    def get(self, document_id: Any) -> Dict[str, Any]:
        if document_id not in self._documents:
            raise DocumentNotFoundError(f"Документ з id={document_id!r} не знайдено")
        return self._documents[document_id].copy()

    def all(self) -> List[Dict[str, Any]]:
        return [document.copy() for document in self._documents.values()]

    def delete_by_id(self, document_id: Any) -> bool:
        if document_id not in self._documents:
            raise DocumentNotFoundError(f"Документ з id={document_id!r} не знайдено")

        deleted = self._documents.pop(document_id)
        self._add_history("delete", document_id, {"document": deleted.copy()})
        self._rebuild_indexes()
        return True

    def delete_many(self, condition: Dict[str, Any]) -> int:
        ids_to_delete = [
            document.id
            for document in self._documents.values()
            if Query.match(document.data, condition)
        ]

        for document_id in ids_to_delete:
            self.delete_by_id(document_id)

        return len(ids_to_delete)

    def update_by_id(self, document_id: Any, updates: Dict[str, Any]) -> Dict[str, Any]:
        if document_id not in self._documents:
            raise DocumentNotFoundError(f"Документ з id={document_id!r} не знайдено")

        document = self._documents[document_id]
        before = document.copy()

        for path, value in updates.items():
            set_nested_value(document.data, path, value)

        self._add_history("update", document_id, {"before": before, "after": document.copy()})
        self._rebuild_indexes()
        return document.copy()

    def update_many(self, condition: Dict[str, Any], updates: Dict[str, Any]) -> int:
        matched_ids = [
            document.id
            for document in self._documents.values()
            if Query.match(document.data, condition)
        ]

        for document_id in matched_ids:
            self.update_by_id(document_id, updates)

        return len(matched_ids)

    def find(
        self,
        condition: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        reverse: bool = False,
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]]

        if (
            condition is not None
            and set(condition.keys()) >= {"field", "op", "value"}
            and condition.get("op") in ("==", "=")
            and condition.get("field") in self._indexes
        ):
            field = condition["field"]
            key = normalize_for_index(condition["value"])
            ids = self._indexes[field].get(key, set())
            result = [self._documents[document_id].copy() for document_id in ids]
        else:
            result = [
                document.copy()
                for document in self._documents.values()
                if Query.match(document.data, condition)
            ]

        if sort_by:
            result.sort(
                key=lambda doc: (
                    get_nested_value(doc, sort_by, default=None) is None,
                    get_nested_value(doc, sort_by, default=None),
                ),
                reverse=reverse,
            )

        return result

    def create_index(self, field: str) -> None:
        index: Dict[Any, set] = {}

        for document in self._documents.values():
            value = get_nested_value(document.data, field, default=MISSING)
            if value is MISSING:
                continue
            key = normalize_for_index(value)
            index.setdefault(key, set()).add(document.id)

        self._indexes[field] = index

    def drop_index(self, field: str) -> None:
        self._indexes.pop(field, None)

    def aggregate(
        self,
        operation: str,
        field: Optional[str] = None,
        condition: Optional[Dict[str, Any]] = None,
    ) -> Any:
        docs = self.find(condition)

        if operation == "count":
            return len(docs)

        if not field:
            raise AggregationError("Для цієї агрегації потрібно вказати поле")

        values = []
        for doc in docs:
            value = get_nested_value(doc, field, default=MISSING)
            if value is MISSING:
                continue
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise AggregationError(f"Агрегація '{operation}' можлива лише для числового поля")
            values.append(value)

        if not values:
            raise AggregationError(f"Немає числових значень у полі '{field}'")

        if operation == "sum":
            return sum(values)
        if operation == "avg":
            return sum(values) / len(values)
        if operation == "min":
            return min(values)
        if operation == "max":
            return max(values)

        raise AggregationError(f"Невідома агрегатна операція: {operation}")

    def group_by(
        self,
        field: str,
        condition: Optional[Dict[str, Any]] = None,
    ) -> Dict[Any, List[Dict[str, Any]]]:
        groups: Dict[Any, List[Dict[str, Any]]] = {}

        for doc in self.find(condition):
            value = get_nested_value(doc, field, default=None)
            key = normalize_for_index(value)
            groups.setdefault(key, []).append(doc)

        return groups

    def to_json_compatible(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "documents": self.all(),
            "indexes": list(self._indexes.keys()),
            "history": self.history,
        }

    def save(self, filename: str) -> None:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.to_json_compatible(), file, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filename: str) -> "Collection":
        try:
            with open(filename, "r", encoding="utf-8") as file:
                raw = json.load(file)
        except json.JSONDecodeError as exc:
            raise InvalidJsonError(f"Файл містить некоректний JSON: {exc}") from exc
        except FileNotFoundError as exc:
            raise DatabaseError(f"Файл не знайдено: {filename}") from exc

        if isinstance(raw, list):
            collection = cls("loaded")
            documents = raw
            indexes = []
            history = []
        elif isinstance(raw, dict):
            collection = cls(raw.get("name", "loaded"))
            documents = raw.get("documents", [])
            indexes = raw.get("indexes", [])
            history = raw.get("history", [])
        else:
            raise InvalidJsonError("Файл має містити список документів або об'єкт колекції")

        if not isinstance(documents, list):
            raise InvalidJsonError("Поле 'documents' має бути списком")

        for document in documents:
            collection.add(document)

        collection.history = history

        for field in indexes:
            collection.create_index(field)

        return collection


@dataclass
class Database:
    collections: Dict[str, Collection] = dataclass_field(default_factory=dict)

    def create_collection(self, name: str) -> Collection:
        if name in self.collections:
            return self.collections[name]
        collection = Collection(name)
        self.collections[name] = collection
        return collection

    def get_collection(self, name: str) -> Collection:
        if name not in self.collections:
            raise DatabaseError(f"Колекція '{name}' не існує")
        return self.collections[name]

    def drop_collection(self, name: str) -> None:
        if name not in self.collections:
            raise DatabaseError(f"Колекція '{name}' не існує")
        del self.collections[name]


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def run_cli() -> None:
    database = Database()
    collection = database.create_collection("default")

    print("JSON Document DB. Введіть 'help' для списку команд.")

    while True:
        try:
            line = input("db> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not line:
            continue

        if line in {"exit", "quit"}:
            break

        if line == "help":
            print('Good luck ;)')
            continue

        try:
            command, *rest = line.split(maxsplit=1)
            argument = rest[0] if rest else ""

            if command == "add":
                try:
                    document = json.loads(argument)
                except json.JSONDecodeError as exc:
                    raise InvalidJsonError(f"Некоректний JSON: {exc}") from exc
                collection.add(document)
                print("Документ додано.")

            elif command == "delete":
                document_id = parse_json_value(argument)
                collection.delete_by_id(document_id)
                print("Документ видалено.")

            elif command == "delete_where":
                field, op, raw_value = argument.split(maxsplit=2)
                value = parse_json_value(raw_value)
                count = collection.delete_many(Query.from_cli(field, op, value))
                print(f"Видалено документів: {count}")

            elif command == "update":
                document_id_raw, field, raw_value = argument.split(maxsplit=2)
                document_id = parse_json_value(document_id_raw)
                value = parse_json_value(raw_value)
                updated = collection.update_by_id(document_id, {field: value})
                print_json(updated)

            elif command == "update_where":
                condition_part, update_part = argument.split(" set ", maxsplit=1)
                field, op, raw_value = condition_part.split(maxsplit=2)
                update_field, raw_new_value = update_part.split(maxsplit=1)
                value = parse_json_value(raw_value)
                new_value = parse_json_value(raw_new_value)
                count = collection.update_many(Query.from_cli(field, op, value), {update_field: new_value})
                print(f"Оновлено документів: {count}")

            elif command == "find":
                field, op, raw_value = argument.split(maxsplit=2)
                value = parse_json_value(raw_value)
                result = collection.find(Query.from_cli(field, op, value))
                print_json(result)

            elif command == "exists":
                result = collection.find(Query.from_cli(argument, "exists", True))
                print_json(result)

            elif command == "sort":
                parts = argument.split()
                field = parts[0]
                reverse = len(parts) > 1 and parts[1].lower() == "desc"
                print_json(collection.find(sort_by=field, reverse=reverse))

            elif command == "aggregate":
                parts = argument.split()
                operation = parts[0]
                field = parts[1] if len(parts) > 1 else None
                print_json(collection.aggregate(operation, field))

            elif command == "groupby":
                print_json(collection.group_by(argument))

            elif command == "index":
                collection.create_index(argument)
                print(f"Індекс для поля '{argument}' створено.")

            elif command == "dropindex":
                collection.drop_index(argument)
                print(f"Індекс для поля '{argument}' видалено.")

            elif command == "save":
                collection.save(argument)
                print(f"Збережено у файл: {argument}")

            elif command == "load":
                collection = Collection.load(argument)
                database.collections["default"] = collection
                print(f"Завантажено з файлу: {argument}")

            elif command == "history":
                print_json(collection.history)

            elif command == "all":
                print_json(collection.all())

            else:
                print("Невідома команда. Введіть 'help'.")

        except Exception as exc:
            print(f"Помилка: {exc}")


if __name__ == "__main__":
    run_cli()