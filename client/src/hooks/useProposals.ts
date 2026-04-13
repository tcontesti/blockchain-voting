import { useState, useEffect, useCallback } from 'react';
import { getAllProposalIds, getProposal, getApprovalTally } from '../algorand/governance-client';
import { toFrontendProposal } from '../algorand/types';
import type { Proposal } from '../mocks/fixtures';

interface UseProposalsResult {
  proposals: Proposal[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useProposals(): UseProposalsResult {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const ids = await getAllProposalIds();

        const results = await Promise.all(
          ids.map(async (id) => {
            const [onChain, tally] = await Promise.all([
              getProposal(id),
              getApprovalTally(id),
            ]);
            if (!onChain || !tally) return null;
            return toFrontendProposal(id, onChain, tally);
          }),
        );

        if (!cancelled) {
          setProposals(results.filter((p): p is Proposal => p !== null));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load proposals');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [tick]);

  return { proposals, loading, error, refetch };
}
