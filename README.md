# Hash Table from Scratch

A hash table implemented from first principles — no `dict`, no `hash()`
doing the real work. This one uses its own string hash function, its own
collision handling (separate chaining), and its own resize/rehash logic.

This project is intentionally **not** reskinned around a theme. A hash
table is a recognized CS-fundamentals exercise, and its value as a
portfolio piece comes from demonstrating the mechanics clearly — forcing
a theme onto it would just get in the way.

Real output, showing 8 words inserted into a table that starts at
capacity 8 (so it has to resize and rehash partway through), including
the fact that "apple" and "mango" collide into the same bucket at
capacity 8, but not anymore once the table resizes to capacity 16:

```
Initial capacity: 8
After inserting 8 words, capacity: 16, load factor: 0.500
Bucket lengths: [0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 3, 0, 1, 0, 2, 0]
apple and mango share a bucket: False

Retrieving all words after the resize:
  apple: 0
  mango: 1
  papaya: 2
  raspberry: 3
  date: 4
  orange: 5
  elderberry: 6
  fig: 7

Final capacity: 16 (doubled from 8 -> 16)
```

## Features

- Custom base-31 polynomial rolling hash for string keys (non-string
  keys fall back to Python's built-in `hash()`), so collisions are
  deterministic and demonstrable rather than dependent on CPython's
  per-process hash randomization
- Collision resolution via separate chaining — each bucket holds a list
  of `(key, value)` pairs, so colliding keys stay independently
  retrievable and deletable
- Automatic resize: once the load factor crosses 0.75, capacity doubles
  and every existing entry is rehashed into the new bucket array
- Dict-like interface: `put`/`get`/`delete` plus `__getitem__`,
  `__setitem__`, `__delitem__`, `__contains__`, `__len__`, `keys()`,
  `values()`, `items()`
- `bucket_lengths()` diagnostic for inspecting how entries are actually
  distributed across buckets

## Tech Stack

Python 3, standard library only

## Getting Started

```bash
git clone https://github.com/Kazenubis/hash-table-from-scratch.git
cd hash-table-from-scratch
python3
```

```python
>>> from hash_table import HashTable
>>> table = HashTable()
>>> table["name"] = "Mahmoud"
>>> table["name"]
'Mahmoud'
```

Run the tests:

```bash
python3 -m unittest test_hash_table.py -v
```

## What I Learned

The resize logic is the one part of a hash table that's easy to get
subtly wrong without a test catching it. My first instinct was to think
of resizing as "copy the old buckets into a bigger array" — but that's
wrong, because a key's bucket index is `hash(key) % capacity`, and
`capacity` just changed. Every single existing entry has to be
re-hashed against the *new* capacity, not just moved to a same-numbered
bucket in a bigger array.

`test_resize_preserves_colliding_keys_from_the_old_table` is the test
that actually proves this: it inserts "apple" and "mango" — two keys
confirmed to collide at capacity 8 — then forces a resize past capacity
8 and checks both keys are still correctly retrievable. If the resize
had just copied bucket contents positionally instead of recomputing
each key's index, this is exactly the kind of bug that would silently
corrupt the table while still *looking* fine for keys that happened not
to collide.
