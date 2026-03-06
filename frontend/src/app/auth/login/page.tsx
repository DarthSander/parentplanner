'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { signIn } from '@/lib/auth';
import api from '@/lib/api';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const session = await signIn(email, password);
      console.log('[login] signIn ok', session);

      let hasHousehold = false;
      try {
        const resp = await api.get('/households/me');
        console.log('[login] household found', resp.data);
        hasHousehold = true;
      } catch (householdErr: unknown) {
        const status = (householdErr as { response?: { status: number } })?.response?.status;
        console.log('[login] household check status:', status);
      }

      if (hasHousehold) {
        router.push('/dashboard');
      } else {
        router.push('/onboarding');
      }
    } catch (err: unknown) {
      console.error('[login] error:', err);
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes('Email not confirmed')) {
        setError('Bevestig eerst je e-mailadres via de link die we hebben gestuurd.');
      } else {
        setError(`Inloggen mislukt: ${msg}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-display font-semibold text-primary text-center mb-2">GezinsAI</h1>
        <p className="text-text-muted text-center mb-8">Log in om verder te gaan</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            label="E-mail"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="je@email.nl"
            required
            autoFocus
          />
          <Input
            label="Wachtwoord"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Wachtwoord"
            required
          />

          {error && <p className="text-sm text-danger">{error}</p>}

          <Button type="submit" loading={loading} className="w-full">
            Inloggen
          </Button>
        </form>

        <p className="text-sm text-text-muted text-center mt-6">
          Nog geen account?{' '}
          <Link href="/auth/register" className="text-primary font-medium hover:underline">
            Registreer
          </Link>
        </p>
      </div>
    </div>
  );
}
