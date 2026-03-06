'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/auth/login');
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div className="text-center">
        <h1 className="text-3xl font-display font-semibold text-primary mb-2">GezinsAI</h1>
        <p className="text-text-muted">Doorsturen...</p>
      </div>
    </div>
  );
}
