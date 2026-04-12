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

**Principi fonamental:** el contracte `SistemaVotacion` es desplega una sola vegada. Cada universitat es connecta de forma independent com a lector, sense necessitat de reiniciar res ni de modificar el contracte.

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

---

## Com s'uneix una nova universitat a la xarxa

El disseny del sistema permet que una nova universitat s'incorpori a una xarxa ja en funcionament sense aturar ni modificar el contracte desplegat. El contracte `SistemaVotacion` es desplega una sola vegada per l'organitzador; les universitats nomes s'hi connecten com a nodes lectors independents.

### Flux d'incorporacio

```
Nova universitat vol unir-se
         │
         ▼
1. Generar compte Algorand propi
   python network/scripts/setup_universities.py
   → Crea un parell de claus (mnemonic + adreca publica)
   → Escriu les credencials a network/.env
         │
         ▼
2. Comunicar l'adreca Algorand a l'organitzador electoral
   (per correu, formulari, o qualsevol canal segur)
         │
         ▼
3. L'organitzador afegeix l'adreca al cens del contracte
   python contracts/scripts/populate_census.py \
       --addresses <ADRECA_NOVA_UNIVERSITAT>
   → Crida cargar_censo_global() sobre el contracte existent
   → NO requereix redesplegament ni reinici
         │
         ▼
4. La universitat configura el seu .env local
   APP_ID=<el mateix APP_ID existent>
   ALGOD_SERVER=<endpoint del node Algorand compartit>
   X_ALGO_MNEMONIC=<el mnemonic generat al pas 1>
         │
         ▼
5. La universitat ja pot llegir eleccions i calcular hashes
   (AlgorandElectionReader connectat al contracte en viu)
```

### Que NO cal fer

- No cal reiniciar el contracte ni redeplegar-lo.
- No cal que les altres universitats facin cap canvi.
- No cal modificar cap fitxer de configuracio del sistema.
- El cens es additiu: afegir una universitat nova no afecta les existents.

### Limitacio actual i TODO

> **TODO:** `config/universities.json` te les tres universitats (UIB, UPC, UAB) hardcoded. Per permetre que qualsevol universitat s'incorpori dinamicament sense modificar codi, cal refactoritzar `network_config.py` i `setup_universities.py` per acceptar un nombre variable de nodes i llegir la llista de participants directament del cens del contracte (box `ct` / `cd`) en lloc d'un fitxer JSON fix.

---

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

---

## Apendix: Desplegament en xarxa real i propers passos

Aquesta seccio descriu com passar de l'entorn de desenvolupament local (AlgoKit localnet) a un desplegament real sobre Algorand Testnet o Mainnet, i quins passos caldria seguir per convertir el sistema en un servei obert on qualsevol universitat pugui participar.

### De localnet a Testnet/Mainnet

El canvi principal es substituir l'endpoint d'algod. Tot el codi de `anchoring/` i `contracts/` funciona identic sobre qualsevol xarxa Algorand; nomes cal actualitzar les variables d'entorn:

| Variable | Localnet | Testnet | Mainnet |
|----------|----------|---------|---------|
| `ALGOD_SERVER` | `http://localhost` | `https://testnet-api.algonode.cloud` | `https://mainnet-api.algonode.cloud` |
| `ALGOD_PORT` | `4001` | `443` | `443` |
| `ALGOD_TOKEN` | `aaa...aaa` | *(buit o token del proveidor)* | *(token del proveidor)* |

Proveïdors publics d'endpoints Algorand: **Nodely** (algonode.cloud), **AlgoExplorer**, o node propi.

**Passos per desplegar a Testnet:**

```bash
# 1. Obtenir ALGO de test (faucet)
#    https://bank.testnet.algorand.network/

# 2. Configurar .env amb l'endpoint de testnet
ALGOD_SERVER=https://testnet-api.algonode.cloud
ALGOD_PORT=443
ALGOD_TOKEN=

# 3. Desplegar el contracte (identic al proces de localnet)
cd contracts
algokit project run build
python scripts/deploy.py    # → APP_ID real a testnet

# 4. Les universitats configuren el seu .env amb el nou APP_ID
APP_ID=<app_id_testnet>
```

A Mainnet el proces es identic pero amb ALGO reals. El cost de desplegament del contracte i de cada transaccio (votar, carregar cens) es cobreix amb ALGO del compte del desplegador.

### Propers passos per a un servei multi-universitat obert

Per transformar el sistema actual en un servei on qualsevol universitat pugui incorporar-se de forma autonoma, caldria abordar els seguents aspectes:

#### 1. Cens obert i autoregistre

Actualment el cens es carrega manualment per l'organitzador (`cargar_censo_global`). Per a un servei obert caldria:

- Afegir un metode `sol·licitar_acces(adreca)` al contracte que registri sol·licituds pendents d'aprovacio.
- O be adoptar un model de cens public: qualsevol adreca registrada a una autoritat de confianca (ex. LDAP universitari) pot votar sense aprovacio manual.
- El llindar K del consens hauria de ser configurable dinamicament o governable per les mateixes universitats participants.

#### 2. Descoberta dinamica de participants

Substituir `universities.json` per una lectura dinamica del cens del contracte:

- Llegir les boxes amb prefix `cd` (cens de participants) per descobrir automaticament quines adreces estan registrades.
- `network_config.py` generaria la llista de nodes a partir de l'estat actual del contracte, sense necessitat de fitxers de configuracio previs.

#### 3. Contracte de notaria Ethereum (capa d'ancoratge)

El directori `network/ethereum/` esta reservat per al `NotaryContract` Solidity que implementa el consens K-de-N:

- Cada universitat envia el seu hash SHA-256 al contracte.
- Quan K universitats envien el mateix hash, el resultat queda ancorat com a oficial a Ethereum.
- Caldria desplegar-lo a Ethereum Sepolia (testnet) o Mainnet i actualitzar `ETHEREUM_RPC_URL` i `NOTARY_CONTRACT_ADDRESS` a cada node.

#### 4. Infraestructura de node per universitat

En produccio, cada universitat hauria d'operar el seu propi node Algorand per garantir la independencia de lectura (un node propi no pot ser censurat per tercers):

```
Universitat X
├── Node algod propi (sincronitzat amb Mainnet)
├── Servei anchoring/ (Python, executa en background)
└── Claus privades en HSM o gestor de secrets (Vault, AWS KMS)
```

Alternativament, per a institucions petites, es pot usar un endpoint public de confianca (Nodely, etc.) mentre no es diposi de node propi.

#### 5. Identitat i autenticacio institucional

Per garantir que cada node es realment una universitat i no un actor malicious:

- Registrar les adreces Algorand en un smart contract de directori (whitelist governada).
- Vincular l'adreca Algorand a un certificat X.509 institucional o a un DID (Decentralized Identifier).
- El llindar K s'hauria d'ajustar a mesura que creix el nombre de participants (ex. K = ceil(2/3 * N) per tolerancia bizantina).

#### Resum de la ruta cap a produccio

```
Estat actual                Propers passos             Produccio
──────────────────────────────────────────────────────────────────
Localnet (AlgoKit)    →    Testnet (Algorand)    →    Mainnet
3 universitats fixes  →    Cens dinamic          →    N universitats
JSON hardcoded        →    Lectura des del cens  →    Autoregistre
Ethereum buit         →    NotaryContract Sepolia→    Ancoratge real
Claus en .env         →    Gestor de secrets     →    HSM/KMS
```

---

## Apendix: Com llegir els arguments de les transaccions (Base64 i ARC-4)

### Per que els arguments apareixen en Base64?

Quan un votant executa `votar_eleccion`, Algorand emmagatzema els arguments de la crida ABI com a bytes crus al registre de la transaccio. L'explorador Lora (i qualsevol altre explorador de blocs) mostra aquests bytes en **Base64** perque es el format estandard per representar dades binaries arbitraries en text. No es cap mecanisme de xifrat: es simplement una codificacio de representacio.

La cadena de codificacio completa es:

```
"Carol"
  → ARC-4 (prefixe de longitud 2 bytes)  →  \x00\x05Carol
  → Base64                                →  AAVDYXJvbA==
  → Explorador Lora (pestanya "App Args") →  AAVDYXJvbA==
```

El primer pas (ARC-4) l'imposa l'estandard ABI d'Algorand: cada argument de tipus `string` porta un prefixe de 2 bytes en big-endian que indica la longitud de la cadena. El segon pas (Base64) el fa l'explorador per poder mostrar qualsevol seqüencia de bytes com a text ASCII.

### Com desxifrar-ho

Per recuperar el valor original cal fer el proces invers: Base64 → bytes crus → saltar els 2 primers bytes (longitud ARC-4) → llegir la resta com a UTF-8.

**Consola del navegador (F12):**
```javascript
// Descodifica i salta els 2 bytes de longitud ARC-4
atob("AAVDYXJvbA==").slice(2)   // → "Carol"
atob("ABBSZWN0b3IxNzc1OTg5NjE1").slice(2)  // → "Rector1775989615"
```

**Python:**
```python
import base64

def arc4_decode(b64: str) -> str:
    raw = base64.b64decode(b64)
    return raw[2:].decode("utf-8")  # salta els 2 bytes de longitud

print(arc4_decode("AAVDYXJvbA=="))               # → Carol
print(arc4_decode("ABBSZWN0b3IxNzc1OTg5NjE1"))   # → Rector1775989615
```

**Eina online:** `base64decode.org` → enganxa el valor → ignora els 2 primers caracters del resultat.

### El primer argument sempre es el selector de metode

Cada crida ABI comenca amb un argument addicional de 4 bytes: el **selector de metode** (hash SHA-512/256 truncat de la signatura del metode). Per exemple:

```
Fh3Jag==  →  bytes \x16\x1d\xc9\x6a  →  selector de votar_eleccion(string,string)void
```

Aquest valor no es un argument del votant; es el identificador intern que el router del contracte usa per saber quina funcio executar. Cal ignorar-lo quan es volen llegir els arguments reals.

### Resum dels arguments de votar_eleccion

| Posicio | Exemple Base64 | Valor decodificat | Significat |
|---------|---------------|-------------------|------------|
| 1 | `Fh3Jag==` | `\x16\x1d\xc9\x6a` | Selector del metode (ignorar) |
| 2 | `ABBSZWN0b3IxNzc1OTg5NjE1` | `Rector1775989615` | Nom de l'eleccio |
| 3 | `AAVDYXJvbA==` | `Carol` | Candidat escollit |

### Privacitat del vot

Els arguments **no estan xifrats**: qualsevol persona que conexi l'adreca Algorand d'un votant pot consultar el seu historial de transaccions i veure exactament per qui ha votat. La privacitat del sistema es basa en el **pseudonimat de les adreces**: si no es coneix a quina persona fisica correspon una adreca, el vot es opac per al public general. L'organitzador electoral, pero, coneix la correspondencia adreca-persona ja que ell mateix ha carregat el cens.
