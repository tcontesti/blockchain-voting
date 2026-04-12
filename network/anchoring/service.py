"""
Modul: service.py
Descripcio: Servei d'ancoratge principal. Cada universitat executa una
            instancia que llegeix l'estat de les eleccions d'Algorand,
            calcula el hash SHA-256 i l'envia al NotaryContract d'Ethereum.
Referencia: BLOCKCHAIN.pdf §7.2.4, §7.3.3
"""

import logging
import os
import sys
import time

from algosdk.v2client.algod import AlgodClient

from .algorand_reader import AlgorandElectionReader
from .ethereum_submitter import EthereumSubmitter
from .hasher import compute_election_hash, compute_election_hash_hex
from .models import AnchoringResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class AnchoringService:
    """
    Servei d'ancoratge per a un node universitari.

    Pot funcionar en dos modes:
    - On-demand: anchor_election() per a una eleccio concreta
    - Polling: run() que escaneja periodicament noves eleccions
    """

    def __init__(
        self,
        university_id: str,
        algod_client: AlgodClient,
        app_id: int,
        eth_submitter: EthereumSubmitter,
    ):
        self.university_id = university_id
        self.reader = AlgorandElectionReader(algod_client, app_id)
        self.submitter = eth_submitter
        self.anchored: set[str] = set()

    def anchor_election(self, election_name: str) -> AnchoringResult | None:
        """
        Ancora una eleccio concreta: llegeix l'estat, calcula hash, envia a Ethereum.

        Returns:
            AnchoringResult o None si l'eleccio no existeix o ja s'ha ancorat
        """
        if election_name in self.anchored:
            logger.info(f"[{self.university_id}] Eleccio '{election_name}' ja ancorada, saltant")
            return None

        if self.submitter.has_already_submitted(election_name):
            logger.info(f"[{self.university_id}] Hash ja enviat a Ethereum per '{election_name}'")
            self.anchored.add(election_name)
            return None

        # Llegir estat des d'Algorand
        state = self.reader.read_election_state(election_name)
        if state is None:
            logger.warning(f"[{self.university_id}] Eleccio '{election_name}' no trobada a Algorand")
            return None

        logger.info(
            f"[{self.university_id}] Estat llegit per '{election_name}': "
            f"{len(state.candidates)} candidats, {sum(state.votes)} vots totals"
        )

        # Calcular hash
        election_hash = compute_election_hash(state)
        hash_hex = compute_election_hash_hex(state)
        logger.info(f"[{self.university_id}] Hash calculat: {hash_hex}")

        # Enviar a Ethereum
        try:
            tx_hash = self.submitter.submit_hash(election_name, election_hash)
        except Exception as e:
            logger.error(f"[{self.university_id}] Error enviant hash: {e}")
            return None

        self.anchored.add(election_name)

        # Comprovar consens
        finalized, official_hash, submissions = self.submitter.check_consensus(election_name)
        if finalized:
            logger.info(
                f"[{self.university_id}] CONSENS ASSOLIT per '{election_name}' "
                f"amb {submissions} enviaments!"
            )
        else:
            logger.info(
                f"[{self.university_id}] Esperant consens per '{election_name}': "
                f"{submissions} enviaments (cal K)"
            )

        return AnchoringResult(
            election_name=election_name,
            hash_hex=hash_hex,
            eth_tx_hash=tx_hash,
            university_id=self.university_id,
            timestamp=time.time(),
        )

    def run(self, poll_interval: int = 10):
        """
        Mode polling: escaneja periodicament noves eleccions i les ancora.
        """
        logger.info(f"[{self.university_id}] Servei d'ancoratge iniciat (interval: {poll_interval}s)")

        while True:
            try:
                elections = self.reader.get_all_election_names()
                for name in elections:
                    if name not in self.anchored:
                        self.anchor_election(name)
            except Exception as e:
                logger.error(f"[{self.university_id}] Error en el cicle de polling: {e}")

            time.sleep(poll_interval)


def main():
    """Punt d'entrada per a l'execucio com a contenidor Docker."""
    university_id = os.environ.get("UNIVERSITY_ID", "unknown")
    algod_server = os.environ.get("ALGOD_SERVER", "http://localhost")
    algod_port = os.environ.get("ALGOD_PORT", "4001")
    algod_token = os.environ.get("ALGOD_TOKEN", "a" * 64)
    app_id = int(os.environ.get("APP_ID", "0"))
    eth_rpc_url = os.environ.get("ETHEREUM_RPC_URL", "http://localhost:8545")
    notary_address = os.environ.get("NOTARY_CONTRACT_ADDRESS", "")
    eth_private_key = os.environ.get("ANCHORING_PRIVATE_KEY", "")
    poll_interval = int(os.environ.get("POLL_INTERVAL", "10"))

    if not app_id:
        logger.error("APP_ID no configurat. Desplegue primer el contracte d'Algorand.")
        sys.exit(1)
    if not notary_address:
        logger.error("NOTARY_CONTRACT_ADDRESS no configurat.")
        sys.exit(1)
    if not eth_private_key:
        logger.error("ANCHORING_PRIVATE_KEY no configurat.")
        sys.exit(1)

    algod_client = AlgodClient(algod_token, f"{algod_server}:{algod_port}")
    submitter = EthereumSubmitter(eth_rpc_url, notary_address, eth_private_key)

    service = AnchoringService(
        university_id=university_id,
        algod_client=algod_client,
        app_id=app_id,
        eth_submitter=submitter,
    )
    service.run(poll_interval=poll_interval)


if __name__ == "__main__":
    main()
