import { create } from 'zustand';
import api from '@/lib/api';

interface Member {
  id: string;
  household_id: string;
  role: 'owner' | 'partner' | 'caregiver' | 'daycare';
  display_name: string;
  email: string | null;
  avatar_url: string | null;
  created_at: string;
}

interface Household {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

interface HouseholdStore {
  household: Household | null;
  members: Member[];
  currentMember: Member | null;
  loading: boolean;
  fetchHousehold: () => Promise<void>;
  fetchMembers: () => Promise<void>;
  setCurrentMember: (member: Member) => void;
}

export const useHouseholdStore = create<HouseholdStore>((set) => ({
  household: null,
  members: [],
  currentMember: null,
  loading: false,

  fetchHousehold: async () => {
    set({ loading: true });
    try {
      const { data } = await api.get('/households/me');
      set({ household: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchMembers: async () => {
    try {
      const { data } = await api.get('/members');
      set({ members: data });
    } catch {
      // silent
    }
  },

  setCurrentMember: (member) => set({ currentMember: member }),
}));
