import type { Proposal, ProposalStatus } from '../mocks/fixtures';

// ── On-chain types (matching the algopy ARC-4 structs) ──────────────
// ARC-56 Proposal struct: (string, string, string[], uint64, uint64)
// Head layout (22 bytes):
//   [0-1]  offset to title  (uint16)
//   [2-3]  offset to description (uint16)
//   [4-5]  offset to options (uint16)
//   [6-13] starting_date (uint64, inline)
//   [14-21] ending_date   (uint64, inline)

export interface OnChainProposal {
  title: string;
  description: string;
  options: string[];
  startingDate: number; // UNIX timestamp
  endingDate: number;   // UNIX timestamp
}

export interface OnChainApprovalTally {
  votesFor: number;
  totalVotes: number;
}

// ── Mapping on-chain → frontend ─────────────────────────────────────

function deriveStatus(
  tally: OnChainApprovalTally,
  startingDate: number,
  endingDate: number,
  now: number,
): ProposalStatus {
  const isApproved = tally.totalVotes > 0 && 3 * tally.votesFor >= 2 * tally.totalVotes;
  // Only treat as rejected if votes were actually cast and threshold wasn't met.
  // Zero votes = no decision yet → always pending, regardless of date.
  const isRejected = tally.totalVotes > 0 && !isApproved;

  if (now >= endingDate) return 'closed';
  if (isRejected) return 'closed';
  if (isApproved && now >= startingDate) return 'voting';
  if (isApproved) return 'approved';
  return 'pending';
}

export function toFrontendProposal(
  id: number,
  onChain: OnChainProposal,
  tally: OnChainApprovalTally,
): Proposal {
  const now = Math.floor(Date.now() / 1000);

  return {
    id: String(id),
    title: onChain.title,
    description: onChain.description,
    author: '',
    createdAt: '',
    startDate: new Date(onChain.startingDate * 1000).toISOString().slice(0, 10),
    endDate: new Date(onChain.endingDate * 1000).toISOString().slice(0, 10),
    status: deriveStatus(tally, onChain.startingDate, onChain.endingDate, now),
    approval: { yes: tally.votesFor, total: tally.totalVotes },
    options: onChain.options.map((title, i) => ({
      id: String(i),
      title,
    })),
  };
}
