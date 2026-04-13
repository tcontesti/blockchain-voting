import algosdk from 'algosdk';
import { APP_ID, algodClient } from './config';
import type { OnChainProposal, OnChainApprovalTally } from './types';
import arc56 from './GovernanceContract.arc56.json';

// ── ARC-56 error decoder ────────────────────────────────────────────
// algod returns "assert failed pc=360" — map the PC back to the
// human-readable message stored in the ARC-56 sourceInfo.

const _pcErrorMap = new Map<number, string>();
for (const entry of arc56.sourceInfo.approval.sourceInfo) {
  for (const pc of entry.pc) {
    _pcErrorMap.set(pc, entry.errorMessage);
  }
}

function decodeContractError(err: unknown): Error {
  const raw = err instanceof Error ? err.message : String(err);
  const match = raw.match(/\bpc=(\d+)/);
  if (match) {
    const msg = _pcErrorMap.get(parseInt(match[1], 10));
    if (msg) return new Error(msg);
  }
  return err instanceof Error ? err : new Error(raw);
}

type TransactionSigner = algosdk.TransactionSigner;

// ── Box key helpers ─────────────────────────────────────────────────
// Prefixes decoded from ARC-56 base64 values:
//   proposals:        "proposals" (cHJvcG9zYWxz)
//   approval_tallies: "at_"       (YXRf)
//   approval_ballots: "ab_"       (YWJf)
//   election_ballots: "eb_"       (ZWJf)

const enc = new TextEncoder();

function proposalBoxKey(id: number): Uint8Array {
  return new Uint8Array([...enc.encode('proposals'), ...algosdk.bigIntToBytes(id, 8)]);
}

function tallyBoxKey(id: number): Uint8Array {
  return new Uint8Array([...enc.encode('at_'), ...algosdk.bigIntToBytes(id, 8)]);
}

function approvalBallotKey(sender: string, proposalId: number): Uint8Array {
  return new Uint8Array([
    ...enc.encode('ab_'),
    ...algosdk.decodeAddress(sender).publicKey,
    ...algosdk.bigIntToBytes(proposalId, 8),
  ]);
}

function electionBallotKey(sender: string, proposalId: number): Uint8Array {
  return new Uint8Array([
    ...enc.encode('eb_'),
    ...algosdk.decodeAddress(sender).publicKey,
    ...algosdk.bigIntToBytes(proposalId, 8),
  ]);
}

// ── ABI method definitions ──────────────────────────────────────────
// Matches the ARC-56 method signatures exactly.

const createProposalMethod = new algosdk.ABIMethod({
  name: 'create_proposal',
  args: [
    { type: 'string', name: 'title' },
    { type: 'string', name: 'description' },
    { type: 'string[]', name: 'options' },
    { type: 'uint64', name: 'starting_date' },
    { type: 'uint64', name: 'ending_date' },
  ],
  returns: { type: 'uint64' },
});

const castProposalVoteMethod = new algosdk.ABIMethod({
  name: 'cast_proposal_vote',
  args: [
    { type: 'uint64', name: 'proposal_id' },
    { type: 'bool', name: 'approve' },
  ],
  returns: { type: 'void' },
});

const castElectionVoteMethod = new algosdk.ABIMethod({
  name: 'cast_election_vote',
  args: [
    { type: 'uint64', name: 'proposal_id' },
    { type: 'uint8[]', name: 'preference_order' },
  ],
  returns: { type: 'void' },
});

// ── Helper: execute an ABI method call via ATC ──────────────────────

async function callMethod(
  signer: TransactionSigner,
  sender: string,
  method: algosdk.ABIMethod,
  methodArgs: algosdk.ABIValue[],
  boxes: { appIndex: number; name: Uint8Array }[] = [],
): Promise<algosdk.ABIResult> {
  const suggestedParams = await algodClient.getTransactionParams().do();

  const composer = new algosdk.AtomicTransactionComposer();
  composer.addMethodCall({
    appID: APP_ID,
    method,
    methodArgs,
    sender,
    signer,
    suggestedParams,
    boxes,
  });

  try {
    const result = await composer.execute(algodClient, 4);
    return result.methodResults[0];
  } catch (err) {
    throw decodeContractError(err);
  }
}

// ── Write operations ────────────────────────────────────────────────

export async function createProposal(
  signer: TransactionSigner,
  sender: string,
  title: string,
  description: string,
  options: string[],
  startingDate: number,
  endingDate: number,
): Promise<{ proposalId: number; txId: string }> {
  // Derive next ID from existing proposal boxes — avoids fragile global state parsing.
  const existingIds = await getAllProposalIds();
  const nextId = existingIds.length > 0 ? Math.max(...existingIds) + 1 : 1;

  const result = await callMethod(
    signer,
    sender,
    createProposalMethod,
    [title, description, options, BigInt(startingDate), BigInt(endingDate)],
    [
      { appIndex: APP_ID, name: proposalBoxKey(nextId) },
      { appIndex: APP_ID, name: tallyBoxKey(nextId) },
    ],
  );

  const proposalId = Number(result.returnValue as bigint);
  return { proposalId, txId: result.txID };
}

export async function castApprovalVote(
  signer: TransactionSigner,
  sender: string,
  proposalId: number,
  approve: boolean,
): Promise<string> {
  const result = await callMethod(
    signer,
    sender,
    castProposalVoteMethod,
    [BigInt(proposalId), approve],
    [
      { appIndex: APP_ID, name: proposalBoxKey(proposalId) },
      { appIndex: APP_ID, name: tallyBoxKey(proposalId) },
      { appIndex: APP_ID, name: approvalBallotKey(sender, proposalId) },
    ],
  );
  return result.txID;
}

export async function castRankedVote(
  signer: TransactionSigner,
  sender: string,
  proposalId: number,
  preferenceOrder: number[],
): Promise<string> {
  const result = await callMethod(
    signer,
    sender,
    castElectionVoteMethod,
    [BigInt(proposalId), preferenceOrder.map((n) => BigInt(n))],
    [
      { appIndex: APP_ID, name: proposalBoxKey(proposalId) },
      { appIndex: APP_ID, name: tallyBoxKey(proposalId) },
      { appIndex: APP_ID, name: electionBallotKey(sender, proposalId) },
    ],
  );
  return result.txID;
}

// ── Has-voted checks ───────────────────────────────────────────────

// Check box existence via the boxes list — avoids 404 console errors from direct reads.
async function boxExists(key: Uint8Array): Promise<boolean> {
  try {
    const { boxes } = await algodClient.getApplicationBoxes(APP_ID).do();
    return boxes.some(
      (b) => b.name.length === key.length && b.name.every((byte, i) => byte === key[i]),
    );
  } catch {
    return false;
  }
}

export async function hasApprovalVoted(sender: string, proposalId: number): Promise<boolean> {
  return boxExists(approvalBallotKey(sender, proposalId));
}

export async function hasElectionVoted(sender: string, proposalId: number): Promise<boolean> {
  return boxExists(electionBallotKey(sender, proposalId));
}

// ── Election ballot reader ──────────────────────────────────────────
// Returns all ranked-preference ballots for a proposal as number[][].
// Each inner array is the voter's option indices in preference order.

export async function getElectionVoterCount(proposalId: number): Promise<number> {
  try {
    const boxes = await algodClient.getApplicationBoxes(APP_ID).do();
    const prefix = enc.encode('eb_');
    const pidBytes = algosdk.bigIntToBytes(proposalId, 8);
    return boxes.boxes.filter(
      (b) =>
        b.name.length === 43 &&
        b.name.slice(0, 3).every((byte, i) => byte === prefix[i]) &&
        b.name.slice(35).every((byte, i) => byte === pidBytes[i]),
    ).length;
  } catch {
    return 0;
  }
}

export async function getElectionBallots(proposalId: number): Promise<number[][]> {
  try {
    const boxes = await algodClient.getApplicationBoxes(APP_ID).do();
    const prefix = enc.encode('eb_');                          // 3 bytes
    const pidBytes = algosdk.bigIntToBytes(proposalId, 8);    // 8 bytes

    const ballotBoxNames = boxes.boxes
      .map((b) => b.name)
      .filter(
        (name) =>
          name.length === 43 &&
          name.slice(0, 3).every((b, i) => b === prefix[i]) &&
          name.slice(35).every((b, i) => b === pidBytes[i]),
      );

    const ballots = await Promise.all(
      ballotBoxNames.map(async (name) => {
        const box = await algodClient.getApplicationBoxByName(APP_ID, name).do();
        return decodePreferenceOrder(box.value);
      }),
    );

    return ballots;
  } catch {
    return [];
  }
}

// ── Read operations ─────────────────────────────────────────────────

async function getCurrentProposalId(): Promise<number> {
  try {
    const app = await algodClient.getApplicationByID(APP_ID).do();
    const globalState = (app.params?.globalState ?? []) as unknown as {
      key: string;
      value: { type: number; uint: bigint | number };
    }[];

    // The key is base64-encoded "proposal_id"
    const proposalIdKey = btoa('proposal_id');
    const entry = globalState.find((kv) => kv.key === proposalIdKey);
    return entry ? Number(entry.value.uint) : 0;
  } catch {
    return 0;
  }
}

export async function getProposal(proposalId: number): Promise<OnChainProposal | null> {
  try {
    const box = await algodClient.getApplicationBoxByName(APP_ID, proposalBoxKey(proposalId)).do();
    return decodeProposal(box.value);
  } catch {
    return null;
  }
}

export async function getApprovalTally(proposalId: number): Promise<OnChainApprovalTally | null> {
  try {
    const box = await algodClient.getApplicationBoxByName(APP_ID, tallyBoxKey(proposalId)).do();
    return decodeTally(box.value);
  } catch {
    return null;
  }
}

export async function getAllProposalIds(): Promise<number[]> {
  try {
    const boxes = await algodClient.getApplicationBoxes(APP_ID).do();
    const proposalPrefix = enc.encode('proposals'); // 9 bytes
    const ids: number[] = [];

    for (const box of boxes.boxes) {
      // proposals box names are 17 bytes: "proposals" (9) + uint64 (8)
      if (
        box.name.length === 17 &&
        box.name.slice(0, 9).every((b, i) => b === proposalPrefix[i])
      ) {
        const id = Number(algosdk.bytesToBigInt(box.name.slice(9)));
        if (id > 0) ids.push(id);
      }
    }

    return ids.sort((a, b) => a - b);
  } catch {
    return [];
  }
}

// ── ABI decoders ────────────────────────────────────────────────────
// Proposal ARC-4 type: (string, string, string[], uint64, uint64)
// ApprovalTally ARC-4 type: (uint32, uint32)

function decodeProposal(data: Uint8Array): OnChainProposal {
  const type = algosdk.ABIType.from('(string,string,string[],uint64,uint64)');
  const decoded = type.decode(data) as [string, string, string[], bigint, bigint];

  return {
    title: decoded[0],
    description: decoded[1],
    options: decoded[2],
    startingDate: Number(decoded[3]),
    endingDate: Number(decoded[4]),
  };
}

function decodePreferenceOrder(data: Uint8Array): number[] {
  const type = algosdk.ABIType.from('uint8[]');
  const decoded = type.decode(data) as bigint[];
  return decoded.map(Number);
}

function decodeTally(data: Uint8Array): OnChainApprovalTally {
  const type = algosdk.ABIType.from('(uint32,uint32)');
  const decoded = type.decode(data) as [bigint, bigint];

  return {
    votesFor: Number(decoded[0]),
    totalVotes: Number(decoded[1]),
  };
}
