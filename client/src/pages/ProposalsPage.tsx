import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Plus, Search, RefreshCw } from 'lucide-react';
import type { ProposalStatus } from '../mocks/fixtures';
import { ProposalCard } from '../components/proposal/ProposalCard';
import { useProposals } from '../hooks/useProposals';

type Filter = 'active' | 'all' | ProposalStatus;
const FILTERS: Filter[] = ['active', 'pending', 'approved', 'voting', 'closed', 'all'];

export function ProposalsPage() {
  const { t } = useTranslation();
  const [filter, setFilter] = useState<Filter>('active');
  const [query, setQuery] = useState('');
  const { proposals, loading, error, refetch } = useProposals();

  const filtered = proposals.filter((p) => {
    if (filter === 'active' && p.status === 'closed') return false;
    if (filter !== 'active' && filter !== 'all' && p.status !== filter) return false;
    if (query && !p.title.toLowerCase().includes(query.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="mx-auto max-w-7xl px-6 py-14">
      <div className="mb-10 flex flex-wrap items-end justify-between gap-6">
        <div>
          <h1 className="font-display text-4xl font-bold tracking-tight text-fg sm:text-5xl">
            {t('proposals.title')}
          </h1>
          <p className="mt-2 text-muted">{t('proposals.subtitle')}</p>
        </div>
        <Link
          to="/proposals/new"
          className="inline-flex h-11 items-center gap-2 rounded-full bg-gradient-to-br from-primary to-accent px-5 text-sm font-semibold text-primary-fg shadow-glow transition hover:brightness-110"
        >
          <Plus size={16} />
          {t('proposals.new')}
        </Link>
      </div>

      <div className="mb-8 flex flex-wrap items-center gap-3">
        <div className="relative min-w-[240px] flex-1">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('common.search')}
            className="h-11 w-full rounded-full border border-border bg-surface pl-11 pr-4 text-sm text-fg placeholder:text-muted focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`h-10 rounded-full border px-4 text-sm font-medium transition ${
                filter === f
                  ? 'border-primary bg-primary text-primary-fg'
                  : 'border-border bg-surface text-muted hover:text-fg'
              }`}
            >
              {t(`proposals.filters.${f}`)}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-2xl border border-border bg-surface" />
          ))}
        </div>
      )}

      {error && !loading && (
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border p-12 text-center">
          <p className="text-sm text-muted">{error}</p>
          <button
            onClick={refetch}
            className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-sm text-muted transition hover:text-fg"
          >
            <RefreshCw size={14} /> Retry
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="rounded-2xl border border-dashed border-border p-12 text-center text-muted">
          {t('proposals.empty')}
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <ProposalCard key={p.id} proposal={p} />
          ))}
        </div>
      )}
    </div>
  );
}
