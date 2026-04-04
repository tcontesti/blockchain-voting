"""
Script: populate_census.py
Descripcio: Pobla el cens electoral amb adreces de prova.
            Util per a testing i desenvolupament amb localnet.
Estat: PLACEHOLDER
Depend: artifacts compilats, contracte desplegat

Instruccions:
  1. Desplega el contracte (deploy.py)
  2. Configura APP_ID al .env
  3. python scripts/populate_census.py
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    TODO: Implementar poblacio del cens.

    Flux previst:
    1. Connectar a localnet via AlgoKit
    2. Generar 5-10 adreces de prova
    3. Cridar generar_cens_global() amb lots de 7 adreces
    4. Verificar que totes les adreces estan al cens
    """
    logger.info("Script de poblacio del cens -- placeholder")
    logger.info("Requereix contracte desplegat amb APP_ID configurat")


if __name__ == "__main__":
    main()
