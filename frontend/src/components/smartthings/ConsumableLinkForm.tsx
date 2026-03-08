'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';

interface InventoryItem {
  id: string;
  name: string;
  current_quantity: number;
  unit: string;
}

interface ConsumableLinkFormProps {
  deviceId: string;
  onLinked: () => void;
}

export default function ConsumableLinkForm({ deviceId, onLinked }: ConsumableLinkFormProps) {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [selectedItemId, setSelectedItemId] = useState('');
  const [usagePerCycle, setUsagePerCycle] = useState('1');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/inventory').then(({ data }) => setItems(data)).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItemId) return;

    setLoading(true);
    setError(null);
    try {
      await api.post(`/smartthings/devices/${deviceId}/consumables`, {
        inventory_item_id: selectedItemId,
        usage_per_cycle: parseFloat(usagePerCycle),
        auto_deduct: true,
      });
      setSelectedItemId('');
      setUsagePerCycle('1');
      onLinked();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Koppelen mislukt.');
    } finally {
      setLoading(false);
    }
  };

  if (items.length === 0) {
    return (
      <Card className="bg-surface-alt">
        <p className="text-xs text-text-muted text-center">
          Geen voorraadartikelen gevonden. Voeg eerst items toe aan je voorraad.
        </p>
      </Card>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && (
        <p className="text-xs text-danger">{error}</p>
      )}

      <div>
        <label className="text-xs font-medium block mb-1">Voorraaditem</label>
        <select
          value={selectedItemId}
          onChange={(e) => setSelectedItemId(e.target.value)}
          className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm"
          required
        >
          <option value="">Selecteer een item...</option>
          {items.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name} ({item.current_quantity} {item.unit})
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-xs font-medium block mb-1">Verbruik per cyclus</label>
        <input
          type="number"
          min="0.1"
          step="0.1"
          value={usagePerCycle}
          onChange={(e) => setUsagePerCycle(e.target.value)}
          className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm"
          required
        />
        <p className="text-xs text-text-muted mt-1">
          Bv: 1 pod per wasbeurt, 0.5 liter per wasbeurt
        </p>
      </div>

      <Button type="submit" loading={loading} className="w-full">
        Koppelen
      </Button>
    </form>
  );
}
