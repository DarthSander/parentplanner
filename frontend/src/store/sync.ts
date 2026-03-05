import { create } from 'zustand';
import api from '@/lib/api';
import { getPendingOperations, removeSyncOperation } from '@/lib/offline';

export interface ConflictData {
  syncOpId: string;
  localVersion: Record<string, unknown>;
  serverVersion: Record<string, unknown>;
  resourceType: string;
}

interface SyncStore {
  isOnline: boolean;
  isSyncing: boolean;
  pendingCount: number;
  conflicts: ConflictData[];
  setOnline: (online: boolean) => void;
  syncPendingOperations: () => Promise<void>;
  resolveConflict: (syncOpId: string, resolution: 'keep_local' | 'keep_server') => void;
  refreshPendingCount: () => Promise<void>;
}

export const useSyncStore = create<SyncStore>((set, get) => ({
  isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
  isSyncing: false,
  pendingCount: 0,
  conflicts: [],

  setOnline: (online) => {
    set({ isOnline: online });
    if (online) get().syncPendingOperations();
  },

  syncPendingOperations: async () => {
    const pending = await getPendingOperations();
    if (pending.length === 0) return;

    set({ isSyncing: true });
    try {
      const { data } = await api.post('/sync', pending);
      const newConflicts: ConflictData[] = [];

      for (const result of data.results) {
        if (result.status === 'ok') {
          await removeSyncOperation(result.id);
        } else if (result.status === 'conflict') {
          const op = pending.find((p) => p.id === result.id);
          if (op) {
            newConflicts.push({
              syncOpId: result.id,
              localVersion: op.payload as Record<string, unknown>,
              serverVersion: result.server_version ?? {},
              resourceType: op.resource_type,
            });
          }
        }
      }

      set({ conflicts: newConflicts });
    } catch {
      // Will retry next time
    } finally {
      set({ isSyncing: false });
      get().refreshPendingCount();
    }
  },

  resolveConflict: (syncOpId, resolution) => {
    if (resolution === 'keep_server') {
      removeSyncOperation(syncOpId);
    }
    set((s) => ({
      conflicts: s.conflicts.filter((c) => c.syncOpId !== syncOpId),
    }));
  },

  refreshPendingCount: async () => {
    const pending = await getPendingOperations();
    set({ pendingCount: pending.length });
  },
}));
