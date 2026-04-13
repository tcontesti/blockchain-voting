import { useState, useEffect, useCallback } from 'react';
import { getProposal, getApprovalTally } from '../algorand/governance-client';
import { toFrontendProposal } from '../algorand/types';
import type { Proposal } from '../mocks/fixtures';

interface UseProposalResult {
  proposal: Proposal | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useProposal(id: string | undefined): UseProposalResult {
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!id) {
      setLoading(false);
      setProposal(null);
      return;
    }

    const numId = parseInt(id, 10);
    if (isNaN(numId)) {
      setLoading(false);
      setError('Invalid proposal ID');
      return;
    }

    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const [onChain, tally] = await Promise.all([
          getProposal(numId),
          getApprovalTally(numId),
        ]);

        if (!cancelled) {
          if (!onChain || !tally) {
            setProposal(null);
            setError('Proposal not found');
          } else {
            setProposal(toFrontendProposal(numId, onChain, tally));
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load proposal');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [id, tick]);

  return { proposal, loading, error, refetch };
}
