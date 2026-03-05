import { RealtimeChannel } from '@supabase/supabase-js';
import { getSupabase } from './auth';
import { useTaskStore } from '@/store/tasks';
import { useInventoryStore } from '@/store/inventory';

let channel: RealtimeChannel | null = null;

export function subscribeToHousehold(householdId: string): () => void {
  const supabase = getSupabase();

  channel = supabase
    .channel(`household:${householdId}`)
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'tasks',
        filter: `household_id=eq.${householdId}`,
      },
      (payload) => {
        const store = useTaskStore.getState();
        if (payload.eventType === 'UPDATE') store.updateTask(payload.new as never);
        if (payload.eventType === 'INSERT') store.addTask(payload.new as never);
        if (payload.eventType === 'DELETE') store.removeTask(payload.old.id);
      },
    )
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'inventory_items',
        filter: `household_id=eq.${householdId}`,
      },
      (payload) => {
        const store = useInventoryStore.getState();
        if (payload.eventType === 'UPDATE') store.updateItem(payload.new as never);
        if (payload.eventType === 'INSERT') store.addItem(payload.new as never);
        if (payload.eventType === 'DELETE') store.removeItem(payload.old.id);
      },
    )
    .subscribe();

  return () => {
    if (channel) {
      supabase.removeChannel(channel);
      channel = null;
    }
  };
}
