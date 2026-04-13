import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, ArrowRight, Plus, Trash2, Check, Wallet } from 'lucide-react';
import { Field, Input, Textarea } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { useAlgorand } from '../hooks/useAlgorand';
import { createProposal } from '../algorand/governance-client';

const STEPS = ['basics', 'dates', 'options', 'review'] as const;

const APPROVAL_BUFFER_DAYS = 3;

function dateToUnix(dateStr: string): number {
  return Math.floor(new Date(dateStr).getTime() / 1000);
}

function minStartDate(): string {
  //const d = new Date();
  //d.setDate(d.getDate() + APPROVAL_BUFFER_DAYS);
  //return d.toISOString().slice(0, 10);
  return new Date().toISOString().slice(0, 10);
}

export function NewProposalPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isConnected, address, signer } = useAlgorand();

  const [step, setStep] = useState(0);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [options, setOptions] = useState(['', '']);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const canNext = (() => {
    if (step === 0) return title.trim() && description.trim();
    if (step === 1) {
      if (!start || !end) return false;
      if (start < minStartDate()) return false;
      if (end <= start) return false;
      return true;
    }
    if (step === 2) return options.filter((o) => o.trim()).length >= 2;
    return true;
  })();

  const handleSubmit = async () => {
    if (!isConnected || !address) return;

    setSubmitting(true);
    setSubmitError(null);

    try {
      const cleanOptions = options.filter((o) => o.trim());
      const { proposalId } = await createProposal(
        signer,
        address,
        title.trim(),
        description.trim(),
        cleanOptions,
        dateToUnix(start),
        dateToUnix(end),
      );
      navigate(`/proposals/${proposalId}`);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : 'Transaction failed. Please try again.',
      );
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-6 py-14">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">
        {t('newProposal.step', { current: step + 1, total: STEPS.length })}
      </div>
      <h1 className="mb-8 font-display text-4xl font-bold tracking-tight text-fg sm:text-5xl">
        {t('newProposal.title')}
      </h1>

      {/* Step indicator */}
      <div className="mb-10 flex items-center gap-2">
        {STEPS.map((s, i) => (
          <div key={s} className="flex flex-1 items-center gap-2">
            <div
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition ${
                i <= step
                  ? 'bg-gradient-to-br from-primary to-accent text-primary-fg'
                  : 'border border-border bg-surface text-muted'
              }`}
            >
              {i < step ? <Check size={14} /> : i + 1}
            </div>
            <div className="text-xs text-muted">{t(`newProposal.steps.${s}`)}</div>
            {i < STEPS.length - 1 && <div className="h-px flex-1 bg-border" />}
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-surface p-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            {step === 0 && (
              <>
                <Field label={t('newProposal.fields.title')}>
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder={t('newProposal.fields.titlePlaceholder')}
                  />
                </Field>
                <Field label={t('newProposal.fields.description')}>
                  <Textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder={t('newProposal.fields.descriptionPlaceholder')}
                    rows={5}
                  />
                </Field>
              </>
            )}

            {step === 1 && (
              <div className="space-y-4">
                <div className="grid gap-6 sm:grid-cols-2">
                  <Field label={t('newProposal.fields.start')}>
                    <Input
                      type="date"
                      value={start}
                      min={minStartDate()}
                      onChange={(e) => setStart(e.target.value)}
                    />
                  </Field>
                  <Field label={t('newProposal.fields.end')}>
                    <Input
                      type="date"
                      value={end}
                      min={start || minStartDate()}
                      onChange={(e) => setEnd(e.target.value)}
                    />
                  </Field>
                </div>
                <p className="text-xs text-muted">
                  Start date must be at least {APPROVAL_BUFFER_DAYS} days from today to allow the approval voting window.
                </p>
                {start && start < minStartDate() && (
                  <p className="text-xs text-rose-500">
                    Start date must be on or after {minStartDate()}.
                  </p>
                )}
                {start && end && end <= start && (
                  <p className="text-xs text-rose-500">End date must be after the start date.</p>
                )}
              </div>
            )}

            {step === 2 && (
              <div className="space-y-3">
                {options.map((opt, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                      {i + 1}
                    </span>
                    <Input
                      value={opt}
                      onChange={(e) => {
                        const next = [...options];
                        next[i] = e.target.value;
                        setOptions(next);
                      }}
                      placeholder={t('newProposal.fields.optionPlaceholder')}
                    />
                    {options.length > 2 && (
                      <button
                        type="button"
                        onClick={() => setOptions(options.filter((_, idx) => idx !== i))}
                        className="flex h-10 w-10 items-center justify-center rounded-full text-muted transition hover:bg-bg hover:text-rose-500"
                        aria-label={t('newProposal.fields.removeOption')}
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => setOptions([...options, ''])}
                  className="inline-flex h-10 items-center gap-2 rounded-full border border-dashed border-border px-4 text-sm text-muted transition hover:border-primary hover:text-primary"
                >
                  <Plus size={14} /> {t('newProposal.fields.addOption')}
                </button>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-5">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted">
                    {t('common.title')}
                  </div>
                  <div className="mt-1 font-display text-xl text-fg">{title || '—'}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted">
                    {t('common.description')}
                  </div>
                  <p className="mt-1 text-sm text-muted">{description || '—'}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-muted">
                      {t('common.startDate')}
                    </div>
                    <div className="mt-1 text-sm text-fg">{start || '—'}</div>
                  </div>
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-muted">
                      {t('common.endDate')}
                    </div>
                    <div className="mt-1 text-sm text-fg">{end || '—'}</div>
                  </div>
                </div>
                <div>
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted">
                    {t('common.options')}
                  </div>
                  <ul className="space-y-2">
                    {options
                      .filter((o) => o.trim())
                      .map((opt, i) => (
                        <li
                          key={i}
                          className="flex items-center gap-3 rounded-xl border border-border bg-elevated px-4 py-2 text-sm text-fg"
                        >
                          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                            {i + 1}
                          </span>
                          {opt}
                        </li>
                      ))}
                  </ul>
                </div>

                {submitError && (
                  <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-500">
                    {submitError}
                  </p>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        <div className="mt-10 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0 || submitting}
            leftIcon={<ArrowLeft size={16} />}
          >
            {t('common.previous')}
          </Button>

          {step < STEPS.length - 1 ? (
            <Button
              onClick={() => setStep((s) => s + 1)}
              disabled={!canNext}
              rightIcon={<ArrowRight size={16} />}
            >
              {t('common.next')}
            </Button>
          ) : !isConnected ? (
            <span className="flex items-center gap-1.5 text-sm text-muted">
              <Wallet size={14} /> Connect your wallet to submit
            </span>
          ) : (
            <Button
              rightIcon={<Check size={16} />}
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? 'Waiting for signature…' : t('newProposal.submit')}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
