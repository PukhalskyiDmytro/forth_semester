import os
import tempfile
import unittest

from json_document_db import (
    AggregationError,
    Collection,
    DocumentNotFoundError,
    DuplicateIdError,
    Query,
)


def sample_collection():
    collection = Collection("students")
    collection.add({
        "id": 1,
        "name": "Ivan",
        "age": 21,
        "group": "MI-11",
        "grades": [90, 85, 100],
        "address": {"city": "Kyiv", "street": "Shevchenka"},
        "active": True,
    })
    collection.add({
        "id": 2,
        "name": "Olena",
        "age": 19,
        "group": "MI-12",
        "grades": [75, 80],
        "address": {"city": "Lviv"},
        "active": False,
    })
    collection.add({
        "id": 3,
        "name": "Petro",
        "age": 22,
        "group": "MI-11",
        "grades": [100, 95],
        "address": {"city": "Kyiv"},
        "active": True,
    })
    return collection


class JsonDocumentDbTests(unittest.TestCase):
    def test_add_and_get_document(self):
        collection = sample_collection()
        doc = collection.get(1)
        self.assertEqual(doc["name"], "Ivan")
        self.assertEqual(doc["address"]["city"], "Kyiv")

    def test_duplicate_id_error(self):
        collection = sample_collection()
        with self.assertRaises(DuplicateIdError):
            collection.add({"id": 1, "name": "Duplicate"})

    def test_delete_by_id(self):
        collection = sample_collection()
        collection.delete_by_id(2)
        with self.assertRaises(DocumentNotFoundError):
            collection.get(2)

    def test_update_nested_field(self):
        collection = sample_collection()
        updated = collection.update_by_id(1, {"address.city": "Odesa"})
        self.assertEqual(updated["address"]["city"], "Odesa")

    def test_find_exact_match(self):
        collection = sample_collection()
        result = collection.find(Query.from_cli("active", "==", True))
        self.assertEqual(len(result), 2)

    def test_find_numeric_comparison(self):
        collection = sample_collection()
        result = collection.find(Query.from_cli("age", ">", 20))
        self.assertEqual({doc["id"] for doc in result}, {1, 3})

    def test_find_nested_field(self):
        collection = sample_collection()
        result = collection.find(Query.from_cli("address.city", "==", "Kyiv"))
        self.assertEqual({doc["id"] for doc in result}, {1, 3})

    def test_find_contains_list_item(self):
        collection = sample_collection()
        result = collection.find(Query.from_cli("grades", "contains", 100))
        self.assertEqual({doc["id"] for doc in result}, {1, 3})

    def test_find_exists(self):
        collection = sample_collection()
        result = collection.find(Query.from_cli("address.street", "exists", True))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)

    def test_complex_and_or_not_query(self):
        collection = sample_collection()
        condition = {
            "and": [
                {"field": "age", "op": ">=", "value": 20},
                {"not": {"field": "name", "op": "==", "value": "Ivan"}},
            ]
        }
        result = collection.find(condition)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Petro")

    def test_aggregations(self):
        collection = sample_collection()
        self.assertEqual(collection.aggregate("count"), 3)
        self.assertEqual(collection.aggregate("sum", "age"), 62)
        self.assertAlmostEqual(collection.aggregate("avg", "age"), 62 / 3)
        self.assertEqual(collection.aggregate("min", "age"), 19)
        self.assertEqual(collection.aggregate("max", "age"), 22)

    def test_aggregation_non_numeric_error(self):
        collection = sample_collection()
        with self.assertRaises(AggregationError):
            collection.aggregate("avg", "name")

    def test_group_by(self):
        collection = sample_collection()
        groups = collection.group_by("group")
        self.assertEqual(len(groups["MI-11"]), 2)
        self.assertEqual(len(groups["MI-12"]), 1)

    def test_sorting(self):
        collection = sample_collection()
        result = collection.find(sort_by="age")
        self.assertEqual([doc["age"] for doc in result], [19, 21, 22])

    def test_sorting_search_results_only(self):
        collection = sample_collection()
        condition = Query.from_cli("active", "==", True)
        result = collection.find(condition, sort_by="age", reverse=True)
        self.assertEqual([doc["id"] for doc in result], [3, 1])
        self.assertNotIn(2, [doc["id"] for doc in result])

    def test_indexed_search(self):
        collection = sample_collection()
        collection.create_index("group")
        result = collection.find(Query.from_cli("group", "==", "MI-11"))
        self.assertEqual({doc["id"] for doc in result}, {1, 3})

    def test_save_and_load(self):
        collection = sample_collection()
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, "db.json")
            collection.save(filename)
            loaded = Collection.load(filename)
        self.assertEqual(loaded.aggregate("count"), 3)
        self.assertEqual(loaded.get(1)["name"], "Ivan")

    def test_delete_many(self):
        collection = sample_collection()
        deleted = collection.delete_many(Query.from_cli("active", "==", False))
        self.assertEqual(deleted, 1)
        self.assertEqual(collection.aggregate("count"), 2)


if __name__ == "__main__":
    unittest.main()
