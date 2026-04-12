"""
Test d'integracio complet del sistema de xarxa universitaria.

Exercita:
  1. Hasher: determinisme i format canonic
  2. ARC-4 decoder: descodificacio de DynamicArray[String] i DynamicArray[UInt64]
  3. Ethereum NotaryContract: desplegament, enviament de hashes, consens K-de-N
  4. Flux complet: 3 universitats ancorant la mateixa eleccio

Requisits: npx hardhat node executant-se al port 8545
"""

import json
import subprocess
import sys
import time
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
            print(f"  ✔ {name}")
            PASSED += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            FAILED += 1
    return decorator


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}: expected {expected!r}, got {actual!r}")


# ============================================================
# 1. TESTS DEL HASHER
# ============================================================
print("\n=== 1. Hasher (SHA-256 deterministic) ===")


@test("Hash deterministic: mateixa entrada → mateix hash")
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
# 3. TESTS ETHEREUM (NotaryContract via Hardhat)
# ============================================================
print("\n=== 3. Ethereum NotaryContract (live Hardhat) ===")

# Iniciar Hardhat node en segon pla
hardhat_proc = None
hardhat_available = False

try:
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    if w3.is_connected():
        hardhat_available = True
        print("  (Hardhat node ja actiu)")
except Exception:
    pass

if not hardhat_available:
    print("  Iniciant Hardhat node...")
    hardhat_proc = subprocess.Popen(
        ["npx", "hardhat", "node"],
        cwd=os.path.join(os.path.dirname(__file__), "ethereum"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Esperar que estigui llest
    for _ in range(20):
        time.sleep(0.5)
        try:
            w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
            if w3.is_connected():
                hardhat_available = True
                print("  Hardhat node iniciat")
                break
        except Exception:
            continue

if hardhat_available:
    # Carregar ABI i bytecode del contracte compilat
    artifact_path = os.path.join(
        os.path.dirname(__file__),
        "ethereum", "artifacts", "contracts",
        "NotaryContract.sol", "NotaryContract.json"
    )

    with open(artifact_path) as f:
        artifact = json.load(f)

    CONTRACT_ABI = artifact["abi"]
    CONTRACT_BYTECODE = artifact["bytecode"]

    # Obtenir comptes de Hardhat
    accounts = w3.eth.accounts
    uni_addresses = accounts[:3]  # UIB, UPC, UAB
    outsider = accounts[4]

    # Claus privades de Hardhat (ben conegudes, nomes per testing)
    HARDHAT_KEYS = [
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
        "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    ]

    THRESHOLD = 2
    notary_contract = None

    @test("Desplegar NotaryContract amb 3 universitats, K=2")
    def _():
        global notary_contract
        NotaryContract = w3.eth.contract(abi=CONTRACT_ABI, bytecode=CONTRACT_BYTECODE)
        tx_hash = NotaryContract.constructor(uni_addresses, THRESHOLD).transact(
            {"from": accounts[0]}
        )
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        assert receipt["status"] == 1, "Desplegament ha fallat"
        notary_contract = w3.eth.contract(
            address=receipt["contractAddress"], abi=CONTRACT_ABI
        )
        print(f"    Contracte a: {receipt['contractAddress']}")

    @test("Llindar es 2")
    def _():
        assert_eq(notary_contract.functions.threshold().call(), 2, "Llindar incorrecte")

    @test("3 universitats registrades")
    def _():
        count = notary_contract.functions.getUniversityCount().call()
        assert_eq(count, 3, "Nombre d'universitats incorrecte")

    # Simular ancoratge complet
    election_name = "Rector2026"
    state = ElectionState("Rector2026", ["Alice", "Bob", "Carol"], [42, 31, 27])
    election_hash = compute_election_hash(state)

    @test("UIB envia hash → no finalitzat (1/2)")
    def _():
        from anchoring.ethereum_submitter import EthereumSubmitter
        sub = EthereumSubmitter("http://127.0.0.1:8545",
                                notary_contract.address, HARDHAT_KEYS[0])
        tx = sub.submit_hash(election_name, election_hash)
        assert tx, "Transaccio buida"
        finalized, _, subs = sub.check_consensus(election_name)
        assert not finalized, "No hauria d'estar finalitzat amb 1 enviament"
        assert_eq(subs, 1, "Hauria de tenir 1 enviament")

    @test("UPC envia hash → CONSENS ASSOLIT (2/2)")
    def _():
        from anchoring.ethereum_submitter import EthereumSubmitter
        sub = EthereumSubmitter("http://127.0.0.1:8545",
                                notary_contract.address, HARDHAT_KEYS[1])
        tx = sub.submit_hash(election_name, election_hash)
        assert tx, "Transaccio buida"
        finalized, official, subs = sub.check_consensus(election_name)
        assert finalized, "Hauria d'estar finalitzat amb K=2 enviaments"
        assert_eq(subs, 2, "Hauria de tenir 2 enviaments")
        assert_eq(official, election_hash, "Hash oficial incorrecte")

    @test("UAB no pot enviar despres de finalitzacio")
    def _():
        from anchoring.ethereum_submitter import EthereumSubmitter
        sub = EthereumSubmitter("http://127.0.0.1:8545",
                                notary_contract.address, HARDHAT_KEYS[2])
        try:
            sub.submit_hash(election_name, election_hash)
            raise AssertionError("Hauria d'haver fallat")
        except Exception as e:
            assert "finalitzada" in str(e).lower() or "revert" in str(e).lower(), \
                f"Error inesperat: {e}"

    @test("Hash oficial coincideix amb el calculat localment")
    def _():
        from anchoring.ethereum_submitter import EthereumSubmitter
        sub = EthereumSubmitter("http://127.0.0.1:8545",
                                notary_contract.address, HARDHAT_KEYS[0])
        finalized, official, _ = sub.check_consensus(election_name)
        expected_hex = compute_election_hash_hex(state)
        actual_hex = "0x" + official.hex()
        assert_eq(actual_hex, expected_hex, "Hash no coincideix")

    # Test amb segona eleccio (hash diferent, consens falla)
    election2 = "Dega2026"
    state_a = ElectionState("Dega2026", ["X", "Y"], [10, 20])
    state_b = ElectionState("Dega2026", ["X", "Y"], [10, 21])  # Diferent!
    hash_a = compute_election_hash(state_a)
    hash_b = compute_election_hash(state_b)

    @test("Desacord: 2 universitats envien hashes diferents → NO consens")
    def _():
        # Desplegar nou contracte per a aquest test
        NotaryContract = w3.eth.contract(abi=CONTRACT_ABI, bytecode=CONTRACT_BYTECODE)
        tx = NotaryContract.constructor(uni_addresses, 2).transact({"from": accounts[0]})
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        contract2 = w3.eth.contract(address=receipt["contractAddress"], abi=CONTRACT_ABI)

        from anchoring.ethereum_submitter import EthereumSubmitter
        sub_uib = EthereumSubmitter("http://127.0.0.1:8545",
                                     contract2.address, HARDHAT_KEYS[0])
        sub_upc = EthereumSubmitter("http://127.0.0.1:8545",
                                     contract2.address, HARDHAT_KEYS[1])

        sub_uib.submit_hash(election2, hash_a)
        sub_upc.submit_hash(election2, hash_b)

        finalized, _, subs = sub_uib.check_consensus(election2)
        assert not finalized, "No hauria de finalitzar amb hashes discordants"
        assert_eq(subs, 2, "Hauria de tenir 2 enviaments")

    # Test AnchoringService amb mock
    @test("AnchoringService detecta enviaments duplicats")
    def _():
        from anchoring.ethereum_submitter import EthereumSubmitter
        sub = EthereumSubmitter("http://127.0.0.1:8545",
                                notary_contract.address, HARDHAT_KEYS[0])
        assert sub.has_already_submitted(election_name), \
            "UIB hauria de figurar com a ja enviat"

else:
    print("  ⚠ Hardhat no disponible, saltant tests d'Ethereum")


# ============================================================
# RESUM
# ============================================================
print(f"\n{'='*50}")
print(f"RESULTAT: {PASSED} tests passats, {FAILED} tests fallats")
print(f"{'='*50}")

# Aturar Hardhat si l'hem iniciat nosaltres
if hardhat_proc:
    hardhat_proc.terminate()
    hardhat_proc.wait()
    print("Hardhat node aturat")

sys.exit(1 if FAILED > 0 else 0)
