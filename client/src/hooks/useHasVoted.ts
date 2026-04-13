import { useState, useEffect } from 'react';
import { hasApprovalVoted, hasElectionVoted } from '../algorand/governance-client';

export function useHasVoted(
  address: string | null,
  proposalId: string | undefined,
  type: 'approval' | 'election',
) {
  const [hasVoted, setHasVoted] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    if (!address || !proposalId) return;
    const numId = parseInt(proposalId, 10);
    if (isNaN(numId)) return;

    let cancelled = false;
    setChecking(true);
    const check = type === 'approval' ? hasApprovalVoted : hasElectionVoted;
    check(address, numId)
      .then((v) => { if (!cancelled) setHasVoted(v); })
      .finally(() => { if (!cancelled) setChecking(false); });

    return () => { cancelled = true; };
  }, [address, proposalId, type]);

  return { hasVoted, checking };
}
