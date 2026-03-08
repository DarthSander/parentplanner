import Link from 'next/link';
import Card from '@/components/ui/Card';
import DeviceStatusBadge from './DeviceStatusBadge';

interface Device {
  id: string;
  device_type: string;
  label: string;
  room: string | null;
  is_running: boolean;
  total_cycles: number;
  last_event_at: string | null;
}

const deviceIcons: Record<string, string> = {
  washer: '\u{1F9FA}',      // sponge - closest to washing
  dryer: '\u{1F32C}',       // wind
  dishwasher: '\u{1F37D}',  // plate
  robot_vacuum: '\u{1F9F9}', // broom
  refrigerator: '\u{2744}',  // snowflake
  oven: '\u{1F525}',         // fire
  air_purifier: '\u{1F4A8}', // dash
  smart_plug: '\u{1F50C}',  // plug
};

const deviceLabels: Record<string, string> = {
  washer: 'Wasmachine',
  dryer: 'Droger',
  dishwasher: 'Vaatwasser',
  robot_vacuum: 'Robotstofzuiger',
  refrigerator: 'Koelkast',
  oven: 'Oven',
  air_purifier: 'Luchtreiniger',
  smart_plug: 'Slim stopcontact',
  other: 'Overig',
};

export default function DeviceCard({ device }: { device: Device }) {
  return (
    <Link href={`/settings/smartthings/${device.id}`}>
      <Card className="hover:shadow-sm transition-shadow">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-lg shrink-0">
              {deviceIcons[device.device_type] || '\u{1F4F1}'}
            </div>
            <div>
              <p className="text-sm font-medium">{device.label}</p>
              <p className="text-xs text-text-muted">
                {deviceLabels[device.device_type] || device.device_type}
                {device.room && ` \u00B7 ${device.room}`}
                {device.total_cycles > 0 && ` \u00B7 ${device.total_cycles} cycli`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <DeviceStatusBadge isRunning={device.is_running} deviceType={device.device_type} />
            <svg className="w-4 h-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </Card>
    </Link>
  );
}
