"""
Modul: conftest.py
Descripcio: Fixtures compartides per als tests del Smart Contract.
            Configura el client AlgoKit, comptes de prova i desplegament
            del contracte per a cada test.
Estat: PLACEHOLDER
Depend: artifacts compilats (algokit project run build)

TODO: Activar quan els artifacts estiguin generats.
      Requereix:
      1. algokit localnet start
      2. algokit project run build (genera el client tipat)
      3. pytest tests/
"""

import pytest


@pytest.fixture(scope="session")
def algorand_client():
    """
    Client AlgoKit connectat a localnet.

    TODO: Descomentar quan algokit-utils estigui instal·lat.
    """
    # import algokit_utils
    # return algokit_utils.AlgorandClient.from_environment()
    pytest.skip("Requereix localnet activa i artifacts compilats")


@pytest.fixture(scope="session")
def deployer(algorand_client):
    """Compte deployer de localnet."""
    # return algorand_client.account.from_environment("DEPLOYER")
    pytest.skip("Requereix localnet activa")


@pytest.fixture
def app_client(algorand_client, deployer):
    """
    Client del contracte SistemaVotacio desplegat.

    TODO: Usar SistemaVotacioFactory del client generat.
    """
    # from smart_contracts.artifacts.voting.voting_client import (
    #     SistemaVotacioFactory,
    # )
    # factory = algorand_client.client.get_typed_app_factory(
    #     SistemaVotacioFactory, default_sender=deployer.address,
    # )
    # client, _ = factory.deploy()
    # return client
    pytest.skip("Requereix artifacts compilats")
