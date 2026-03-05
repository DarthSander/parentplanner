'use client';

import { useSyncStore } from '@/store/sync';

export default function SyncStatusBar() {
  const { isOnline, isSyncing, pendingCount } = useSyncStore();

  if (isOnline && !isSyncing && pendingCount === 0) return null;

  return (
    <div className={`px-4 py-2 text-xs font-medium text-center ${
      !isOnline ? 'bg-warning/10 text-warning' :
      isSyncing ? 'bg-primary/10 text-primary' :
      'bg-surface-alt text-text-muted'
    }`}>
      {!isOnline && 'Je bent offline. Wijzigingen worden later gesynchroniseerd.'}
      {isOnline && isSyncing && 'Synchroniseren...'}
      {isOnline && !isSyncing && pendingCount > 0 && `${pendingCount} wijziging(en) wachten op synchronisatie`}
    </div>
  );
}
