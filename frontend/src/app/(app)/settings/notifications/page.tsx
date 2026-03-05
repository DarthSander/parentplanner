'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { toast } from '@/components/ui/Toast';

interface NotificationPrefs {
  preferred_channel: 'push' | 'email' | 'whatsapp';
  aggression_level: number;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  partner_escalation_enabled: boolean;
  partner_escalation_after_days: number;
}

export default function NotificationsPage() {
  const [prefs, setPrefs] = useState<NotificationPrefs | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/notifications/preferences')
      .then(({ data }) => setPrefs(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!prefs) return;
    setSaving(true);
    try {
      await api.patch('/notifications/preferences', prefs);
      toast('Voorkeuren opgeslagen', 'success');
    } catch {
      toast('Kon voorkeuren niet opslaan', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading || !prefs) {
    return <p className="text-sm text-text-muted text-center py-8">Laden...</p>;
  }

  const aggressionLabels = ['', 'Zacht', 'Normaal', 'Assertief', 'Dringend', 'Maximaal'];

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-display font-semibold">Notificaties</h2>

      <Card>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1">Voorkeurskanaal</label>
            <select
              value={prefs.preferred_channel}
              onChange={(e) => setPrefs({ ...prefs, preferred_channel: e.target.value as NotificationPrefs['preferred_channel'] })}
              className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm"
            >
              <option value="push">Push notificatie</option>
              <option value="email">E-mail</option>
              <option value="whatsapp">WhatsApp</option>
            </select>
          </div>

          <div>
            <label className="text-sm font-medium block mb-1">
              Intensiteit: {aggressionLabels[prefs.aggression_level]}
            </label>
            <input
              type="range"
              min={1}
              max={5}
              value={prefs.aggression_level}
              onChange={(e) => setPrefs({ ...prefs, aggression_level: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-[10px] text-text-muted">
              <span>Zacht</span>
              <span>Maximaal</span>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-1">
              <label className="text-sm font-medium block mb-1">Stille uren van</label>
              <input
                type="time"
                value={prefs.quiet_hours_start || '22:00'}
                onChange={(e) => setPrefs({ ...prefs, quiet_hours_start: e.target.value })}
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm"
              />
            </div>
            <div className="flex-1">
              <label className="text-sm font-medium block mb-1">tot</label>
              <input
                type="time"
                value={prefs.quiet_hours_end || '07:00'}
                onChange={(e) => setPrefs({ ...prefs, quiet_hours_end: e.target.value })}
                className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="escalation"
              checked={prefs.partner_escalation_enabled}
              onChange={(e) => setPrefs({ ...prefs, partner_escalation_enabled: e.target.checked })}
              className="rounded"
            />
            <label htmlFor="escalation" className="text-sm">
              Partner notificeren bij lang openstaande taken
            </label>
          </div>
        </div>
      </Card>

      <Button onClick={handleSave} loading={saving} className="w-full">
        Opslaan
      </Button>
    </div>
  );
}
