"""
Script: simulate_election.py
Descripcio: Simula un cicle electoral complet sobre el contracte SistemaVotacion
            desplegat a localnet, reflectint l'arquitectura real del sistema:

            - USUARIS: estan al cens, proposen eleccions i voten.
            - UNIVERSITATS: nodes validadors que llegeixen els resultats i
              calculen el hash SHA-256 per a l'ancoratge K-de-N a Ethereum.
              No formen part del cens de votants.

Flux:
  FASE 0 - Generar i finançar 8 comptes d'usuari
  FASE 1 - Carregar els 8 usuaris al cens global
  FASE 2 - L'usuari #1 proposa l'eleccio "Rector2026"
  FASE 3 - L'usuari #1 carrega el cens de la proposta (tots 8)
  FASE 4 - Usuaris voten la proposta fins assolir majoria
            → eleccio generada automaticament al contracte
  FASE 5 - Els 8 usuaris voten a l'eleccio
  FASE 6 - Nodes universitaris llegeixen resultats i calculen hash SHA-256
            (simula l'ancoratge que faria el NotaryContract d'Ethereum)

Us:
  cd blockchain-voting/contracts
  poetry run python ../network/scripts/simulate_election.py

Pre-requisits:
  - algokit localnet start
  - Contracte desplegat: poetry run python scripts/deploy.py
  - network/.env amb APP_ID i mnemonics de les universitats
"""

import os
import sys
from pathlib import Path

CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"
ROOT_DIR      = Path(__file__).parent.parent.parent
NETWORK_DIR   = ROOT_DIR / "network"

sys.path.insert(0, str(CONTRACTS_DIR))
sys.path.insert(0, str(NETWORK_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "network" / ".env", override=True)

try:
    import algokit_utils
    from algosdk.atomic_transaction_composer import AccountTransactionSigner
    from smart_contracts.artifacts.voting.voting_client import (
        SistemaVotacionClient,
        CargarCensoGlobalArgs,
        CargarCensoPropuestaArgs,
        CrearPropuestaArgs,
        VotarPropuestaArgs,
        VotarEleccionArgs,
    )
except ImportError as e:
    print(f"\nERROR: {e}")
    print("\nExecuta aquest script des de l'entorn Poetry del contracte:")
    print("  cd contracts/")
    print("  poetry run python ../network/scripts/simulate_election.py")
    sys.exit(1)

from algosdk import mnemonic as algo_mnemonic_module, account, transaction
from algosdk.v2client.algod import AlgodClient

from anchoring.algorand_reader import AlgorandElectionReader
from anchoring.hasher import compute_election_hash_hex

# ─────────────────────────────────────────────────────────────────────────────
# Configuracio
# ─────────────────────────────────────────────────────────────────────────────

APP_ID      = int(os.environ["APP_ID"])
ALGOD_TOKEN = os.environ.get("ALGOD_TOKEN", "a" * 64)
ALGOD_URL   = f"{os.environ.get('ALGOD_SERVER', 'http://localhost')}:{os.environ.get('ALGOD_PORT', '4001')}"

# Nodes universitaris (validadors, NO votants)
UNIVERSITY_MNEMONICS = {
    "UIB": os.environ["UIB_ALGO_MNEMONIC"],
    "UPC": os.environ["UPC_ALGO_MNEMONIC"],
    "UAB": os.environ["UAB_ALGO_MNEMONIC"],
}

import time as _time
NOM_PROPOSTA = f"Rector{int(_time.time())}"  # Nom unic per evitar conflictes entre execucions
CANDIDATS    = ["Alice", "Bob", "Carol"]
NUM_USUARIS  = 8

# Distribucio de vots a l'eleccio: Alice guanya (4), Bob segon (3), Carol tercer (1)
VOTS_ELECCIO = ["Alice", "Alice", "Alice", "Alice", "Bob", "Bob", "Bob", "Carol"]

ARC32_PATH = CONTRACTS_DIR / "smart_contracts" / "artifacts" / "voting" / "SistemaVotacion.arc32.json"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def sep(titol: str):
    print(f"\n{'='*60}\n  {titol}\n{'='*60}")


def get_account(mn: str) -> tuple[str, str]:
    private_key = algo_mnemonic_module.to_private_key(mn)
    address = account.address_from_private_key(private_key)
    return address, private_key


def algod_client() -> AlgodClient:
    return AlgodClient(ALGOD_TOKEN, ALGOD_URL)


def typed_client(private_key: str, addr: str) -> SistemaVotacionClient:
    """Retorna un client tipat per a un compte concret (usuari o admin)."""
    signer = AccountTransactionSigner(private_key)
    algorand = algokit_utils.AlgorandClient.from_environment()
    algorand.set_signer(sender=addr, signer=signer)
    app_client = algokit_utils.AppClient(
        algokit_utils.AppClientParams(
            app_id=APP_ID,
            algorand=algorand,
            default_sender=addr,
            default_signer=signer,
            app_spec=ARC32_PATH.read_text(),
        )
    )
    return SistemaVotacionClient(app_client)


def financar(disp_addr: str, disp_key: str, addr: str, client: AlgodClient,
             amt: int = 2_000_000):
    """
    Envia ALGO des del dispenser a una adreça si no te prou saldo.

    El valor per defecte es 2 ALGO per cobrir el MBR (Minimum Balance
    Requirement) de les boxes del contracte: cada box de cens o de
    proposta reserva microALGO addicionals al saldo minim del compte.
    L'usuari #1 necessita mes saldo perque crea la proposta i carrega
    el cens complet (fins a 8 boxes addicionals).
    """
    saldo = client.account_info(addr).get("amount", 0)
    if saldo >= amt - 500_000:
        return
    sp = client.suggested_params()
    txn = transaction.PaymentTxn(sender=disp_addr, sp=sp, receiver=addr, amt=amt)
    stxn = txn.sign(disp_key)
    client.send_transaction(stxn)
    transaction.wait_for_confirmation(client, stxn.get_txid(), 4)


# ─────────────────────────────────────────────────────────────────────────────
# Fases
# ─────────────────────────────────────────────────────────────────────────────

def fase0_generar_usuaris() -> list[tuple[str, str]]:
    """
    Genera 8 comptes d'usuari nous i els finança des del dispenser de localnet.

    Usa el dispenser de KMD d'AlgoKit (compte pre-finançat amb milers d'ALGO)
    en lloc del compte deployer, que pot quedar buit despres de multiples
    execucions. L'usuari #1 rep 5 ALGO perque crea la proposta i carrega el
    cens (mes boxes = mes MBR). La resta reben 2 ALGO per poder votar.

    Retorna llista de (adreca, clau_privada).
    """
    sep("FASE 0: Generar i finançar 8 usuaris")

    # Obtenim el dispenser de localnet via AlgoKit (KMD, sempre pre-finançat)
    algorand = algokit_utils.AlgorandClient.from_environment()
    try:
        dispenser = algorand.account.localnet_dispenser()
        disp_addr = dispenser.address
        disp_key   = dispenser.private_key
    except Exception:
        # Fallback: usa DEPLOYER_MNEMONIC si localnet_dispenser no esta disponible
        deployer_mn = os.environ.get("DEPLOYER_MNEMONIC", "")
        if not deployer_mn:
            print("  ERROR: DEPLOYER_MNEMONIC no configurat i localnet_dispenser no disponible")
            sys.exit(1)
        disp_addr, disp_key = get_account(deployer_mn)

    client = algod_client()
    usuaris = []

    for i in range(NUM_USUARIS):
        private_key, addr = account.generate_account()
        # L'usuari #1 crea la proposta i carrega el cens complet:
        # necessita mes saldo per cobrir el MBR de totes les boxes.
        amt = 5_000_000 if i == 0 else 2_000_000
        financar(disp_addr, disp_key, addr, client, amt=amt)
        usuaris.append((addr, private_key))
        print(f"  Usuari {i+1}: {addr[:28]}... finançat ({amt // 1_000_000} ALGO)")

    return usuaris


def fase1_carregar_cens(usuaris: list[tuple[str, str]]):
    """
    Carrega els 8 usuaris al cens global del contracte.
    Max 7 adreces per transaccio (limitacio del contracte).

    El deployer fa les crides com a administrador del contracte.
    Assegurem que te prou saldo per cobrir el MBR de les boxes del cens
    (cada adreca al cens global crea una box que incrementa el MBR minim).
    """
    sep("FASE 1: Carregar 8 usuaris al cens global")

    deployer_mn = os.environ.get("DEPLOYER_MNEMONIC", "")
    disp_addr, disp_key = get_account(deployer_mn)

    # Assegurar que el deployer te prou ALGO per als costos de MBR de les boxes
    algod = algod_client()
    algorand = algokit_utils.AlgorandClient.from_environment()
    try:
        dispenser = algorand.account.localnet_dispenser()
        financar(dispenser.address, dispenser.private_key, disp_addr, algod, amt=10_000_000)
    except Exception:
        pass  # Si no hi ha dispenser, assumim que el deployer te prou saldo

    client = typed_client(disp_key, disp_addr)
    adreces = [addr for addr, _ in usuaris]

    # Lot 1: primers 7 usuaris
    client.send.cargar_censo_global(
        args=CargarCensoGlobalArgs(direcciones=adreces[:7])
    )
    print(f"  Lot 1: {len(adreces[:7])} usuaris carregats")

    # Lot 2: l'usuari restant
    client.send.cargar_censo_global(
        args=CargarCensoGlobalArgs(direcciones=adreces[7:])
    )
    print(f"  Lot 2: {len(adreces[7:])} usuari carregat")
    print(f"  Total al cens global: {NUM_USUARIS} usuaris")


def fase2_crear_proposta(usuaris: list[tuple[str, str]]):
    """
    L'usuari #1 crea la proposta d'eleccio amb 3 candidats.
    Declara que el cens de la proposta tindra 8 membres.
    """
    sep("FASE 2: Usuari #1 proposa l'eleccio")

    addr, key = usuaris[0]
    typed_client(key, addr).send.crear_propuesta(
        args=CrearPropuestaArgs(
            nombre_propuesta=NOM_PROPOSTA,
            candidatos=CANDIDATS,
            total_censo=NUM_USUARIS,
        )
    )
    print(f"  Proposta '{NOM_PROPOSTA}' creada per l'usuari #1 ({addr[:20]}...)")
    print(f"  Candidats: {CANDIDATS}")
    print(f"  Cens declarat: {NUM_USUARIS} votants")


def fase3_carregar_cens_proposta(usuaris: list[tuple[str, str]]):
    """
    L'usuari #1 (creador) carrega els 8 usuaris al cens de la proposta.
    Max 4 adreces per transaccio.
    """
    sep("FASE 3: Usuari #1 carrega el cens de la proposta")

    addr_creador, key_creador = usuaris[0]
    client = typed_client(key_creador, addr_creador)
    adreces = [addr for addr, _ in usuaris]

    # El contracte permet max 4 adreces per crida a cargar_censo_propuesta
    lots = [adreces[i:i+4] for i in range(0, len(adreces), 4)]
    for idx, lot in enumerate(lots):
        client.send.cargar_censo_propuesta(
            args=CargarCensoPropuestaArgs(
                nombre_propuesta=NOM_PROPOSTA,
                censo_lote=lot,
            )
        )
        print(f"  Lot {idx+1}: {len(lot)} usuaris carregats")

    print(f"  Total al cens de la proposta: {NUM_USUARIS} usuaris")


def fase4_votar_proposta(usuaris: list[tuple[str, str]]):
    """
    Els usuaris voten la proposta fins assolir la majoria (ceil(50% de 8) = 5).
    Quan s'assoleix el llindar, el contracte genera l'eleccio automaticament.
    """
    sep("FASE 4: Usuaris voten la proposta (llindar: 5 de 8)")

    reader = AlgorandElectionReader(algod_client(), APP_ID)

    for i, (addr, key) in enumerate(usuaris):
        typed_client(key, addr).send.votar_propuesta(
            args=VotarPropuestaArgs(nombre_propuesta=NOM_PROPOSTA)
        )
        print(f"  Usuari #{i+1} ha votat la proposta")

        if NOM_PROPOSTA in reader.get_all_election_names():
            print(f"\n  *** ELECCIO '{NOM_PROPOSTA}' GENERADA! (llindar assolit al vot #{i+1}) ***")
            break


def fase5_votar_eleccio(usuaris: list[tuple[str, str]]):
    """
    Els 8 usuaris voten a l'eleccio, cadascun per un candidat.
    Distribucio: Alice x4, Bob x3, Carol x1.
    """
    sep("FASE 5: Els 8 usuaris voten a l'eleccio")

    for i, ((addr, key), candidat) in enumerate(zip(usuaris, VOTS_ELECCIO)):
        typed_client(key, addr).send.votar_eleccion(
            args=VotarEleccionArgs(
                nombre_eleccion=NOM_PROPOSTA,
                candidato=candidat,
            )
        )
        print(f"  Usuari #{i+1} vota per '{candidat}'")


def fase6_ancoratge_universitari():
    """
    Cada node universitari llegeix independentment els resultats del contracte
    i calcula el hash SHA-256. En un sistema en produccio, cada universitat
    enviaria aquest hash al NotaryContract d'Ethereum i quan K=2 coincidissin
    el resultat quedaria ancorat com a oficial.
    """
    sep("FASE 6: Nodes universitaris validen i calculen el hash")

    reader = AlgorandElectionReader(algod_client(), APP_ID)
    state = reader.read_election_state(NOM_PROPOSTA)

    if not state:
        print("  ERROR: no s'ha pogut llegir l'estat")
        return

    # Mostrar resultats
    print(f"\n  Eleccio : {state.election_name}")
    print(f"  Round   : {state.block_round}\n")

    resultats = sorted(zip(state.candidates, state.votes), key=lambda x: x[1], reverse=True)
    max_vots = max(state.votes) if state.votes else 1
    for i, (cand, vots) in enumerate(resultats):
        barra = "█" * int(vots * 20 / max(max_vots, 1))
        guany = " ← GUANYADOR" if i == 0 else ""
        print(f"  {cand:<12} {barra:<22} {vots} vots{guany}")

    hash_hex = compute_election_hash_hex(state)
    print(f"\n  Hash SHA-256 (empremta digital del resultat):")
    print(f"  {hash_hex}\n")

    # Cada universitat llegeix i calcula independentment
    print("  Validacio per node universitari:")
    hashes = {}
    for nom, mn in UNIVERSITY_MNEMONICS.items():
        # Cada universitat usa el seu propi node algod (aqui tots apunten al mateix localnet)
        uni_reader = AlgorandElectionReader(algod_client(), APP_ID)
        uni_state = uni_reader.read_election_state(NOM_PROPOSTA)
        uni_hash = compute_election_hash_hex(uni_state)
        hashes[nom] = uni_hash
        coincideix = "✔ coincideix" if uni_hash == hash_hex else "✗ DISCREPANCIA"
        print(f"  {nom}: {uni_hash[:18]}... {coincideix}")

    # Simular consens K-de-N (K=2)
    hash_counts = {}
    for h in hashes.values():
        hash_counts[h] = hash_counts.get(h, 0) + 1

    consens_hash, consens_count = max(hash_counts.items(), key=lambda x: x[1])
    threshold_k = 2

    print(f"\n  Consens K-de-N (K={threshold_k} de N={len(UNIVERSITY_MNEMONICS)}):")
    if consens_count >= threshold_k:
        print(f"  *** CONSENS ASSOLIT ({consens_count}/{len(UNIVERSITY_MNEMONICS)} universitats) ***")
        print(f"  Hash oficial: {consens_hash}")
        print(f"  → En produccio: aquest hash s'ancoraria al NotaryContract d'Ethereum")
    else:
        print(f"  Consens NO assolit ({consens_count}/{threshold_k} requerits)")

    print(f"\n  Explora a Lora: http://localhost:5173/localnet/application/{APP_ID}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def prefase_financar_contracte():
    """
    Finança el compte del contracte amb ALGO addicionals per cobrir el MBR.

    El contracte Algorand te un compte propi (derivat de l'APP_ID). Cada box
    que crea (cens, proposta, eleccio, vots) incrementa el MBR minim d'aquest
    compte. Amb nomes 1 ALGO inicial no n'hi ha prou per a totes les boxes de
    la simulacio. Enviem 10 ALGO addicionals per garantir que la simulacio
    completa no falli per MBR insuficient.
    """
    from algosdk.logic import get_application_address

    deployer_mn = os.environ.get("DEPLOYER_MNEMONIC", "")
    disp_addr, disp_key = get_account(deployer_mn)
    client = algod_client()

    contract_addr = get_application_address(APP_ID)
    saldo = client.account_info(contract_addr).get("amount", 0)
    print(f"  Saldo actual del contracte: {saldo / 1_000_000:.4f} ALGO")

    if saldo < 5_000_000:
        financar(disp_addr, disp_key, contract_addr, client, amt=10_000_000)
        nou_saldo = client.account_info(contract_addr).get("amount", 0)
        print(f"  Contracte finançat: {nou_saldo / 1_000_000:.4f} ALGO")
    else:
        print(f"  Contracte ja te prou saldo ({saldo / 1_000_000:.4f} ALGO)")


if __name__ == "__main__":
    print("\nSIMULACIO ELECTORAL - SistemaVotacion")
    print(f"APP_ID: {APP_ID}  |  Eleccio: {NOM_PROPOSTA}")
    print(f"Usuaris votants: {NUM_USUARIS}  |  Nodes universitaris: {len(UNIVERSITY_MNEMONICS)}")

    try:
        sep("PRE-FASE: Finançar compte del contracte (MBR)")
        prefase_financar_contracte()
        usuaris = fase0_generar_usuaris()
        fase1_carregar_cens(usuaris)
        fase2_crear_proposta(usuaris)
        fase3_carregar_cens_proposta(usuaris)
        fase4_votar_proposta(usuaris)
        fase5_votar_eleccio(usuaris)
        fase6_ancoratge_universitari()
        print("\n  Simulacio completada!")
    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
