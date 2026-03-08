'use client';

import { useState } from 'react';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';

interface ShoppingList {
  id: string;
  name: string;
  status: string;
  ai_generated: boolean;
  item_count: number;
  sent_at: string | null;
  delivered_at: string | null;
  created_at: string;
}

interface Props {
  lists: ShoppingList[];
  activeList: ShoppingList | null;
  onRefresh: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  open: 'Open',
  sent_to_picknick: 'Naar Picknick gestuurd',
  delivered: 'Bezorgd',
};

const STATUS_VARIANTS: Record<string, 'default' | 'success' | 'warning'> = {
  open: 'default',
  sent_to_picknick: 'warning',
  delivered: 'success',
};

export default function ShoppingListView({ lists, activeList, onRefresh }: Props) {
  const [sending, setSending] = useState<string | null>(null);
  const [marking, setMarking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sendToPicknick = async (listId: string) => {
    setSending(listId);
    setError(null);
    try {
      const { data } = await api.post(`/picknick/lists/${listId}/send`);
      alert(data.message);
      onRefresh();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'object' ? detail.message : detail || 'Versturen mislukt.');
    } finally {
      setSending(null);
    }
  };

  const markDelivered = async (listId: string) => {
    setMarking(listId);
    setError(null);
    try {
      await api.post(`/picknick/lists/${listId}/delivered`);
      onRefresh();
    } catch {
      setError('Markeren als bezorgd mislukt.');
    } finally {
      setMarking(null);
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return '';
    return new Date(iso).toLocaleString('nl-NL', {
      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
    });
  };

  if (lists.length === 0) {
    return (
      <Card>
        <div className="text-center py-6">
          <p className="text-sm text-text-muted">Nog geen boodschappenlijsten.</p>
          <p className="text-xs text-text-muted mt-1">
            Gebruik de AI-aanbevelingen om een lijst te maken.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger text-sm rounded-xl p-3">
          {error}
        </div>
      )}

      {lists.map((list) => (
        <Card key={list.id} className={list.status === 'open' ? 'border-primary/20' : ''}>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{list.name}</p>
                  {list.ai_generated && (
                    <Badge variant="default" size="sm">AI</Badge>
                  )}
                </div>
                <p className="text-xs text-text-muted">
                  {list.item_count} item(s) &middot; {formatDate(list.created_at)}
                </p>
              </div>
              <Badge variant={STATUS_VARIANTS[list.status] || 'default'}>
                {STATUS_LABELS[list.status] || list.status}
              </Badge>
            </div>

            {list.status === 'open' && list.item_count > 0 && (
              <Button
                className="w-full"
                onClick={() => sendToPicknick(list.id)}
                loading={sending === list.id}
              >
                🛒 In één klik naar Picknick
              </Button>
            )}

            {list.status === 'sent_to_picknick' && (
              <div className="space-y-1">
                {list.sent_at && (
                  <p className="text-xs text-text-muted">Verstuurd: {formatDate(list.sent_at)}</p>
                )}
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={() => markDelivered(list.id)}
                  loading={marking === list.id}
                >
                  Markeer als bezorgd (update voorraad)
                </Button>
              </div>
            )}

            {list.status === 'delivered' && list.delivered_at && (
              <p className="text-xs text-success">
                ✓ Bezorgd op {formatDate(list.delivered_at)}. Voorraad bijgewerkt.
              </p>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}
