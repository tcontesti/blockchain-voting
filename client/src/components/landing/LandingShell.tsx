import type { ReactNode } from 'react';
import { HowItWorks } from './HowItWorks';
import { FeatureGrid } from './FeatureGrid';
import { CTASection } from './CTASection';
import { LandingVariantSwitcher } from './LandingVariantSwitcher';

export type LandingVariant = 'v1' | 'v2' | 'v3' | 'v4' | 'v5';

export function LandingShell({ hero, variant }: { hero: ReactNode; variant: LandingVariant }) {
  return (
    <>
      {hero}
      <HowItWorks />
      <FeatureGrid />
      <CTASection />
      <LandingVariantSwitcher current={variant} />
    </>
  );
}
