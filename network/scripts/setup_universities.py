"""
Script: setup_universities.py
Descripcio: Genera comptes d'Algorand i carteres d'Ethereum per a
            cada universitat definida a universities.json.
            Escriu les claus al fitxer network/.env.

Us:
  python network/scripts/setup_universities.py

Referencia: BLOCKCHAIN.pdf §10.1 (Configuracio del cens)
"""

import json
import logging
import sys
from pathlib import Path

from algosdk import account, mnemonic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NETWORK_DIR = Path(__file__).parent.parent
CONFIG_PATH = NETWORK_DIR / "config" / "universities.json"


def main():
    # Carregar configuracio
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    env_lines = [
        "# =============================================",
        "# Generat automaticament per setup_universities.py",
        "# =============================================",
        "",
        "# ALGORAND",
        "ALGOD_SERVER=http://localhost",
        "ALGOD_PORT=4001",
        "ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "",
        "# SMART CONTRACT",
        "APP_ID=",
        "",
        "# ETHEREUM",
        "ETHEREUM_RPC_URL=http://localhost:8545",
        "NOTARY_CONTRACT_ADDRESS=",
        "",
    ]

    algo_addresses = []
    eth_addresses = []

    for uni in config["universities"]:
        uni_id = uni["id"].upper()
        uni_name = uni["name"]

        # Generar compte Algorand
        algo_private_key, algo_address = account.generate_account()
        algo_mnemonic = mnemonic.from_private_key(algo_private_key)

        # Generar cartera Ethereum
        try:
            from web3 import Account as EthAccount
            eth_account = EthAccount.create()
            eth_private_key = eth_account.key.hex()
            eth_address = eth_account.address
        except ImportError:
            # Fallback: generar clau aleatoria
            import secrets
            eth_private_key = "0x" + secrets.token_hex(32)
            eth_address = "(web3 no disponible)"

        algo_addresses.append(algo_address)
        eth_addresses.append(eth_address)

        logger.info(f"\n{'='*60}")
        logger.info(f"  {uni_name} ({uni_id})")
        logger.info(f"  Algorand: {algo_address}")
        logger.info(f"  Ethereum: {eth_address}")

        env_lines.extend([
            f"# {uni_name}",
            f"{uni['algorand_mnemonic_env']}={algo_mnemonic}",
            f"{uni['ethereum_private_key_env']}={eth_private_key}",
            "",
        ])

    # Escriure .env
    env_path = NETWORK_DIR / ".env"
    env_path.write_text("\n".join(env_lines) + "\n")
    logger.info(f"\nClaus escrites a: {env_path}")

    # Resum
    print("\n" + "=" * 60)
    print("RESUM - Adreces per a la configuracio:")
    print("=" * 60)
    print(f"\nLlindar K = {config['threshold_k']}")

    print("\nAdreces Algorand (per al cens):")
    for uni, addr in zip(config["universities"], algo_addresses):
        print(f"  {uni['id']}: {addr}")

    print("\nAdreces Ethereum (per al NotaryContract):")
    for uni, addr in zip(config["universities"], eth_addresses):
        print(f"  {uni['id']}: {addr}")

    # Generar comanda de desplegament
    eth_addrs_csv = ",".join(eth_addresses)
    print(f"\nPer desplegar el NotaryContract:")
    print(f"  cd network/ethereum")
    print(f"  UNIVERSITY_ADDRESSES={eth_addrs_csv} \\")
    print(f"  THRESHOLD_K={config['threshold_k']} \\")
    print(f"  npx hardhat run scripts/deploy.js --network localhost")


if __name__ == "__main__":
    main()
