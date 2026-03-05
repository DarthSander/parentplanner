'use client';

import { useEffect, useState } from 'react';
import { useInventoryStore } from '@/store/inventory';
import InventoryCard from '@/components/inventory/InventoryCard';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import { toast } from '@/components/ui/Toast';

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

  const lowStock = items.filter((i) => i.current_quantity <= i.threshold_quantity);
  const inStock = items.filter((i) => i.current_quantity > i.threshold_quantity);

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
        <Button size="sm" onClick={() => setShowForm(true)}>+ Nieuw item</Button>
      </div>

      {loading ? (
        <p className="text-sm text-text-muted text-center py-8">Voorraad laden...</p>
      ) : (
        <>
          {lowStock.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-warning mb-2">Bijna op ({lowStock.length})</h3>
              <div className="space-y-2">
                {lowStock.map((item) => <InventoryCard key={item.id} item={item} />)}
              </div>
            </div>
          )}

          {inStock.length > 0 && (
            <div>
              <h3 className="text-sm font-medium mb-2">Op voorraad ({inStock.length})</h3>
              <div className="space-y-2">
                {inStock.map((item) => <InventoryCard key={item.id} item={item} />)}
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
          <Input label="Categorie" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="bijv. baby, food, cleaning" />
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
