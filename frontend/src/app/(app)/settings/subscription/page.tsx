'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { toast } from '@/components/ui/Toast';

interface Subscription {
  id: string;
  tier: 'free' | 'standard' | 'family';
  status: string;
  current_period_end: string | null;
  trial_ends_at: string | null;
}

const tierDetails: Record<string, { name: string; price: string; features: string[] }> = {
  free: {
    name: 'Gratis',
    price: '0',
    features: ['Max 2 leden', 'Basis taakbeheer'],
  },
  standard: {
    name: 'Standaard',
    price: '8,99',
    features: ['AI-analyse', 'Kalender koppeling', 'Push notificaties', 'Max 4 leden', 'Patronen'],
  },
  family: {
    name: 'Gezin',
    price: '13,99',
    features: ['Alles van Standaard', 'Onbeperkte leden', 'Oppas & opvang rollen', 'WhatsApp briefing', 'Automatische voorraad'],
  },
};

export default function SubscriptionPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/subscriptions/me')
      .then(({ data }) => setSubscription(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleCheckout = async (tier: string) => {
    try {
      const { data } = await api.post('/subscriptions/checkout', { tier });
      if (data.url) window.location.href = data.url;
    } catch {
      toast('Kon checkout niet starten', 'error');
    }
  };

  const handlePortal = async () => {
    try {
      const { data } = await api.post('/subscriptions/portal');
      if (data.url) window.location.href = data.url;
    } catch {
      toast('Kon facturatieportaal niet openen', 'error');
    }
  };

  if (loading) return <p className="text-sm text-text-muted text-center py-8">Laden...</p>;

  const currentTier = subscription?.tier || 'free';

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-display font-semibold">Abonnement</h2>

      {subscription && subscription.tier !== 'free' && (
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">{tierDetails[currentTier].name}</p>
              <p className="text-xs text-text-muted">{subscription.status}</p>
            </div>
            <Button size="sm" variant="secondary" onClick={handlePortal}>
              Beheer
            </Button>
          </div>
        </Card>
      )}

      <div className="space-y-3">
        {Object.entries(tierDetails).map(([tier, details]) => (
          <Card key={tier} className={tier === currentTier ? 'border-primary' : ''}>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">{details.name}</h3>
                <span className="text-lg font-display font-semibold">
                  {details.price === '0' ? 'Gratis' : `${details.price}/mnd`}
                </span>
              </div>
              <ul className="space-y-1">
                {details.features.map((f) => (
                  <li key={f} className="text-xs text-text-muted flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              {tier !== currentTier && tier !== 'free' && (
                <Button size="sm" className="w-full mt-2" onClick={() => handleCheckout(tier)}>
                  Upgrade naar {details.name}
                </Button>
              )}
              {tier === currentTier && (
                <Badge variant="primary">Huidig plan</Badge>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
