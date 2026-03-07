'use client';

import { useEffect, useMemo, useState } from 'react';
import { InventoryItem, useInventoryStore } from '@/store/inventory';
import AISuggestionBar from '@/components/ai/AISuggestionBar';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import { toast } from '@/components/ui/Toast';

const CATEGORY_EMOJI: Record<string, string> = {
  baby: 'B',
  schoonmaak: 'S',
  food: 'F',
  eten: 'F',
  cleaning: 'S',
  boodschappen: 'L',
};

function InventoryItemRow({ item }: { item: InventoryItem }) {
  const { patchItem } = useInventoryStore();
  const [adjusting, setAdjusting] = useState(false);

  const isLow = item.current_quantity <= item.threshold_quantity;
  const isEmpty = item.current_quantity === 0;
  const ratio = Math.min(1, item.current_quantity / Math.max(item.threshold_quantity * 2, 1));
  const barColor = isEmpty ? 'bg-danger' : isLow ? 'bg-warning' : 'bg-success';

  // Days remaining calculation
  const daysRemaining = item.average_consumption_rate && item.average_consumption_rate > 0
    ? Math.floor(item.current_quantity / item.average_consumption_rate)
    : null;

  const adjustQuantity = async (delta: number) => {
    const newQty = Math.max(0, item.current_quantity + delta);
    setAdjusting(true);
    try {
      await patchItem(item.id, { current_quantity: newQty });
    } catch {
      toast('Kon hoeveelheid niet aanpassen', 'error');
    } finally {
      setAdjusting(false);
    }
  };

  return (
    <div className={`p-3 rounded-lg bg-surface border transition-colors ${
      isEmpty ? 'border-danger/40' : isLow ? 'border-warning/40' : 'border-border'
    }`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            {item.category && (
              <span className="w-5 h-5 rounded text-[10px] font-bold flex items-center justify-center bg-surface-alt text-text-muted">
                {CATEGORY_EMOJI[item.category.toLowerCase()] || item.category[0]?.toUpperCase()}
              </span>
            )}
            <span className="text-sm font-medium truncate">{item.name}</span>
            {isEmpty && <Badge variant="danger">Op</Badge>}
            {isLow && !isEmpty && <Badge variant="warning">Laag</Badge>}
          </div>

          {/* Progress bar */}
          <div className="w-full h-1.5 bg-surface-alt rounded-full mt-1.5 mb-1">
            <div
              className={`h-full rounded-full transition-all ${barColor}`}
              style={{ width: `${ratio * 100}%` }}
            />
          </div>

          <div className="flex items-center gap-3 text-xs text-text-muted">
            <span className="font-medium">
              {item.current_quantity} {item.unit}
            </span>
            {daysRemaining !== null && (
              <span className={daysRemaining <= 3 ? 'text-danger font-medium' : ''}>
                ~{daysRemaining} dagen
              </span>
            )}
            {item.average_consumption_rate ? (
              <span>{item.average_consumption_rate.toFixed(1)}/{item.unit.slice(0, 3)}/dag</span>
            ) : null}
          </div>
        </div>

        {/* +/- buttons */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => adjustQuantity(-1)}
            disabled={adjusting || item.current_quantity <= 0}
            className="w-8 h-8 rounded-lg border border-border bg-surface-alt flex items-center justify-center
              text-text-main font-bold text-sm hover:bg-border disabled:opacity-30 transition-colors"
          >
            -
          </button>
          <button
            onClick={() => adjustQuantity(1)}
            disabled={adjusting}
            className="w-8 h-8 rounded-lg border border-border bg-surface-alt flex items-center justify-center
              text-text-main font-bold text-sm hover:bg-border disabled:opacity-30 transition-colors"
          >
            +
          </button>
        </div>
      </div>
    </div>
  );
}

export default function InventoryPage() {
  const { items, loading, fetchItems, createItem } = useInventoryStore();
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [quantity, setQuantity] = useState('0');
  const [unit, setUnit] = useState('stuks');
  const [threshold, setThreshold] = useState('1');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  // Group by category
  const { outOfStock, lowStock, inStock } = useMemo(() => {
    const out: InventoryItem[] = [];
    const low: InventoryItem[] = [];
    const ok: InventoryItem[] = [];
    for (const i of items) {
      if (i.current_quantity === 0) out.push(i);
      else if (i.current_quantity <= i.threshold_quantity) low.push(i);
      else ok.push(i);
    }
    return { outOfStock: out, lowStock: low, inStock: ok };
  }, [items]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    try {
      await createItem({
        name: name.trim(),
        category: category || undefined,
        current_quantity: parseFloat(quantity),
        unit,
        threshold_quantity: parseFloat(threshold),
      } as never);
      toast('Item toegevoegd', 'success');
      setShowForm(false);
      setName('');
      setCategory('');
      setQuantity('0');
    } catch {
      toast('Kon item niet toevoegen', 'error');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-display font-semibold">Voorraad</h2>
        <Button size="sm" onClick={() => setShowForm(true)}>+ Nieuw</Button>
      </div>

      <AISuggestionBar page="inventory" maxItems={2} compact />

      {loading ? (
        <p className="text-sm text-text-muted text-center py-8">Voorraad laden...</p>
      ) : (
        <>
          {outOfStock.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-danger mb-2">
                Op ({outOfStock.length})
              </h3>
              <div className="space-y-2">
                {outOfStock.map((item) => <InventoryItemRow key={item.id} item={item} />)}
              </div>
            </div>
          )}

          {lowStock.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-warning mb-2">
                Bijna op ({lowStock.length})
              </h3>
              <div className="space-y-2">
                {lowStock.map((item) => <InventoryItemRow key={item.id} item={item} />)}
              </div>
            </div>
          )}

          {inStock.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted mb-2">
                Op voorraad ({inStock.length})
              </h3>
              <div className="space-y-2">
                {inStock.map((item) => <InventoryItemRow key={item.id} item={item} />)}
              </div>
            </div>
          )}

          {items.length === 0 && (
            <p className="text-sm text-text-muted text-center py-8">
              Nog geen items. Voeg je eerste voorraaditem toe.
            </p>
          )}
        </>
      )}

      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title="Nieuw voorraaditem">
        <form onSubmit={handleCreate} className="flex flex-col gap-4">
          <Input label="Naam" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
          <Input label="Categorie" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="bijv. baby, schoonmaak, eten" />
          <div className="flex gap-3">
            <Input label="Aantal" type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} min={0} />
            <Input label="Eenheid" value={unit} onChange={(e) => setUnit(e.target.value)} />
          </div>
          <Input label="Drempel (melding bij)" type="number" value={threshold} onChange={(e) => setThreshold(e.target.value)} min={0} />
          <div className="flex gap-2 pt-2">
            <Button type="submit" loading={creating}>Toevoegen</Button>
            <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>Annuleren</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
