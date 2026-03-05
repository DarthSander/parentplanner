'use client';

import { InventoryItem } from '@/store/inventory';
import Badge from '@/components/ui/Badge';

interface InventoryCardProps {
  item: InventoryItem;
  onClick?: () => void;
}

export default function InventoryCard({ item, onClick }: InventoryCardProps) {
  const isLow = item.current_quantity <= item.threshold_quantity;
  const isEmpty = item.current_quantity === 0;

  return (
    <div
      onClick={onClick}
      className={`flex items-center justify-between p-3 rounded-md bg-surface border cursor-pointer
        hover:shadow-sm transition-shadow
        ${isEmpty ? 'border-danger' : isLow ? 'border-warning' : 'border-border'}`}
    >
      <div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{item.name}</span>
          {item.category && <Badge>{item.category}</Badge>}
        </div>
        <span className="text-xs text-text-muted">
          {item.current_quantity} {item.unit}
          {item.average_consumption_rate
            ? ` (${item.average_consumption_rate.toFixed(1)} ${item.unit}/dag)`
            : ''}
        </span>
      </div>
      <div className="flex items-center gap-2">
        {isEmpty && <Badge variant="danger">Op</Badge>}
        {isLow && !isEmpty && <Badge variant="warning">Bijna op</Badge>}
      </div>
    </div>
  );
}
