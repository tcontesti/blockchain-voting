import { useTranslation } from 'react-i18next';
import { Badge } from '../ui/Badge';
import type { ProposalStatus } from '../../mocks/fixtures';
import { Clock, CheckCircle2, Vote, Archive } from 'lucide-react';

const map = {
  pending: { tone: 'warning', icon: Clock },
  approved: { tone: 'primary', icon: CheckCircle2 },
  voting: { tone: 'success', icon: Vote },
  closed: { tone: 'neutral', icon: Archive },
} as const;

export function StatusBadge({ status }: { status: ProposalStatus }) {
  const { t } = useTranslation();
  const conf = map[status];
  const Icon = conf.icon;
  return (
    <Badge tone={conf.tone}>
      <Icon size={12} />
      {t(`proposals.status.${status}`)}
    </Badge>
  );
}
