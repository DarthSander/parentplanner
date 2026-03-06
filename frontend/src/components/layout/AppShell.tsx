'use client';

import { useEffect } from 'react';
import Header from './Header';
import BottomNav from './BottomNav';
import ToastContainer from '@/components/ui/Toast';
import { useHouseholdStore } from '@/store/household';
import { useSyncStore } from '@/store/sync';
import { subscribeToHousehold } from '@/lib/realtime';

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { household, fetchHousehold, fetchMembers } = useHouseholdStore();
  const { setOnline, syncPendingOperations, refreshPendingCount } = useSyncStore();

  // Load household data on mount
  useEffect(() => {
    fetchHousehold();
    fetchMembers();
    refreshPendingCount();
  }, [fetchHousehold, fetchMembers, refreshPendingCount]);

  // Online/offline listeners
  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [setOnline]);

  // Sync pending operations on mount
  useEffect(() => {
    syncPendingOperations();
  }, [syncPendingOperations]);

  // Realtime subscription via SSE
  useEffect(() => {
    const unsubscribe = subscribeToHousehold();
    return unsubscribe;
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pb-20 max-w-lg mx-auto px-4 py-4">
        {children}
      </main>
      <BottomNav />
      <ToastContainer />
    </div>
  );
}
