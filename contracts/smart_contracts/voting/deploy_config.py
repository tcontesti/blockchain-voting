"""
Modul: deploy_config.py
Descripcio: Configuracio de desplegament del Smart Contract de votacio.
            Desplega el contracte SistemaVotacio a la xarxa configurada
            (localnet per defecte) i opcionalment pobla el cens inicial.
Estat: PLACEHOLDER
Depend: contract.py, artifacts generats per AlgoKit

TODO: Actualitzar quan es generin els artifacts compilats.
      El client tipat (SistemaVotacioFactory) es genera automaticament
      amb `algokit project run build`.
"""

import logging

logger = logging.getLogger(__name__)


def deploy() -> None:
    """
    Desplega el Smart Contract SistemaVotacio.

    Per executar:
      cd contracts/
      algokit project run build
      algokit project deploy localnet
    """
    # TODO: Substituir per SistemaVotacioFactory quan es compili
    # from smart_contracts.artifacts.voting.voting_client import (
    #     SistemaVotacioFactory,
    # )
    #
    # algorand = algokit_utils.AlgorandClient.from_environment()
    # deployer = algorand.account.from_environment("DEPLOYER")
    #
    # factory = algorand.client.get_typed_app_factory(
    #     SistemaVotacioFactory, default_sender=deployer.address,
    # )
    #
    # app_client, result = factory.deploy(
    #     on_update=algokit_utils.OnUpdate.AppendApp,
    #     on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
    # )
    #
    # if result.operation_performed in [
    #     algokit_utils.OperationPerformed.Create,
    #     algokit_utils.OperationPerformed.Replace,
    # ]:
    #     # Finançar el contracte per cobrir Minimum Balance Requirement
    #     algorand.send.payment(
    #         algokit_utils.PaymentParams(
    #             amount=algokit_utils.AlgoAmount(algo=1),
    #             sender=deployer.address,
    #             receiver=app_client.app_address,
    #         )
    #     )
    #
    # logger.info(
    #     f"Contracte desplegat: {app_client.app_name} (ID: {app_client.app_id})"
    # )

    logger.warning("deploy_config.py: Placeholder. " "Compila primer amb 'algokit project run build'.")
