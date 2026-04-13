import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, BadgeCheck, Keyboard, Wallet } from 'lucide-react';
import { Link } from 'react-router-dom';
import { RankingList } from '../components/vote/RankingList';
import { VoteReceipt } from '../components/vote/VoteReceipt';
import { Button } from '../components/ui/Button';
import { useProposal } from '../hooks/useProposal';
import { useAlgorand } from '../hooks/useAlgorand';
import { useHasVoted } from '../hooks/useHasVoted';
import { castRankedVote } from '../algorand/governance-client';
import type { ProposalOption } from '../mocks/fixtures';

export function VotePage() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { proposal, loading, error } = useProposal(id);
  const { isConnected, address, signer } = useAlgorand();
  const { hasVoted } = useHasVoted(address, id, 'election');

  const [options, setOptions] = useState<ProposalOption[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<{ txId: string; ranking: ProposalOption[] } | null>(null);

  // Initialise options once the proposal loads
  useEffect(() => {
    if (proposal) setOptions(proposal.options);
  }, [proposal?.id]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-14">
        <div className="mb-6 h-5 w-20 animate-pulse rounded-full bg-surface" />
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-2xl bg-surface" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !proposal) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-20 text-center text-muted">
        {error ?? 'Proposal not found.'}
      </div>
    );
  }

  const handleSubmit = async () => {
    if (!isConnected || !address) return;

    const proposalId = parseInt(proposal.id, 10);
    // preferenceOrder: indices of the original options in ranked order
    const preferenceOrder = options.map((o) => parseInt(o.id, 10));

    setSubmitting(true);
    setSubmitError(null);

    try {
      const txId = await castRankedVote(signer, address, proposalId, preferenceOrder);
      setReceipt({ txId, ranking: options });
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : 'Transaction failed. Please try again.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-6 py-14">
      <button
        onClick={() => navigate(-1)}
        className="mb-6 inline-flex items-center gap-2 text-sm text-muted transition hover:text-fg"
      >
        <ArrowLeft size={16} /> {t('common.back')}
      </button>

      <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted">
        {proposal.title}
      </div>
      <h1 className="font-display text-4xl font-bold tracking-tight text-fg sm:text-5xl">
        {t('vote.title')}
      </h1>
      <p className="mt-3 max-w-xl text-muted">{t('vote.subtitle')}</p>

      {hasVoted ? (
        <div className="mt-10 flex flex-col items-center gap-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-10 text-center">
          <BadgeCheck size={36} className="text-emerald-500" />
          <p className="text-lg font-semibold text-emerald-500">{t('vote.alreadyVoted')}</p>
          <p className="text-sm text-muted">{t('vote.alreadyVotedHint')}</p>
          <Link
            to={`/proposals/${proposal.id}/results`}
            className="mt-2 inline-flex h-10 items-center gap-2 rounded-full border border-border px-5 text-sm font-medium text-muted transition hover:text-fg"
          >
            {t('proposal.resultsCta')}
          </Link>
        </div>
      ) : (
        <>
          <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted">
            <Keyboard size={14} /> {t('vote.keyboardHint')}
          </div>

          <div className="mt-8">
            <RankingList options={options} onChange={setOptions} />
          </div>

          {submitError && (
            <p className="mt-4 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-500">
              {submitError}
            </p>
          )}

          <div className="mt-10 flex items-center justify-end gap-3">
            {!isConnected && (
              <span className="flex items-center gap-1.5 text-sm text-muted">
                <Wallet size={14} /> Connect your wallet to vote
              </span>
            )}
            <Button
              size="lg"
              onClick={handleSubmit}
              disabled={!isConnected || submitting}
            >
              {submitting ? 'Waiting for signature…' : t('vote.submit')}
            </Button>
          </div>
        </>
      )}

      {receipt && (
        <VoteReceipt
          open={true}
          onClose={() => {
            setReceipt(null);
            navigate(`/proposals/${proposal.id}/results`);
          }}
          proposalTitle={proposal.title}
          ranking={receipt.ranking}
          txId={receipt.txId}
        />
      )}
    </div>
  );
}
