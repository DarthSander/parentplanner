'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

interface PicknickStatus {
  connected: boolean;
  country_code: string | null;
  last_synced_at: string | null;
  list_count: number;
  integration_id: string | null;
}

export default function PicknickSettingsPage() {
  const router = useRouter();
  const [status, setStatus] = useState<PicknickStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [countryCode, setCountryCode] = useState('NL');

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const { data } = await api.get('/picknick/status');
      setStatus(data);
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setError('Picknick is alleen beschikbaar in het Gezin-abonnement.');
      }
    } finally {
      setLoading(false);
    }
  };

  const connect = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnecting(true);
    setError(null);
    try {
      await api.post('/picknick/connect', { email, password, country_code: countryCode });
      setEmail('');
      setPassword('');
      await fetchStatus();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(
        typeof detail === 'object' ? detail.message : detail || 'Verbinden mislukt.'
      );
    } finally {
      setConnecting(false);
    }
  };

  const disconnect = async () => {
    if (!confirm('Weet je zeker dat je Picknick wilt loskoppelen? Je boodschappenlijsten worden verwijderd.')) return;
    try {
      await api.delete('/picknick/disconnect');
      setStatus({ connected: false, country_code: null, last_synced_at: null, list_count: 0, integration_id: null });
    } catch {
      setError('Loskoppelen mislukt.');
    }
  };

  const manualSync = async () => {
    setSyncing(true);
    setError(null);
    try {
      const { data } = await api.post('/picknick/sync');
      alert(data.message);
      await fetchStatus();
    } catch (err: any) {
      setError('Synchronisatie mislukt.');
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
        <h2 className="text-xl font-display font-semibold">Picknick</h2>
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
            <p className="text-sm text-text-muted mb-4">
              Koppel je Picknick-account om boodschappenlijsten direct vanuit GezinsAI naar
              Picknick te sturen. De AI houdt je voorraad bij en stelt proactief voor wat je
              moet bestellen op basis van je agenda, apparaten en aankooppatronen.
            </p>

            <form onSubmit={connect} className="space-y-3">
              <Input
                label="E-mailadres"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jouw@email.nl"
                required
              />
              <Input
                label="Wachtwoord"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Picknick wachtwoord"
                required
              />
              <div>
                <label className="block text-xs font-medium text-text-muted mb-1">Land</label>
                <select
                  value={countryCode}
                  onChange={(e) => setCountryCode(e.target.value)}
                  className="w-full border border-border rounded-xl px-3 py-2 text-sm bg-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  <option value="NL">Nederland</option>
                  <option value="DE">Duitsland</option>
                  <option value="BE">België</option>
                </select>
              </div>
              <Button type="submit" className="w-full" loading={connecting}>
                Verbinden met Picknick
              </Button>
            </form>
          </Card>

          <Card className="bg-amber-50 border-amber-200">
            <p className="text-xs text-amber-800 leading-relaxed">
              <strong>Let op:</strong> GezinsAI gebruikt de Picknick app-API. Dit is geen
              officiële integratie. Picknick kan de API op elk moment wijzigen, waardoor de
              koppeling tijdelijk niet werkt. Je wachtwoord wordt versleuteld opgeslagen en
              nooit gedeeld.
            </p>
          </Card>

          <Card className="bg-primary/5 border-primary/10">
            <p className="text-xs text-text-muted leading-relaxed">
              <strong>Wat kan Picknick-integratie?</strong><br />
              Voorraad bijna op? Automatisch op de boodschappenlijst. Opvangdag morgen? AI
              checkt luiers en flesvoeding. Vaatwasser klaar? Vaatwasmiddel op de lijst.
              Alles in één klik naar Picknick.
            </p>
          </Card>
        </>
      ) : (
        <>
          {/* Connected status */}
          <Card>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium">Picknick verbonden</p>
                  <p className="text-xs text-text-muted">
                    {status.country_code} &middot; {status.list_count} lijst(en) &middot; Sync: {formatDate(status.last_synced_at)}
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

          {/* Actions */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="secondary"
              onClick={() => router.push('/shopping')}
            >
              Boodschappenlijst
            </Button>
            <Button
              variant="secondary"
              onClick={manualSync}
              loading={syncing}
            >
              Sync orders
            </Button>
          </div>

          {/* Info */}
          <Card className="bg-primary/5 border-primary/10">
            <p className="text-xs text-text-muted leading-relaxed">
              De AI synchroniseert dagelijks je ordergeschiedenis om patronen te herkennen.
              Gebruik de boodschappenpagina om AI-aanbevelingen te bekijken en in één klik
              naar Picknick te sturen.
            </p>
          </Card>
        </>
      )}
    </div>
  );
}
