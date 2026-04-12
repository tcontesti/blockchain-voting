"""
Script: setup_universities.py
Descripcio: Genera comptes d'Algorand per a cadascuna de les tres universitats
            definides a config/universities.json (UIB, UPC, UAB) i escriu les
            credencials al fitxer network/.env.

            Aquest script es el primer pas per configurar la xarxa de nodes
            universitaris. Cada universitat necessita un compte Algorand propi
            per poder participar com a node independent al sistema de votacio.

            Flux d'us:
              1. Executar aquest script -> genera comptes i escriu network/.env
              2. Desplegar el contracte SistemaVotacion (deploy.py)
              3. Carregar les adreces generades al cens electoral (populate_census.py)
              4. Les universitats ja poden llegir l'estat de les eleccions

            El fitxer .env generat conte:
              - Configuracio de connexio a algod (localnet per defecte)
              - Camp APP_ID buit (s'omplira despres del desplegament)
              - Mnemonic d'Algorand per a cada universitat

            IMPORTANT: El fitxer .env conte claus privades (mnemonics) i NO
            s'ha de pujar mai al repositori. Esta inclosa al .gitignore.

Us:
  python network/scripts/setup_universities.py

Referencia: BLOCKCHAIN.pdf §10.1 (Configuracio del cens)
"""

import json
import logging
import sys
from pathlib import Path

from algosdk import account, mnemonic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NETWORK_DIR = Path(__file__).parent.parent
CONFIG_PATH = NETWORK_DIR / "config" / "universities.json"


def main():
    """
    Punt d'entrada principal del script.

    Llegeix la configuracio de universitats des de universities.json,
    genera un parell de claus Algorand per a cadascuna, i escriu totes
    les credencials al fitxer network/.env en format compatible amb
    python-dotenv i Docker Compose.

    Al final, mostra un resum amb les adreces generades i el llindar K
    configurat, util per a la posterior configuracio del cens electoral.
    """
    # Carregar configuracio de les universitats
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    env_lines = [
        "# =============================================",
        "# Generat automaticament per setup_universities.py",
        "# =============================================",
        "",
        "# ALGORAND",
        "ALGOD_SERVER=http://localhost",
        "ALGOD_PORT=4001",
        "ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "",
        "# SMART CONTRACT",
        "APP_ID=",
        "",
    ]

    algo_addresses = []

    for uni in config["universities"]:
        uni_id = uni["id"].upper()
        uni_name = uni["name"]

        # Generar parell de claus Algorand (clau privada + adreca publica)
        algo_private_key, algo_address = account.generate_account()
        # Convertir la clau privada a frase mnemonica de 25 paraules
        algo_mnemonic = mnemonic.from_private_key(algo_private_key)

        algo_addresses.append(algo_address)

        logger.info(f"\n{'='*60}")
        logger.info(f"  {uni_name} ({uni_id})")
        logger.info(f"  Algorand: {algo_address}")

        env_lines.extend([
            f"# {uni_name}",
            f"{uni['algorand_mnemonic_env']}={algo_mnemonic}",
            "",
        ])

    # Escriure el fitxer .env amb totes les credencials
    env_path = NETWORK_DIR / ".env"
    env_path.write_text("\n".join(env_lines) + "\n")
    logger.info(f"\nClaus escrites a: {env_path}")

    # Mostrar resum de les adreces generades
    print("\n" + "=" * 60)
    print("RESUM - Adreces per a la configuracio:")
    print("=" * 60)
    print(f"\nLlindar K = {config['threshold_k']}")

    print("\nAdreces Algorand (per al cens):")
    for uni, addr in zip(config["universities"], algo_addresses):
        print(f"  {uni['id']}: {addr}")


if __name__ == "__main__":
    main()
