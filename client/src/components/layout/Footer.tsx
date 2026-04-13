import { useTranslation } from 'react-i18next';

export function Footer() {
  const { t } = useTranslation();
  return (
    <footer className="border-t border-border/60 bg-surface/40">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 py-8 text-sm text-muted md:flex-row">
        <div className="flex items-center gap-2">
          <span className="font-display text-fg">{t('brand')}</span>
          <span>· {t('landing.footer.tagline')}</span>
        </div>
        <div>© {new Date().getFullYear()} · {t('landing.footer.rights')}</div>
      </div>
    </footer>
  );
}
