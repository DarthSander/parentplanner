'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
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

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);

  // Form state
  const [childName, setChildName] = useState('');
  const [childAgeWeeks, setChildAgeWeeks] = useState('');
  const [situation, setSituation] = useState('couple');
  const [workOwner, setWorkOwner] = useState('fulltime');
  const [workPartner, setWorkPartner] = useState('fulltime');
  const [daycareDays, setDaycareDays] = useState<string[]>([]);
  const [hasCaregiver, setHasCaregiver] = useState(false);
  const [painPoints, setPainPoints] = useState<string[]>([]);

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

  const handleSubmit = async () => {
    setLoading(true);
    try {
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
    } catch {
      toast('Er ging iets mis. Probeer het opnieuw.', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (step === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
        <div className="max-w-sm text-center">
          <h1 className="text-3xl font-display font-semibold text-primary mb-4">Welkom bij GezinsAI</h1>
          <p className="text-text-muted mb-8">
            We stellen een paar vragen om je gezinssituatie te begrijpen.
            De AI maakt daarna een startpakket op maat.
          </p>
          <Button onClick={() => setStep(1)} className="w-full">Start</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="max-w-sm mx-auto space-y-6">
        <div className="flex gap-1">
          {[1, 2, 3].map((s) => (
            <div key={s} className={`h-1 flex-1 rounded-full ${step >= s ? 'bg-primary' : 'bg-border'}`} />
          ))}
        </div>

        {step === 1 && (
          <Card padding="lg">
            <h2 className="text-lg font-display font-semibold mb-4">Over je kind</h2>
            <div className="space-y-4">
              <Input label="Naam kind (optioneel)" value={childName} onChange={(e) => setChildName(e.target.value)} />
              <Input label="Leeftijd in weken" type="number" value={childAgeWeeks} onChange={(e) => setChildAgeWeeks(e.target.value)} min={0} max={260} />
              <div>
                <label className="text-sm font-medium block mb-1">Situatie</label>
                <select value={situation} onChange={(e) => setSituation(e.target.value)}
                  className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm">
                  <option value="couple">Koppel</option>
                  <option value="single">Alleenstaand</option>
                  <option value="co_parent">Co-ouderschap</option>
                </select>
              </div>
              <Button onClick={() => setStep(2)} className="w-full">Volgende</Button>
            </div>
          </Card>
        )}

        {step === 2 && (
          <Card padding="lg">
            <h2 className="text-lg font-display font-semibold mb-4">Werk en opvang</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-1">Jouw werksituatie</label>
                <select value={workOwner} onChange={(e) => setWorkOwner(e.target.value)}
                  className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm">
                  <option value="fulltime">Voltijd</option>
                  <option value="parttime">Deeltijd</option>
                  <option value="leave">Verlof</option>
                  <option value="none">Niet werkend</option>
                </select>
              </div>
              {situation === 'couple' && (
                <div>
                  <label className="text-sm font-medium block mb-1">Partner werksituatie</label>
                  <select value={workPartner} onChange={(e) => setWorkPartner(e.target.value)}
                    className="w-full px-3 py-2 rounded-md border border-border bg-surface text-sm">
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
                    <button key={day} onClick={() => toggleDay(day)}
                      className={`w-10 h-10 rounded-full text-xs font-medium transition-colors
                        ${daycareDays.includes(day) ? 'bg-primary text-white' : 'bg-surface-alt text-text-muted'}`}>
                      {dayLabels[day]}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="caregiver" checked={hasCaregiver}
                  onChange={(e) => setHasCaregiver(e.target.checked)} className="rounded" />
                <label htmlFor="caregiver" className="text-sm">Er is een oppas (oma, nanny, etc.)</label>
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => setStep(1)}>Terug</Button>
                <Button onClick={() => setStep(3)} className="flex-1">Volgende</Button>
              </div>
            </div>
          </Card>
        )}

        {step === 3 && (
          <Card padding="lg">
            <h2 className="text-lg font-display font-semibold mb-4">Waar loop je tegenaan?</h2>
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {painPointOptions.map((pp) => (
                  <button key={pp.value} onClick={() => togglePainPoint(pp.value)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-colors
                      ${painPoints.includes(pp.value)
                        ? 'bg-primary text-white'
                        : 'bg-surface-alt text-text-muted'
                      }`}>
                    {pp.label}
                  </button>
                ))}
              </div>
              <div className="flex gap-2 pt-2">
                <Button variant="secondary" onClick={() => setStep(2)}>Terug</Button>
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
