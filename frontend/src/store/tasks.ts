import { create } from 'zustand';
import api from '@/lib/api';

export interface Task {
  id: string;
  household_id: string;
  title: string;
  description: string | null;
  category: 'baby_care' | 'household' | 'work' | 'private';
  task_type: 'quick' | 'prep';
  assigned_to: string | null;
  due_date: string | null;
  recurrence_rule: string | null;
  estimated_minutes: number | null;
  dependencies: string[] | null;
  status: 'open' | 'in_progress' | 'done' | 'snoozed';
  snooze_count: number;
  ai_generated: boolean;
  version: number;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

interface TaskStore {
  tasks: Task[];
  loading: boolean;
  fetchTasks: () => Promise<void>;
  addTask: (task: Task) => void;
  updateTask: (task: Task) => void;
  removeTask: (id: string) => void;
  createTask: (data: Partial<Task>) => Promise<Task>;
  patchTask: (id: string, data: Partial<Task> & { version: number }) => Promise<Task>;
  completeTask: (id: string) => Promise<void>;
  snoozeTask: (id: string) => Promise<void>;
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  loading: false,

  fetchTasks: async () => {
    set({ loading: true });
    try {
      const { data } = await api.get('/tasks');
      set({ tasks: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  addTask: (task) => set((s) => ({ tasks: [...s.tasks, task] })),

  updateTask: (task) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.id === task.id ? { ...t, ...task } : t)),
    })),

  removeTask: (id) =>
    set((s) => ({ tasks: s.tasks.filter((t) => t.id !== id) })),

  createTask: async (data) => {
    const { data: task } = await api.post('/tasks', data);
    set((s) => ({ tasks: [...s.tasks, task] }));
    return task;
  },

  patchTask: async (id, data) => {
    const { data: task } = await api.patch(`/tasks/${id}`, data);
    get().updateTask(task);
    return task;
  },

  completeTask: async (id) => {
    await api.post(`/tasks/${id}/complete`);
    get().updateTask({ id, status: 'done' } as Task);
  },

  snoozeTask: async (id) => {
    const { data: task } = await api.post(`/tasks/${id}/snooze`);
    get().updateTask(task);
  },
}));
