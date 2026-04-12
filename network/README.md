# Network: Arquitectura de Nodes Universitaris

Simulacio de la xarxa institucional descrita al document tecnic (§3.2.2, §7.3.3, §9.7, §10.2). Tres universitats operen com a nodes independents que llegeixen l'estat electoral d'Algorand i calculen hashes deterministics per a futur ancoratge.

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
│ Lector +   │  │ Lector +   │  │ Lector +   │
│ Hasher     │  │ Hasher     │  │ Hasher     │
└────────────┘  └────────────┘  └────────────┘
```

**Universitats simulades:**

| ID  | Nom                                    |
|-----|----------------------------------------|
| UIB | Universitat de les Illes Balears        |
| UPC | Universitat Politecnica de Catalunya    |
| UAB | Universitat Autonoma de Barcelona       |

## Estructura de directoris

```
network/
├── config/
│   ├── universities.json       # Definicio de les 3 universitats i llindar K=2
│   └── network_config.py       # Carregador Python: llegeix JSON + variables d'entorn
├── anchoring/
│   ├── algorand_reader.py      # Llegeix estat d'eleccions des de box storage (ARC-4)
│   ├── hasher.py               # Hash SHA-256 deterministic (JSON canonic)
│   ├── models.py               # ElectionState dataclass
│   └── requirements.txt        # py-algorand-sdk, python-dotenv
├── ethereum/                   # Buit -- per desenvolupar (NotaryContract, etc.)
├── scripts/
│   └── setup_universities.py   # Genera comptes Algorand per a les 3 universitats
├── test_integration.py         # 12 tests (hasher + ARC-4 decoder)
└── .env.example                # Plantilla de variables d'entorn
```

## Inici rapid

### 1. Instal·lar dependencies

```bash
pip install py-algorand-sdk python-dotenv
```

### 2. Executar tests

```bash
# Tests d'integracio (hasher + ARC-4, autonoms sense dependencies externes)
cd network
python test_integration.py
```

### 3. Configurar la xarxa

```bash
# Generar comptes Algorand per a les 3 universitats
python network/scripts/setup_universities.py
```

Aixo crea `network/.env` amb:
- 3 mnemonics d'Algorand (un per universitat)
- Adreces per configurar el cens

### 4. Desplegar contracte Algorand

```bash
algokit localnet start
cd contracts
algokit project run build
python scripts/deploy.py            # → APP_ID
```

## Components

### Algorand Reader (`anchoring/algorand_reader.py`)

Llegeix l'estat de les eleccions des del box storage del contracte:
- Descodifica `DynamicArray[String]` (candidats) des de boxes amb prefix `ec`
- Descodifica `DynamicArray[UInt64]` (vots) des de boxes amb prefix `ev`
- Retorna un `ElectionState` amb nom, candidats i vots

### Hasher (`anchoring/hasher.py`)

Calcula un hash SHA-256 deterministic d'una representacio JSON canonica:
```json
{"candidates":["Alice","Bob"],"election":"Rector2026","votes":[42,31]}
```
Claus ordenades, sense espais. Garanteix que tots els nodes calculen el mateix hash.

### Configuracio (`config/`)

`universities.json` defineix les 3 universitats i el llindar K=2. `network_config.py` carrega la configuracio i resol secrets des de variables d'entorn.

### Ethereum (`ethereum/`)

Directori reservat per al contracte de notaria (NotaryContract). Pendent d'implementacio.

## Variables d'entorn

| Variable | Descripcio |
|----------|------------|
| `ALGOD_SERVER` | URL del node Algorand (defecte: `http://localhost`) |
| `ALGOD_PORT` | Port d'algod (defecte: `4001`) |
| `ALGOD_TOKEN` | Token d'autenticacio d'algod |
| `APP_ID` | ID del contracte SistemaVotacion desplegat |
| `UIB_ALGO_MNEMONIC` | Mnemonic Algorand de la UIB |
| `UPC_ALGO_MNEMONIC` | Mnemonic Algorand de la UPC |
| `UAB_ALGO_MNEMONIC` | Mnemonic Algorand de la UAB |
