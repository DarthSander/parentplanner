'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import DeviceStatusBadge from '@/components/smartthings/DeviceStatusBadge';
import ConsumableLinkForm from '@/components/smartthings/ConsumableLinkForm';

interface Device {
  id: string;
  device_type: string;
  label: string;
  room: string | null;
  is_running: boolean;
  total_cycles: number;
  last_event_at: string | null;
  current_state: Record<string, any> | null;
}

interface Consumable {
  id: string;
  device_id: string;
  inventory_item_id: string;
  inventory_item_name: string | null;
  usage_per_cycle: number;
  auto_deduct: boolean;
}

interface DeviceStats {
  total_cycles: number;
  cycles_this_week: number;
  cycles_this_month: number;
  avg_cycles_per_week: number;
  consumables_status: Array<{
    name: string;
    current_quantity: number;
    unit: string;
    usage_per_cycle: number;
    cycles_remaining: number;
    is_low: boolean;
  }>;
}

interface DeviceEvent {
  id: string;
  event_type: string;
  event_data: Record<string, any> | null;
  created_at: string;
}

const deviceLabels: Record<string, string> = {
  washer: 'Wasmachine',
  dryer: 'Droger',
  dishwasher: 'Vaatwasser',
  robot_vacuum: 'Robotstofzuiger',
  refrigerator: 'Koelkast',
  oven: 'Oven',
  air_purifier: 'Luchtreiniger',
  smart_plug: 'Slim stopcontact',
};

const eventLabels: Record<string, string> = {
  cycle_started: 'Cyclus gestart',
  cycle_completed: 'Cyclus afgerond',
  door_opened: 'Deur geopend',
  door_closed: 'Deur gesloten',
  error: 'Fout',
  power_on: 'Ingeschakeld',
  power_off: 'Uitgeschakeld',
  filter_alert: 'Filter melding',
  temperature_alert: 'Temperatuur melding',
};

export default function DeviceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const deviceId = params.deviceId as string;

  const [device, setDevice] = useState<Device | null>(null);
  const [consumables, setConsumables] = useState<Consumable[]>([]);
  const [stats, setStats] = useState<DeviceStats | null>(null);
  const [events, setEvents] = useState<DeviceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showLinkForm, setShowLinkForm] = useState(false);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchAll();
  }, [deviceId]);

  const fetchAll = async () => {
    try {
      const [deviceRes, consumablesRes, statsRes, eventsRes] = await Promise.all([
        api.get(`/smartthings/devices/${deviceId}`),
        api.get(`/smartthings/devices/${deviceId}/consumables`),
        api.get(`/smartthings/devices/${deviceId}/stats`),
        api.get(`/smartthings/devices/${deviceId}/events?limit=20`),
      ]);
      setDevice(deviceRes.data);
      setConsumables(consumablesRes.data);
      setStats(statsRes.data);
      setEvents(eventsRes.data);
    } catch {
      // device not found
    } finally {
      setLoading(false);
    }
  };

  const syncDevice = async () => {
    setSyncing(true);
    try {
      const { data } = await api.post(`/smartthings/devices/${deviceId}/sync`);
      setDevice(data);
    } catch {
      // ignore
    } finally {
      setSyncing(false);
    }
  };

  const unlinkConsumable = async (consumableId: string) => {
    try {
      await api.delete(`/smartthings/consumables/${consumableId}`);
      setConsumables((prev) => prev.filter((c) => c.id !== consumableId));
    } catch {
      // ignore
    }
  };

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleString('nl-NL', {
      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
    });
  };

  if (loading) {
    return <p className="text-sm text-text-muted text-center py-8">Laden...</p>;
  }

  if (!device) {
    return <p className="text-sm text-text-muted text-center py-8">Apparaat niet gevonden.</p>;
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.back()}
          className="p-1 rounded-lg hover:bg-surface-alt transition-colors"
        >
          <svg className="w-5 h-5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div className="flex-1">
          <h2 className="text-xl font-display font-semibold">{device.label}</h2>
          <p className="text-xs text-text-muted">
            {deviceLabels[device.device_type] || device.device_type}
            {device.room && ` \u00B7 ${device.room}`}
          </p>
        </div>
        <DeviceStatusBadge isRunning={device.is_running} deviceType={device.device_type} />
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 gap-2">
          <Card className="text-center">
            <p className="text-2xl font-display font-semibold">{stats.cycles_this_week}</p>
            <p className="text-xs text-text-muted">Deze week</p>
          </Card>
          <Card className="text-center">
            <p className="text-2xl font-display font-semibold">{stats.cycles_this_month}</p>
            <p className="text-xs text-text-muted">Deze maand</p>
          </Card>
          <Card className="text-center">
            <p className="text-2xl font-display font-semibold">{stats.total_cycles}</p>
            <p className="text-xs text-text-muted">Totaal cycli</p>
          </Card>
          <Card className="text-center">
            <p className="text-2xl font-display font-semibold">{stats.avg_cycles_per_week}</p>
            <p className="text-xs text-text-muted">Gem. per week</p>
          </Card>
        </div>
      )}

      {/* Consumables status */}
      {stats && stats.consumables_status.length > 0 && (
        <div>
          <h3 className="text-sm font-medium mb-2">Verbruiksartikelen</h3>
          <div className="space-y-2">
            {stats.consumables_status.map((cs, i) => (
              <Card key={i} className={cs.is_low ? 'border-warning/30 bg-warning/5' : ''}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{cs.name}</p>
                    <p className="text-xs text-text-muted">
                      {cs.current_quantity} {cs.unit} &middot; {cs.usage_per_cycle} per beurt &middot;
                      nog ~{cs.cycles_remaining} beurten
                    </p>
                  </div>
                  {cs.is_low && <Badge variant="warning">Bijna op</Badge>}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Linked consumables management */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium">Gekoppelde voorraad</h3>
          <button
            onClick={() => setShowLinkForm(!showLinkForm)}
            className="text-xs text-primary font-medium"
          >
            {showLinkForm ? 'Annuleren' : '+ Toevoegen'}
          </button>
        </div>

        {showLinkForm && (
          <Card className="mb-2">
            <ConsumableLinkForm
              deviceId={deviceId}
              onLinked={() => {
                setShowLinkForm(false);
                fetchAll();
              }}
            />
          </Card>
        )}

        {consumables.length === 0 && !showLinkForm ? (
          <Card>
            <p className="text-xs text-text-muted text-center py-2">
              Geen voorraadartikelen gekoppeld. Koppel bv. wasmiddel om automatisch
              het verbruik bij te houden.
            </p>
          </Card>
        ) : (
          <div className="space-y-1">
            {consumables.map((c) => (
              <Card key={c.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm">{c.inventory_item_name || 'Onbekend item'}</p>
                    <p className="text-xs text-text-muted">
                      {c.usage_per_cycle} per cyclus &middot; {c.auto_deduct ? 'Auto-afschrijving aan' : 'Handmatig'}
                    </p>
                  </div>
                  <button
                    onClick={() => unlinkConsumable(c.id)}
                    className="p-1 rounded text-text-muted hover:text-danger transition-colors"
                    title="Ontkoppelen"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Recent events */}
      <div>
        <h3 className="text-sm font-medium mb-2">Recente activiteit</h3>
        {events.length === 0 ? (
          <Card>
            <p className="text-xs text-text-muted text-center py-2">Nog geen activiteit.</p>
          </Card>
        ) : (
          <div className="space-y-1">
            {events.map((event) => (
              <div key={event.id} className="flex items-center gap-3 py-1.5 px-1">
                <div className="w-2 h-2 rounded-full bg-primary/40 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium">{eventLabels[event.event_type] || event.event_type}</p>
                  <p className="text-xs text-text-muted">{formatDate(event.created_at)}</p>
                </div>
                {event.event_data?.duration_minutes && (
                  <p className="text-xs text-text-muted">{event.event_data.duration_minutes} min</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sync button */}
      <Button variant="secondary" className="w-full" onClick={syncDevice} loading={syncing}>
        Status vernieuwen
      </Button>
    </div>
  );
}
