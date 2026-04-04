"""
Script: deploy.py
Descripcio: Script de desplegament del Smart Contract de votacio.
            Usa AlgoKit per desplegar a localnet o testnet.
Estat: PLACEHOLDER
Depend: artifacts compilats (algokit project run build)

Instruccions:
  1. cd contracts/
  2. algokit localnet start
  3. algokit project run build
  4. python scripts/deploy.py
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    TODO: Implementar desplegament complet.
    Requereix els artifacts compilats del contracte.
    """
    logger.info("Script de desplegament -- placeholder")
    logger.info("Usa 'algokit project run build' per compilar")
    logger.info("Usa 'algokit project deploy localnet' per desplegar")


if __name__ == "__main__":
    main()
