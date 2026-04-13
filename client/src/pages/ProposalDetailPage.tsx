import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, CalendarDays, Clock, RefreshCw, ThumbsUp, ThumbsDown, Wallet } from 'lucide-react';
import { formatDate } from '../mocks/fixtures';
import { ApprovalBar } from '../components/proposal/ApprovalBar';
import { StatusBadge } from '../components/proposal/StatusBadge';
import { useProposal } from '../hooks/useProposal';
import { useAlgorand } from '../hooks/useAlgorand';
import { useHasVoted } from '../hooks/useHasVoted';
import { castApprovalVote } from '../algorand/governance-client';

export function ProposalDetailPage() {
  const { id } = useParams();
  const { t, i18n } = useTranslation();
  const locale = i18n.resolvedLanguage ?? 'en';
  const navigate = useNavigate();
  const { proposal, loading, error, refetch } = useProposal(id);
  const { isConnected, address, signer } = useAlgorand();
  const { hasVoted: hasApprovalVoted } = useHasVoted(address, id, 'approval');
  const { hasVoted: hasElectionVoted } = useHasVoted(address, id, 'election');

  const [voting, setVoting] = useState<'approve' | 'reject' | null>(null);
  const [voteError, setVoteError] = useState<string | null>(null);
  const [votedTxId, setVotedTxId] = useState<string | null>(null);

  const handleApprovalVote = async (approve: boolean) => {
    if (!isConnected || !address || !proposal) return;

    setVoting(approve ? 'approve' : 'reject');
    setVoteError(null);

    try {
      const txId = await castApprovalVote(
        signer,
        address,
        parseInt(proposal.id, 10),
        approve,
      );
      setVotedTxId(txId);
      refetch();
    } catch (err) {
      setVoteError(err instanceof Error ? err.message : 'Transaction failed.');
    } finally {
      setVoting(null);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-14">
        <div className="mb-8 h-5 w-20 animate-pulse rounded-full bg-surface" />
        <div className="h-12 w-2/3 animate-pulse rounded-2xl bg-surface" />
        <div className="mt-10 grid gap-6 md:grid-cols-[1.5fr_1fr]">
          <div className="h-64 animate-pulse rounded-2xl bg-surface" />
          <div className="h-64 animate-pulse rounded-2xl bg-surface" />
        </div>
      </div>
    );
  }

  if (error || !proposal) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-20 text-center">
        <p className="mb-4 text-muted">{error ?? 'Proposal not found.'}</p>
        <button
          onClick={refetch}
          className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-sm text-muted transition hover:text-fg"
        >
          <RefreshCw size={14} /> Retry
        </button>
      </div>
    );
  }

  const voteCta = (() => {
    if (proposal.status === 'voting') {
      return { label: t('proposal.voteCta'), to: `/proposals/${proposal.id}/vote` };
    }
    if (proposal.status === 'closed') {
      return { label: t('proposal.resultsCta'), to: `/proposals/${proposal.id}/results` };
    }
    return null;
  })();

  return (
    <div className="mx-auto max-w-4xl px-6 py-14">
      <button
        onClick={() => navigate(-1)}
        className="mb-8 inline-flex items-center gap-2 text-sm text-muted transition hover:text-fg"
      >
        <ArrowLeft size={16} /> {t('common.back')}
      </button>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <StatusBadge status={proposal.status} />
      </div>

      <h1 className="font-display text-4xl font-bold tracking-tight text-fg sm:text-5xl">
        {proposal.title}
      </h1>

      <div className="mt-5 inline-flex items-center gap-2 text-sm text-muted">
        <CalendarDays size={14} />
        {formatDate(proposal.startDate, locale)} → {formatDate(proposal.endDate, locale)}
      </div>

      <div className="mt-10 grid gap-6 md:grid-cols-[1.5fr_1fr]">
        {/* Main content */}
        <div className="rounded-2xl border border-border bg-surface p-6">
          {proposal.description && (
            <>
              <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
                {t('proposal.summary')}
              </h2>
              <p className="leading-relaxed text-fg">{proposal.description}</p>
            </>
          )}

          <h2 className="mb-3 mt-8 text-xs font-semibold uppercase tracking-wider text-muted">
            {t('proposal.options')}
          </h2>
          <ul className="space-y-2">
            {proposal.options.map((opt, i) => (
              <li
                key={opt.id}
                className="flex items-start gap-3 rounded-xl border border-border bg-elevated px-4 py-3"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {i + 1}
                </span>
                <div>
                  <div className="text-sm font-medium text-fg">{opt.title}</div>
                  {opt.description && <div className="text-xs text-muted">{opt.description}</div>}
                </div>
              </li>
            ))}
          </ul>

        </div>

        {/* Sidebar */}
        <aside className="flex flex-col gap-5">
          <div className="rounded-2xl border border-border bg-surface p-6">
            <ApprovalBar yes={proposal.approval.yes} total={proposal.approval.total} />
          </div>

          {/* Approval voting (pending proposals) */}
          {proposal.status === 'pending' && (
            <div className="rounded-2xl border border-border bg-surface p-5">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">
                {t('proposal.approvalCta')}
              </h3>

              {votedTxId || hasApprovalVoted ? (
                <p className="text-sm text-emerald-500">
                  {t('proposal.alreadyVoted')} ✓
                </p>
              ) : !isConnected ? (
                <p className="flex items-center gap-1.5 text-sm text-muted">
                  <Wallet size={14} /> Connect wallet to vote
                </p>
              ) : (
                <div className="flex gap-3">
                  <button
                    onClick={() => handleApprovalVote(true)}
                    disabled={!!voting}
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 py-2.5 text-sm font-semibold text-emerald-600 transition hover:bg-emerald-500/20 disabled:opacity-50 dark:text-emerald-400"
                  >
                    <ThumbsUp size={15} />
                    {voting === 'approve' ? '…' : 'Approve'}
                  </button>
                  <button
                    onClick={() => handleApprovalVote(false)}
                    disabled={!!voting}
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-full border border-rose-500/40 bg-rose-500/10 py-2.5 text-sm font-semibold text-rose-600 transition hover:bg-rose-500/20 disabled:opacity-50 dark:text-rose-400"
                  >
                    <ThumbsDown size={15} />
                    {voting === 'reject' ? '…' : 'Reject'}
                  </button>
                </div>
              )}

              {voteError && (
                <p className="mt-3 text-xs text-rose-500">{voteError}</p>
              )}
            </div>
          )}

          {/* Approved but election not yet started */}
          {proposal.status === 'approved' && (
            <div className="flex flex-1 flex-col justify-center rounded-2xl border border-primary/30 bg-primary/5 p-5">
              <div className="mb-1.5 flex items-center gap-2 text-sm font-semibold text-primary">
                <Clock size={15} />
                {t('proposal.waitingToStart')}
              </div>
              <p className="text-sm text-muted">
                {t('proposal.votingOpensOn', { date: formatDate(proposal.startDate, locale) })}
              </p>
            </div>
          )}

          {/* CTA for voting/closed */}
          {voteCta && (
            proposal.status === 'closed' ? (
              <>
                <p className="text-sm text-muted">{t('proposal.closedNotice')}</p>
                <Link
                  to={voteCta.to}
                  className="inline-flex h-12 items-center justify-center rounded-full bg-gradient-to-br from-primary to-accent px-6 text-sm font-semibold text-primary-fg shadow-glow transition hover:brightness-110"
                >
                  {voteCta.label}
                </Link>
              </>
            ) : (
              <div className="flex flex-col gap-3">
                {hasElectionVoted ? (
                  <p className="text-sm text-emerald-500">{t('proposal.alreadyVoted')} ✓</p>
                ) : (
                  <Link
                    to={voteCta.to}
                    className="inline-flex h-12 items-center justify-center rounded-full bg-gradient-to-br from-primary to-accent px-6 text-sm font-semibold text-primary-fg shadow-glow transition hover:brightness-110"
                  >
                    {voteCta.label}
                  </Link>
                )}
                <Link
                  to={`/proposals/${proposal.id}/results`}
                  className="inline-flex h-10 items-center justify-center rounded-full border border-border px-6 text-sm font-medium text-muted transition hover:text-fg"
                >
                  {t('proposal.resultsCta')}
                </Link>
              </div>
            )
          )}
        </aside>
      </div>
    </div>
  );
}
