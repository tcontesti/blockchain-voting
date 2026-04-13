import { useTranslation } from 'react-i18next';
import { Check } from 'lucide-react';

interface Props {
  yes: number;
  total: number;
  compact?: boolean;
}

export function ApprovalBar({ yes, total, compact = false }: Props) {
  const { t } = useTranslation();
  const pct = total > 0 ? (yes / total) * 100 : 0;
  const thresholdPct = 66.666;
  const reached = pct >= thresholdPct;

  return (
    <div className="w-full">
      {!compact && (
        <div className="mb-2 flex items-center justify-between text-xs">
          <span className="font-medium text-muted">{t('proposals.approval.label')}</span>
          <span className="tabular-nums text-muted">
            {yes} {t('proposals.approval.of')} {total}
          </span>
        </div>
      )}
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-border/70">
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-all ${
            reached ? 'bg-emerald-500' : 'bg-gradient-to-r from-primary to-accent'
          }`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
        {/* 2/3 marker */}
        <div
          className="absolute top-1/2 h-4 w-0.5 -translate-y-1/2 bg-fg/70"
          style={{ left: `${thresholdPct}%` }}
          aria-hidden
        />
      </div>
      {!compact && (
        <div className="mt-1.5 flex items-center justify-between text-xs">
          <span className="text-muted">{t('proposals.approval.threshold')}</span>
          {reached && (
            <span className="inline-flex items-center gap-1 font-medium text-emerald-500">
              <Check size={12} />
              {t('proposals.approval.reached')}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
