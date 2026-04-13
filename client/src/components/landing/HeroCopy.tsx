import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Sparkles } from 'lucide-react';

export function HeroCopy({ counter }: { counter: number }) {
  const { t } = useTranslation();
  return (
    <div className="relative z-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-surface/70 px-3 py-1.5 text-xs font-medium text-muted backdrop-blur"
      >
        <Sparkles size={14} className="text-primary" />
        {t('landing.hero.eyebrow')}
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.05 }}
        className="font-display text-5xl font-bold leading-[1.05] tracking-tight text-fg sm:text-6xl lg:text-7xl"
      >
        {t('landing.hero.titleA')}
        <br />
        <span className="grad-text">{t('landing.hero.titleB')}</span>
        <br />
        {t('landing.hero.titleC')}
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.15 }}
        className="mt-6 max-w-xl text-lg leading-relaxed text-muted"
      >
        {t('landing.hero.subtitle')}
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.25 }}
        className="mt-8 flex flex-wrap items-center gap-4"
      >
        <Link
          to="/proposals"
          className="inline-flex h-12 items-center justify-center gap-2 rounded-full bg-gradient-to-br from-primary to-accent px-6 text-sm font-semibold text-primary-fg shadow-glow transition hover:brightness-110"
        >
          {t('landing.hero.ctaPrimary')}
          <ArrowRight size={16} />
        </Link>
        <a
          href="#how"
          className="inline-flex h-12 items-center justify-center rounded-full border border-border bg-surface px-6 text-sm font-semibold text-fg transition hover:border-primary hover:text-primary"
        >
          {t('landing.hero.ctaSecondary')}
        </a>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.35 }}
        className="mt-10 flex items-center gap-3 text-sm text-muted"
      >
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
        </span>
        <span>
          <span className="tabular-nums font-semibold text-fg">{counter.toLocaleString()}</span>{' '}
          {t('landing.hero.counter')}
        </span>
      </motion.div>
    </div>
  );
}

export function HeroBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10">
      <div className="absolute -left-40 top-0 h-[520px] w-[520px] rounded-full bg-primary/20 blur-3xl" />
      <div className="absolute -right-40 top-40 h-[520px] w-[520px] rounded-full bg-accent/20 blur-3xl" />
    </div>
  );
}
