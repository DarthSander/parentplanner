'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function GeneratingPage() {
  const router = useRouter();

  useEffect(() => {
    // AI generation happens server-side, redirect after a delay
    const timer = setTimeout(() => {
      router.push('/dashboard');
    }, 5000);
    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div className="text-center max-w-sm">
        <div className="mb-6">
          <svg className="animate-spin mx-auto w-12 h-12 text-primary" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        </div>
        <h2 className="text-xl font-display font-semibold text-primary mb-2">AI denkt mee...</h2>
        <p className="text-sm text-text-muted">
          We maken een startpakket op maat met taken, een voorraadlijst en een slimme verdeling.
        </p>
      </div>
    </div>
  );
}
