"""
Modul: network_config.py
Descripcio: Carrega la configuracio de la xarxa d'universitats des del
            fitxer universities.json i resol les credencials criptografiques
            des de les variables d'entorn del sistema.

            Cada universitat te associat un mnemonic d'Algorand que permet
            derivar tant l'adreca publica (per al cens electoral) com la
            clau privada (per signar transaccions). Aquestes credencials
            NO s'emmagatzemen al JSON per seguretat; nomes s'hi guarda el
            nom de la variable d'entorn on es troben (ex: "UIB_ALGO_MNEMONIC").

            Flux tipic d'us:
              1. setup_universities.py genera els comptes i escriu network/.env
              2. Es carrega el .env (manualment o amb python-dotenv)
              3. load_universities() llegeix el JSON i resol els mnemonics
                 des de les variables d'entorn

Referencia: BLOCKCHAIN.pdf §3.2.2 (Nodes institucionals), §10.1 (Configuracio)
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class UniversityNode:
    """
    Representa un node institucional dins la xarxa de votacio.

    Cada universitat participant opera com a node independent que:
      - Te el seu propi compte Algorand (derivat del mnemonic)
      - Te el seu propi compte Ethereum (clau privada ECDSA)
      - Llegeix l'estat electoral de forma autonoma
      - Calcula el hash SHA-256 dels resultats independentment
      - Envia el hash signat al contracte NotaryContract d'Ethereum

    Atributs:
        id:                   Identificador curt de la universitat (ex: "uib").
        name:                 Nom complet (ex: "Universitat de les Illes Balears").
        algorand_mnemonic:    Frase mnemonica de 25 paraules per al compte Algorand.
        ethereum_private_key: Clau privada Ethereum (hex) per signar transaccions
                              d'ancoratge. Buida si no s'ha configurat.
    """
    id: str
    name: str
    algorand_mnemonic: str
    ethereum_private_key: str = ""

    @property
    def algorand_address(self) -> str:
        """
        Deriva l'adreca publica Algorand des del mnemonic.

        Returns:
            Adreca Algorand de 58 caracters (base32 amb checksum).

        Raises:
            ValueError: Si el mnemonic es buit o invalid.
        """
        from algosdk import mnemonic
        return mnemonic.to_public_key(self.algorand_mnemonic)

    @property
    def algorand_private_key(self) -> str:
        """
        Deriva la clau privada Algorand des del mnemonic.

        Returns:
            Clau privada en format base64 compatible amb algosdk.

        Raises:
            ValueError: Si el mnemonic es buit o invalid.
        """
        from algosdk import mnemonic
        return mnemonic.to_private_key(self.algorand_mnemonic)

    @property
    def ethereum_address(self) -> str:
        """
        Deriva l'adreca publica Ethereum des de la clau privada.

        Returns:
            Adreca Ethereum amb prefix 0x (42 caracters).

        Raises:
            ValueError: Si la clau privada es buida.
        """
        from eth_account import Account
        return Account.from_key(self.ethereum_private_key).address


CONFIG_DIR = Path(__file__).parent


def load_config() -> dict:
    """
    Carrega el fitxer universities.json amb la definicio de la xarxa.

    El JSON conte la llista d'universitats (id, nom, referencies a variables
    d'entorn) i el llindar de consens K (nombre minim d'universitats que han
    de coincidir per validar un resultat).

    Returns:
        Diccionari amb les claus "universities" (llista) i "threshold_k" (enter).
    """
    config_path = CONFIG_DIR / "universities.json"
    with open(config_path) as f:
        return json.load(f)


def load_universities() -> tuple[list[UniversityNode], int]:
    """
    Carrega les universitats i resol les credencials des de variables d'entorn.

    Per a cada universitat definida al JSON, llegeix el mnemonic d'Algorand
    des de la variable d'entorn indicada (ex: "UIB_ALGO_MNEMONIC").
    Si la variable no esta definida, el mnemonic queda com a cadena buida
    i les propietats algorand_address/algorand_private_key llancaran error.

    Returns:
        Tupla amb:
          - Llista d'objectes UniversityNode (un per universitat)
          - Llindar K (enter): nombre minim de nodes que han de coincidir
            per validar un ancoratge (per defecte 2 de 3)
    """
    config = load_config()
    threshold_k = config["threshold_k"]
    nodes = []

    for uni in config["universities"]:
        algo_mnemonic = os.environ.get(uni["algorand_mnemonic_env"], "")
        eth_private_key = os.environ.get(uni.get("ethereum_private_key_env", ""), "")

        nodes.append(UniversityNode(
            id=uni["id"],
            name=uni["name"],
            algorand_mnemonic=algo_mnemonic,
            ethereum_private_key=eth_private_key,
        ))

    return nodes, threshold_k


def get_algod_config() -> dict:
    """
    Retorna la configuracio de connexio al node algod des de variables d'entorn.

    Llegeix les variables ALGOD_SERVER, ALGOD_PORT i ALGOD_TOKEN per configurar
    la connexio al node Algorand. Si no estan definides, usa els valors per
    defecte corresponents a AlgoKit localnet (desenvolupament local).

    Returns:
        Diccionari amb les claus:
          - "server": URL base del node (defecte: "http://localhost")
          - "port": Port del node (defecte: 4001)
          - "token": Token d'autenticacio (defecte: 64 'a' per a localnet)
    """
    return {
        "server": os.environ.get("ALGOD_SERVER", "http://localhost"),
        "port": int(os.environ.get("ALGOD_PORT", "4001")),
        "token": os.environ.get(
            "ALGOD_TOKEN",
            "a" * 64,
        ),
    }
