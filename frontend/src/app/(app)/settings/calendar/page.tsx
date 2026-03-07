'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';

interface CalendarIntegration {
  id: string;
  provider: string;
  external_calendar_id: string;
  sync_enabled: boolean;
  last_synced_at: string | null;
}

interface SyncResult {
  integration_id: string;
  provider: string;
  created: number;
  updated: number;
  skipped: number;
  error?: string;
}

export default function CalendarSettingsPage() {
  const router = useRouter();
  const [integrations, setIntegrations] = useState<CalendarIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [syncResults, setSyncResults] = useState<SyncResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchIntegrations();

    // Handle OAuth callback: ?code=... is in the URL after Google redirect
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    if (code) {
      // Microsoft OAuth includes a 'state' param we set; Google does not (or uses it differently)
      const provider = state === 'outlook' ? 'outlook' : 'google';
      handleOAuthCallback(code, provider);
      // Clean URL
      router.replace('/settings/calendar');
    }
  }, []);

  const fetchIntegrations = async () => {
    try {
      const { data } = await api.get('/calendar/integrations');
      setIntegrations(data);
    } catch {
      // ignore — no integrations yet
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthCallback = async (code: string, provider: 'google' | 'outlook') => {
    setConnecting(true);
    setError(null);
    const redirectUri = `${window.location.origin}/settings/calendar`;
    try {
      const endpoint = provider === 'outlook'
        ? '/calendar/integrations/outlook'
        : '/calendar/integrations/google';
      const { data } = await api.post(endpoint, { code, redirect_uri: redirectUri });
      setIntegrations((prev) => {
        const exists = prev.find((i) => i.id === data.id);
        if (exists) return prev.map((i) => (i.id === data.id ? data : i));
        return [...prev, data];
      });
    } catch (err: any) {
      const label = provider === 'outlook' ? 'Outlook' : 'Google Calendar';
      setError(err?.response?.data?.detail || `${label} verbinden mislukt.`);
    } finally {
      setConnecting(false);
    }
  };

  const connectGoogle = async () => {
    setConnecting(true);
    setError(null);
    const redirectUri = `${window.location.origin}/settings/calendar`;
    try {
      const { data } = await api.get('/calendar/integrations/google/auth-url', {
        params: { redirect_uri: redirectUri },
      });
      window.location.href = data.auth_url;
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Kan Google OAuth URL niet ophalen.');
      setConnecting(false);
    }
  };

  const connectOutlook = async () => {
    setConnecting(true);
    setError(null);
    const redirectUri = `${window.location.origin}/settings/calendar`;
    try {
      const { data } = await api.get('/calendar/integrations/outlook/auth-url', {
        params: { redirect_uri: redirectUri },
      });
      window.location.href = data.auth_url;
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Kan Outlook OAuth URL niet ophalen.');
      setConnecting(false);
    }
  };

  const disconnectIntegration = async (id: string) => {
    if (!confirm('Weet je zeker dat je deze kalender wil loskoppelen? Alle gesynchroniseerde afspraken worden verwijderd.')) return;
    try {
      await api.delete(`/calendar/integrations/${id}`);
      setIntegrations((prev) => prev.filter((i) => i.id !== id));
    } catch {
      setError('Loskoppelen mislukt. Probeer opnieuw.');
    }
  };

  const syncNow = async () => {
    setSyncing(true);
    setError(null);
    setSyncResults(null);
    try {
      const { data } = await api.post('/calendar/sync');
      setSyncResults(data);
      // Refresh integration list (last_synced_at updated)
      await fetchIntegrations();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Synchronisatie mislukt.');
    } finally {
      setSyncing(false);
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return 'Nog nooit';
    return new Date(iso).toLocaleString('nl-NL', {
      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
    });
  };

  const hasGoogle = integrations.some((i) => i.provider === 'google');
  const hasOutlook = integrations.some((i) => i.provider === 'outlook');

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
        <h2 className="text-xl font-display font-semibold">Agenda koppelingen</h2>
      </div>

      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger text-sm rounded-xl p-3">
          {error}
        </div>
      )}

      {/* Connected integrations */}
      {loading ? (
        <p className="text-sm text-text-muted text-center py-8">Laden...</p>
      ) : integrations.length === 0 ? (
        <Card>
          <p className="text-sm text-text-muted text-center py-4">
            Geen agenda&apos;s gekoppeld. Verbind je Google Calendar om afspraken te synchroniseren.
          </p>
        </Card>
      ) : (
        <div className="space-y-2">
          {integrations.map((integration) => (
            <Card key={integration.id}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                    {integration.provider === 'google' ? (
                      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none">
                        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                      </svg>
                    ) : integration.provider === 'outlook' ? (
                      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none">
                        <rect x="2" y="2" width="9" height="9" fill="#F25022"/>
                        <rect x="13" y="2" width="9" height="9" fill="#7FBA00"/>
                        <rect x="2" y="13" width="9" height="9" fill="#00A4EF"/>
                        <rect x="13" y="13" width="9" height="9" fill="#FFB900"/>
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium capitalize">
                      {integration.provider === 'google' ? 'Google Calendar' : integration.provider === 'outlook' ? 'Outlook / Office 365' : 'CalDAV'}
                    </p>
                    <p className="text-xs text-text-muted">
                      Gesynchroniseerd: {formatDate(integration.last_synced_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={integration.sync_enabled ? 'primary' : 'default'}>
                    {integration.sync_enabled ? 'Actief' : 'Gepauzeerd'}
                  </Badge>
                  <button
                    onClick={() => disconnectIntegration(integration.id)}
                    className="p-1.5 rounded-lg text-danger hover:bg-danger/10 transition-colors"
                    title="Loskoppelen"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Sync results */}
      {syncResults && (
        <Card>
          <p className="text-sm font-medium mb-2">Synchronisatie resultaat</p>
          {syncResults.map((result) => (
            <div key={result.integration_id} className="text-xs text-text-muted space-y-0.5">
              {result.error ? (
                <p className="text-danger">{result.provider}: {result.error}</p>
              ) : (
                <p>
                  {result.provider}: {result.created} nieuw, {result.updated} bijgewerkt, {result.skipped} ongewijzigd
                </p>
              )}
            </div>
          ))}
        </Card>
      )}

      {/* Actions */}
      <div className="space-y-3">
        {!hasGoogle && (
          <Button
            className="w-full"
            onClick={connectGoogle}
            loading={connecting}
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="currentColor" opacity="0.8"/>
            </svg>
            Google Calendar verbinden
          </Button>
        )}

        {!hasOutlook && (
          <Button
            variant="secondary"
            className="w-full"
            onClick={connectOutlook}
            loading={connecting}
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none">
              <rect x="2" y="2" width="9" height="9" fill="#F25022"/>
              <rect x="13" y="2" width="9" height="9" fill="#7FBA00"/>
              <rect x="2" y="13" width="9" height="9" fill="#00A4EF"/>
              <rect x="13" y="13" width="9" height="9" fill="#FFB900"/>
            </svg>
            Outlook / Office 365 verbinden
          </Button>
        )}

        {integrations.length > 0 && (
          <Button
            variant="secondary"
            className="w-full"
            onClick={syncNow}
            loading={syncing}
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Nu synchroniseren
          </Button>
        )}
      </div>

      {/* Info */}
      <Card className="bg-primary/5 border-primary/10">
        <p className="text-xs text-text-muted leading-relaxed">
          <strong>Hoe werkt het?</strong><br />
          Na het koppelen worden je Google of Outlook agenda-afspraken automatisch geïmporteerd.
          De AI herkent opvangdagen, medische afspraken, verjaardagen, daguitjes en vakanties — en maakt automatisch de juiste taken aan.
          Afgeronde taken worden teruggeschreven naar je agenda. Synchronisatie loopt elke avond automatisch, of je tikt op &quot;Nu synchroniseren&quot;.
        </p>
      </Card>
    </div>
  );
}
