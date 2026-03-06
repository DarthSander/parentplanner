'use client';

import { useState, useRef } from 'react';
import api from '@/lib/api';
import { useHouseholdStore } from '@/store/household';
import { useTaskStore } from '@/store/tasks';
import { toast } from '@/components/ui/Toast';

interface ParsedTask {
  title: string;
  category: string;
  task_type: string;
  estimated_minutes: number | null;
  suggested_assignee_id: string | null;
  due_date: string | null;
  reasoning: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  baby_care: 'Babyzorg',
  household: 'Huishouden',
  work: 'Werk',
  private: 'Prive',
};

const CATEGORY_COLORS: Record<string, string> = {
  baby_care: 'bg-blue-100 text-blue-800',
  household: 'bg-green-100 text-green-800',
  work: 'bg-purple-100 text-purple-800',
  private: 'bg-orange-100 text-orange-800',
};

export default function SmartTaskInput({ onCreated }: { onCreated?: () => void }) {
  const [text, setText] = useState('');
  const [parsing, setParsing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [preview, setPreview] = useState<ParsedTask | null>(null);
  const { members } = useHouseholdStore();
  const { createTask } = useTaskStore();
  const inputRef = useRef<HTMLInputElement>(null);

  const handleParse = async () => {
    if (!text.trim() || text.trim().length < 2) return;
    setParsing(true);
    try {
      const { data } = await api.post('/ai/parse-task', { text: text.trim() });
      setPreview(data);
    } catch {
      // If AI fails, create a minimal preview so user can still create
      setPreview({
        title: text.trim(),
        category: 'household',
        task_type: 'quick',
        estimated_minutes: null,
        suggested_assignee_id: null,
        due_date: null,
        reasoning: '',
      });
    } finally {
      setParsing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (preview) {
        handleConfirm();
      } else {
        handleParse();
      }
    }
    if (e.key === 'Escape') {
      setPreview(null);
      setText('');
    }
  };

  const handleConfirm = async () => {
    if (!preview) return;
    setCreating(true);
    try {
      await createTask({
        title: preview.title,
        category: preview.category as never,
        task_type: preview.task_type as never,
        estimated_minutes: preview.estimated_minutes ?? undefined,
        assigned_to: preview.suggested_assignee_id ?? undefined,
        due_date: preview.due_date ?? undefined,
      } as never);
      toast('Taak aangemaakt', 'success');
      setText('');
      setPreview(null);
      onCreated?.();
      inputRef.current?.focus();
    } catch {
      toast('Kon taak niet aanmaken', 'error');
    } finally {
      setCreating(false);
    }
  };

  const assigneeName = preview?.suggested_assignee_id
    ? members.find((m) => m.id === preview.suggested_assignee_id)?.display_name
    : null;

  return (
    <div className="mb-4">
      <div className="relative flex items-center gap-2">
        <div className="flex-1 relative">
          <input
            ref={inputRef}
            type="text"
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              if (preview) setPreview(null);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Typ wat er gedaan moet worden... bijv. 'luiers kopen voor woensdag'"
            className="w-full px-4 py-3 rounded-xl border border-border bg-surface shadow-sm text-sm
              placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30
              focus:border-primary transition-all"
          />
          {text.length > 0 && !preview && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-text-muted">
              Enter
            </span>
          )}
        </div>
        <button
          onClick={preview ? handleConfirm : handleParse}
          disabled={!text.trim() || parsing || creating}
          className="px-4 py-3 rounded-xl bg-primary text-white text-sm font-medium
            disabled:opacity-40 hover:bg-primary-light transition-colors whitespace-nowrap"
        >
          {parsing ? (
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              AI denkt...
            </span>
          ) : preview ? (
            creating ? 'Aanmaken...' : 'Bevestig'
          ) : (
            'Voeg toe'
          )}
        </button>
      </div>

      {/* AI preview card */}
      {preview && (
        <div className="mt-2 p-3 rounded-xl bg-surface border border-primary/20 shadow-sm">
          <div className="flex items-start justify-between gap-2 mb-2">
            <p className="text-sm font-medium text-text-main">{preview.title}</p>
            <button
              onClick={() => { setPreview(null); setText(''); }}
              className="text-text-muted hover:text-danger text-xs shrink-0"
            >
              Annuleer
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${CATEGORY_COLORS[preview.category] || 'bg-surface-alt text-text-muted'}`}>
              {CATEGORY_LABELS[preview.category] || preview.category}
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-surface-alt text-text-muted">
              {preview.task_type === 'quick' ? 'Snel' : 'Voorbereiding'}
            </span>
            {preview.estimated_minutes && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-surface-alt text-text-muted">
                ~{preview.estimated_minutes} min
              </span>
            )}
            {assigneeName && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-accent/10 text-accent">
                {assigneeName}
              </span>
            )}
            {preview.due_date && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-surface-alt text-text-muted">
                {new Date(preview.due_date).toLocaleDateString('nl-NL', { weekday: 'short', day: 'numeric', month: 'short' })}
              </span>
            )}
          </div>

          {preview.reasoning && (
            <p className="mt-2 text-xs text-text-muted italic">{preview.reasoning}</p>
          )}
        </div>
      )}
    </div>
  );
}
