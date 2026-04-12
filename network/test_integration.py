"""
Test d'integracio del sistema de xarxa universitaria.

Verifica el correcte funcionament dels components de lectura i verificacio
que cada node universitari utilitza per processar els resultats electorals
de la blockchain Algorand:

  1. Hasher (SHA-256 deterministic):
     Comprova que el hash calculat es deterministic (mateixa entrada -> mateix
     hash), que qualsevol canvi en candidats, vots o nom d'eleccio produeix
     un hash diferent, i que el format canonic JSON es correcte.

  2. Decoder ARC-4:
     Verifica la codificacio i descodificacio dels formats binaris ARC-4
     que el contracte SistemaVotacion usa per emmagatzemar les dades al
     Box Storage: DynamicArray[String] per als candidats i
     DynamicArray[UInt64] per als vots.

Aquests tests son completament autonoms i no requereixen cap dependencia
externa (ni localnet, ni algod, ni Hardhat). Exerciten la logica pura
de transformacio de dades.

Us:
  cd network/
  python test_integration.py

Resultat esperat: 12 tests passats, 0 tests fallats.
"""

import json
import sys
import hashlib
import struct
import os

# Afegir network/ al path per poder importar els paquets locals
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
    """
    Decorador que executa una funcio com a test i registra el resultat.

    Captura qualsevol excepcio com a fallada del test. Si la funcio
    s'executa sense errors, el test es considera passat.

    Args:
        name: Descripcio del test que es mostra per pantalla.
    """
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
    """
    Comprova que dos valors son iguals. Llanca AssertionError si no ho son.

    Args:
        actual:   Valor obtingut.
        expected: Valor esperat.
        msg:      Missatge descriptiu de l'error (opcional).
    """
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


# ============================================================
# 1. TESTS DEL HASHER
# ============================================================
# Verifiquen que el hash SHA-256 es deterministic i sensible a
# qualsevol canvi en les dades electorals. Aixo es critic perque
# tots els nodes universitaris han de produir el MATEIX hash per
# al mateix estat, permetent el consens K-de-N.
# ============================================================
print("\n=== 1. Hasher (SHA-256 deterministic) ===")


@test("Hash deterministic: mateixa entrada \u2192 mateix hash")
def _():
    """Dos calculs amb les mateixes dades han de produir el mateix hash."""
    state = ElectionState("Rector2026", ["Alice", "Bob", "Carol"], [10, 5, 8])
    h1 = compute_election_hash(state)
    h2 = compute_election_hash(state)
    assert_eq(h1, h2, "Hash no deterministic")


@test("Hash canvia amb vots diferents")
def _():
    """Un sol vot de diferencia ha de produir un hash completament diferent."""
    s1 = ElectionState("Rector2026", ["Alice", "Bob"], [10, 5])
    s2 = ElectionState("Rector2026", ["Alice", "Bob"], [10, 6])
    assert compute_election_hash(s1) != compute_election_hash(s2), "Hash hauria de canviar"


@test("Hash canvia amb candidats diferents")
def _():
    """Canviar un nom de candidat ha de produir un hash diferent."""
    s1 = ElectionState("Rector2026", ["Alice", "Bob"], [10, 5])
    s2 = ElectionState("Rector2026", ["Alice", "Charlie"], [10, 5])
    assert compute_election_hash(s1) != compute_election_hash(s2), "Hash hauria de canviar"


@test("Hash canvia amb nom d'eleccio diferent")
def _():
    """Dues eleccions amb el mateix resultat pero nom diferent tenen hashes diferents."""
    s1 = ElectionState("Rector2026", ["Alice", "Bob"], [10, 5])
    s2 = ElectionState("Dega2026", ["Alice", "Bob"], [10, 5])
    assert compute_election_hash(s1) != compute_election_hash(s2), "Hash hauria de canviar"


@test("Format canonic es JSON amb claus ordenades i sense espais")
def _():
    """El hash ha de correspondre exactament al format JSON canonic definit."""
    state = ElectionState("Test", ["B", "A"], [1, 2])
    canonical = json.dumps(
        {"candidates": ["B", "A"], "election": "Test", "votes": [1, 2]},
        sort_keys=True, separators=(",", ":")
    )
    expected = hashlib.sha256(canonical.encode("utf-8")).digest()
    assert_eq(compute_election_hash(state), expected, "Format canonic incorrecte")


@test("Hash hex te prefix 0x i 66 caracters")
def _():
    """El format hexadecimal ha de ser compatible amb bytes32 de Solidity."""
    state = ElectionState("Test", ["A"], [0])
    h = compute_election_hash_hex(state)
    assert h.startswith("0x"), "Falta prefix 0x"
    assert_eq(len(h), 66, "Longitud incorrecta")


# ============================================================
# 2. TESTS DEL DECODER ARC-4
# ============================================================
# Verifiquen que la codificacio/descodificacio ARC-4 es correcta.
# El contracte SistemaVotacion emmagatzema els candidats com a
# DynamicArray[String] i els vots com a DynamicArray[UInt64] al
# Box Storage. Aquests tests construeixen dades binaries a ma
# i comproven que el decoder les interpreta correctament.
# ============================================================
print("\n=== 2. ARC-4 Decoder ===")


@test("abi_encode_string codifica correctament")
def _():
    """Verifica la codificacio ARC-4 d'una cadena: 2 bytes longitud + UTF-8."""
    result = _abi_encode_string("hello")
    assert_eq(result, b"\x00\x05hello", "Codificacio incorrecta")


@test("abi_encode_string amb cadena buida")
def _():
    """Una cadena buida es codifica com a 2 bytes zero (longitud = 0)."""
    result = _abi_encode_string("")
    assert_eq(result, b"\x00\x00", "Cadena buida incorrecta")


@test("Decode DynamicArray[UInt64] amb 3 elements")
def _():
    """Descodifica un array de 3 recomptes de vots: [100, 200, 300]."""
    data = struct.pack(">H", 3)  # count = 3
    data += struct.pack(">Q", 100)
    data += struct.pack(">Q", 200)
    data += struct.pack(">Q", 300)
    result = _decode_dynamic_uint64_array(data)
    assert_eq(result, [100, 200, 300], "Descodificacio UInt64 incorrecta")


@test("Decode DynamicArray[UInt64] buit")
def _():
    """Un array buit (count=0) ha de retornar llista buida."""
    data = struct.pack(">H", 0)
    result = _decode_dynamic_uint64_array(data)
    assert_eq(result, [], "Array buit hauria de ser []")


@test("Decode DynamicArray[String] amb 2 elements")
def _():
    """Descodifica un array de 2 noms de candidats: ["AB", "CD"]."""
    # Construir manualment el format binari ARC-4
    str1 = b"\x00\x02AB"  # longitud=2 + contingut "AB"
    str2 = b"\x00\x02CD"  # longitud=2 + contingut "CD"

    # Offsets relatius al byte posterior al count
    # offset[0] = 4 (salta 2 slots d'offset de 2 bytes cadascun)
    # offset[1] = 4 + 4 = 8 (salta offset[0] + str1)
    data = struct.pack(">H", 2)   # count = 2 elements
    data += struct.pack(">H", 4)  # offset del primer string
    data += struct.pack(">H", 8)  # offset del segon string
    data += str1
    data += str2

    result = _decode_dynamic_string_array(data)
    assert_eq(result, ["AB", "CD"], "Descodificacio String incorrecta")


@test("Decode DynamicArray[String] buit")
def _():
    """Un array buit de strings (count=0) ha de retornar llista buida."""
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
