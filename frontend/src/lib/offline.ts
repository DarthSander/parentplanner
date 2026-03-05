import { openDB, IDBPDatabase } from 'idb';

const DB_NAME = 'gezinsai-offline';
const SYNC_STORE = 'syncQueue';
const CACHE_STORE = 'dataCache';
const DB_VERSION = 1;

interface SyncOperation {
  id: string;
  operation: 'create' | 'update' | 'delete';
  resource_type: string;
  resource_id?: string;
  payload: Record<string, unknown>;
  client_timestamp: string;
  processed: boolean;
}

let dbInstance: IDBPDatabase | null = null;

export async function getOfflineDB(): Promise<IDBPDatabase> {
  if (dbInstance) return dbInstance;

  dbInstance = await openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(SYNC_STORE)) {
        db.createObjectStore(SYNC_STORE, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(CACHE_STORE)) {
        db.createObjectStore(CACHE_STORE, { keyPath: 'key' });
      }
    },
  });

  return dbInstance;
}

export async function queueOfflineOperation(op: Omit<SyncOperation, 'client_timestamp' | 'processed'>) {
  const db = await getOfflineDB();
  await db.add(SYNC_STORE, {
    ...op,
    client_timestamp: new Date().toISOString(),
    processed: false,
  });

  // Trigger background sync if available
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    const registration = await navigator.serviceWorker.ready;
    await (registration as unknown as { sync: { register: (tag: string) => Promise<void> } }).sync.register('sync-queue');
  }
}

export async function getPendingOperations(): Promise<SyncOperation[]> {
  const db = await getOfflineDB();
  return db.getAll(SYNC_STORE);
}

export async function removeSyncOperation(id: string) {
  const db = await getOfflineDB();
  await db.delete(SYNC_STORE, id);
}

export async function cacheData(key: string, data: unknown) {
  const db = await getOfflineDB();
  await db.put(CACHE_STORE, { key, data, cached_at: new Date().toISOString() });
}

export async function getCachedData<T>(key: string): Promise<T | null> {
  const db = await getOfflineDB();
  const result = await db.get(CACHE_STORE, key);
  return result?.data ?? null;
}
