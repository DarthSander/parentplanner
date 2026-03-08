'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import DeviceCard from '@/components/smartthings/DeviceCard';

interface SmartThingsStatus {
  connected: boolean;
  location_id: string | null;
  last_synced_at: string | null;
  device_count: number;
}

interface Device {
  id: string;
  device_type: string;
  label: string;
  room: string | null;
  is_running: boolean;
  total_cycles: number;
  last_event_at: string | null;
}

export default function SmartThingsSettingsPage() {
  const router = useRouter();
  const [status, setStatus] = useState<SmartThingsStatus | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus();

    // Handle OAuth callback
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    if (code) {
      handleOAuthCallback(code);
      router.replace('/settings/smartthings');
    }
  }, []);

  const fetchStatus = async () => {
    try {
      const { data } = await api.get('/smartthings/status');
      setStatus(data);
      if (data.connected) {
        const devicesRes = await api.get('/smartthings/devices');
        setDevices(devicesRes.data);
      }
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setError('SmartThings is alleen beschikbaar in het Gezin-abonnement.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthCallback = async (code: string) => {
    setConnecting(true);
    setError(null);
    const redirectUri = `${window.location.origin}/settings/smartthings`;
    try {
      await api.post(`/smartthings/callback?redirect_uri=${encodeURIComponent(redirectUri)}`, {
        code,
      });
      await fetchStatus();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'SmartThings verbinden mislukt.');
    } finally {
      setConnecting(false);
    }
  };

  const connectSmartThings = async () => {
    setConnecting(true);
    setError(null);
    const redirectUri = `${window.location.origin}/settings/smartthings`;
    try {
      const { data } = await api.get('/smartthings/auth-url', {
        params: { redirect_uri: redirectUri },
      });
      window.location.href = data.auth_url;
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Kan SmartThings niet verbinden.');
      setConnecting(false);
    }
  };

  const disconnect = async () => {
    if (!confirm('Weet je zeker dat je SmartThings wilt loskoppelen? Alle apparaatdata wordt verwijderd.')) return;
    try {
      await api.delete('/smartthings/disconnect');
      setStatus({ connected: false, location_id: null, last_synced_at: null, device_count: 0 });
      setDevices([]);
    } catch {
      setError('Loskoppelen mislukt.');
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return 'Nog nooit';
    return new Date(iso).toLocaleString('nl-NL', {
      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
    });
  };

  const runningDevices = devices.filter((d) => d.is_running);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.back()}
          className="p-1 rounded-lg hover:bg-surface-alt transition-colors"
        >
          <svg className="w-5 h-5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h2 className="text-xl font-display font-semibold">SmartThings</h2>
      </div>

      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger text-sm rounded-xl p-3">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-text-muted text-center py-8">Laden...</p>
      ) : !status?.connected ? (
        <>
          <Card>
            <p className="text-sm text-text-muted text-center py-4">
              Koppel je Samsung SmartThings account om je slimme apparaten te verbinden.
              De AI houdt bij wanneer je wasmachine, droger of vaatwasser klaar is en beheert
              automatisch je voorraad wasmiddel, vaatwastabletten en meer.
            </p>
          </Card>

          <Button className="w-full" onClick={connectSmartThings} loading={connecting}>
            SmartThings verbinden
          </Button>

          <Card className="bg-primary/5 border-primary/10">
            <p className="text-xs text-text-muted leading-relaxed">
              <strong>Wat kan SmartThings?</strong><br />
              Wasmachine klaar? Je krijgt een melding en de AI maakt een &quot;was ophangen&quot; taak.
              Wasmiddel op? Automatisch op de boodschappenlijst. De AI leert je waspatroon
              en voorspelt wanneer je nieuwe voorraad nodig hebt.
            </p>
          </Card>
        </>
      ) : (
        <>
          {/* Connection status */}
          <Card>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium">SmartThings verbonden</p>
                  <p className="text-xs text-text-muted">
                    {status.device_count} apparaten &middot; Gesynchroniseerd: {formatDate(status.last_synced_at)}
                  </p>
                </div>
              </div>
              <button
                onClick={disconnect}
                className="p-1.5 rounded-lg text-danger hover:bg-danger/10 transition-colors"
                title="Loskoppelen"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </Card>

          {/* Running devices highlight */}
          {runningDevices.length > 0 && (
            <Card className="bg-accent/5 border-accent/20">
              <p className="text-sm font-medium mb-1">Nu actief</p>
              {runningDevices.map((d) => (
                <p key={d.id} className="text-xs text-text-muted">
                  {d.label} is bezig...
                </p>
              ))}
            </Card>
          )}

          {/* Device list */}
          <div>
            <h3 className="text-sm font-medium mb-2">Apparaten</h3>
            {devices.length === 0 ? (
              <Card>
                <p className="text-sm text-text-muted text-center py-4">
                  Geen apparaten gevonden. Controleer je SmartThings app.
                </p>
              </Card>
            ) : (
              <div className="space-y-2">
                {devices.map((device) => (
                  <DeviceCard key={device.id} device={device} />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
