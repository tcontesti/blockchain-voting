# Blockchain Voting System

Sistema de Votacio Electronica descentralitzat basat en Algorand.
UIB -- 21782 Laboratori de Projectes de Software -- Maig 2026.

---

## Descripcio

Prototip funcional d'un sistema de votacio electronica descentralitzat, segur,
transparent i auditable. Desenvolupat com a projecte formatiu per a l'aprenentatge
de la tecnologia blockchain i els contractes intel·ligents.

El principi fonamental que guia tot el disseny es l'eliminacio del punt unic de
fallada. La logica electoral resideix integrement dins un contracte intel·ligent
immutable desplegat a la xarxa Algorand, i cap servidor intermediari te acces a
les claus privades dels votants.

## Estat actual

El projecte es troba en fase d'implementacio (Sprint 3 de 5).

| Component | Estat |
|-----------|-------|
| Arquitectura C4 | Completat |
| Abast i requisits | Completat |
| Mockup UI (7 pantalles) | Completat |
| Smart Contracts (algopy) | En curs |
| Frontend React | En curs |
| Servei anchoring | Pendent |
| Tests E2E | Pendent |

## Stack tecnologic

| Capa | Tecnologia |
|------|-----------|
| Smart Contracts | algopy (Algorand Python) / TEAL / ARC-4 / AlgoKit |
| Blockchain | Algorand (PPoS/VRF) -- localnet Docker |
| Anchoring | Solidity / Ethereum Sepolia / Web3.py |
| Frontend | React 19 / Tailwind CSS / Bun / algosdk / WalletConnect SDK |
| Wallet | Pera Wallet (WalletConnect) |
| Infraestructura | Docker / docker-compose |
| Tests SC | AlgoKit testing framework (Python) + Hardhat (Solidity) |

## Estructura del repositori

    blockchain-voting/
    contracts/                          # Smart Contracts algopy
      smart_contracts/voting/           # Codi font dels contractes
        contract.py                     # Router principal (5 @abimethod)
        verificador.py                  # 7 funcions de validacio
        logica_votacio.py               # Votacio pluralitat / Schulze
        logica_propostes.py             # Modul de propostes
        generador_eleccions.py          # Generacio automatica d'eleccions
        constants.py                    # Constants i prefixos Box Storage
        deploy_config.py                # Configuracio de desplegament
      tests/                            # Tests unitaris (AlgoKit)
        test_votacio.py                 # 5 tests votacio
        test_doble_vot.py               # 5 tests prevencio doble vot
        test_propostes.py               # 5 tests propostes
        test_generador.py               # 4 tests generador
      scripts/                          # Scripts de desplegament
        deploy.py
        populate_census.py
    docs/                               # GitHub Pages (landing page)

## Prerequisits

- Docker i Docker Compose
- AlgoKit >= 2.0
- Bun >= 1.0 (frontend)
- Python >= 3.12

## Configuracio inicial

    git clone https://github.com/tcontesti/blockchain-voting.git
    cd blockchain-voting
    cp .env.example .env

Edita el fitxer `.env` amb els valors necessaris abans de continuar.

## Instruccions de desplegament

Les instruccions completes de desplegament, configuracio de l'entorn Docker
i AlgoKit, i execucio dels tests s'actualitzaran a mesura que avanci la
implementacio.

## Equip

| Membre | GitHub | Rol |
|--------|--------|-----|
| Toni Contesti | @tcontesti | Cap de Projecte |
| Jordi Vanyo | @jvanyom | Frontend / UX (React, Tailwind, Bun) |
| Marc Link | @linkcla | Smart Contracts (algopy, AlgoKit) / QA |
| Dylan Luigi Canning | @dylanluigi | Arquitectura / Anchoring (Solidity) |

## Documentacio

- [Wiki del projecte](https://github.com/tcontesti/blockchain-voting/wiki)
- [Landing page](https://tcontesti.github.io/blockchain-voting/)
- [Backlog](https://github.com/tcontesti/blockchain-voting/issues)
- [Milestones](https://github.com/tcontesti/blockchain-voting/milestones)

---

UIB -- 21782 Laboratori de Projectes de Software -- Maig 2026
