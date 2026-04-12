"""
Script: verify_anchoring.py
Descripcio: Verifica l'estat d'ancoratge d'una eleccio al NotaryContract.
            Consulta el contracte d'Ethereum per comprovar si el consens
            K-de-N s'ha assolit.

Us:
  python network/scripts/verify_anchoring.py --election "Rector2026"
  python network/scripts/verify_anchoring.py --all

Referencia: BLOCKCHAIN.pdf §3.1.5 (Verificabilitat individual)
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "network"))


def verify_election(election_name: str, eth_rpc: str, notary_address: str, universities: list):
    """Verifica l'estat d'ancoratge d'una eleccio."""
    from anchoring.ethereum_submitter import EthereumSubmitter

    # Usem la primera universitat per fer consultes (nomes lectura)
    uni = universities[0]
    if not uni.ethereum_private_key:
        logger.error("Cal al menys una universitat amb clau Ethereum configurada")
        return

    submitter = EthereumSubmitter(eth_rpc, notary_address, uni.ethereum_private_key)
    finalized, official_hash, submissions = submitter.check_consensus(election_name)

    print(f"\nEleccio: {election_name}")
    print(f"  Finalitzada: {'SI' if finalized else 'NO'}")
    print(f"  Enviaments:  {submissions}")
    if finalized:
        print(f"  Hash oficial: 0x{official_hash.hex()}")

    # Mostrar detall per universitat
    for uni in universities:
        if not uni.ethereum_private_key:
            continue
        sub = EthereumSubmitter(eth_rpc, notary_address, uni.ethereum_private_key)
        has_sub = sub.has_already_submitted(election_name)
        print(f"  {uni.id} ({uni.ethereum_address[:12]}...): {'ENVIAT' if has_sub else 'PENDENT'}")


def main():
    parser = argparse.ArgumentParser(description="Verifica l'ancoratge d'eleccions")
    parser.add_argument("--election", type=str, help="Nom de l'eleccio a verificar")
    parser.add_argument("--all", action="store_true", help="Verifica totes les eleccions")
    args = parser.parse_args()

    if not args.election and not args.all:
        parser.error("Especifica --election NOM o --all")

    # Carregar .env
    from dotenv import load_dotenv
    env_path = ROOT_DIR / "network" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv(ROOT_DIR / ".env")

    notary_address = os.environ.get("NOTARY_CONTRACT_ADDRESS", "")
    eth_rpc = os.environ.get("ETHEREUM_RPC_URL", "http://localhost:8545")

    if not notary_address:
        logger.error("NOTARY_CONTRACT_ADDRESS no configurat")
        sys.exit(1)

    from config.network_config import load_universities
    universities, threshold_k = load_universities()
    print(f"Llindar K = {threshold_k}, Universitats N = {len(universities)}")

    if args.election:
        verify_election(args.election, eth_rpc, notary_address, universities)
    elif args.all:
        # Llegir eleccions des d'Algorand
        app_id = int(os.environ.get("APP_ID", "0"))
        if not app_id:
            logger.error("APP_ID no configurat (necessari amb --all)")
            sys.exit(1)

        from algosdk.v2client.algod import AlgodClient
        from anchoring.algorand_reader import AlgorandElectionReader

        server = os.environ.get("ALGOD_SERVER", "http://localhost")
        port = os.environ.get("ALGOD_PORT", "4001")
        token = os.environ.get("ALGOD_TOKEN", "a" * 64)

        algod = AlgodClient(token, f"{server}:{port}")
        reader = AlgorandElectionReader(algod, app_id)
        elections = reader.get_all_election_names()

        if not elections:
            print("\nNo hi ha eleccions actives.")
        else:
            for name in elections:
                verify_election(name, eth_rpc, notary_address, universities)


if __name__ == "__main__":
    main()
