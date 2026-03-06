'use client';

import { useState, useEffect, useRef } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { useTaskStore } from '@/store/tasks';
import { useHouseholdStore } from '@/store/household';
import { toast } from '@/components/ui/Toast';
import api from '@/lib/api';

interface TaskFormProps {
  onClose: () => void;
}

interface AISuggestion {
  category: string;
  task_type: string;
  estimated_minutes: number | null;
  suggested_assignee_id: string | null;
  reasoning: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  baby_care: 'Babyzorg',
  household: 'Huishouden',
  work: 'Werk',
  private: 'Prive',
};

export default function TaskForm({ onClose }: TaskFormProps) {
  const { createTask } = useTaskStore();
  const { members } = useHouseholdStore();
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState<string>('household');
  const [taskType, setTaskType] = useState<string>('quick');
  const [assignedTo, setAssignedTo] = useState<string>('');
  const [dueDate, setDueDate] = useState('');
  const [estimatedMinutes, setEstimatedMinutes] = useState('');

  // AI suggestion state
  const [suggestion, setSuggestion] = useState<AISuggestion | null>(null);
  const [suggesting, setSuggesting] = useState(false);
  const [appliedFields, setAppliedFields] = useState<Set<string>>(new Set());
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch AI suggestion when title changes (debounced 700ms)
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (title.trim().length < 3) {
      setSuggestion(null);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSuggesting(true);
      try {
        const { data } = await api.post('/ai/suggest-task', { title: title.trim() });
        setSuggestion(data);
      } catch {
        // silent — AI is optional
      } finally {
        setSuggesting(false);
      }
    }, 700);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [title]);

  const applyCategory = () => {
    if (!suggestion) return;
    setCategory(suggestion.category);
    setAppliedFields((prev) => new Set(prev).add('category'));
  };

  const applyType = () => {
    if (!suggestion) return;
    setTaskType(suggestion.task_type);
    setAppliedFields((prev) => new Set(prev).add('task_type'));
  };

  const applyMinutes = () => {
    if (!suggestion?.estimated_minutes) return;
    setEstimatedMinutes(String(suggestion.estimated_minutes));
    setAppliedFields((prev) => new Set(prev).add('minutes'));
  };

  const applyAssignee = () => {
    if (!suggestion?.suggested_assignee_id) return;
    setAssignedTo(suggestion.suggested_assignee_id);
    setAppliedFields((prev) => new Set(prev).add('assignee'));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    try {
      await createTask({
        title: title.trim(),
        category: category as 'baby_care' | 'household' | 'work' | 'private',
        task_type: taskType as 'quick' | 'prep',
        assigned_to: assignedTo || undefined,
        due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
        estimated_minutes: estimatedMinutes ? parseInt(estimatedMinutes) : undefined,
      } as never);
      toast('Taak aangemaakt', 'success');
      onClose();
    } catch {
      toast('Kon taak niet aanmaken', 'error');
    } finally {
      setLoading(false);
    }
  };

  const suggestionAssigneeName = suggestion?.suggested_assignee_id
    ? members.find((m) => m.id === suggestion.suggested_assignee_id)?.display_name
    : null;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="relative">
        <Input
          label="Titel"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Wat moet er gedaan worden?"
          required
          autoFocus
        />
        {suggesting && (
          <span className="absolute right-2 bottom-2 text-xs text-text-muted flex items-center gap-1">
            <span className="inline-block w-2.5 h-2.5 border-2 border-text-muted/40 border-t-primary rounded-full animate-spin" />
            AI denkt mee
          </span>
        )}
      </div>

      {/* AI suggestion chips */}
      {suggestion && (
        <div className="bg-primary/5 border border-primary/15 rounded-lg p-3">
          <p className="text-xs text-primary font-medium mb-2">AI-suggestie</p>
          <div className="flex flex-wrap gap-1.5">
            {!appliedFields.has('category') && (
              <button
                type="button"
                onClick={applyCategory}
                className="px-2.5 py-1 rounded-full text-xs bg-white border border-primary/30 text-primary hover:bg-primary hover:text-white transition-colors"
              >
                {CATEGORY_LABELS[suggestion.category] || suggestion.category}
              </button>
            )}
            {!appliedFields.has('task_type') && (
              <button
                type="button"
                onClick={applyType}
                className="px-2.5 py-1 rounded-full text-xs bg-white border border-primary/30 text-primary hover:bg-primary hover:text-white transition-colors"
              >
                {suggestion.task_type === 'quick' ? 'Snel' : 'Voorbereiding'}
              </button>
            )}
            {suggestion.estimated_minutes && !appliedFields.has('minutes') && (
              <button
                type="button"
                onClick={applyMinutes}
                className="px-2.5 py-1 rounded-full text-xs bg-white border border-primary/30 text-primary hover:bg-primary hover:text-white transition-colors"
              >
                ~{suggestion.estimated_minutes} min
              </button>
            )}
            {suggestionAssigneeName && !appliedFields.has('assignee') && (
              <button
                type="button"
                onClick={applyAssignee}
                className="px-2.5 py-1 rounded-full text-xs bg-white border border-accent/40 text-accent hover:bg-accent hover:text-white transition-colors"
              >
                {suggestionAssigneeName}
              </button>
            )}
          </div>
          {suggestion.reasoning && (
            <p className="mt-1.5 text-xs text-text-muted italic">{suggestion.reasoning}</p>
          )}
        </div>
      )}

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-text-main">Categorie</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-main"
        >
          <option value="baby_care">Babyzorg</option>
          <option value="household">Huishouden</option>
          <option value="work">Werk</option>
          <option value="private">Prive</option>
        </select>
      </div>

      <div className="flex gap-3">
        <div className="flex-1">
          <label className="text-sm font-medium text-text-main">Type</label>
          <select
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
            className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-main mt-1"
          >
            <option value="quick">Snel</option>
            <option value="prep">Voorbereiding</option>
          </select>
        </div>
        <div className="flex-1">
          <Input
            label="Geschatte duur (min)"
            type="number"
            value={estimatedMinutes}
            onChange={(e) => setEstimatedMinutes(e.target.value)}
            min={1}
            max={1440}
          />
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-text-main">Toewijzen aan</label>
        <select
          value={assignedTo}
          onChange={(e) => setAssignedTo(e.target.value)}
          className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-main"
        >
          <option value="">Niemand</option>
          {members.map((m) => (
            <option key={m.id} value={m.id}>{m.display_name}</option>
          ))}
        </select>
      </div>

      <Input
        label="Deadline"
        type="datetime-local"
        value={dueDate}
        onChange={(e) => setDueDate(e.target.value)}
      />

      <div className="flex gap-2 pt-2">
        <Button type="submit" loading={loading}>Aanmaken</Button>
        <Button type="button" variant="secondary" onClick={onClose}>Annuleren</Button>
      </div>
    </form>
  );
}
