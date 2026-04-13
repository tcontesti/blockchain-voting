"""

************************************
Implementat utilitzant eines d'Inteligència Artificial juntament amb el meu
input (@dylancanning).
Concretament Opus 4.6 d'Anthropic.
************************************

Script: add_university.py
Descripcio: Afegeix dinamicament una nova universitat a la xarxa de nodes
            mentre el sistema esta en funcionament.

            Accions que executa:
              1. Genera un parell de claus Algorand (mnemonic de 25 paraules)
              2. Genera un parell de claus Ethereum (ECDSA)
              3. Afegeix la nova universitat a universities.json
              4. Recalcula el llindar K = ceil(2/3 * N)
              5. Afegeix les credencials al fitxer .env
              6. (Opcional) Registra l'adreca al cens global del contracte
                 Algorand via cargar_censo_global()

            Prerequisits per al registre al contracte (--register):
              - algokit localnet start
              - Contracte desplegat amb APP_ID configurat al .env
              - DEPLOYER_MNEMONIC configurat al .env

Us:
  # Nomes generar claus i actualitzar configuracio:
  cd contracts/
  poetry run python ../network/scripts/add_university.py \\
    --id uv --name "Universitat de Valencia"

  # Generar + registrar al cens del contracte Algorand:
  poetry run python ../network/scripts/add_university.py \\
    --id uv --name "Universitat de Valencia" --register

Referencia: BLOCKCHAIN.pdf §3.2.2 (Nodes institucionals), DEPLOYMENT_ARCHITECTURE.md §3
"""

import argparse
import json
import logging
import math
import os
import re
import secrets
import sys
from pathlib import Path

from algosdk import account, mnemonic
from eth_account import Account

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

NETWORK_DIR = Path(__file__).parent.parent
ROOT_DIR = NETWORK_DIR.parent
CONTRACTS_DIR = ROOT_DIR / "contracts"
CONFIG_PATH = NETWORK_DIR / "config" / "universities.json"
ENV_PATH = NETWORK_DIR / ".env"


def validate_id(uni_id: str) -> str:
    """Valida que l'ID sigui alfanumeric en minuscules, sense espais."""
    uni_id = uni_id.lower().strip()
    if not re.match(r"^[a-z][a-z0-9_]{1,15}$", uni_id):
        print(f"ERROR: ID '{uni_id}' invalid. Usa 2-16 caracters alfanumerics en minuscules (ex: 'uv', 'ub', 'upf')")
        sys.exit(1)
    return uni_id


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(config: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")


def check_duplicate(config: dict, uni_id: str):
    """Comprova que la universitat no existeixi ja a la configuracio."""
    existing_ids = [u["id"] for u in config["universities"]]
    if uni_id in existing_ids:
        print(f"ERROR: La universitat '{uni_id}' ja existeix a universities.json")
        print(f"  Universitats actuals: {', '.join(existing_ids)}")
        sys.exit(1)


def generate_keys() -> tuple[str, str, str, str]:
    """
    Genera parells de claus Algorand i Ethereum.

    Returns:
        (algo_mnemonic, algo_address, eth_private_key, eth_address)
    """
    algo_private_key, algo_address = account.generate_account()
    algo_mn = mnemonic.from_private_key(algo_private_key)

    eth_private_key = "0x" + secrets.token_hex(32)
    eth_address = Account.from_key(eth_private_key).address

    return algo_mn, algo_address, eth_private_key, eth_address


def update_json(config: dict, uni_id: str, uni_name: str) -> dict:
    """Afegeix la universitat al JSON i recalcula threshold_k."""
    algo_env = f"{uni_id.upper()}_ALGO_MNEMONIC"
    eth_env = f"{uni_id.upper()}_ETH_PRIVATE_KEY"

    config["universities"].append({
        "id": uni_id,
        "name": uni_name,
        "algorand_mnemonic_env": algo_env,
        "ethereum_private_key_env": eth_env,
    })

    # Recalcular K = ceil(2/3 * N)
    n = len(config["universities"])
    config["threshold_k"] = math.ceil(2 * n / 3)

    return config


def append_to_env(uni_id: str, uni_name: str, algo_mn: str, eth_private_key: str):
    """Afegeix les noves credencials al final del fitxer .env."""
    algo_env = f"{uni_id.upper()}_ALGO_MNEMONIC"
    eth_env = f"{uni_id.upper()}_ETH_PRIVATE_KEY"

    new_lines = [
        "",
        f"# {uni_name}",
        f"{algo_env}={algo_mn}",
        f"{eth_env}={eth_private_key}",
        "",
    ]

    if ENV_PATH.exists():
        content = ENV_PATH.read_text()
        if not content.endswith("\n"):
            content += "\n"
        content += "\n".join(new_lines)
        ENV_PATH.write_text(content)
    else:
        print(f"  AVIS: {ENV_PATH} no existeix. Executa primer setup_universities.py")
        sys.exit(1)


def register_in_contract(algo_address: str):
    """
    Registra l'adreca Algorand de la nova universitat al cens global
    del contracte SistemaVotacion. Requereix localnet + contracte desplegat.
    """
    sys.path.insert(0, str(CONTRACTS_DIR))
    sys.path.insert(0, str(NETWORK_DIR))

    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
    load_dotenv(ENV_PATH, override=True)

    try:
        import algokit_utils
        from algosdk import mnemonic as algo_mnemonic_module
        from algosdk.atomic_transaction_composer import AccountTransactionSigner
        from algosdk.v2client.algod import AlgodClient
        from algosdk import account as algo_account, transaction
        from smart_contracts.artifacts.voting.voting_client import (
            SistemaVotacionClient,
            CargarCensoGlobalArgs,
        )
    except ImportError as e:
        print(f"\n  ERROR: {e}")
        print("  Executa des de l'entorn Poetry del contracte:")
        print("    cd contracts/")
        print("    poetry run python ../network/scripts/add_university.py ...")
        sys.exit(1)

    app_id = int(os.environ.get("APP_ID", "0"))
    if app_id == 0:
        print("  ERROR: APP_ID no configurat al .env")
        sys.exit(1)

    deployer_mn = os.environ.get("DEPLOYER_MNEMONIC", "")
    if not deployer_mn:
        print("  ERROR: DEPLOYER_MNEMONIC no configurat al .env")
        sys.exit(1)

    deployer_key = algo_mnemonic_module.to_private_key(deployer_mn)
    deployer_addr = algo_account.address_from_private_key(deployer_key)

    algod_token = os.environ.get("ALGOD_TOKEN", "a" * 64)
    algod_url = f"{os.environ.get('ALGOD_SERVER', 'http://localhost')}:{os.environ.get('ALGOD_PORT', '4001')}"
    algod_client = AlgodClient(algod_token, algod_url)

    # Finançar el deployer si cal (per cobrir MBR de la nova box)
    algorand = algokit_utils.AlgorandClient.from_environment()
    try:
        dispenser = algorand.account.localnet_dispenser()
        saldo = algod_client.account_info(deployer_addr).get("amount", 0)
        if saldo < 5_000_000:
            sp = algod_client.suggested_params()
            txn = transaction.PaymentTxn(
                sender=dispenser.address, sp=sp,
                receiver=deployer_addr, amt=5_000_000,
            )
            stxn = txn.sign(dispenser.private_key)
            algod_client.send_transaction(stxn)
            transaction.wait_for_confirmation(algod_client, stxn.get_txid(), 4)
    except Exception:
        pass

    # Registrar al cens global
    arc32_path = CONTRACTS_DIR / "smart_contracts" / "artifacts" / "voting" / "SistemaVotacion.arc32.json"
    signer = AccountTransactionSigner(deployer_key)
    algorand.set_signer(sender=deployer_addr, signer=signer)

    app_client = algokit_utils.AppClient(
        algokit_utils.AppClientParams(
            app_id=app_id,
            algorand=algorand,
            default_sender=deployer_addr,
            default_signer=signer,
            app_spec=arc32_path.read_text(),
        )
    )
    typed = SistemaVotacionClient(app_client)

    typed.send.cargar_censo_global(
        args=CargarCensoGlobalArgs(direcciones=[algo_address])
    )

    logger.info(f"  Adreca registrada al cens global del contracte (APP_ID={app_id})")


def main():
    parser = argparse.ArgumentParser(
        description="Afegeix una nova universitat a la xarxa de votacio",
    )
    parser.add_argument("--id", required=True, help="Identificador curt (ex: 'uv', 'ub')")
    parser.add_argument("--name", required=True, help="Nom complet (ex: 'Universitat de Valencia')")
    parser.add_argument(
        "--register", action="store_true",
        help="Registrar l'adreca al cens del contracte Algorand (requereix localnet + APP_ID)",
    )
    args = parser.parse_args()

    uni_id = validate_id(args.id)
    uni_name = args.name.strip()

    # 1. Carregar i validar
    config = load_config()
    check_duplicate(config, uni_id)

    old_n = len(config["universities"])
    old_k = config["threshold_k"]

    logger.info(f"\n{'='*60}")
    logger.info(f"  AFEGIR UNIVERSITAT: {uni_name} ({uni_id.upper()})")
    logger.info(f"{'='*60}")

    # 2. Generar claus
    algo_mn, algo_address, eth_private_key, eth_address = generate_keys()

    logger.info(f"\n  Claus generades:")
    logger.info(f"    Algorand: {algo_address}")
    logger.info(f"    Ethereum: {eth_address}")

    # 3. Actualitzar universities.json
    config = update_json(config, uni_id, uni_name)
    save_config(config)

    new_n = len(config["universities"])
    new_k = config["threshold_k"]

    logger.info(f"\n  universities.json actualitzat:")
    logger.info(f"    Universitats: {old_n} → {new_n}")
    logger.info(f"    Llindar K:    {old_k} → {new_k}")

    # 4. Afegir credencials al .env
    append_to_env(uni_id, uni_name, algo_mn, eth_private_key)
    logger.info(f"  Credencials afegides a {ENV_PATH}")

    # 5. Registrar al contracte (opcional)
    if args.register:
        logger.info(f"\n  Registrant al cens del contracte Algorand...")
        register_in_contract(algo_address)
    else:
        logger.info(f"\n  Per registrar al contracte, torna a executar amb --register")
        logger.info(f"  o crida manualment cargar_censo_global(['{algo_address}'])")

    # Resum final
    logger.info(f"\n{'='*60}")
    logger.info(f"  RESUM")
    logger.info(f"{'='*60}")
    logger.info(f"  Xarxa actual: N={new_n} universitats, K={new_k} per consens")
    logger.info(f"  Nodes:")
    for uni in config["universities"]:
        marker = " ← NOU" if uni["id"] == uni_id else ""
        logger.info(f"    {uni['id'].upper()}: {uni['name']}{marker}")


if __name__ == "__main__":
    main()
