'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { getAccessToken } from '@/lib/auth';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card from '@/components/ui/Card';
import { toast } from '@/components/ui/Toast';

const painPointOptions = [
  { value: 'sleep_deprivation', label: 'Slaaptekort' },
  { value: 'task_distribution', label: 'Taakverdeling' },
  { value: 'groceries', label: 'Boodschappen vergeten' },
  { value: 'schedule', label: 'Agenda-chaos' },
  { value: 'finances', label: 'Financien bijhouden' },
];

const dayOptions = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
const dayLabels: Record<string, string> = {
  monday: 'Ma', tuesday: 'Di', wednesday: 'Wo', thursday: 'Do', friday: 'Vr',
};

// Total steps: 0 = welcome, 1 = gezin opzetten, 2 = kind, 3 = werk/opvang, 4 = pijnpunten
const TOTAL_STEPS = 4;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace('/auth/login');
    }
  }, [router]);

  // Step 1: Gezin opzetten
  const [partnerName, setPartnerName] = useState('');
  const [partnerEmail, setPartnerEmail] = useState('');
  const [hasPartner, setHasPartner] = useState(true);
  const [caregiverName, setCaregiverName] = useState('');
  const [caregiverEmail, setCaregiverEmail] = useState('');
  const [hasCaregiver, setHasCaregiver] = useState(false);
  const [invitesSent, setInvitesSent] = useState(false);

  // Step 2: Kind
  const [childName, setChildName] = useState('');
  const [childAgeWeeks, setChildAgeWeeks] = useState('');
  const [situation, setSituation] = useState('couple');
  const [workOwner, setWorkOwner] = useState('fulltime');
  const [workPartner, setWorkPartner] = useState('fulltime');
  const [daycareDays, setDaycareDays] = useState<string[]>([]);

  // Step 4: Pijnpunten
  const [painPoints, setPainPoints] = useState<string[]>([]);
  const [debugError, setDebugError] = useState('');

  const toggleDay = (day: string) => {
    setDaycareDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day],
    );
  };

  const togglePainPoint = (pp: string) => {
    setPainPoints((prev) =>
      prev.includes(pp) ? prev.filter((p) => p !== pp) : [...prev, pp],
    );
  };

  const handleSendInvites = async () => {
    const invites = [];
    if (hasPartner && partnerEmail && partnerName) {
      invites.push({ email: partnerEmail, display_name: partnerName, role: 'partner' });
    }
    if (hasCaregiver && caregiverEmail && caregiverName) {
      invites.push({ email: caregiverEmail, display_name: caregiverName, role: 'caregiver' });
    }

    if (invites.length === 0) {
      setStep(2);
      return;
    }

    setLoading(true);
    const errors: string[] = [];
    for (const invite of invites) {
      try {
        await api.post('/members/invite', invite);
      } catch {
        errors.push(invite.display_name);
      }
    }
    setLoading(false);
    setInvitesSent(true);

    if (errors.length > 0) {
      toast(`Uitnodiging mislukt voor: ${errors.join(', ')}`, 'error');
    } else {
      toast('Uitnodigingen verstuurd!', 'success');
    }
    setStep(2);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setDebugError('');
    try {
      // Ensure household exists (created by register page, fallback just in case)
      try {
        await api.get('/households/me');
      } catch {
        await api.post('/households', { name: 'Mijn gezin' });
      }

      await api.post('/onboarding', {
        child_name: childName || undefined,
        child_age_weeks: childAgeWeeks ? parseInt(childAgeWeeks) : undefined,
        situation,
        work_situation_owner: workOwner,
        work_situation_partner: situation === 'couple' ? workPartner : undefined,
        daycare_days: daycareDays.length > 0 ? daycareDays : undefined,
        has_caregiver: hasCaregiver,
        pain_points: painPoints.length > 0 ? painPoints : undefined,
      });
      router.push('/onboarding/generating');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : JSON.stringify(err);
      const status = (err as { response?: { status: number; data: unknown } })?.response?.status;
      const data = (err as { response?: { status: number; data: unknown } })?.response?.data;
      setDebugError(`Status: ${status} | ${msg} | ${JSON.stringify(data)}`);
    } finally {
      setLoading(false);
    }
  };

  // Welcome screen
  if (step === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
        <div className="max-w-sm text-center">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
            <span className="text-3xl">🏠</span>
          </div>
          <h1 className="text-3xl font-display font-semibold text-primary mb-4">Welkom bij GezinsAI</h1>
          <p className="text-text-muted mb-8">
            We stellen een paar vragen om je gezinssituatie te begrijpen.
            De AI maakt daarna een persoonlijk startpakket aan.
          </p>
          <Button onClick={() => setStep(1)} className="w-full">Start (4 stappen)</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="max-w-sm mx-auto space-y-6">
        {/* Progress bar (steps 1-4) */}
        <div className="flex gap-1">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className={`h-1 flex-1 rounded-full transition-colors ${step >= s ? 'bg-primary' : 'bg-border'}`} />
          ))}
        </div>

        {/* Step 1: Gezin opzetten */}
        {step === 1 && (
          <Card padding="lg">
            <h2 className="text-lg font-display font-semibold mb-1">Je gezin</h2>
            <p className="text-sm text-text-muted mb-4">Wie doet er mee? Je kan ook later mensen toevoegen.</p>

            <div className="space-y-4">
              {/* Partner */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <input
                    type="checkbox"
                    id="has-partner"
                    checked={hasPartner}
                    onChange={(e) => setHasPartner(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="has-partner" className="text-sm font-medium">Ik heb een partner</label>
                </div>
                {hasPartner && (
                  <div className="pl-6 space-y-2">
                    <Input
                      label="Naam partner"
                      value={partnerName}
                      onChange={(e) => setPartnerName(e.target.value)}
                      placeholder="Voornaam"
                    />
                    <Input
                      label="E-mail partner"
                      type="email"
                      value={partnerEmail}
                      onChange={(e) => setPartnerEmail(e.target.value)}
                      placeholder="partner@email.nl"
                    />
                  </div>
                )}
              </div>

              {/* Caregiver */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <input
                    type="checkbox"
                    id="has-caregiver"
                    checked={hasCaregiver}
                    onChange={(e) => setHasCaregiver(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="has-caregiver" className="text-sm font-medium">Er is een oppas (oma, nanny, etc.)</label>
                </div>
                {hasCaregiver && (
                  <div className="pl-6 space-y-2">
                    <Input
                      label="Naam oppas"
                      value={caregiverName}
                      onChange={(e) => setCaregiverName(e.target.value)}
                      placeholder="Voornaam"
                    />
                    <Input
                      label="E-mail oppas"
                      type="email"
                      value={caregiverEmail}
                      onChange={(e) => setCaregiverEmail(e.target.value)}
                      placeholder="oppas@email.nl"
                    />
                  </div>
                )}
              </div>

              <p className="text-xs text-text-muted">
                Uitnodigingen worden per e-mail verstuurd. Ze kunnen daarna inloggen en meedoen.
              </p>

              <Button
                onClick={handleSendInvites}
                loading={loading}
                className="w-full"
              >
                {(hasPartner && partnerEmail) || (hasCaregiver && caregiverEmail)
                  ? 'Verstuur uitnodigingen en ga verder'
                  : 'Overslaan, ga verder'}
              </Button>
            </div>
          </Card>
        )}

        {/* Step 2: Kind */}
        {step === 2 && (
          <Card padding="lg">
            <h2 className="text-lg font-display font-semibold mb-4">Over je kind</h2>
            <div className="space-y-4">
              <Input label="Naam kind (optioneel)" value={childName} onChange={(e) => setChildName(e.target.value)} />
              <Input
                label="Leeftijd in weken"
                type="number"
                value={childAgeWeeks}
                onChange={(e) => setChildAgeWeeks(e.target.value)}
                min={0}
                max={260}
              />
              <div>
                <label className="text-sm font-medium block mb-1">Gezinssituatie</label>
                <select
                  value={situation}
                  onChange={(e) => setSituation(e.target.value)}
                  className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm"
                >
                  <option value="couple">Koppel</option>
                  <option value="single">Alleenstaand</option>
                  <option value="co_parent">Co-ouderschap</option>
                </select>
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => setStep(1)}>Terug</Button>
                <Button onClick={() => setStep(3)} className="flex-1">Volgende</Button>
              </div>
            </div>
          </Card>
        )}

        {/* Step 3: Werk en opvang */}
        {step === 3 && (
          <Card padding="lg">
            <h2 className="text-lg font-display font-semibold mb-4">Werk en opvang</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-1">Jouw werksituatie</label>
                <select
                  value={workOwner}
                  onChange={(e) => setWorkOwner(e.target.value)}
                  className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm"
                >
                  <option value="fulltime">Voltijd</option>
                  <option value="parttime">Deeltijd</option>
                  <option value="leave">Verlof</option>
                  <option value="none">Niet werkend</option>
                </select>
              </div>
              {situation === 'couple' && (
                <div>
                  <label className="text-sm font-medium block mb-1">Werksituatie partner</label>
                  <select
                    value={workPartner}
                    onChange={(e) => setWorkPartner(e.target.value)}
                    className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm"
                  >
                    <option value="fulltime">Voltijd</option>
                    <option value="parttime">Deeltijd</option>
                    <option value="leave">Verlof</option>
                    <option value="none">Niet werkend</option>
                  </select>
                </div>
              )}
              <div>
                <label className="text-sm font-medium block mb-2">Opvangdagen</label>
                <div className="flex gap-2">
                  {dayOptions.map((day) => (
                    <button
                      key={day}
                      type="button"
                      onClick={() => toggleDay(day)}
                      className={`w-10 h-10 rounded-full text-xs font-medium transition-colors
                        ${daycareDays.includes(day) ? 'bg-primary text-white' : 'bg-surface-alt text-text-muted'}`}
                    >
                      {dayLabels[day]}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => setStep(2)}>Terug</Button>
                <Button onClick={() => setStep(4)} className="flex-1">Volgende</Button>
              </div>
            </div>
          </Card>
        )}

        {/* Step 4: Pijnpunten */}
        {step === 4 && (
          <Card padding="lg">
            <h2 className="text-lg font-display font-semibold mb-2">Waar loop je tegenaan?</h2>
            <p className="text-sm text-text-muted mb-4">De AI leert hiervan en houdt er rekening mee.</p>
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {painPointOptions.map((pp) => (
                  <button
                    key={pp.value}
                    type="button"
                    onClick={() => togglePainPoint(pp.value)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-colors
                      ${painPoints.includes(pp.value)
                        ? 'bg-primary text-white'
                        : 'bg-surface-alt text-text-muted'
                      }`}
                  >
                    {pp.label}
                  </button>
                ))}
              </div>
              {debugError && (
                <p className="text-xs bg-red-50 border border-red-200 rounded p-2 break-all text-red-700">
                  {debugError}
                </p>
              )}
              <div className="flex gap-2 pt-2">
                <Button variant="secondary" onClick={() => setStep(3)}>Terug</Button>
                <Button onClick={handleSubmit} loading={loading} className="flex-1">
                  Klaar, genereer mijn plan!
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
