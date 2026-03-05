'use client';

interface Distribution {
  member_id: string;
  display_name: string;
  completed_count: number;
  open_count: number;
  percentage: number;
}

interface TaskDistributionBarProps {
  distribution: Distribution[];
}

const colors = ['bg-primary', 'bg-accent', 'bg-primary-light', 'bg-accent-light'];

export default function TaskDistributionBar({ distribution }: TaskDistributionBarProps) {
  const total = distribution.reduce((sum, d) => sum + d.completed_count, 0);
  if (total === 0) return null;

  return (
    <div className="space-y-2">
      <div className="flex h-3 rounded-full overflow-hidden bg-surface-alt">
        {distribution.map((d, i) => (
          <div
            key={d.member_id}
            className={`${colors[i % colors.length]} transition-all`}
            style={{ width: `${d.percentage}%` }}
          />
        ))}
      </div>
      <div className="flex justify-between text-xs text-text-muted">
        {distribution.map((d, i) => (
          <div key={d.member_id} className="flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${colors[i % colors.length]}`} />
            <span>{d.display_name}: {d.completed_count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
