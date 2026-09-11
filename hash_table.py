"""
Hash Table from Scratch — separate chaining for collision resolution,
automatic resize (doubling + full rehash) once the load factor crosses a
threshold. A from-scratch string hash function is used (rather than just
calling Python's built-in `hash()`) so collisions are deterministic and
demonstrable, not dependent on CPython's hash randomization.
"""


class HashTable:
    def __init__(self, initial_capacity=8, load_factor_threshold=0.75):
        if initial_capacity < 1:
            raise ValueError("initial_capacity must be at least 1")
        self._capacity = initial_capacity
        self._load_factor_threshold = load_factor_threshold
        self._size = 0
        self._buckets = [[] for _ in range(self._capacity)]

    @staticmethod
    def _hash_key(key):
        """A simple polynomial rolling hash for strings (base 31, the
        classic choice — large enough to spread short strings well,
        small enough to compute cheaply). Non-string keys fall back to
        Python's built-in hash, masked to a non-negative integer."""
        if isinstance(key, str):
            h = 0
            for char in key:
                h = (h * 31 + ord(char)) & 0xFFFFFFFF
            return h
        return hash(key) & 0xFFFFFFFF

    def _bucket_index(self, key, capacity=None):
        capacity = capacity or self._capacity
        return self._hash_key(key) % capacity

    @property
    def capacity(self):
        return self._capacity

    def load_factor(self):
        return self._size / self._capacity

    def __len__(self):
        return self._size

    def put(self, key, value):
        index = self._bucket_index(key)
        bucket = self._buckets[index]
        for i, (existing_key, _existing_value) in enumerate(bucket):
            if existing_key == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self._size += 1

        if self.load_factor() > self._load_factor_threshold:
            self._resize(self._capacity * 2)

    def get(self, key, default=None):
        index = self._bucket_index(key)
        for existing_key, existing_value in self._buckets[index]:
            if existing_key == key:
                return existing_value
        return default

    def __getitem__(self, key):
        index = self._bucket_index(key)
        for existing_key, existing_value in self._buckets[index]:
            if existing_key == key:
                return existing_value
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.put(key, value)

    def delete(self, key):
        index = self._bucket_index(key)
        bucket = self._buckets[index]
        for i, (existing_key, _existing_value) in enumerate(bucket):
            if existing_key == key:
                del bucket[i]
                self._size -= 1
                return
        raise KeyError(key)

    def __delitem__(self, key):
        self.delete(key)

    def __contains__(self, key):
        index = self._bucket_index(key)
        return any(existing_key == key for existing_key, _ in self._buckets[index])

    def _resize(self, new_capacity):
        """Doubling the bucket array means every key's bucket index
        potentially changes (index depends on `capacity`), so every
        existing entry has to be re-hashed into the new array — this is
        the one part of a hash table that's easy to get subtly wrong by
        just copying old buckets over positionally instead of
        recomputing each key's index."""
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = [[] for _ in range(new_capacity)]
        for bucket in old_buckets:
            for key, value in bucket:
                index = self._bucket_index(key)
                self._buckets[index].append((key, value))

    def keys(self):
        return [key for bucket in self._buckets for key, _ in bucket]

    def values(self):
        return [value for bucket in self._buckets for _, value in bucket]

    def items(self):
        return [(key, value) for bucket in self._buckets for key, value in bucket]

    def bucket_lengths(self):
        """Diagnostic: how many entries are in each bucket — useful for
        demonstrating that collisions really do land in the same bucket
        and get chained rather than overwriting each other."""
        return [len(bucket) for bucket in self._buckets]
