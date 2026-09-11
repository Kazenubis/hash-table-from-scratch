"""
Tests for HashTable — basic CRUD, collision chaining (using real string
keys confirmed to collide under this table's own hash function), and
resize/rehash correctness.
"""

import unittest

from hash_table import HashTable


class TestBasicCRUD(unittest.TestCase):
    def test_put_and_get(self):
        table = HashTable()
        table.put("name", "Mahmoud")
        self.assertEqual(table.get("name"), "Mahmoud")

    def test_get_missing_key_returns_default(self):
        table = HashTable()
        self.assertIsNone(table.get("missing"))
        self.assertEqual(table.get("missing", "fallback"), "fallback")

    def test_getitem_missing_key_raises_keyerror(self):
        table = HashTable()
        with self.assertRaises(KeyError):
            table["missing"]

    def test_setitem_and_getitem(self):
        table = HashTable()
        table["count"] = 1
        self.assertEqual(table["count"], 1)

    def test_updating_existing_key_does_not_increase_size(self):
        table = HashTable()
        table.put("key", "first")
        table.put("key", "second")
        self.assertEqual(len(table), 1)
        self.assertEqual(table.get("key"), "second")

    def test_delete_removes_key(self):
        table = HashTable()
        table.put("key", "value")
        table.delete("key")
        self.assertNotIn("key", table)
        self.assertEqual(len(table), 0)

    def test_delete_missing_key_raises_keyerror(self):
        table = HashTable()
        with self.assertRaises(KeyError):
            table.delete("missing")

    def test_delitem(self):
        table = HashTable()
        table["key"] = "value"
        del table["key"]
        self.assertNotIn("key", table)

    def test_contains(self):
        table = HashTable()
        table.put("present", 1)
        self.assertIn("present", table)
        self.assertNotIn("absent", table)

    def test_len_tracks_size(self):
        table = HashTable()
        self.assertEqual(len(table), 0)
        table.put("a", 1)
        table.put("b", 2)
        self.assertEqual(len(table), 2)

    def test_keys_values_items(self):
        table = HashTable()
        table.put("a", 1)
        table.put("b", 2)
        self.assertCountEqual(table.keys(), ["a", "b"])
        self.assertCountEqual(table.values(), [1, 2])
        self.assertCountEqual(table.items(), [("a", 1), ("b", 2)])

    def test_load_factor(self):
        table = HashTable(initial_capacity=8)
        table.put("a", 1)
        self.assertAlmostEqual(table.load_factor(), 1 / 8)

    def test_non_string_keys_work(self):
        table = HashTable()
        table.put(42, "answer")
        table.put((1, 2), "tuple key")
        self.assertEqual(table.get(42), "answer")
        self.assertEqual(table.get((1, 2)), "tuple key")

    def test_initial_capacity_must_be_positive(self):
        with self.assertRaises(ValueError):
            HashTable(initial_capacity=0)


class TestCollisionChaining(unittest.TestCase):
    """These keys are confirmed (empirically, not by hand) to collide
    under HashTable._hash_key at capacity=8 — see the module docstring
    in hash_table.py for how the base-31 polynomial hash works. Real
    collisions, not simulated ones, are what actually exercise the
    separate-chaining logic."""

    def test_apple_and_mango_collide_at_capacity_8(self):
        table = HashTable(initial_capacity=8)
        # Confirmed: both hash to bucket index 2 at capacity 8.
        self.assertEqual(table._bucket_index("apple"), table._bucket_index("mango"))

    def test_colliding_keys_are_both_independently_retrievable(self):
        # Small threshold-proof capacity so no resize happens mid-test —
        # only 2 of 8 buckets are touched, well under the 0.75 threshold.
        table = HashTable(initial_capacity=8)
        table.put("apple", "red fruit")
        table.put("mango", "tropical fruit")

        self.assertEqual(table.get("apple"), "red fruit")
        self.assertEqual(table.get("mango"), "tropical fruit")
        # Both entries really did land in the same bucket, chained.
        index = table._bucket_index("apple")
        self.assertEqual(len(table._buckets[index]), 2)

    def test_deleting_one_colliding_key_leaves_the_other_intact(self):
        table = HashTable(initial_capacity=8)
        table.put("apple", "red fruit")
        table.put("mango", "tropical fruit")

        table.delete("apple")

        self.assertNotIn("apple", table)
        self.assertEqual(table.get("mango"), "tropical fruit")
        self.assertEqual(len(table), 1)

    def test_updating_one_colliding_key_leaves_the_other_intact(self):
        table = HashTable(initial_capacity=8)
        table.put("date", "a fruit")
        table.put("orange", "a citrus fruit")  # confirmed: collides with "date" at bucket 6

        table.put("date", "a sweet dried fruit")

        self.assertEqual(table.get("date"), "a sweet dried fruit")
        self.assertEqual(table.get("orange"), "a citrus fruit")
        self.assertEqual(len(table), 2)

    def test_four_way_collision_chains_correctly(self):
        # Confirmed: "grape", "honeydew", "lemon", "quince" all hash to
        # bucket index 3 at capacity 8 — a longer chain than a 2-way
        # collision, worth its own test.
        table = HashTable(initial_capacity=8)
        words = ["grape", "honeydew", "lemon", "quince"]
        for i, word in enumerate(words):
            table.put(word, i)

        index = table._bucket_index("grape")
        self.assertEqual(len(table._buckets[index]), 4)
        for i, word in enumerate(words):
            self.assertEqual(table.get(word), i)


class TestResizeAndRehash(unittest.TestCase):
    def test_resize_doubles_capacity_once_threshold_crossed(self):
        table = HashTable(initial_capacity=8, load_factor_threshold=0.75)
        # 8 * 0.75 = 6, so the 7th entry (load factor 7/8 > 0.75) triggers a resize.
        for i in range(7):
            table.put(f"key{i}", i)

        self.assertEqual(table.capacity, 16)

    def test_all_keys_remain_retrievable_after_resize(self):
        table = HashTable(initial_capacity=8, load_factor_threshold=0.75)
        entries = {f"key{i}": i * 10 for i in range(50)}
        for key, value in entries.items():
            table.put(key, value)

        # 50 entries should have forced several resizes by now.
        self.assertGreater(table.capacity, 8)
        for key, value in entries.items():
            self.assertEqual(table.get(key), value)
        self.assertEqual(len(table), 50)

    def test_resize_preserves_colliding_keys_from_the_old_table(self):
        # "apple" and "mango" collide at capacity 8 (see TestCollisionChaining).
        # Once the table resizes past that, they land in a NEW pair of
        # buckets (not necessarily the same bucket as each other) — the
        # resize has to actually recompute each key's index, not just
        # copy old bucket contents into new bucket positions.
        table = HashTable(initial_capacity=8, load_factor_threshold=0.75)
        table.put("apple", "red fruit")
        table.put("mango", "tropical fruit")
        for i in range(10):
            table.put(f"filler{i}", i)

        self.assertGreater(table.capacity, 8)
        self.assertEqual(table.get("apple"), "red fruit")
        self.assertEqual(table.get("mango"), "tropical fruit")

    def test_size_is_unchanged_by_resize(self):
        table = HashTable(initial_capacity=4, load_factor_threshold=0.75)
        for i in range(20):
            table.put(f"key{i}", i)
        self.assertEqual(len(table), 20)

    def test_load_factor_drops_after_resize(self):
        table = HashTable(initial_capacity=8, load_factor_threshold=0.75)
        for i in range(7):
            table.put(f"key{i}", i)
        # 7 entries, capacity now 16 -> load factor well under the threshold.
        self.assertLess(table.load_factor(), 0.75)

    def test_bucket_lengths_sum_to_size(self):
        table = HashTable(initial_capacity=8)
        for word in ["apple", "mango", "papaya", "raspberry", "date", "orange"]:
            table.put(word, True)
        self.assertEqual(sum(table.bucket_lengths()), len(table))


if __name__ == "__main__":
    unittest.main()
