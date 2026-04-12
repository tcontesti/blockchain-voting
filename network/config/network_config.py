"""
Modul: network_config.py
Descripcio: Carrega la configuracio de la xarxa d'universitats
            des de universities.json i resol els secrets des de
            variables d'entorn.
Referencia: BLOCKCHAIN.pdf §3.2.2, §10.1
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class UniversityNode:
    """Representa un node institucional (universitat)."""
    id: str
    name: str
    algorand_mnemonic: str
    ethereum_private_key: str

    @property
    def ethereum_address(self) -> str:
        """Deriva l'adreca Ethereum des de la clau privada."""
        from web3 import Account
        return Account.from_key(self.ethereum_private_key).address

    @property
    def algorand_address(self) -> str:
        """Deriva l'adreca Algorand des del mnemonic."""
        from algosdk import mnemonic
        return mnemonic.to_public_key(self.algorand_mnemonic)

    @property
    def algorand_private_key(self) -> str:
        """Deriva la clau privada Algorand des del mnemonic."""
        from algosdk import mnemonic
        return mnemonic.to_private_key(self.algorand_mnemonic)


CONFIG_DIR = Path(__file__).parent


def load_config() -> dict:
    """Carrega el fitxer universities.json."""
    config_path = CONFIG_DIR / "universities.json"
    with open(config_path) as f:
        return json.load(f)


def load_universities() -> tuple[list[UniversityNode], int]:
    """
    Carrega les universitats i resol els secrets des de les variables d'entorn.

    Returns:
        (llista de UniversityNode, llindar K)
    """
    config = load_config()
    threshold_k = config["threshold_k"]
    nodes = []

    for uni in config["universities"]:
        algo_mnemonic = os.environ.get(uni["algorand_mnemonic_env"], "")
        eth_private_key = os.environ.get(uni["ethereum_private_key_env"], "")

        nodes.append(UniversityNode(
            id=uni["id"],
            name=uni["name"],
            algorand_mnemonic=algo_mnemonic,
            ethereum_private_key=eth_private_key,
        ))

    return nodes, threshold_k


def get_algod_config() -> dict:
    """Retorna la configuracio de connexio a algod des de variables d'entorn."""
    return {
        "server": os.environ.get("ALGOD_SERVER", "http://localhost"),
        "port": int(os.environ.get("ALGOD_PORT", "4001")),
        "token": os.environ.get(
            "ALGOD_TOKEN",
            "a" * 64,
        ),
    }


def get_ethereum_config() -> dict:
    """Retorna la configuracio de connexio a Ethereum des de variables d'entorn."""
    return {
        "rpc_url": os.environ.get("ETHEREUM_RPC_URL", "http://localhost:8545"),
        "notary_address": os.environ.get("NOTARY_CONTRACT_ADDRESS", ""),
    }
