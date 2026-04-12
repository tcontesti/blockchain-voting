"""
Script: deploy.py
Descripcio: Desplegament del Smart Contract SistemaVotacion a localnet.
            Usa AlgoKit per compilar, desplegar i finanqar el contracte.
Depend: artifacts compilats (algokit project run build)

Instruccions:
  1. cd contracts/
  2. algokit localnet start
  3. algokit project run build
  4. python scripts/deploy.py
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def deploy() -> int | None:
    """
    Desplega el contracte SistemaVotacion a localnet.

    Returns:
        L'APP_ID del contracte desplegat, o None si falla.
    """
    try:
        import algokit_utils
    except ImportError:
        logger.error("algokit-utils no instal·lat. Executa: poetry install")
        return None

    try:
        from smart_contracts.artifacts.voting.voting_client import (
            SistemaVotacionFactory,
        )
    except ImportError:
        logger.error(
            "Client tipat no trobat. Compila primer amb:\n"
            "  algokit project run build"
        )
        return None

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer = algorand.account.from_environment("DEPLOYER")

    logger.info(f"Deployer: {deployer.address}")

    factory = algorand.client.get_typed_app_factory(
        SistemaVotacionFactory,
        default_sender=deployer.address,
    )

    app_client, result = factory.deploy(
        on_update=algokit_utils.OnUpdate.AppendApp,
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
    )

    if result.operation_performed in [
        algokit_utils.OperationPerformed.Create,
        algokit_utils.OperationPerformed.Replace,
    ]:
        # Finanqar el contracte per cobrir Minimum Balance Requirement
        algorand.send.payment(
            algokit_utils.PaymentParams(
                amount=algokit_utils.AlgoAmount(algo=1),
                sender=deployer.address,
                receiver=app_client.app_address,
            )
        )
        logger.info("Contracte finanqat amb 1 ALGO per MBR")

    logger.info(
        f"Contracte desplegat: {app_client.app_name} "
        f"(APP_ID: {app_client.app_id})"
    )

    # Escriure APP_ID al fitxer .env si existeix
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        lines = env_path.read_text().splitlines()
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("APP_ID="):
                lines[i] = f"APP_ID={app_client.app_id}"
                updated = True
                break
        if not updated:
            lines.append(f"APP_ID={app_client.app_id}")
        env_path.write_text("\n".join(lines) + "\n")
        logger.info(f"APP_ID={app_client.app_id} escrit a {env_path}")

    return app_client.app_id


def main() -> None:
    app_id = deploy()
    if app_id is None:
        sys.exit(1)
    print(f"APP_ID={app_id}")


if __name__ == "__main__":
    main()
