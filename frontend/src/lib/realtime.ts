/**
 * Realtime via Server-Sent Events — replaces Supabase Realtime.
 *
 * The backend SSE endpoint is GET /sse (authenticated via Bearer token).
 * Events have the shape:  event: <type>\ndata: <json>\n\n
 *
 * Event types:
 *   task.created / task.updated / task.deleted
 *   inventory.created / inventory.updated / inventory.deleted
 */

import { useTaskStore } from '@/store/tasks';
import { useInventoryStore } from '@/store/inventory';
import api from './api';

let eventSource: EventSource | null = null;

function buildSSEUrl(): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  // Pass token as query param since EventSource does not support custom headers
  return `${baseUrl}/sse${token ? `?token=${encodeURIComponent(token)}` : ''}`;
}

async function fetchFullTask(id: string) {
  try {
    const { data } = await api.get(`/tasks/${id}`);
    return data;
  } catch {
    return null;
  }
}

async function fetchFullItem(id: string) {
  try {
    const { data } = await api.get(`/inventory/${id}`);
    return data;
  } catch {
    return null;
  }
}

export function subscribeToHousehold(): () => void {
  if (typeof window === 'undefined') return () => {};
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }

  const url = buildSSEUrl();
  eventSource = new EventSource(url);

  eventSource.addEventListener('task.created', async (e: MessageEvent) => {
    const { id } = JSON.parse(e.data);
    const task = await fetchFullTask(id);
    if (task) useTaskStore.getState().addTask(task);
  });

  eventSource.addEventListener('task.updated', async (e: MessageEvent) => {
    const { id } = JSON.parse(e.data);
    const task = await fetchFullTask(id);
    if (task) useTaskStore.getState().updateTask(task);
  });

  eventSource.addEventListener('task.deleted', (e: MessageEvent) => {
    const { id } = JSON.parse(e.data);
    useTaskStore.getState().removeTask(id);
  });

  eventSource.addEventListener('inventory.created', async (e: MessageEvent) => {
    const { id } = JSON.parse(e.data);
    const item = await fetchFullItem(id);
    if (item) useInventoryStore.getState().addItem(item);
  });

  eventSource.addEventListener('inventory.updated', async (e: MessageEvent) => {
    const { id } = JSON.parse(e.data);
    const item = await fetchFullItem(id);
    if (item) useInventoryStore.getState().updateItem(item);
  });

  eventSource.addEventListener('inventory.deleted', (e: MessageEvent) => {
    const { id } = JSON.parse(e.data);
    useInventoryStore.getState().removeItem(id);
  });

  eventSource.onerror = () => {
    // Browser will auto-reconnect for EventSource on network errors
  };

  return () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  };
}
