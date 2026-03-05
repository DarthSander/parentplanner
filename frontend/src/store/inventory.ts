import { create } from 'zustand';
import api from '@/lib/api';

export interface InventoryItem {
  id: string;
  household_id: string;
  name: string;
  category: string | null;
  current_quantity: number;
  unit: string;
  threshold_quantity: number;
  average_consumption_rate: number | null;
  last_restocked_at: string | null;
  preferred_store_url: string | null;
  created_at: string;
  updated_at: string;
}

interface InventoryStore {
  items: InventoryItem[];
  loading: boolean;
  fetchItems: () => Promise<void>;
  addItem: (item: InventoryItem) => void;
  updateItem: (item: InventoryItem) => void;
  removeItem: (id: string) => void;
  createItem: (data: Partial<InventoryItem>) => Promise<InventoryItem>;
  patchItem: (id: string, data: Partial<InventoryItem>) => Promise<InventoryItem>;
  reportLow: (id: string, message: string) => Promise<void>;
  restockItem: (id: string, quantity: number) => Promise<void>;
}

export const useInventoryStore = create<InventoryStore>((set, get) => ({
  items: [],
  loading: false,

  fetchItems: async () => {
    set({ loading: true });
    try {
      const { data } = await api.get('/inventory');
      set({ items: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  addItem: (item) => set((s) => ({ items: [...s.items, item] })),

  updateItem: (item) =>
    set((s) => ({
      items: s.items.map((i) => (i.id === item.id ? { ...i, ...item } : i)),
    })),

  removeItem: (id) =>
    set((s) => ({ items: s.items.filter((i) => i.id !== id) })),

  createItem: async (data) => {
    const { data: item } = await api.post('/inventory', data);
    set((s) => ({ items: [...s.items, item] }));
    return item;
  },

  patchItem: async (id, data) => {
    const { data: item } = await api.patch(`/inventory/${id}`, data);
    get().updateItem(item);
    return item;
  },

  reportLow: async (id, message) => {
    await api.post(`/inventory/${id}/report-low`, { message });
  },

  restockItem: async (id, quantity) => {
    const { data: item } = await api.post(`/inventory/${id}/restock`, { quantity });
    get().updateItem(item);
  },
}));
