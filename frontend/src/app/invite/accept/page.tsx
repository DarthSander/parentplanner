'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import api from '@/lib/api';
import Button from '@/components/ui/Button';

function InviteAcceptContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');
  const [invite, setInvite] = useState<{ household_name: string; role: string; inviter_name: string } | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('Geen uitnodigingstoken gevonden.');
      setLoading(false);
      return;
    }
    api.get(`/members/invite/validate?token=${token}`)
      .then(({ data }) => setInvite(data))
      .catch(() => setError('Deze uitnodiging is ongeldig of verlopen.'))
      .finally(() => setLoading(false));
  }, [token]);

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await api.post('/members/invite/accept', { token });
      router.push('/dashboard');
    } catch {
      setError('Kon uitnodiging niet accepteren. Ben je ingelogd?');
    } finally {
      setAccepting(false);
    }
  };

  if (loading) return <p className="text-text-muted">Uitnodiging laden...</p>;
  if (error) return <p className="text-danger">{error}</p>;

  return (
    <div className="text-center">
      <h2 className="text-xl font-display font-semibold mb-4">Je bent uitgenodigd!</h2>
      <p className="text-text-muted mb-6">
        {invite?.inviter_name} heeft je uitgenodigd als <strong>{invite?.role}</strong> voor{' '}
        <strong>{invite?.household_name}</strong>.
      </p>
      <Button onClick={handleAccept} loading={accepting}>
        Uitnodiging accepteren
      </Button>
    </div>
  );
}

export default function InviteAcceptPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm bg-surface rounded-lg shadow-md p-6">
        <Suspense fallback={<p className="text-text-muted">Laden...</p>}>
          <InviteAcceptContent />
        </Suspense>
      </div>
    </div>
  );
}
