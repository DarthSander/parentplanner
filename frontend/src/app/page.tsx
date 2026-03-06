'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken } from '@/lib/auth';
import api from '@/lib/api';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    (async () => {
      const token = getAccessToken();
      if (!token) {
        router.replace('/auth/login');
        return;
      }
      try {
        await api.get('/households/me');
        router.replace('/dashboard');
      } catch {
        router.replace('/onboarding');
      }
    })();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <h1 className="text-3xl font-display font-semibold text-primary mb-2">GezinsAI</h1>
        <p className="text-text-muted">Laden...</p>
      </div>
    </div>
  );
}
