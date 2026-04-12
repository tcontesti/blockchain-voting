"""
Modul: ethereum_submitter.py
Descripcio: Envia el hash de l'estat d'una eleccio al contracte
            NotaryContract d'Ethereum i consulta l'estat de consens.
Referencia: BLOCKCHAIN.pdf §7.3.3, §8.3.2
"""

import logging

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

logger = logging.getLogger(__name__)

# ABI minim del NotaryContract (nomes les funcions necessaries)
NOTARY_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "electionId", "type": "string"},
            {"internalType": "bytes32", "name": "hash", "type": "bytes32"},
        ],
        "name": "submitHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "string", "name": "electionId", "type": "string"},
        ],
        "name": "getElectionStatus",
        "outputs": [
            {"internalType": "bool", "name": "finalized", "type": "bool"},
            {"internalType": "bytes32", "name": "officialHash", "type": "bytes32"},
            {"internalType": "uint256", "name": "submissions", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "string", "name": "electionId", "type": "string"},
            {"internalType": "address", "name": "university", "type": "address"},
        ],
        "name": "getSubmission",
        "outputs": [
            {"internalType": "bytes32", "name": "", "type": "bytes32"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "string", "name": "electionId", "type": "string"},
            {"internalType": "address", "name": "university", "type": "address"},
        ],
        "name": "hasSubmitted",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


class EthereumSubmitter:
    """Envia hashes al NotaryContract i consulta l'estat de consens."""

    def __init__(self, rpc_url: str, contract_address: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        # Suport per a xarxes PoA (Sepolia)
        try:
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        except Exception:
            pass

        self.account = self.w3.eth.account.from_key(private_key)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=NOTARY_ABI,
        )

    def submit_hash(self, election_name: str, election_hash: bytes) -> str:
        """
        Envia el hash d'una eleccio al NotaryContract.

        Args:
            election_name: Identificador de l'eleccio
            election_hash: Hash SHA-256 de 32 bytes

        Returns:
            Hash de la transaccio d'Ethereum
        """
        nonce = self.w3.eth.get_transaction_count(self.account.address)

        tx = self.contract.functions.submitHash(
            election_name,
            election_hash,
        ).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "gas": 200_000,
            "gasPrice": self.w3.eth.gas_price,
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        logger.info(
            f"Hash enviat per '{election_name}' | "
            f"tx: {tx_hash.hex()} | "
            f"status: {'OK' if receipt['status'] == 1 else 'FAIL'}"
        )

        return tx_hash.hex()

    def check_consensus(self, election_name: str) -> tuple[bool, bytes, int]:
        """
        Consulta l'estat de consens d'una eleccio.

        Returns:
            (finalitzat, hash_oficial, nombre_enviaments)
        """
        finalized, official_hash, submissions = (
            self.contract.functions.getElectionStatus(election_name).call()
        )
        return finalized, official_hash, submissions

    def has_already_submitted(self, election_name: str) -> bool:
        """Comprova si aquest node ja ha enviat hash per l'eleccio."""
        return self.contract.functions.hasSubmitted(
            election_name, self.account.address
        ).call()
