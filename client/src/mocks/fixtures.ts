export type ProposalStatus = 'pending' | 'approved' | 'voting' | 'closed';

export interface ProposalOption {
  id: string;
  title: string;
  description?: string;
}

export interface Proposal {
  id: string;
  title: string;
  description: string;
  author: string;
  createdAt: string;
  startDate: string;
  endDate: string;
  status: ProposalStatus;
  approval: { yes: number; total: number };
  options: ProposalOption[];
  /** For closed/voting proposals: ranked results (index 0 = winner) */
  results?: { optionId: string; points: number; firstChoice: number }[];
}

export const proposals: Proposal[] = [
  {
    id: 'grant-2026',
    title: 'Community grant recipient 2026',
    description:
      'Choose which of the four finalist projects receives this year\'s community grant. Voters will rank all four in order of preference.',
    author: 'aina.eth',
    createdAt: '2026-03-12',
    startDate: '2026-04-15',
    endDate: '2026-04-22',
    status: 'voting',
    approval: { yes: 86, total: 120 },
    options: [
      { id: 'opt-a', title: 'Open archive for local press', description: 'An open archive of local journalism from the past 40 years.' },
      { id: 'opt-b', title: 'Neighborhood energy co-op', description: 'Seed funding for a shared rooftop solar network.' },
      { id: 'opt-c', title: 'After-school coding club', description: 'Weekly coding classes for public school students.' },
      { id: 'opt-d', title: 'Accessible transit mapping', description: 'Crowdsourced accessibility data for public transport.' },
    ],
  },
  {
    id: 'assembly-chair',
    title: 'Next assembly chair',
    description:
      'Pick the next chair of the neighborhood assembly for a one-year term. Candidates presented themselves at the March meetup.',
    author: 'roc.eth',
    createdAt: '2026-03-28',
    startDate: '2026-04-20',
    endDate: '2026-04-27',
    status: 'approved',
    approval: { yes: 94, total: 120 },
    options: [
      { id: 'c1', title: 'Marta Puig' },
      { id: 'c2', title: 'Adrià Font' },
      { id: 'c3', title: 'Leire Sanz' },
    ],
  },
  {
    id: 'library-hours',
    title: 'Extended library opening hours',
    description:
      'Should the central library stay open later on weekdays? Voters will rank the four schedule proposals drafted by the council.',
    author: 'nuria.eth',
    createdAt: '2026-04-02',
    startDate: '2026-04-25',
    endDate: '2026-05-02',
    status: 'pending',
    approval: { yes: 48, total: 120 },
    options: [
      { id: 'h1', title: 'Keep current hours' },
      { id: 'h2', title: 'Close at 21:00 weekdays' },
      { id: 'h3', title: 'Close at 22:00 weekdays' },
      { id: 'h4', title: '24h Wednesdays only' },
    ],
  },
  {
    id: 'park-name',
    title: 'Name for the new riverside park',
    description:
      'Four names were proposed by residents. The one with the highest ranking will be adopted by the council.',
    author: 'jordi.eth',
    createdAt: '2026-02-10',
    startDate: '2026-03-01',
    endDate: '2026-03-08',
    status: 'closed',
    approval: { yes: 102, total: 120 },
    options: [
      { id: 'p1', title: 'Parc del Meandre' },
      { id: 'p2', title: 'Parc Montserrat Roig' },
      { id: 'p3', title: 'Parc de la Confluència' },
      { id: 'p4', title: 'Parc dels Til·lers' },
    ],
    results: [
      { optionId: 'p2', points: 412, firstChoice: 58 },
      { optionId: 'p1', points: 361, firstChoice: 44 },
      { optionId: 'p3', points: 288, firstChoice: 12 },
      { optionId: 'p4', points: 219, firstChoice: 6 },
    ],
  },
];

export function getProposal(id: string | undefined): Proposal | undefined {
  return proposals.find((p) => p.id === id);
}

export function formatDate(iso: string, locale: string): string {
  try {
    return new Intl.DateTimeFormat(locale, { year: 'numeric', month: 'short', day: 'numeric' }).format(new Date(iso));
  } catch {
    return iso;
  }
}
