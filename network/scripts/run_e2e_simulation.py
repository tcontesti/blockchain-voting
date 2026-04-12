"""
Script: run_e2e_simulation.py
Descripcio: Simulacio end-to-end del sistema de votacio amb ancoratge K-de-N.

Flux complet:
  1. Verifica que AlgoKit localnet esta activa
  2. Connecta al contracte d'Algorand desplegat
  3. Connecta al NotaryContract d'Ethereum
  4. Crea una proposta d'eleccio
  5. Carrega el cens de la proposta
  6. Vota a la proposta fins assolir el llindar (genera eleccio)
  7. Vota a l'eleccio generada
  8. Cada universitat: llegeix estat → calcula hash → envia a Ethereum
  9. Verifica el consens K-de-N

Pre-requisits:
  - algokit localnet start
  - Contracte d'Algorand desplegat (APP_ID configurat)
  - NotaryContract desplegat (NOTARY_CONTRACT_ADDRESS configurat)
  - network/.env configurat (setup_universities.py)

Us:
  cd blockchain-voting/
  python network/scripts/run_e2e_simulation.py
"""

import logging
import os
import sys
import time
from pathlib import Path

# Afegir el directori arrel al path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "network"))

from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def check_localnet():
    """Verifica que AlgoKit localnet esta activa."""
    from algosdk.v2client.algod import AlgodClient

    server = os.environ.get("ALGOD_SERVER", "http://localhost")
    port = os.environ.get("ALGOD_PORT", "4001")
    token = os.environ.get("ALGOD_TOKEN", "a" * 64)

    client = AlgodClient(token, f"{server}:{port}")
    try:
        status = client.status()
        logger.info(f"Localnet activa - Round: {status['last-round']}")
        return client
    except Exception as e:
        logger.error(f"Localnet no disponible: {e}")
        logger.error("Executa: algokit localnet start")
        sys.exit(1)


def run_simulation():
    """Executa la simulacio completa."""

    # Carregar .env
    env_path = ROOT_DIR / "network" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv(ROOT_DIR / ".env")

    app_id = int(os.environ.get("APP_ID", "0"))
    notary_address = os.environ.get("NOTARY_CONTRACT_ADDRESS", "")

    if not app_id:
        logger.error("APP_ID no configurat. Desplega el contracte primer.")
        sys.exit(1)

    if not notary_address:
        logger.error("NOTARY_CONTRACT_ADDRESS no configurat. Desplega el NotaryContract primer.")
        sys.exit(1)

    # 1. Verificar localnet
    print("\n" + "=" * 60)
    print("FASE 1: Verificar localnet")
    print("=" * 60)
    algod_client = check_localnet()

    # 2. Carregar universitats
    print("\n" + "=" * 60)
    print("FASE 2: Carregar configuracio d'universitats")
    print("=" * 60)
    from config.network_config import load_universities
    universities, threshold_k = load_universities()
    logger.info(f"Universitats carregades: {len(universities)} (K={threshold_k})")
    for uni in universities:
        logger.info(f"  {uni.id}: Algo={uni.algorand_address[:12]}... Eth={uni.ethereum_address}")

    # 3. Llegir estat d'una eleccio existent
    print("\n" + "=" * 60)
    print("FASE 3: Llegir eleccions des d'Algorand")
    print("=" * 60)
    from anchoring.algorand_reader import AlgorandElectionReader
    reader = AlgorandElectionReader(algod_client, app_id)
    elections = reader.get_all_election_names()

    if not elections:
        logger.warning("No hi ha eleccions actives al contracte.")
        logger.info(
            "Per crear una eleccio, usa el contracte per:\n"
            "  1. Carregar el cens global\n"
            "  2. Crear una proposta\n"
            "  3. Carregar el cens de la proposta\n"
            "  4. Votar fins al llindar"
        )
        print("\nSimulacio finalitzada (sense eleccions per ancorar)")
        return

    logger.info(f"Eleccions trobades: {elections}")

    # 4. Ancoratge K-de-N
    print("\n" + "=" * 60)
    print("FASE 4: Ancoratge K-de-N a Ethereum")
    print("=" * 60)
    from anchoring.hasher import compute_election_hash, compute_election_hash_hex
    from anchoring.ethereum_submitter import EthereumSubmitter

    eth_rpc = os.environ.get("ETHEREUM_RPC_URL", "http://localhost:8545")

    for election_name in elections:
        logger.info(f"\n--- Ancorant eleccio: {election_name} ---")

        # Llegir estat
        state = reader.read_election_state(election_name)
        if state is None:
            logger.warning(f"No s'ha pogut llegir l'estat de '{election_name}'")
            continue

        logger.info(f"Candidats: {state.candidates}")
        logger.info(f"Vots:      {state.votes}")

        # Calcular hash
        election_hash = compute_election_hash(state)
        hash_hex = compute_election_hash_hex(state)
        logger.info(f"Hash SHA-256: {hash_hex}")

        # Cada universitat envia el hash
        for uni in universities:
            if not uni.ethereum_private_key:
                logger.warning(f"  {uni.id}: clau Ethereum no configurada, saltant")
                continue

            try:
                submitter = EthereumSubmitter(eth_rpc, notary_address, uni.ethereum_private_key)

                if submitter.has_already_submitted(election_name):
                    logger.info(f"  {uni.id}: ja ha enviat hash, saltant")
                    continue

                tx_hash = submitter.submit_hash(election_name, election_hash)
                logger.info(f"  {uni.id}: hash enviat! tx={tx_hash}")

                # Comprovar consens
                finalized, official_hash, submissions = submitter.check_consensus(election_name)
                if finalized:
                    logger.info(
                        f"\n  *** CONSENS ASSOLIT per '{election_name}' ***"
                        f"\n  Hash oficial: 0x{official_hash.hex()}"
                        f"\n  Enviaments: {submissions}"
                    )
                    break
                else:
                    logger.info(f"  Enviaments: {submissions}/{threshold_k} (esperant consens)")

            except Exception as e:
                logger.error(f"  {uni.id}: error -> {e}")

    # 5. Resum final
    print("\n" + "=" * 60)
    print("RESUM FINAL")
    print("=" * 60)

    for election_name in elections:
        try:
            uni = universities[0]
            if uni.ethereum_private_key:
                submitter = EthereumSubmitter(eth_rpc, notary_address, uni.ethereum_private_key)
                finalized, official_hash, submissions = submitter.check_consensus(election_name)
                status = "FINALITZADA" if finalized else "PENDENT"
                print(f"  {election_name}: {status} ({submissions} enviaments)")
                if finalized:
                    print(f"    Hash oficial: 0x{official_hash.hex()}")
        except Exception:
            pass

    print("\nSimulacio completada!")


if __name__ == "__main__":
    run_simulation()
