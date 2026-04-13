import { useState, useEffect, useCallback } from 'react';
import { getElectionVoterCount } from '../algorand/governance-client';

export function useElectionVoterCount(proposalId: string | undefined, live = false) {
  const [count, setCount] = useState(0);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!proposalId) return;
    const numId = parseInt(proposalId, 10);
    if (isNaN(numId)) return;

    let cancelled = false;
    getElectionVoterCount(numId).then((n) => { if (!cancelled) setCount(n); });
    return () => { cancelled = true; };
  }, [proposalId, tick]);

  // Poll every 10 s while the election is live
  useEffect(() => {
    if (!live) return;
    const interval = setInterval(() => setTick((t) => t + 1), 10_000);
    return () => clearInterval(interval);
  }, [live]);

  return { count, refetch };
}
