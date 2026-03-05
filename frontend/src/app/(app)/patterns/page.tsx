'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { toast } from '@/components/ui/Toast';
import { useHouseholdStore } from '@/store/household';

interface Pattern {
  id: string;
  pattern_type: string;
  member_id: string | null;
  description: string;
  confidence_score: number;
  first_detected_at: string;
  last_confirmed_at: string;
}

const patternTypeLabels: Record<string, string> = {
  task_avoidance: 'Taakvermijding',
  task_affinity: 'Taakvoorkeur',
  inventory_rate: 'Verbruik',
  schedule_conflict: 'Agendaconflict',
  complementary_split: 'Goede verdeling',
};

const patternTypeVariants: Record<string, 'danger' | 'success' | 'warning' | 'primary' | 'default'> = {
  task_avoidance: 'warning',
  task_affinity: 'success',
  inventory_rate: 'default',
  schedule_conflict: 'danger',
  complementary_split: 'primary',
};

export default function PatternsPage() {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const { members } = useHouseholdStore();

  useEffect(() => {
    api.get('/patterns')
      .then(({ data }) => setPatterns(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      await api.post('/patterns/analyze-now');
      toast('Analyse gestart, dit kan even duren', 'info');
    } catch {
      toast('Kon analyse niet starten', 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  const getMemberName = (memberId: string | null) => {
    if (!memberId) return 'Huishouden';
    return members.find((m) => m.id === memberId)?.display_name || 'Onbekend';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-display font-semibold">Patronen</h2>
        <Button size="sm" variant="secondary" onClick={handleAnalyze} loading={analyzing}>
          Analyseer nu
        </Button>
      </div>

      {loading ? (
        <p className="text-sm text-text-muted text-center py-8">Patronen laden...</p>
      ) : patterns.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-8">
          Nog geen patronen gedetecteerd. De AI analyseert wekelijks je gezinsactiviteiten.
        </p>
      ) : (
        <div className="space-y-3">
          {patterns.map((pattern) => (
            <Card key={pattern.id}>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant={patternTypeVariants[pattern.pattern_type]}>
                    {patternTypeLabels[pattern.pattern_type] || pattern.pattern_type}
                  </Badge>
                  <span className="text-xs text-text-muted">{getMemberName(pattern.member_id)}</span>
                </div>
                <p className="text-sm">{pattern.description}</p>
                <div className="flex items-center gap-3 text-xs text-text-muted">
                  <span>Betrouwbaarheid: {Math.round(pattern.confidence_score * 100)}%</span>
                  <span>Laatst bevestigd: {new Date(pattern.last_confirmed_at).toLocaleDateString('nl-NL')}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
