"""
Modul: ethereum_submitter.py
Descripcio: Envia el hash SHA-256 d'una eleccio al contracte NotaryContract
            desplegat a Ethereum (Sepolia Testnet o xarxa local Hardhat).

            Cada node universitari usa aquest modul per signar i enviar una
            transaccio Ethereum que registra el hash dels resultats electorals.
            El contracte NotaryContract aplica la logica K-de-N: nomes ancora
            el resultat quan K universitats independents envien el mateix hash.

            El modul firma la transaccio amb ECDSA usant la clau privada
            Ethereum de la universitat (carregada des de variables d'entorn).

Referencia: BLOCKCHAIN.pdf §7.3.3 (Gestor d'ancoratge), §9.7 (Ancoratge K-de-N)
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ABI minim del NotaryContract: nomes el metode submitHash
NOTARY_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "electionId", "type": "string"},
            {"internalType": "bytes32", "name": "resultHash", "type": "bytes32"},
        ],
        "name": "submitHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "string", "name": "electionId", "type": "string"},
            {"indexed": False, "internalType": "bytes32", "name": "resultHash", "type": "bytes32"},
            {"indexed": False, "internalType": "address", "name": "submitter", "type": "address"},
        ],
        "name": "HashSubmitted",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "string", "name": "electionId", "type": "string"},
            {"indexed": False, "internalType": "bytes32", "name": "resultHash", "type": "bytes32"},
            {"indexed": False, "internalType": "uint256", "name": "confirmations", "type": "uint256"},
        ],
        "name": "ResultAnchored",
        "type": "event",
    },
]


@dataclass
class SubmissionResult:
    """
    Resultat d'enviar un hash al contracte NotaryContract.

    Atributs:
        success:    True si la transaccio s'ha enviat i confirmat.
        tx_hash:    Hash de la transaccio Ethereum (hex amb prefix 0x).
        anchored:   True si el contracte ha emès l'event ResultAnchored
                    (el llindar K s'ha assolit amb aquesta submissio).
        error:      Missatge d'error si success es False.
    """
    success: bool
    tx_hash: str = ""
    anchored: bool = False
    error: str = ""


class EthereumSubmitter:
    """
    Client per enviar hashes d'eleccions al contracte NotaryContract d'Ethereum.

    Cada universitat instancia un EthereumSubmitter amb la seva clau privada
    i l'adreca del contracte. Quan una eleccio finalitza, envia el hash
    SHA-256 signat amb ECDSA al contracte, que valida que msg.sender
    pertany a la whitelist d'universitats autoritzades.

    Atributs:
        w3:               Client Web3 connectat al node Ethereum.
        contract:         Instancia del contracte NotaryContract.
        account:          Compte Ethereum de la universitat (derivat de la clau privada).
        private_key:      Clau privada Ethereum per signar transaccions.
    """

    def __init__(self, rpc_url: str, contract_address: str, private_key: str):
        """
        Inicialitza el submitter connectant-se al node Ethereum.

        Args:
            rpc_url:          URL JSON-RPC del node Ethereum
                              (ex: "http://localhost:8545" per Hardhat,
                               o URL de Sepolia per a testnet).
            contract_address: Adreca del NotaryContract desplegat (0x...).
            private_key:      Clau privada Ethereum de la universitat (hex).

        Raises:
            ImportError: Si web3 no esta instal·lat (pip install web3).
        """
        from web3 import Web3

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=NOTARY_ABI,
        )
        self.private_key = private_key
        self.account = self.w3.eth.account.from_key(private_key)

    def submit_hash(self, election_id: str, result_hash: bytes) -> SubmissionResult:
        """
        Envia el hash d'una eleccio al contracte NotaryContract.

        Construeix, signa i envia una transaccio que crida submitHash()
        al contracte. Espera la confirmacio i comprova si l'event
        ResultAnchored ha estat emès (indicant que el llindar K s'ha assolit).

        Args:
            election_id: Nom de l'eleccio (ex: "Rector2026").
            result_hash: Hash SHA-256 de 32 bytes dels resultats.

        Returns:
            SubmissionResult amb l'estat de la transaccio.
        """
        try:
            # Construir la transaccio
            tx = self.contract.functions.submitHash(
                election_id,
                result_hash,
            ).build_transaction({
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 200_000,
                "gasPrice": self.w3.eth.gas_price,
            })

            # Signar amb ECDSA
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)

            # Enviar i esperar confirmacio
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if receipt["status"] != 1:
                return SubmissionResult(
                    success=False,
                    tx_hash=tx_hash.hex(),
                    error="Transaccio revertida pel contracte",
                )

            # Comprovar si s'ha emès l'event ResultAnchored
            anchored = False
            anchored_logs = self.contract.events.ResultAnchored().process_receipt(receipt)
            if anchored_logs:
                anchored = True
                logger.info(
                    f"ResultAnchored emès per '{election_id}' amb "
                    f"{anchored_logs[0]['args']['confirmations']} confirmacions"
                )

            return SubmissionResult(
                success=True,
                tx_hash=tx_hash.hex(),
                anchored=anchored,
            )

        except Exception as e:
            logger.error(f"Error enviant hash per '{election_id}': {e}")
            return SubmissionResult(success=False, error=str(e))
