'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { useTaskStore } from '@/store/tasks';
import { useInventoryStore } from '@/store/inventory';
import { toast } from '@/components/ui/Toast';

interface SuggestionAction {
  label: string;
  action_type: 'create_task' | 'restock_item' | 'open_chat' | 'navigate';
  payload: Record<string, unknown>;
}

interface Suggestion {
  id: string;
  icon: string;
  message: string;
  priority: number;
  context: string;
  actions: SuggestionAction[];
}

const ICON_MAP: Record<string, string> = {
  alert: '!',
  inventory: '~',
  clock: ':',
  bag: '*',
  warning: '!',
  snooze: 'z',
  assign: '>',
};

const PRIORITY_STYLES: Record<number, string> = {
  1: 'border-danger/30 bg-danger/5',
  2: 'border-accent/30 bg-accent/5',
  3: 'border-primary/20 bg-primary/5',
};

const ICON_STYLES: Record<number, string> = {
  1: 'bg-danger/15 text-danger',
  2: 'bg-accent/15 text-accent',
  3: 'bg-primary/15 text-primary',
};

interface AISuggestionBarProps {
  page?: string;
  maxItems?: number;
  compact?: boolean;
}

export default function AISuggestionBar({ page = 'all', maxItems = 3, compact = false }: AISuggestionBarProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { createTask } = useTaskStore();
  const { restockItem } = useInventoryStore();

  useEffect(() => {
    api.get(`/ai/suggestions?page=${page}`)
      .then(({ data }) => setSuggestions(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page]);

  const handleAction = async (action: SuggestionAction, suggestionId: string) => {
    switch (action.action_type) {
      case 'navigate':
        router.push(action.payload.path as string);
        break;
      case 'create_task':
        try {
          await createTask(action.payload as never);
          toast('Taak aangemaakt', 'success');
          setDismissed((prev) => new Set([...prev, suggestionId]));
        } catch {
          toast('Kon taak niet aanmaken', 'error');
        }
        break;
      case 'restock_item':
        try {
          await restockItem(action.payload.item_id as string, 0);
          toast('Item bijgevuld', 'success');
          setDismissed((prev) => new Set([...prev, suggestionId]));
        } catch {
          toast('Kon item niet bijvullen', 'error');
        }
        break;
      case 'open_chat':
        // Store message in sessionStorage so chat page can pick it up
        sessionStorage.setItem('chat_prefill', action.payload.message as string);
        router.push('/chat');
        break;
    }
  };

  const dismiss = (id: string) => {
    setDismissed((prev) => new Set([...prev, id]));
  };

  const visible = suggestions
    .filter((s) => !dismissed.has(s.id))
    .slice(0, maxItems);

  if (loading || visible.length === 0) return null;

  if (compact) {
    return (
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
        {visible.map((s) => (
          <button
            key={s.id}
            onClick={() => s.actions[0] && handleAction(s.actions[0], s.id)}
            className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-medium whitespace-nowrap
              transition-all hover:shadow-sm shrink-0 ${PRIORITY_STYLES[s.priority] || PRIORITY_STYLES[3]}`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${ICON_STYLES[s.priority] || ICON_STYLES[3]}`}>
              {ICON_MAP[s.icon] || '?'}
            </span>
            <span className="text-text-main">{s.message.length > 50 ? s.message.slice(0, 50) + '...' : s.message}</span>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {visible.map((s) => (
        <div
          key={s.id}
          className={`relative rounded-xl border p-3 transition-all ${PRIORITY_STYLES[s.priority] || PRIORITY_STYLES[3]}`}
        >
          <button
            onClick={() => dismiss(s.id)}
            className="absolute top-2 right-2 text-text-muted hover:text-text-main text-xs p-1"
            aria-label="Sluiten"
          >
            x
          </button>

          <div className="flex items-start gap-2.5 pr-6">
            <span className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mt-0.5 ${ICON_STYLES[s.priority] || ICON_STYLES[3]}`}>
              {ICON_MAP[s.icon] || '?'}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-text-main leading-snug">{s.message}</p>
              {s.actions.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {s.actions.map((action, i) => (
                    <button
                      key={i}
                      onClick={() => handleAction(action, s.id)}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors
                        ${i === 0
                          ? 'bg-primary text-white hover:bg-primary-light'
                          : 'bg-surface-alt text-text-muted hover:bg-border'
                        }`}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
