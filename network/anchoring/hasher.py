"""
Modul: hasher.py
Descripcio: Calcula el hash SHA-256 deterministic de l'estat d'una eleccio.

            La funcio principal d'aquest modul es garantir que tots els nodes
            universitaris (UIB, UPC, UAB) produeixin exactament el MATEIX hash
            per a un mateix estat electoral. Aixo es fonamental per al mecanisme
            de consens K-de-N: si K universitats envien el mateix hash al
            contracte de notaria, el resultat queda ancorat com a oficial.

            El determinisme s'aconsegueix mitjancant una representacio JSON
            canonica de l'estat:
              - Claus del diccionari ordenades alfabeticament (sort_keys=True)
              - Sense espais ni salts de linia (separators=(",", ":"))
              - Codificacio UTF-8

            Exemple de representacio canonica:
              {"candidates":["Alice","Bob"],"election":"Rector2026","votes":[42,31]}

            Qualsevol canvi en els candidats, els vots o el nom de l'eleccio
            produeix un hash completament diferent, detectant aixi qualsevol
            manipulacio o discrepancia entre nodes.

Referencia: BLOCKCHAIN.pdf §7.3.3 (Hash deterministic), §9.7 (Integritat)
"""

import hashlib
import json

from .models import ElectionState


def compute_election_hash(state: ElectionState) -> bytes:
    """
    Calcula el hash SHA-256 de la representacio canonica d'una eleccio.

    Construeix un diccionari amb tres claus:
      - "candidates": llista de noms de candidats (ordre original)
      - "election": nom identificador de l'eleccio
      - "votes": llista de recomptes de vots (corresponent als candidats)

    El diccionari es serialitza a JSON canonic (claus ordenades, sense espais)
    i se n'obte el digest SHA-256.

    Args:
        state: Estat de l'eleccio llegit des d'Algorand (ElectionState).
               Ha de contenir election_name, candidates i votes.

    Returns:
        Hash SHA-256 de 32 bytes (bytes). Tots els nodes que llegeixin el
        mateix estat produiran exactament el mateix hash.

    Exemple:
        >>> state = ElectionState("Rector2026", ["Alice", "Bob"], [42, 31])
        >>> h = compute_election_hash(state)
        >>> len(h)
        32
    """
    canonical = {
        "candidates": state.candidates,
        "election": state.election_name,
        "votes": state.votes,
    }
    canonical_json = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).digest()


def compute_election_hash_hex(state: ElectionState) -> str:
    """
    Calcula el hash SHA-256 i el retorna com a cadena hexadecimal amb prefix 0x.

    Format de sortida: "0x" seguit de 64 caracters hexadecimals (64 hex = 32 bytes).
    Compatible amb el format bytes32 de Solidity per a l'ancoratge a Ethereum.

    Args:
        state: Estat de l'eleccio llegit des d'Algorand (ElectionState).

    Returns:
        Cadena de 66 caracters (ex: "0xab12...ef56").

    Exemple:
        >>> state = ElectionState("Rector2026", ["Alice", "Bob"], [42, 31])
        >>> h = compute_election_hash_hex(state)
        >>> h.startswith("0x") and len(h) == 66
        True
    """
    return "0x" + compute_election_hash(state).hex()
