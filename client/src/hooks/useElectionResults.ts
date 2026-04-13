import { useState, useEffect, useCallback } from 'react';
import { getElectionBallots } from '../algorand/governance-client';

export interface OptionResult {
  optionId: string;
  firstChoiceVotes: number;
  finalRank: number; // 0 = winner
}

// Schulze method (Schwartz Sequential Dropping / path-strength variant).
//
// 1. Build pairwise matrix d[i][j] = #voters who prefer i over j.
// 2. Compute strongest-path matrix p[i][j] using Floyd-Warshall:
//    p[i][j] = max over all paths i→...→j of the minimum edge on the path.
//    Initialise: p[i][j] = d[i][j] if d[i][j] > d[j][i], else 0.
//    Propagate: p[i][j] = max(p[i][j], min(p[i][k], p[k][j])) for each k.
// 3. Rank: i beats j if p[i][j] > p[j][i]. Sort by number of options beaten.
function computeSchulze(ballots: number[][], numOptions: number): OptionResult[] {
  if (ballots.length === 0) return [];

  // Step 1: pairwise preference counts
  const d: number[][] = Array.from({ length: numOptions }, () => new Array(numOptions).fill(0));
  for (const ballot of ballots) {
    for (let rankI = 0; rankI < ballot.length; rankI++) {
      for (let rankJ = rankI + 1; rankJ < ballot.length; rankJ++) {
        const i = ballot[rankI]; // voter ranked i above j
        const j = ballot[rankJ];
        if (i < numOptions && j < numOptions) d[i][j]++;
      }
    }
  }

  // Step 2: strongest-path matrix (Floyd-Warshall)
  const p: number[][] = Array.from({ length: numOptions }, (_, i) =>
    Array.from({ length: numOptions }, (_, j) => {
      if (i === j) return 0;
      return d[i][j] > d[j][i] ? d[i][j] : 0;
    }),
  );

  for (let k = 0; k < numOptions; k++) {
    for (let i = 0; i < numOptions; i++) {
      for (let j = 0; j < numOptions; j++) {
        if (i === j) continue;
        p[i][j] = Math.max(p[i][j], Math.min(p[i][k], p[k][j]));
      }
    }
  }

  // Step 3: rank by number of options each candidate beats via strongest path
  const wins = Array.from({ length: numOptions }, (_, i) => {
    let count = 0;
    for (let j = 0; j < numOptions; j++) {
      if (i !== j && p[i][j] > p[j][i]) count++;
    }
    return { optionId: i, wins: count };
  });

  // Sort descending by wins; ties broken by option index (deterministic)
  wins.sort((a, b) => b.wins - a.wins || a.optionId - b.optionId);

  // First-choice counts (for display only — not used in Schulze ranking)
  const firstChoiceCounts = new Array(numOptions).fill(0);
  for (const ballot of ballots) {
    if (ballot.length > 0 && ballot[0] < numOptions) firstChoiceCounts[ballot[0]]++;
  }

  return wins.map(({ optionId }, rank) => ({
    optionId: String(optionId),
    firstChoiceVotes: firstChoiceCounts[optionId],
    finalRank: rank,
  }));
}

interface UseElectionResultsResult {
  results: OptionResult[];
  totalVoters: number;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useElectionResults(
  proposalId: string | undefined,
  numOptions: number,
): UseElectionResultsResult {
  const [results, setResults] = useState<OptionResult[]>([]);
  const [totalVoters, setTotalVoters] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!proposalId || numOptions === 0) return;
    const numId = parseInt(proposalId, 10);
    if (isNaN(numId)) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    async function load() {
      try {
        const ballots = await getElectionBallots(numId);
        if (!cancelled) {
          setResults(computeSchulze(ballots, numOptions));
          setTotalVoters(ballots.length);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load results');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [proposalId, numOptions, tick]);

  return { results, totalVoters, loading, error, refetch };
}
