import { BallotBoxHero } from '../components/landing/BallotBoxHero';
import { VoicesChorusHero } from '../components/landing/VoicesChorusHero';
import { RippleMapHero } from '../components/landing/RippleMapHero';
import { TallyMarksHero } from '../components/landing/TallyMarksHero';
import { VoteBloomHero } from '../components/landing/VoteBloomHero';
import { LandingShell } from '../components/landing/LandingShell';

export function LandingPage() {
  return <LandingShell variant="v1" hero={<BallotBoxHero />} />;
}

export function LandingPageV2() {
  return <LandingShell variant="v2" hero={<VoicesChorusHero />} />;
}

export function LandingPageV3() {
  return <LandingShell variant="v3" hero={<RippleMapHero />} />;
}

export function LandingPageV4() {
  return <LandingShell variant="v4" hero={<TallyMarksHero />} />;
}

export function LandingPageV5() {
  return <LandingShell variant="v5" hero={<VoteBloomHero />} />;
}
