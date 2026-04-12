"""
Modul: hasher.py
Descripcio: Calcula el hash SHA-256 deterministic de l'estat d'una eleccio.
            Totes les universitats han de produir el MATEIX hash per al
            mateix estat, garantint el consens K-de-N.
Referencia: BLOCKCHAIN.pdf §7.3.3, §9.7
"""

import hashlib
import json

from .models import ElectionState


def compute_election_hash(state: ElectionState) -> bytes:
    """
    Calcula el hash SHA-256 de la representacio canonica de l'eleccio.

    Format canonic (JSON amb claus ordenades, sense espais):
    {"candidates":["Alice","Bob"],"election":"Rector2026","votes":[5,3]}

    Args:
        state: Estat de l'eleccio llegit des d'Algorand

    Returns:
        Hash SHA-256 de 32 bytes
    """
    canonical = {
        "candidates": state.candidates,
        "election": state.election_name,
        "votes": state.votes,
    }
    canonical_json = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).digest()


def compute_election_hash_hex(state: ElectionState) -> str:
    """Retorna el hash SHA-256 com a cadena hexadecimal amb prefix 0x."""
    return "0x" + compute_election_hash(state).hex()
