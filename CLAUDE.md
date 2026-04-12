# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Decentralized electronic voting system on Algorand blockchain (UIB - Laboratory of Software Projects). Uses algopy/TEAL smart contracts with ARC-4 routing, React 19 frontend (pending), and Ethereum Sepolia anchoring (pending). Code uses Spanish/Catalan naming conventions.

## Build & Test Commands

All smart contract work is in the `contracts/` directory, managed by Poetry (Python 3.12+).

```bash
# Smart contracts
cd contracts/
algokit project run build          # Compile algopy → TEAL
algokit localnet start             # Start local Algorand network
algokit localnet stop              # Stop localnet
algokit project deploy localnet    # Deploy to localnet

# Tests (require localnet running + compiled artifacts)
pytest tests/                      # Run all tests (25 cases across 4 modules)
pytest tests/test_votacio.py -v    # Single module
pytest tests/test_votacio.py::TestVotacioEleccio::test_vot_valid -v  # Single test

# Ethereum Notary Contract
cd network/ethereum/
npm install && npx hardhat test    # Run Solidity tests (standalone, no Algorand needed)
npx hardhat node                   # Start local Ethereum node

# Network simulation (requires localnet + both contracts deployed)
python network/scripts/setup_universities.py     # Generate university accounts
python network/scripts/run_e2e_simulation.py     # Full end-to-end flow
python network/scripts/verify_anchoring.py --all # Check anchoring status
```

## Architecture

**Smart Contract** (`contracts/smart_contracts/voting/contract.py`): Single ARC-4 contract (`SistemaVotacion`) with 5 ABI methods:
- `cargar_censo_global()` — Load census (max 7 addresses/tx)
- `crear_propuesta()` — Create proposal
- `cargar_censo_propuesta()` — Load proposal census
- `votar_propuesta()` — Vote on proposal
- `votar_eleccion()` — Vote in election

**Storage**: 10 BoxMap prefixes defined in `constants.py` — census (`P_CENSO_*`), proposals (`P_PROP_*`), elections (`P_ELEC_*`). BoxMap chosen over local state for scalability.

**Key design patterns**:
- Guard verifiers (DT-02): 10 verification subroutines separated from router logic
- 2-stage voting: proposals → elections, with automatic election generation at `ceil(50% census)` threshold (DT-04/DT-05)
- Plurality voting implemented; Schulze method pending (Issue #29)

**Network layer** (`network/`): Simulates 3 universities (UIB, UPC, UAB) as institutional node operators with K-of-N cross-chain anchoring:
- `network/ethereum/` — Solidity NotaryContract (Hardhat, `npx hardhat test` to verify)
- `network/anchoring/` — Python service that reads Algorand box storage, computes SHA-256, submits to Ethereum
- `network/config/universities.json` — University definitions (N=3, K=2)
- `network/docker-compose.yml` — Orchestrates Hardhat node + 3 anchoring services
- `network/scripts/` — setup_universities.py, run_e2e_simulation.py, verify_anchoring.py

**Planned containers** (not yet implemented):
- React 19 + Tailwind + Bun frontend with Pera Wallet/WalletConnect

## Environment

Copy `.env.example` to `.env`. Key variables: `ALGOD_SERVER`, `ALGOD_PORT`, `ALGOD_TOKEN` (Algorand node), `APP_ID` (deployed contract), `ETHEREUM_RPC_URL` (Sepolia), and `VITE_*` prefixed vars for frontend.

## Test Modules

| Module | Focus |
|--------|-------|
| `test_votacio.py` | Voting logic (6 tests) |
| `test_doble_vot.py` | Double-vote prevention (5 tests) |
| `test_propostes.py` | Proposal lifecycle (9 tests) |
| `test_generador.py` | Election generation (5 tests) |

Tests require `algokit localnet start` and `algokit project run build` before running. All currently marked `@pytest.mark.skip` pending fixture implementation in `conftest.py`.
