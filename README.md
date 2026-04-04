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

El projecte es troba en fase d'implementacio. L'arquitectura, l'abast i el disseny
de la interficie d'usuari estan completats. El codi del backend (Smart Contracts)
i del frontend (React) estan en desenvolupament.

## Stack tecnologic

| Capa | Tecnologia |
|------|-----------|
| Smart Contracts | PyTeal / TEAL / ARC-4 / AlgorKit |
| Blockchain | Algorand (PPoS/VRF) -- localnet Docker |
| Anchoring | Solidity / Ethereum Sepolia / Web3.py |
| Frontend | React 19 / Vite / algosdk / WalletConnect SDK |
| Wallet | Pera Wallet (WalletConnect) |
| Infraestructura | Docker / docker-compose |
| Tests SC | AlgorKit testing framework (Python) + Hardhat (Solidity) |

## Estructura del repositori

    blockchain-voting/
    contracts/          # Smart Contracts PyTeal/TEAL
      src/              # Codi font dels contractes
      tests/            # Tests unitaris (AlgorKit)
      scripts/          # Scripts de desplegament
    frontend/           # Aplicacio React/Vite
      src/
        pages/          # 7 pagines
        components/     # Components reutilitzables
        modules/        # WalletConnect, TransactionBuilder
        hooks/          # React hooks
        i18n/           # Traduccions EN/ES/CA
      public/
    anchoring/          # Servei d'ancoratge Ethereum
      src/              # Gestor d'ancoratge Python
      contracts/        # Ethereum Notary Contract (Solidity)
      tests/            # Tests Hardhat
    docs/               # GitHub Pages + documentacio
    .github/
      workflows/        # GitHub Actions CI
      ISSUE_TEMPLATE/

## Prerequisits

- Docker i Docker Compose
- AlgorKit >= 2.0
- Node.js >= 20 o Bun >= 1.0
- Python >= 3.11

## Configuracio inicial

    git clone https://github.com/tcontesti/blockchain-voting.git
    cd blockchain-voting
    cp .env.example .env

Edita el fitxer `.env` amb els valors necessaris abans de continuar.

## Instruccions de desplegament

Les instruccions completes de desplegament, configuracio de l'entorn Docker
i AlgorKit, i execucio dels tests s'actualitzaran a mesura que avanci la
implementacio.

## Equip

| Membre | GitHub | Rol |
|--------|--------|-----|
| Toni Contesti | @tcontesti | Cap de Projecte |
| Jordi Vanyo | @jvanyom | Frontend / UX |
| Marc Link | @linkcla | QA / Seguretat |
| Dylan Luigi Canning | @dylanluigi | Arquitectura / Smart Contracts |

## Documentacio

- [Wiki del projecte](https://github.com/tcontesti/blockchain-voting/wiki)
- [Landing page](https://tcontesti.github.io/blockchain-voting/)
- [Backlog](https://github.com/tcontesti/blockchain-voting/issues)
- [Milestones](https://github.com/tcontesti/blockchain-voting/milestones)

---

UIB -- 21782 Laboratori de Projectes de Software -- Maig 2026
