'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getSession } from '@/lib/auth';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    getSession().then((session) => {
      if (session) {
        router.replace('/dashboard');
      } else {
        router.replace('/auth/login');
      }
    });
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
