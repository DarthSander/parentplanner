'use client';

import Link from 'next/link';

export default function CheckEmailPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm text-center">
        <h1 className="text-3xl font-display font-semibold text-primary mb-2">GezinsAI</h1>
        <div className="mt-8 p-6 bg-surface rounded-2xl shadow-sm border border-border">
          <div className="text-4xl mb-4">✉️</div>
          <h2 className="text-xl font-semibold mb-2">Check je e-mail</h2>
          <p className="text-text-muted text-sm mb-4">
            We hebben een bevestigingslink gestuurd. Klik op de link in de mail om je account te activeren.
          </p>
          <p className="text-xs text-text-muted">
            Geen mail ontvangen?{' '}
            <Link href="/auth/register" className="text-primary hover:underline">
              Probeer opnieuw
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
