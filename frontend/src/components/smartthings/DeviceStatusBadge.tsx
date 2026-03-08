import Badge from '@/components/ui/Badge';

interface DeviceStatusBadgeProps {
  isRunning: boolean;
  deviceType: string;
}

const runningLabels: Record<string, string> = {
  washer: 'Wast...',
  dryer: 'Droogt...',
  dishwasher: 'Wast af...',
  robot_vacuum: 'Zuigt...',
  oven: 'Aan',
};

export default function DeviceStatusBadge({ isRunning, deviceType }: DeviceStatusBadgeProps) {
  if (isRunning) {
    return <Badge variant="accent">{runningLabels[deviceType] || 'Actief'}</Badge>;
  }
  return <Badge variant="default">Uit</Badge>;
}
