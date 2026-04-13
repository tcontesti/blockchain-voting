# Voting Network: Deployment Architecture

This document describes the target architecture for a production-ready, scalable network of institutional nodes (universities) for the blockchain-based voting system. It reflects the revised scope (see BLOCKCHAIN.pdf, section 3.7) which replaced the original centralized anchoring service with a distributed K-of-N model.

## 1. Institutional Node Architecture

In a real-world deployment, each participating university operates its own **Institutional Voting Node**. This ensures that no single entity controls the entire voting process and that the results are verified by multiple independent parties. The guiding principle is the **elimination of single points of failure** (see BLOCKCHAIN.pdf, section 7): no individual component can modify, censor, or invalidate a vote by itself.

### Components per University
Each university should deploy a stack consisting of:
1.  **Algorand Full Node (`algod`):** A participation node synchronized with the Algorand network. Implemented in Go, it exposes a standard REST API compatible with the Algorand SDK. This ensures the university reads the election state directly from their own copy of the ledger, preventing censorship. The node serves exclusively as the entry point to the network — it contains no business logic and has no access to voter keys (section 7.2.2).
2.  **Anchoring Service:** A Python-based service (containerized) that:
    *   Connects to the local `algod` node via the AlgoSDK REST API.
    *   Monitors the Algorand smart contract for finalized elections.
    *   Calculates a **deterministic SHA-256 hash** of the final vote count (the blockchain state corresponding to the ballot).
    *   Signs the hash cryptographically with **ECDSA** using the university's institutional private key.
    *   Submits this signed hash to the **Ethereum Notary Contract** via JSON-RPC (Web3.py) for cross-chain anchoring.
3.  **Key Management (HSM/KMS):** Institutional private keys (for signing the anchoring transactions) should be stored in a Hardware Security Module (HSM) or a secure cloud KMS (e.g., AWS KMS, HashiCorp Vault) rather than local `.env` files. In the prototype, keys are managed via environment variables for simplicity.

### Why This Model?
The initial design (1st deliverable) used a single centralized Python service to read Algorand state and write to Ethereum. This introduced a single point of failure: if the service was compromised or produced an incorrect hash, the anchoring offered no real guarantee. The revised model (section 3.7.4) distributes this responsibility across all institutional nodes, so that **to manipulate the anchoring, an attacker would need to compromise K nodes simultaneously** — cryptographically infeasible in practice.

---

## 2. Ethereum Notary Contract (K-of-N Consensus)

The Ethereum smart contract (Solidity, deployed on Sepolia Testnet) acts as a **decentralized "supreme court"** — a notari public that provides an immutable, independently auditable record of election results on a second blockchain.

### How It Works
1.  **Whitelist:** The contract maintains a registry of Ethereum addresses belonging to authorized university nodes. During onboarding, each university provides both an Algorand address (for reading election state) and an Ethereum address (for anchoring).
2.  **Submission:** When a university's anchoring service detects a finalized election, it computes the SHA-256 hash of the final state and sends a transaction to the Ethereum contract.
3.  **Validation:** The contract verifies that `msg.sender` is in the whitelist of authorized addresses. Submissions from unknown addresses are rejected.
4.  **Consensus Threshold:** The contract aggregates hashes per `election_id`. It does **not** finalize the result until $K$ out of $N$ authorized universities have submitted the **same hash** for the same election (e.g., 2 out of 3 in the prototype, or 5 out of 7 in a larger deployment).
5.  **Publication & Event Emission:** Once the threshold is reached, the contract:
    *   Marks the result as **"Anchored"** on-chain.
    *   Emits a Solidity event (e.g., `ResultAnchored(electionId, hash, timestamp)`) that provides a permanent, publicly queryable proof of anchoring.

### Security Properties
*   **Byzantine fault tolerance:** A single compromised node cannot forge an anchored result — the hash would not match the honest nodes.
*   **Deterministic verification:** Since all nodes read the same Algorand ledger state, honest nodes will always compute identical SHA-256 hashes. Any disagreement is an immediate signal of compromise or misconfiguration.
*   **Cross-chain immutability:** Once anchored on Ethereum, the result is protected by Ethereum's own consensus mechanism, independent of Algorand.

---

## 3. Network Configuration

The list of authorized university nodes is defined statically in `network/config/universities.json`. Each entry specifies the university's identifier, name, and references to environment variables for both Algorand and Ethereum credentials.

**Current configuration (N=3, K=2):**

| University | Algorand Key Env          | Ethereum Key Env         |
|------------|---------------------------|--------------------------|
| UIB        | `UIB_ALGO_MNEMONIC`       | `UIB_ETH_PRIVATE_KEY`    |
| UPC        | `UPC_ALGO_MNEMONIC`       | `UPC_ETH_PRIVATE_KEY`    |
| UAB        | `UAB_ALGO_MNEMONIC`       | `UAB_ETH_PRIVATE_KEY`    |

To add a new university: add an entry to `universities.json`, add the corresponding environment variables to `.env`, and update the Ethereum NotaryContract whitelist.

---

## 4. Implementation Roadmap (Step-by-Step Commit Plan)

This section describes the logical order for committing changes to the main branch. Each step is self-contained and testable independently.

### Step 1: Smart Contract (Algorand) — *Already on `main`*
**Branch:** `main` (already merged)
**What:** The `SistemaVotacion` ARC-4 contract with all 5 ABI methods, guard verifiers, BoxMap storage, and the 2-stage voting flow (proposals → elections).
**Files:** `contracts/smart_contracts/voting/contract.py`, `constants.py`
**Tests:** `pytest tests/` (25 cases across 4 modules)
**Why first:** Everything else depends on the contract being deployed and functional.

---

### Step 2: Network Configuration & University Setup
**Branch:** `feature/network-config`
**What:** Static configuration of the 3 university nodes with both Algorand and Ethereum credentials.
**Files:**
- `network/config/universities.json` — university definitions with Algorand + Ethereum key references
- `network/config/network_config.py` — `UniversityNode` dataclass with `algorand_address`, `algorand_private_key`, `ethereum_address` properties; `load_universities()` resolves both credential types from env vars
- `network/scripts/setup_universities.py` — generates Algorand (mnemonic) and Ethereum (ECDSA) key pairs for each university, writes to `.env`
- `network/.env.example` — template with all required variables

**Tests:** Run `setup_universities.py` and verify that `.env` contains valid keys for all 3 universities.
**Why this order:** The anchoring layer needs configured nodes before it can do anything.

---

### Step 3: Algorand State Reader (Box Storage Decoder)
**Branch:** `feature/algorand-reader`
**What:** Module that reads election state (candidates + vote counts) from Algorand Box Storage by decoding ARC-4 binary formats.
**Files:**
- `network/anchoring/models.py` — `ElectionState` dataclass
- `network/anchoring/algorand_reader.py` — `AlgorandElectionReader` with ARC-4 decoders (`_decode_dynamic_string_array`, `_decode_dynamic_uint64_array`)

**Tests:** `test_integration.py` section 2 (ARC-4 decoder tests, 6 cases)
**Why this order:** The hasher and consensus modules consume `ElectionState` objects produced by the reader.

---

### Step 4: Deterministic Hasher (SHA-256)
**Branch:** `feature/hasher`
**What:** Computes a deterministic SHA-256 hash of election results using canonical JSON serialization (sorted keys, no whitespace, UTF-8).
**Files:**
- `network/anchoring/hasher.py` — `compute_election_hash()` (returns bytes), `compute_election_hash_hex()` (returns `0x`-prefixed hex compatible with Solidity `bytes32`)

**Tests:** `test_integration.py` section 1 (hasher tests, 6 cases). Key property: identical input → identical hash across all nodes.
**Why this order:** The hash is the fundamental unit of the K-of-N consensus — without deterministic hashing, the entire anchoring model fails.

---

### Step 5: K-of-N Consensus Logic
**Branch:** `feature/consensus`
**What:** Local verification of consensus among university nodes before submitting to Ethereum. Groups hashes by value, checks if any group meets the K threshold, and identifies agreeing/dissenting nodes.
**Files:**
- `network/anchoring/consensus.py` — `check_consensus()` function, `ConsensusResult` dataclass

**Tests:** `test_integration.py` section 3 (consensus tests, 5 cases). Covers: unanimous agreement, partial agreement, total disagreement, empty input, K=1 edge case.
**Why this order:** Consensus verification happens before Ethereum submission — it gates whether gas should be spent.

---

### Step 6: Ethereum Submitter (Web3.py)
**Branch:** `feature/ethereum-submitter`
**What:** Client that constructs, signs (ECDSA), and sends transactions to the Ethereum NotaryContract. Handles transaction building, nonce management, gas estimation, and receipt parsing (including `ResultAnchored` event detection).
**Files:**
- `network/anchoring/ethereum_submitter.py` — `EthereumSubmitter` class, `SubmissionResult` dataclass, minimal `NOTARY_ABI` (only `submitHash` method + events)

**Tests:** Requires a running Hardhat node with the NotaryContract deployed. Tested end-to-end via the simulation script (Step 8).
**Why this order:** Depends on the hasher (Step 4) for the hash format and consensus (Step 5) for the submission decision.

---

### Step 7: Anchoring Service Orchestrator
**Branch:** `feature/anchoring-service`
**What:** High-level service that ties together all anchoring components for a single university node. Provides `compute_hash()` and `anchor()` methods.
**Files:**
- `network/anchoring/anchoring_service.py` — `AnchoringService` class, `AnchoringResult` dataclass

**Tests:** Tested via the simulation script (Step 8).
**Why this order:** This is the integration layer — it composes Steps 3-6 into a single interface.

---

### Step 8: End-to-End Simulation
**Branch:** `feature/e2e-simulation`
**What:** Script that runs a complete electoral cycle on localnet: generates users, loads census, creates proposal, votes to threshold, generates election, votes in election, then each university node independently reads results, computes hash, and verifies K-of-N consensus.
**Files:**
- `network/scripts/simulate_election.py` — 7-phase simulation using `AnchoringService` and `check_consensus`
- `network/test_integration.py` — 17 autonomous tests (no external dependencies)

**How to run:**
```bash
# Terminal 1: Start Algorand localnet
algokit localnet start

# Terminal 2: Deploy contract and run simulation
cd contracts/
algokit project run build
poetry run python scripts/deploy.py
poetry run python ../network/scripts/simulate_election.py

# Autonomous tests (no localnet needed)
cd network/
python test_integration.py
```

**Why last:** This is the validation step that proves all components work together.

---

### Future Steps (Not Yet Implemented)
These are documented for completeness but are out of scope for the current prototype:

- **Ethereum NotaryContract (Solidity):** Implement `NotaryContract.sol` with whitelist, `submitHash()`, K-of-N threshold logic, and `ResultAnchored` event. Deploy to Sepolia.
- **Docker Compose orchestration:** Production-grade `docker-compose.yml` bundling algod + anchoring service per university.
- **Frontend (React 19):** Web application with Pera Wallet integration for voting.
- **Verification script:** `verify_anchoring.py` that queries the Ethereum contract to confirm anchoring status.
