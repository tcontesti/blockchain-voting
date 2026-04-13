import algosdk from 'algosdk';

// ── LocalNet configuration ──────────────────────────────────────────
// Uses localhost so the Docker container can reach
// the AlgoKit LocalNet running on the host machine.
const ALGOD_SERVER = 'http://localhost';
const ALGOD_PORT = 4001;
const ALGOD_TOKEN = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';

const INDEXER_SERVER = 'http://localhost';
const INDEXER_PORT = 8980;
const INDEXER_TOKEN = '';

// ── Contract App ID ─────────────────────────────────────────────────
// Deploy your GovernanceContract to LocalNet and paste the App ID here.
export const APP_ID = 1014;

// ── SDK clients ─────────────────────────────────────────────────────
export const algodClient = new algosdk.Algodv2(ALGOD_TOKEN, ALGOD_SERVER, ALGOD_PORT);
export const indexerClient = new algosdk.Indexer(INDEXER_TOKEN, INDEXER_SERVER, INDEXER_PORT);
