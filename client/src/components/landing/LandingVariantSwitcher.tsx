import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import type { LandingVariant } from './LandingShell';

const VARIANTS = [
  { id: 'v1', to: '/', label: 'Ballot box' },
  { id: 'v2', to: '/v2', label: 'Chorus' },
  { id: 'v3', to: '/v3', label: 'Ripple map' },
  { id: 'v4', to: '/v4', label: 'Tally' },
  { id: 'v5', to: '/v5', label: 'Bloom' },
] as const;

export function LandingVariantSwitcher({ current }: { current: LandingVariant }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4, duration: 0.5 }}
      className="pointer-events-none fixed inset-x-0 bottom-6 z-40 flex justify-center px-4"
    >
      <div className="pointer-events-auto flex items-center gap-1 rounded-full border border-border/80 bg-elevated/90 p-1.5 shadow-xl backdrop-blur-xl">
        <div className="px-2 text-[10px] font-semibold uppercase tracking-wider text-muted">
          Landing
        </div>
        {VARIANTS.map((v) => {
          const active = current === v.id;
          return (
            <Link
              key={v.id}
              to={v.to}
              className={`relative rounded-full px-3 py-1.5 text-xs font-medium transition ${
                active ? 'text-primary-fg' : 'text-muted hover:text-fg'
              }`}
            >
              {active && (
                <motion.span
                  layoutId="variant-active"
                  className="absolute inset-0 -z-10 rounded-full bg-gradient-to-br from-primary to-accent shadow-glow"
                  transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                />
              )}
              {v.label}
            </Link>
          );
        })}
      </div>
    </motion.div>
  );
}
