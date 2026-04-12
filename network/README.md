# Network: Arquitectura de Nodes Universitaris

Simulació de la xarxa institucional descrita al document tècnic (§3.2.2, §7.3.3, §9.7, §10.2). Tres universitats operen com a nodes independents que ancoren els resultats electorals d'Algorand a Ethereum mitjançant un mecanisme de consens **K-de-N**.

## Arquitectura

```
┌─────────────────────────────────────────────────┐
│  AlgoKit Localnet (Docker)                      │
│  algod + indexer + KMD                          │
│  Contracte SistemaVotacion desplegat aquí        │
└──────────────────────┬──────────────────────────┘
                       │ REST API (:4001)
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│ Anchoring  │  │ Anchoring  │  │ Anchoring  │
│ UIB        │  │ UPC        │  │ UAB        │
│ (Python)   │  │ (Python)   │  │ (Python)   │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      │ submitHash()  │               │
      └───────────────┼───────────────┘
                      ▼
             ┌─────────────────┐
             │ Ethereum Node   │
             │ (Hardhat local) │
             │ NotaryContract  │
             │ K=2 de N=3      │
             └─────────────────┘
```

**Universitats simulades:**

| ID  | Nom                                    |
|-----|----------------------------------------|
| UIB | Universitat de les Illes Balears        |
| UPC | Universitat Politècnica de Catalunya    |
| UAB | Universitat Autònoma de Barcelona       |

## Estructura de directoris

```
network/
├── config/
│   ├── universities.json       # Definició de les 3 universitats i llindar K=2
│   └── network_config.py       # Carregador Python: llegeix JSON + variables d'entorn
├── anchoring/
│   ├── service.py              # Servei principal (mode polling o on-demand)
│   ├── algorand_reader.py      # Llegeix estat d'eleccions des de box storage (ARC-4)
│   ├── hasher.py               # Hash SHA-256 determinístic (JSON canònic)
│   ├── ethereum_submitter.py   # Envia hash al NotaryContract via Web3
│   ├── models.py               # ElectionState, AnchoringResult
│   ├── Dockerfile              # Imatge Python 3.12 per al contenidor
│   └── requirements.txt        # py-algorand-sdk, web3, python-dotenv
├── ethereum/
│   ├── contracts/
│   │   └── NotaryContract.sol  # Contracte Solidity K-de-N (18 tests)
│   ├── test/
│   │   └── NotaryContract.test.js
│   ├── scripts/
│   │   └── deploy.js           # Desplegament amb whitelist + llindar
│   ├── hardhat.config.js
│   ├── package.json
│   └── Dockerfile              # Node Hardhat per a Docker
├── scripts/
│   ├── setup_universities.py   # Genera comptes Algorand + Ethereum
│   ├── run_e2e_simulation.py   # Simulació completa del flux
│   └── verify_anchoring.py     # Verificació d'ancoratge a Ethereum
├── docker-compose.yml          # Orquestra Hardhat + 3 serveis d'ancoratge
├── test_integration.py         # 21 tests d'integració (hasher + ARC-4 + Ethereum)
└── .env.example                # Plantilla de variables d'entorn
```

## Inici ràpid

### 1. Instal·lar dependències

```bash
# Ethereum (Hardhat)
cd network/ethereum
npm install

# Python (anchoring)
pip install py-algorand-sdk web3 python-dotenv
```

### 2. Executar tests

```bash
# Tests del contracte Solidity (18 tests, autònom)
cd network/ethereum
npx hardhat test

# Tests d'integració complets (21 tests, inicia Hardhat automàticament)
cd network
python test_integration.py
```

### 3. Configurar la xarxa

```bash
# Generar comptes per a les 3 universitats
python network/scripts/setup_universities.py
```

Això crea `network/.env` amb:
- 3 mnemonics d'Algorand (un per universitat)
- 3 claus privades d'Ethereum (un per universitat)
- Adreces per configurar el cens i el NotaryContract

### 4. Desplegar contractes

```bash
# Algorand (requereix algokit)
algokit localnet start
cd contracts
algokit project run build
python scripts/deploy.py            # → APP_ID

# Ethereum (Hardhat local)
cd network/ethereum
npx hardhat node &                  # Inicia node al port 8545
UNIVERSITY_ADDRESSES=0x...,0x...,0x... \
THRESHOLD_K=2 \
npx hardhat run scripts/deploy.js --network localhost  # → NOTARY_CONTRACT_ADDRESS
```

### 5. Executar amb Docker

```bash
cd network

# Configurar .env amb APP_ID i NOTARY_CONTRACT_ADDRESS
cp .env.example .env
# Editar .env amb els valors obtinguts als passos anteriors

# Arrancar tot
docker compose up --build
```

Això inicia:
- **hardhat**: node Ethereum local al port 8545
- **anchoring-uib**: servei d'ancoratge UIB
- **anchoring-upc**: servei d'ancoratge UPC
- **anchoring-uab**: servei d'ancoratge UAB

Els serveis d'ancoratge es connecten a AlgoKit localnet via `host.docker.internal:4001`.

### 6. Simulació end-to-end

```bash
python network/scripts/run_e2e_simulation.py
```

Flux:
1. Verifica que localnet està activa
2. Llegeix les eleccions des d'Algorand
3. Cada universitat calcula el hash SHA-256 de l'estat
4. Cada universitat envia el hash al NotaryContract
5. Verifica si s'ha assolit el consens K-de-N

### 7. Verificar ancoratge

```bash
# Verificar una elecció concreta
python network/scripts/verify_anchoring.py --election "Rector2026"

# Verificar totes les eleccions
python network/scripts/verify_anchoring.py --all
```

## Com funciona el consens K-de-N

1. Una elecció es completa a Algorand (votació finalitzada)
2. Cada universitat llegeix l'estat des del seu node Algorand (box storage amb prefixos `ec` i `ev`)
3. Calcula el hash SHA-256 d'una representació JSON canònica:
   ```json
   {"candidates":["Alice","Bob"],"election":"Rector2026","votes":[42,31]}
   ```
4. Envia el hash signat (ECDSA) al `NotaryContract` d'Ethereum
5. Quan **K** de **N** universitats envien el **mateix hash**, el contracte l'ancora com a resultat oficial
6. Un hash discordant (node compromès) no assoleix el llindar i no s'ancora

## Variables d'entorn

| Variable | Descripció |
|----------|------------|
| `ALGOD_SERVER` | URL del node Algorand (defecte: `http://localhost`) |
| `ALGOD_PORT` | Port d'algod (defecte: `4001`) |
| `ALGOD_TOKEN` | Token d'autenticació d'algod |
| `APP_ID` | ID del contracte SistemaVotacion desplegat |
| `ETHEREUM_RPC_URL` | URL del node Ethereum (defecte: `http://localhost:8545`) |
| `NOTARY_CONTRACT_ADDRESS` | Adreça del NotaryContract desplegat |
| `UIB_ALGO_MNEMONIC` | Mnemonic Algorand de la UIB |
| `UIB_ETH_PRIVATE_KEY` | Clau privada Ethereum de la UIB |
| `UPC_ALGO_MNEMONIC` | Mnemonic Algorand de la UPC |
| `UPC_ETH_PRIVATE_KEY` | Clau privada Ethereum de la UPC |
| `UAB_ALGO_MNEMONIC` | Mnemonic Algorand de la UAB |
| `UAB_ETH_PRIVATE_KEY` | Clau privada Ethereum de la UAB |
| `POLL_INTERVAL` | Interval de polling en segons (defecte: `10`) |
