"""
Modul: anchoring_service.py
Descripcio: Servei d'ancoratge que orquestra el flux complet per a un node
            universitari: llegeix l'estat electoral d'Algorand, calcula el
            hash SHA-256, verifica el consens K-de-N, i envia el hash al
            contracte NotaryContract d'Ethereum.

            Aquest modul unifica els components individuals (algorand_reader,
            hasher, consensus, ethereum_submitter) en un flux coherent que
            cada universitat executa de forma independent.

Referencia: BLOCKCHAIN.pdf §7.2.4 (Servei d'Anchoring), §7.3.3 (Components)
"""

import logging
from dataclasses import dataclass

from algosdk.v2client.algod import AlgodClient

from .algorand_reader import AlgorandElectionReader
from .consensus import ConsensusResult, check_consensus
from .ethereum_submitter import EthereumSubmitter, SubmissionResult
from .hasher import compute_election_hash_hex

logger = logging.getLogger(__name__)


@dataclass
class AnchoringResult:
    """
    Resultat complet del proces d'ancoratge d'una eleccio.

    Atributs:
        election_name: Nom de l'eleccio processada.
        hash_hex:      Hash SHA-256 calculat (0x...).
        consensus:     Resultat de la verificacio de consens K-de-N.
        submission:    Resultat de l'enviament a Ethereum (None si no s'ha enviat).
    """

    election_name: str
    hash_hex: str
    consensus: ConsensusResult
    submission: SubmissionResult | None = None


class AnchoringService:
    """
    Servei d'ancoratge per a un node universitari.

    Coordina el flux complet:
      1. Llegeix l'estat electoral des d'Algorand (AlgorandElectionReader)
      2. Calcula el hash SHA-256 deterministic (hasher)
      3. Recull els hashes de tots els nodes i verifica consens (consensus)
      4. Si hi ha consens, envia el hash a Ethereum (EthereumSubmitter)

    Atributs:
        node_id:       Identificador del node universitari (ex: "uib").
        reader:        Lector d'estat electoral d'Algorand.
        submitter:     Client per enviar hashes a Ethereum (opcional).
        threshold_k:   Llindar minim de consens.
    """

    def __init__(
        self,
        node_id: str,
        algod_client: AlgodClient,
        app_id: int,
        threshold_k: int,
        eth_submitter: EthereumSubmitter | None = None,
    ):
        self.node_id = node_id
        self.reader = AlgorandElectionReader(algod_client, app_id)
        self.submitter = eth_submitter
        self.threshold_k = threshold_k

    def compute_hash(self, election_name: str) -> str | None:
        """
        Llegeix l'estat d'una eleccio i calcula el hash SHA-256.

        Args:
            election_name: Nom de l'eleccio.

        Returns:
            Hash hex (0x...) o None si l'eleccio no existeix.
        """
        state = self.reader.read_election_state(election_name)
        if state is None:
            logger.warning(f"[{self.node_id}] Eleccio '{election_name}' no trobada")
            return None
        hash_hex = compute_election_hash_hex(state)
        logger.info(f"[{self.node_id}] Hash calculat per '{election_name}': {hash_hex[:18]}...")
        return hash_hex

    def anchor(
        self,
        election_name: str,
        node_hashes: dict[str, str],
    ) -> AnchoringResult:
        """
        Executa el flux complet d'ancoratge: consens + enviament a Ethereum.

        Args:
            election_name: Nom de l'eleccio.
            node_hashes:   Diccionari {node_id: hash_hex} amb els hashes
                           calculats per tots els nodes de la xarxa.

        Returns:
            AnchoringResult amb l'estat complet del proces.
        """
        my_hash = node_hashes.get(self.node_id, "")

        # Verificar consens K-de-N
        consensus = check_consensus(node_hashes, self.threshold_k)

        submission = None
        if consensus.reached and self.submitter and my_hash == consensus.consensus_hash:
            # Nomes enviem si formem part del consens
            result_hash_bytes = bytes.fromhex(consensus.consensus_hash[2:])
            submission = self.submitter.submit_hash(election_name, result_hash_bytes)
            if submission.success:
                logger.info(f"[{self.node_id}] Hash enviat a Ethereum: tx={submission.tx_hash[:18]}...")
                if submission.anchored:
                    logger.info(f"[{self.node_id}] RESULTAT ANCORAT a Ethereum per '{election_name}'")
        elif not consensus.reached:
            logger.warning(f"[{self.node_id}] Ancoratge no executat: consens no assolit")

        return AnchoringResult(
            election_name=election_name,
            hash_hex=my_hash,
            consensus=consensus,
            submission=submission,
        )
