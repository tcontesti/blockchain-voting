"""
Modul: models.py
Descripcio: Models de dades per al servei d'ancoratge.
Referencia: BLOCKCHAIN.pdf §7.3.3
"""

from dataclasses import dataclass, field


@dataclass
class ElectionState:
    """Estat final d'una eleccio llegit des d'Algorand."""
    election_name: str
    candidates: list[str]
    votes: list[int]
    block_round: int = 0


@dataclass
class AnchoringResult:
    """Resultat d'un proces d'ancoratge a Ethereum."""
    election_name: str
    hash_hex: str
    eth_tx_hash: str
    university_id: str
    timestamp: float = 0.0
