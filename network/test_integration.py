"""
Test d'integracio del sistema de xarxa universitaria.

Exercita:
  1. Hasher: determinisme i format canonic
  2. ARC-4 decoder: descodificacio de DynamicArray[String] i DynamicArray[UInt64]

Requisits: cap (tests autonoms sense dependencies externes)
"""

import json
import sys
import hashlib
import struct
import os

# Afegir network/ al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from anchoring.models import ElectionState
from anchoring.hasher import compute_election_hash, compute_election_hash_hex
from anchoring.algorand_reader import (
    _abi_encode_string,
    _decode_dynamic_string_array,
    _decode_dynamic_uint64_array,
)

PASSED = 0
FAILED = 0


def test(name):
    """Decorador simple per a tests."""
    def decorator(func):
        global PASSED, FAILED
        try:
            func()
            print(f"  \u2714 {name}")
            PASSED += 1
        except Exception as e:
            print(f"  \u2717 {name}: {e}")
            FAILED += 1
    return decorator


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


# ============================================================
# 1. TESTS DEL HASHER
# ============================================================
print("\n=== 1. Hasher (SHA-256 deterministic) ===")


@test("Hash deterministic: mateixa entrada \u2192 mateix hash")
def _():
    state = ElectionState("Rector2026", ["Alice", "Bob", "Carol"], [10, 5, 8])
    h1 = compute_election_hash(state)
    h2 = compute_election_hash(state)
    assert_eq(h1, h2, "Hash no deterministic")


@test("Hash canvia amb vots diferents")
def _():
    s1 = ElectionState("Rector2026", ["Alice", "Bob"], [10, 5])
    s2 = ElectionState("Rector2026", ["Alice", "Bob"], [10, 6])
    assert compute_election_hash(s1) != compute_election_hash(s2), "Hash hauria de canviar"


@test("Hash canvia amb candidats diferents")
def _():
    s1 = ElectionState("Rector2026", ["Alice", "Bob"], [10, 5])
    s2 = ElectionState("Rector2026", ["Alice", "Charlie"], [10, 5])
    assert compute_election_hash(s1) != compute_election_hash(s2), "Hash hauria de canviar"


@test("Hash canvia amb nom d'eleccio diferent")
def _():
    s1 = ElectionState("Rector2026", ["Alice", "Bob"], [10, 5])
    s2 = ElectionState("Dega2026", ["Alice", "Bob"], [10, 5])
    assert compute_election_hash(s1) != compute_election_hash(s2), "Hash hauria de canviar"


@test("Format canonic es JSON amb claus ordenades i sense espais")
def _():
    state = ElectionState("Test", ["B", "A"], [1, 2])
    canonical = json.dumps(
        {"candidates": ["B", "A"], "election": "Test", "votes": [1, 2]},
        sort_keys=True, separators=(",", ":")
    )
    expected = hashlib.sha256(canonical.encode("utf-8")).digest()
    assert_eq(compute_election_hash(state), expected, "Format canonic incorrecte")


@test("Hash hex te prefix 0x i 66 caracters")
def _():
    state = ElectionState("Test", ["A"], [0])
    h = compute_election_hash_hex(state)
    assert h.startswith("0x"), "Falta prefix 0x"
    assert_eq(len(h), 66, "Longitud incorrecta")


# ============================================================
# 2. TESTS DEL DECODER ARC-4
# ============================================================
print("\n=== 2. ARC-4 Decoder ===")


@test("abi_encode_string codifica correctament")
def _():
    result = _abi_encode_string("hello")
    assert_eq(result, b"\x00\x05hello", "Codificacio incorrecta")


@test("abi_encode_string amb cadena buida")
def _():
    result = _abi_encode_string("")
    assert_eq(result, b"\x00\x00", "Cadena buida incorrecta")


@test("Decode DynamicArray[UInt64] amb 3 elements")
def _():
    # 3 elements: [100, 200, 300]
    data = struct.pack(">H", 3)  # count = 3
    data += struct.pack(">Q", 100)
    data += struct.pack(">Q", 200)
    data += struct.pack(">Q", 300)
    result = _decode_dynamic_uint64_array(data)
    assert_eq(result, [100, 200, 300], "Descodificacio UInt64 incorrecta")


@test("Decode DynamicArray[UInt64] buit")
def _():
    data = struct.pack(">H", 0)
    result = _decode_dynamic_uint64_array(data)
    assert_eq(result, [], "Array buit hauria de ser []")


@test("Decode DynamicArray[String] amb 2 elements")
def _():
    # Construir manualment: ["AB", "CD"]
    # Header: count=2, offset0, offset1
    # Cada offset es relatiu al byte 0 de dades (despres dels offsets)
    str1 = b"\x00\x02AB"  # len=2 + "AB"
    str2 = b"\x00\x02CD"  # len=2 + "CD"

    # Offsets relatius al byte 2 (despres del count)
    # offset[0] = 4 (skip 2 offset slots of 2 bytes each)
    # offset[1] = 4 + 4 = 8
    data = struct.pack(">H", 2)  # count
    data += struct.pack(">H", 4)  # offset to str1 (2 offsets * 2 bytes = 4)
    data += struct.pack(">H", 8)  # offset to str2
    data += str1
    data += str2

    result = _decode_dynamic_string_array(data)
    assert_eq(result, ["AB", "CD"], "Descodificacio String incorrecta")


@test("Decode DynamicArray[String] buit")
def _():
    data = struct.pack(">H", 0)
    result = _decode_dynamic_string_array(data)
    assert_eq(result, [], "Array buit hauria de ser []")


# ============================================================
# RESUM
# ============================================================
print(f"\n{'='*50}")
print(f"RESULTAT: {PASSED} tests passats, {FAILED} tests fallats")
print(f"{'='*50}")

sys.exit(1 if FAILED > 0 else 0)
