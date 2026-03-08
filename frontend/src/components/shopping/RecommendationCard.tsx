'use client';

import Badge from '@/components/ui/Badge';
import Card from '@/components/ui/Card';

interface RecommendedItem {
  name: string;
  quantity: number;
  unit: string | null;
  reason: string;
  priority: 'urgent' | 'normal' | 'suggestion';
  source: string;
  estimated_price: number | null;
}

const SOURCE_ICONS: Record<string, string> = {
  inventory_low: '📦',
  calendar: '📅',
  smartthings: '🏠',
  pattern: '📊',
};

const PRIORITY_VARIANTS: Record<string, 'danger' | 'warning' | 'default'> = {
  urgent: 'danger',
  normal: 'warning',
  suggestion: 'default',
};

const PRIORITY_LABELS: Record<string, string> = {
  urgent: 'Urgent',
  normal: 'Normaal',
  suggestion: 'Tip',
};

export default function RecommendationCard({ item }: { item: RecommendedItem }) {
  const icon = SOURCE_ICONS[item.source] || '🛒';
  const variant = PRIORITY_VARIANTS[item.priority] || 'default';

  return (
    <Card className={item.priority === 'urgent' ? 'border-danger/30 bg-danger/5' : ''}>
      <div className="flex items-start gap-3">
        <span className="text-xl mt-0.5">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium">
              {item.quantity > 1 ? `${item.quantity}${item.unit ? ` ${item.unit}` : 'x'} ` : ''}
              {item.name}
            </p>
            <Badge variant={variant} size="sm">
              {PRIORITY_LABELS[item.priority]}
            </Badge>
          </div>
          <p className="text-xs text-text-muted mt-0.5">{item.reason}</p>
          {item.estimated_price && (
            <p className="text-xs text-text-muted mt-0.5">
              ~€{item.estimated_price.toFixed(2)}
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}
