# Network: Arquitectura de Nodes Universitaris

Xarxa institucional descrita al document tecnic (BLOCKCHAIN.pdf §3.2.2, §7.3.3, §9.7, §10.2). Cada universitat opera com a node independent que llegeix l'estat electoral d'Algorand, calcula hashes SHA-256 deterministics, verifica el consens K-de-N, i envia el hash al contracte NotaryContract d'Ethereum per a l'ancoratge.

## Arquitectura

```
┌─────────────────────────────────────────────────┐
│  AlgoKit Localnet (Docker)                      │
│  algod + indexer + KMD                          │
│  Contracte SistemaVotacion desplegat aqui        │
└──────────────────────┬──────────────────────────┘
                       │ REST API (:4001)
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│ Node UIB   │  │ Node UPC   │  │ Node UAB   │
│ (Python)   │  │ (Python)   │  │ (Python)   │
│ Reader  +  │  │ Reader  +  │  │ Reader  +  │
│ Hasher  +  │  │ Hasher  +  │  │ Hasher  +  │
│ Consensus  │  │ Consensus  │  │ Consensus  │
└──────┬─────┘  └──────┬─────┘  └──────┬─────┘
       │               │               │
       └───────────────┼───────────────┘
                       │ ECDSA + JSON-RPC
                       ▼
          ┌─────────────────────────┐
          │  Ethereum (Sepolia)     │
          │  NotaryContract         │
          │  K-de-N consensus       │
          │  Whitelist + Anchoring  │
          └─────────────────────────┘
```

**Principi fonamental:** el contracte `SistemaVotacion` es desplega una sola vegada. Cada universitat s'hi connecta de forma independent com a node lector. Universitats noves es poden afegir **en calent** sense reiniciar cap servei.

## Universitats simulades (per defecte)

| ID  | Nom                                    | Algorand Key          | Ethereum Key          |
|-----|----------------------------------------|-----------------------|-----------------------|
| UIB | Universitat de les Illes Balears       | `UIB_ALGO_MNEMONIC`   | `UIB_ETH_PRIVATE_KEY` |
| UPC | Universitat Politecnica de Catalunya   | `UPC_ALGO_MNEMONIC`   | `UPC_ETH_PRIVATE_KEY` |
| UAB | Universitat Autonoma de Barcelona      | `UAB_ALGO_MNEMONIC`   | `UAB_ETH_PRIVATE_KEY` |

**Llindar de consens:** K=2 de N=3 (recalculat automaticament com `ceil(2/3 * N)` en afegir universitats).

## Estructura de directoris

```
network/
├── config/
│   ├── universities.json          # Definicio de les universitats i llindar K
│   └── network_config.py          # UniversityNode dataclass + load_universities()
├── anchoring/
│   ├── models.py                  # ElectionState dataclass
│   ├── algorand_reader.py         # Lectura d'eleccions des de box storage (ARC-4)
│   ├── hasher.py                  # Hash SHA-256 deterministic (JSON canonic)
│   ├── consensus.py               # Logica de consens K-de-N
│   ├── ethereum_submitter.py      # Enviament de hashes a Ethereum (Web3.py)
│   └── anchoring_service.py       # Orquestrador del flux complet per node
├── ethereum/                      # Reservat per al NotaryContract (Solidity)
├── scripts/
│   ├── setup_universities.py      # Genera comptes Algorand+Ethereum per a totes les universitats
│   ├── add_university.py          # Afegeix una universitat en calent (claus + JSON + .env + cens)
│   └── simulate_election.py       # Simulacio completa del cicle electoral
├── test_integration.py            # 17 tests autonoms (hasher + ARC-4 + consens)
├── .env.example                   # Plantilla de variables d'entorn
└── .env                           # Credencials reals (NO pujar al repositori)
```

---

## Inici rapid

### Prerequisits

- Python 3.12+
- [AlgoKit](https://github.com/algorandfoundation/algokit-cli) instal·lat
- Docker (per a AlgoKit localnet)
- Poetry (gestor de dependencies del projecte)

### Pas 1: Instal·lar dependencies

```bash
cd contracts/
poetry install
poetry run pip install eth-account    # Per a claus Ethereum
```

### Pas 2: Tests autonoms (sense dependencies externes)

```bash
cd network/
python test_integration.py
# Resultat esperat: 17 tests passats, 0 tests fallats
```

### Pas 3: Arrancar Algorand localnet

```bash
algokit localnet start
```

### Pas 4: Generar comptes per a les universitats

```bash
cd contracts/
poetry run python ../network/scripts/setup_universities.py
```

Aixo genera per a cada universitat:
- Mnemonic Algorand (25 paraules)
- Clau privada Ethereum (ECDSA)
- Tot escrit a `network/.env`

### Pas 5: Compilar i desplegar el contracte

```bash
cd contracts/
algokit compile py smart_contracts/voting/contract.py
poetry run python scripts/deploy.py
```

El deploy imprimeix l'`APP_ID`. Actualitza `network/.env`:
```
APP_ID=<el valor que ha imprès>
```

### Pas 6: Executar la simulacio electoral completa

```bash
cd contracts/
poetry run python ../network/scripts/simulate_election.py
```

La simulacio executa 7 fases:

| Fase | Accio |
|------|-------|
| Pre  | Finança el compte del contracte (MBR) |
| 0    | Genera i finança 8 comptes d'usuari |
| 1    | Carrega els 8 usuaris al cens global |
| 2    | L'usuari #1 proposa l'eleccio |
| 3    | L'usuari #1 carrega el cens de la proposta |
| 4    | Usuaris voten la proposta fins assolir majoria (eleccio generada automaticament) |
| 5    | Els 8 usuaris voten a l'eleccio |
| 6    | Nodes universitaris llegeixen resultats, calculen hash i verifiquen consens K-de-N |

---

## Afegir universitats en calent

Es poden afegir universitats mentre la xarxa esta en funcionament, **sense reiniciar cap servei**.

### Nomes configuracio (claus + JSON + .env)

```bash
cd contracts/
poetry run python ../network/scripts/add_university.py \
  --id uv --name "Universitat de Valencia"
```

### Configuracio + registre al cens del contracte Algorand

```bash
poetry run python ../network/scripts/add_university.py \
  --id uv --name "Universitat de Valencia" --register
```

### Que fa `add_university.py`

1. Valida que l'ID no existeixi ja
2. Genera claus Algorand (mnemonic) + Ethereum (ECDSA)
3. Afegeix l'entrada a `universities.json`
4. Recalcula `threshold_k = ceil(2/3 * N)` automaticament
5. Afegeix les credencials a `.env` (sense sobreescriure les existents)
6. Amb `--register`: crida `cargar_censo_global()` al contracte Algorand per registrar l'adreca al cens

### Recalcul automatic del llindar K

| Universitats (N) | Llindar (K) |
|:-:|:-:|
| 3 | 2 |
| 4 | 3 |
| 5 | 4 |
| 7 | 5 |

### Recarga en calent

Els scripts recarreguen la configuracio des de disc a cada execucio. Si un proces ja esta en funcionament (ex: `simulate_election.py`), la fase 6 recarrega `universities.json` i `.env` automaticament abans de verificar el consens, detectant universitats afegides sense reiniciar.

---

## Components

### Algorand Reader (`anchoring/algorand_reader.py`)

Llegeix l'estat de les eleccions des del box storage del contracte:
- Descodifica `DynamicArray[String]` (candidats) des de boxes amb prefix `ec`
- Descodifica `DynamicArray[UInt64]` (vots) des de boxes amb prefix `ev`
- Retorna un `ElectionState` amb nom, candidats, vots i round

### Hasher (`anchoring/hasher.py`)

Calcula un hash SHA-256 deterministic d'una representacio JSON canonica:
```json
{"candidates":["Alice","Bob"],"election":"Rector2026","votes":[42,31]}
```
Claus ordenades, sense espais, UTF-8. Garanteix que tots els nodes calculen el **mateix hash** per al mateix estat.

### Consens K-de-N (`anchoring/consensus.py`)

Verifica localment si almenys K nodes han calculat el mateix hash:
- Agrupa hashes per valor
- Identifica nodes d'acord i nodes discrepants
- Retorna `ConsensusResult` amb `reached`, `consensus_hash`, `agreeing_nodes`, `dissenting_nodes`

### Ethereum Submitter (`anchoring/ethereum_submitter.py`)

Client per enviar hashes al contracte NotaryContract d'Ethereum:
- Construeix transaccions, les signa amb ECDSA, les envia via JSON-RPC
- Detecta l'event `ResultAnchored` quan el llindar K s'assoleix al contracte
- Import lazy de `web3`: no requereix instal·lacio fins que s'usa realment

### Servei d'Ancoratge (`anchoring/anchoring_service.py`)

Orquestra el flux complet per a un node universitari:
1. `compute_hash(election)` -- llegeix Algorand + calcula SHA-256
2. `anchor(election, node_hashes)` -- verifica consens + envia a Ethereum si escau

### Configuracio (`config/`)

`universities.json` defineix les universitats, credencials (per referencia a env vars) i llindar K.
`network_config.py` exposa `UniversityNode` amb propietats `algorand_address`, `algorand_private_key` i `ethereum_address`.

## Variables d'entorn

| Variable | Descripcio | Defecte |
|----------|------------|---------|
| `ALGOD_SERVER` | URL del node Algorand | `http://localhost` |
| `ALGOD_PORT` | Port d'algod | `4001` |
| `ALGOD_TOKEN` | Token d'autenticacio d'algod | `aaa...a` (64 a) |
| `APP_ID` | ID del contracte SistemaVotacion desplegat | *(obligatori)* |
| `ETHEREUM_RPC_URL` | URL JSON-RPC del node Ethereum | `http://localhost:8545` |
| `NOTARY_CONTRACT_ADDRESS` | Adreca del NotaryContract | *(quan estigui desplegat)* |
| `{ID}_ALGO_MNEMONIC` | Mnemonic Algorand de la universitat | *(generat per setup)* |
| `{ID}_ETH_PRIVATE_KEY` | Clau privada Ethereum de la universitat | *(generat per setup)* |
| `DEPLOYER_MNEMONIC` | Mnemonic de l'administrador del contracte | *(per al registre al cens)* |

---

## De localnet a Testnet/Mainnet

Tot el codi funciona identic sobre qualsevol xarxa Algorand. Nomes cal actualitzar les variables d'entorn:

| Variable | Localnet | Testnet | Mainnet |
|----------|----------|---------|---------|
| `ALGOD_SERVER` | `http://localhost` | `https://testnet-api.algonode.cloud` | `https://mainnet-api.algonode.cloud` |
| `ALGOD_PORT` | `4001` | `443` | `443` |
| `ALGOD_TOKEN` | `aaa...aaa` | *(buit o token del proveidor)* | *(token del proveidor)* |

Proveidors publics d'endpoints Algorand: **Nodely** (algonode.cloud), **AlgoExplorer**, o node propi.

**Desplegar a Testnet:**

```bash
# 1. Obtenir ALGO de test: https://bank.testnet.algorand.network/
# 2. Configurar .env amb l'endpoint de testnet
# 3. Compilar i desplegar (identic a localnet)
cd contracts/
algokit compile py smart_contracts/voting/contract.py
poetry run python scripts/deploy.py
# 4. Actualitzar APP_ID al .env de cada universitat
```

---

## Apendix: Com llegir els arguments de les transaccions (Base64 i ARC-4)

### Per que els arguments apareixen en Base64?

Algorand emmagatzema els arguments de les crides ABI com a bytes crus. L'explorador mostra aquests bytes en **Base64** (codificacio de representacio, no xifrat).

La cadena de codificacio completa:

```
"Carol"
  --> ARC-4 (prefix de longitud 2 bytes)  -->  \x00\x05Carol
  --> Base64                              -->  AAVDYXJvbA==
```

### Com descodificar-ho

**Consola del navegador (F12):**
```javascript
atob("AAVDYXJvbA==").slice(2)   // --> "Carol"
```

**Python:**
```python
import base64

def arc4_decode(b64: str) -> str:
    raw = base64.b64decode(b64)
    return raw[2:].decode("utf-8")

print(arc4_decode("AAVDYXJvbA=="))  # --> Carol
```

### El primer argument sempre es el selector de metode

Cada crida ABI comenca amb 4 bytes: el **selector de metode** (hash SHA-512/256 truncat de la signatura). Cal ignorar-lo per llegir els arguments reals.

| Posicio | Exemple Base64 | Valor decodificat | Significat |
|---------|---------------|-------------------|------------|
| 1 | `Fh3Jag==` | `\x16\x1d\xc9\x6a` | Selector del metode (ignorar) |
| 2 | `ABBSZWN0b3IxNzc1OTg5NjE1` | `Rector1775989615` | Nom de l'eleccio |
| 3 | `AAVDYXJvbA==` | `Carol` | Candidat escollit |

### Privacitat del vot

Els arguments **no estan xifrats**: qualsevol persona que conexi l'adreca Algorand d'un votant pot veure per qui ha votat. La privacitat es basa en el **pseudonimat de les adreces**: si no es coneix a quina persona correspon una adreca, el vot es opac per al public.
