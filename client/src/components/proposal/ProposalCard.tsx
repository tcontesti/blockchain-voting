import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { Proposal } from '../../mocks/fixtures';
import { formatDate } from '../../mocks/fixtures';
import { ApprovalBar } from './ApprovalBar';
import { StatusBadge } from './StatusBadge';

export function ProposalCard({ proposal }: { proposal: Proposal }) {
  const { t, i18n } = useTranslation();
  const locale = i18n.resolvedLanguage ?? 'en';
  const pct = proposal.approval.total > 0
    ? Math.round((proposal.approval.yes / proposal.approval.total) * 100)
    : 0;

  return (
    <Link
      to={`/proposals/${proposal.id}`}
      className="group flex flex-col rounded-2xl border border-border/70 bg-surface/80 p-6 transition hover:-translate-y-0.5 hover:border-primary/60 hover:shadow-glow"
    >
      <StatusBadge status={proposal.status} />

      <h3 className="mt-4 font-display text-lg font-semibold text-fg group-hover:text-primary">
        {proposal.title}
      </h3>
      <p className="mt-1.5 line-clamp-2 text-sm text-muted">{proposal.description}</p>

      <div className="mt-5 flex items-center justify-between text-xs text-muted">
        <span>{formatDate(proposal.endDate, locale)}</span>
        <span className="tabular-nums">
          {pct}% · {t('proposals.card.options', { count: proposal.options.length })}
        </span>
      </div>
      <div className="mt-2">
        <ApprovalBar yes={proposal.approval.yes} total={proposal.approval.total} compact />
      </div>
    </Link>
  );
}
