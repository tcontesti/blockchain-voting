"""
Modul: consensus.py
Descripcio: Implementa la logica de consens K-de-N per a l'ancoratge
            distribuit dels resultats electorals.

            En el model de xarxa, cada universitat calcula independentment
            el hash SHA-256 dels resultats. Abans d'enviar el hash a
            Ethereum, el sistema verifica localment si hi ha consens:
            es a dir, si almenys K dels N nodes han calculat el mateix hash.

            Aixo permet:
              - Detectar discrepancies entre nodes abans de gastar gas
              - Registrar quines universitats coincideixen i quines no
              - Simular el comportament del NotaryContract sense Ethereum

Referencia: BLOCKCHAIN.pdf §9.7 (Ancoratge K-de-N), §7.3.3 (Consens)
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConsensusResult:
    """
    Resultat de la verificacio de consens K-de-N.

    Atributs:
        reached:          True si almenys K nodes coincideixen en el hash.
        consensus_hash:   Hash amb mes coincidencies (hex amb prefix 0x).
        agreeing_nodes:   Llista d'IDs de nodes que coincideixen amb el hash.
        dissenting_nodes: Llista d'IDs de nodes que NO coincideixen.
        total_nodes:      Nombre total de nodes (N).
        threshold_k:      Llindar minim requerit (K).
        all_hashes:       Diccionari {node_id: hash_hex} amb tots els hashes.
    """

    reached: bool
    consensus_hash: str
    agreeing_nodes: list[str]
    dissenting_nodes: list[str] = field(default_factory=list)
    total_nodes: int = 0
    threshold_k: int = 0
    all_hashes: dict[str, str] = field(default_factory=dict)


def check_consensus(
    node_hashes: dict[str, str],
    threshold_k: int,
) -> ConsensusResult:
    """
    Verifica si hi ha consens K-de-N entre els hashes calculats pels nodes.

    Agrupa els hashes per valor i comprova si algun hash ha estat calculat
    per almenys K nodes. Si es aixi, el consens s'ha assolit i el hash
    es considera oficial.

    Args:
        node_hashes: Diccionari {node_id: hash_hex} amb el hash calculat
                     per cada universitat (ex: {"uib": "0xab12...", ...}).
        threshold_k: Nombre minim de nodes que han de coincidir (K).

    Returns:
        ConsensusResult amb l'estat del consens.
    """
    if not node_hashes:
        return ConsensusResult(
            reached=False,
            consensus_hash="",
            agreeing_nodes=[],
            total_nodes=0,
            threshold_k=threshold_k,
            all_hashes={},
        )

    # Agrupar nodes per hash
    hash_groups: dict[str, list[str]] = {}
    for node_id, hash_hex in node_hashes.items():
        hash_groups.setdefault(hash_hex, []).append(node_id)

    # Trobar el hash amb mes coincidencies
    best_hash = max(hash_groups, key=lambda h: len(hash_groups[h]))
    agreeing = hash_groups[best_hash]
    all_node_ids = set(node_hashes.keys())
    dissenting = list(all_node_ids - set(agreeing))

    reached = len(agreeing) >= threshold_k

    if reached:
        logger.info(
            f"Consens assolit: {len(agreeing)}/{len(node_hashes)} nodes "
            f"(K={threshold_k}) amb hash {best_hash[:18]}..."
        )
    else:
        logger.warning(f"Consens NO assolit: {len(agreeing)}/{len(node_hashes)} nodes " f"(K={threshold_k} requerits)")

    if dissenting:
        logger.warning(f"Nodes discrepants: {dissenting}")

    return ConsensusResult(
        reached=reached,
        consensus_hash=best_hash,
        agreeing_nodes=agreeing,
        dissenting_nodes=dissenting,
        total_nodes=len(node_hashes),
        threshold_k=threshold_k,
        all_hashes=node_hashes,
    )
