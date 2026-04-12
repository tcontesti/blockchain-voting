"""
Script: populate_census.py
Descripcio: Pobla el cens electoral amb adreces de prova.
            Util per a testing i desenvolupament amb localnet.
Depend: artifacts compilats, contracte desplegat

Instruccions:
  1. Desplega el contracte (deploy.py)
  2. Configura APP_ID al .env
  3. python scripts/populate_census.py [--extra-voters N]
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def populate_census(app_id: int, addresses: list[str]) -> None:
    """
    Carrega adreces al cens global del contracte.

    El contracte limita a 7 adreces per transaccio (cargar_censo_global),
    aixi que enviem en lots.
    """
    try:
        import algokit_utils
        from algosdk.v2client.algod import AlgodClient
    except ImportError:
        logger.error("Dependecies no instal·lades. Executa: poetry install")
        sys.exit(1)

    try:
        from smart_contracts.artifacts.voting.voting_client import (
            SistemaVotacionFactory,
        )
    except ImportError:
        logger.error(
            "Client tipat no trobat. Compila primer amb:\n"
            "  algokit project run build"
        )
        sys.exit(1)

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer = algorand.account.from_environment("DEPLOYER")

    factory = algorand.client.get_typed_app_factory(
        SistemaVotacionFactory,
        default_sender=deployer.address,
    )
    app_client = factory.get_app_client_by_id(app_id)

    BATCH_SIZE = 7
    total = len(addresses)

    for i in range(0, total, BATCH_SIZE):
        batch = addresses[i:i + BATCH_SIZE]
        logger.info(f"Carregant lot {i // BATCH_SIZE + 1}: {len(batch)} adreces")

        app_client.send.cargar_censo_global(
            args={"direcciones": batch}
        )

    logger.info(f"Cens carregat: {total} adreces en {(total + BATCH_SIZE - 1) // BATCH_SIZE} lots")


def generate_test_accounts(algorand_client, count: int) -> list[tuple[str, str]]:
    """
    Genera comptes de prova i els finanqa des del dispenser de localnet.

    Returns:
        Llista de (adreca, clau_privada)
    """
    from algosdk import account

    accounts = []
    for i in range(count):
        private_key, address = account.generate_account()
        # Finanqar amb 10 ALGO des del dispenser
        try:
            import algokit_utils
            algorand_client.send.payment(
                algokit_utils.PaymentParams(
                    amount=algokit_utils.AlgoAmount(algo=10),
                    sender=algorand_client.account.from_environment("DEPLOYER").address,
                    receiver=address,
                )
            )
        except Exception as e:
            logger.warning(f"No s'ha pogut finanqar {address}: {e}")
        accounts.append((address, private_key))
        logger.info(f"  Compte de prova {i + 1}: {address}")

    return accounts


def main() -> None:
    parser = argparse.ArgumentParser(description="Pobla el cens electoral")
    parser.add_argument("--app-id", type=int, help="APP_ID del contracte")
    parser.add_argument("--extra-voters", type=int, default=5,
                        help="Nombre de votants de prova addicionals (defecte: 5)")
    parser.add_argument("--addresses", nargs="*",
                        help="Adreces Algorand a afegir al cens")
    args = parser.parse_args()

    # Obtenir APP_ID
    app_id = args.app_id
    if not app_id:
        import os
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent.parent / ".env")
        app_id = int(os.environ.get("APP_ID", "0"))

    if not app_id:
        logger.error("APP_ID no configurat. Desplegue primer el contracte.")
        sys.exit(1)

    # Recol·lectar adreces
    addresses = list(args.addresses) if args.addresses else []

    # Generar votants de prova si cal
    if args.extra_voters > 0:
        import algokit_utils
        algorand = algokit_utils.AlgorandClient.from_environment()
        logger.info(f"Generant {args.extra_voters} comptes de prova...")
        test_accounts = generate_test_accounts(algorand, args.extra_voters)
        addresses.extend(addr for addr, _ in test_accounts)

    if not addresses:
        logger.warning("Cap adreca per carregar al cens")
        sys.exit(0)

    populate_census(app_id, addresses)
    logger.info("Poblacio del cens completada!")


if __name__ == "__main__":
    main()
