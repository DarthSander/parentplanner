'use client';

import Avatar from '@/components/ui/Avatar';
import { useHouseholdStore } from '@/store/household';
import { useSyncStore } from '@/store/sync';

export default function Header() {
  const { household, currentMember } = useHouseholdStore();
  const { isOnline, isSyncing, pendingCount } = useSyncStore();

  return (
    <header className="sticky top-0 z-30 bg-surface border-b border-border">
      <div className="flex items-center justify-between h-14 px-4 max-w-lg mx-auto">
        <div>
          <h1 className="text-lg font-display font-semibold text-primary">
            {household?.name || 'GezinsAI'}
          </h1>
          {!isOnline && (
            <span className="text-[10px] text-warning font-medium">Offline</span>
          )}
          {isSyncing && (
            <span className="text-[10px] text-primary-light font-medium">Synchroniseren...</span>
          )}
          {!isSyncing && pendingCount > 0 && isOnline && (
            <span className="text-[10px] text-text-muted">{pendingCount} wachtend</span>
          )}
        </div>
        {currentMember && (
          <Avatar
            name={currentMember.display_name}
            url={currentMember.avatar_url}
            size="sm"
          />
        )}
      </div>
    </header>
  );
}
