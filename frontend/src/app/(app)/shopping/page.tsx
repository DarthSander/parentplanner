'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import RecommendationCard from '@/components/shopping/RecommendationCard';
import ShoppingListView from '@/components/shopping/ShoppingListView';

interface RecommendedItem {
  name: string;
  quantity: number;
  unit: string | null;
  reason: string;
  priority: 'urgent' | 'normal' | 'suggestion';
  source: string;
  picknick_product_id: string | null;
  inventory_item_id: string | null;
  estimated_price: number | null;
}

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

type Tab = 'recommendations' | 'list';

export default function ShoppingPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('recommendations');
  const [connected, setConnected] = useState<boolean | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendedItem[]>([]);
  const [contextSummary, setContextSummary] = useState('');
  const [lists, setLists] = useState<ShoppingList[]>([]);
  const [activeList, setActiveList] = useState<ShoppingList | null>(null);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [loadingList, setLoadingList] = useState(false);
  const [addingToList, setAddingToList] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const { data } = await api.get('/picknick/status');
      setConnected(data.connected);
      if (data.connected) {
        await Promise.all([fetchRecommendations(), fetchLists()]);
      }
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setConnected(false);
      }
    }
  };

  const fetchRecommendations = async () => {
    setLoadingRecs(true);
    try {
      const { data } = await api.get('/picknick/recommendations');
      setRecommendations(data.items || []);
      setContextSummary(data.context_summary || '');
    } catch {
      setError('Aanbevelingen laden mislukt.');
    } finally {
      setLoadingRecs(false);
    }
  };

  const fetchLists = async () => {
    setLoadingList(true);
    try {
      const { data } = await api.get('/picknick/lists');
      setLists(data);
      const open = data.find((l: ShoppingList) => l.status === 'open');
      setActiveList(open || null);
    } catch {
    } finally {
      setLoadingList(false);
    }
  };

  const addAllToList = async () => {
    setAddingToList(true);
    setError(null);
    try {
      const { data } = await api.post('/picknick/recommendations/add-to-list');
      await fetchLists();
      setTab('list');
    } catch (err: any) {
      setError('Toevoegen aan lijst mislukt.');
    } finally {
      setAddingToList(false);
    }
  };

  const urgentCount = recommendations.filter((r) => r.priority === 'urgent').length;

  if (connected === null) {
    return <p className="text-sm text-text-muted text-center py-12">Laden...</p>;
  }

  if (!connected) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-display font-semibold">Boodschappen</h2>
        <Card>
          <div className="text-center py-6 space-y-3">
            <div className="w-12 h-12 rounded-full bg-surface-alt mx-auto flex items-center justify-center">
              <svg className="w-6 h-6 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <p className="text-sm text-text-muted">
              Koppel je Picknick-account om AI-boodschappenlijsten te gebruiken.
            </p>
            <Button onClick={() => router.push('/settings/picknick')}>
              Picknick koppelen
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-display font-semibold">Boodschappen</h2>
        {urgentCount > 0 && (
          <Badge variant="danger">{urgentCount} urgent</Badge>
        )}
      </div>

      {error && (
        <div className="bg-danger/10 border border-danger/20 text-danger text-sm rounded-xl p-3">
          {error}
        </div>
      )}

      {/* Tab switcher */}
      <div className="flex rounded-xl overflow-hidden border border-border">
        <button
          onClick={() => setTab('recommendations')}
          className={`flex-1 py-2 text-sm font-medium transition-colors ${
            tab === 'recommendations'
              ? 'bg-primary text-white'
              : 'bg-surface text-text-muted hover:bg-surface-alt'
          }`}
        >
          AI-aanbevelingen
        </button>
        <button
          onClick={() => setTab('list')}
          className={`flex-1 py-2 text-sm font-medium transition-colors ${
            tab === 'list'
              ? 'bg-primary text-white'
              : 'bg-surface text-text-muted hover:bg-surface-alt'
          }`}
        >
          Mijn lijst {activeList && `(${activeList.item_count})`}
        </button>
      </div>

      {tab === 'recommendations' && (
        <>
          {contextSummary && (
            <p className="text-xs text-text-muted px-1">
              Gebaseerd op: {contextSummary}
            </p>
          )}

          {loadingRecs ? (
            <p className="text-sm text-text-muted text-center py-8">AI analyseert je situatie...</p>
          ) : recommendations.length === 0 ? (
            <Card>
              <div className="text-center py-6">
                <p className="text-sm text-text-muted">Geen aanbevelingen op dit moment.</p>
                <p className="text-xs text-text-muted mt-1">
                  Voeg voorraad toe en koppel je agenda voor slimmere aanbevelingen.
                </p>
              </div>
            </Card>
          ) : (
            <>
              <div className="space-y-2">
                {recommendations.map((item, i) => (
                  <RecommendationCard key={i} item={item} />
                ))}
              </div>

              <Button
                className="w-full"
                onClick={addAllToList}
                loading={addingToList}
              >
                Alles toevoegen aan boodschappenlijst
              </Button>
            </>
          )}
        </>
      )}

      {tab === 'list' && (
        <ShoppingListView
          lists={lists}
          activeList={activeList}
          onRefresh={fetchLists}
        />
      )}
    </div>
  );
}
