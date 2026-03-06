'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { signUp } from '@/lib/auth';
import api from '@/lib/api';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [householdName, setHouseholdName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await signUp(email, password, displayName);
      // Create household after registration
      await api.post('/households', {
        name: householdName || `${displayName}'s gezin`,
        display_name: displayName,
      });
      router.push('/onboarding');
    } catch {
      setError('Registratie mislukt. Probeer het opnieuw.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-display font-semibold text-primary text-center mb-2">GezinsAI</h1>
        <p className="text-text-muted text-center mb-8">Maak een account aan</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            label="Jouw naam"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Voornaam"
            required
            autoFocus
          />
          <Input
            label="Naam van je gezin"
            value={householdName}
            onChange={(e) => setHouseholdName(e.target.value)}
            placeholder="Bijv. Familie De Vries"
          />
          <Input
            label="E-mail"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="je@email.nl"
            required
          />
          <Input
            label="Wachtwoord"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Minimaal 8 tekens"
            required
            minLength={8}
          />

          {error && <p className="text-sm text-danger">{error}</p>}

          <Button type="submit" loading={loading} className="w-full">
            Account aanmaken
          </Button>
        </form>

        <p className="text-sm text-text-muted text-center mt-6">
          Al een account?{' '}
          <Link href="/auth/login" className="text-primary font-medium hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
