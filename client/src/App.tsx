import { Route, Routes } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import {
  LandingPage,
  LandingPageV2,
  LandingPageV3,
  LandingPageV4,
  LandingPageV5,
} from './pages/LandingPage';
import { ProposalsPage } from './pages/ProposalsPage';
import { ProposalDetailPage } from './pages/ProposalDetailPage';
import { NewProposalPage } from './pages/NewProposalPage';
import { VotePage } from './pages/VotePage';
import { ResultsPage } from './pages/ResultsPage';

export default function App() {
  return (
    <div className="flex min-h-full flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/v2" element={<LandingPageV2 />} />
          <Route path="/v3" element={<LandingPageV3 />} />
          <Route path="/v4" element={<LandingPageV4 />} />
          <Route path="/v5" element={<LandingPageV5 />} />
          <Route path="/proposals" element={<ProposalsPage />} />
          <Route path="/proposals/new" element={<NewProposalPage />} />
          <Route path="/proposals/:id" element={<ProposalDetailPage />} />
          <Route path="/proposals/:id/vote" element={<VotePage />} />
          <Route path="/proposals/:id/results" element={<ResultsPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
