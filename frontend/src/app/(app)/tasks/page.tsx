'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTaskStore, Task } from '@/store/tasks';
import AISuggestionBar from '@/components/ai/AISuggestionBar';
import SwipeableTaskCard from '@/components/tasks/SwipeableTaskCard';
import TaskForm from '@/components/tasks/TaskForm';
import SmartTaskInput from '@/components/tasks/SmartTaskInput';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';

type Filter = 'all' | 'open' | 'done' | 'baby_care' | 'household';

export default function TasksPage() {
  const router = useRouter();
  const { tasks, loading, fetchTasks } = useTaskStore();
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<Filter>('open');

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const now = new Date();
  const todayEnd = new Date(now);
  todayEnd.setHours(23, 59, 59, 999);
  const weekEnd = new Date(now);
  weekEnd.setDate(weekEnd.getDate() + 7);

  // Filter first
  const filteredTasks = useMemo(() => tasks.filter((t) => {
    if (filter === 'open') return t.status !== 'done';
    if (filter === 'done') return t.status === 'done';
    if (filter === 'baby_care') return t.category === 'baby_care' && t.status !== 'done';
    if (filter === 'household') return t.category === 'household' && t.status !== 'done';
    return true;
  }), [tasks, filter]);

  // Group by time: Nu doen / Binnenkort / Later / Terugkerend / Afgerond
  const grouped = useMemo(() => {
    if (filter === 'done') {
      return { done: filteredTasks };
    }

    const nuDoen: Task[] = [];
    const binnenkort: Task[] = [];
    const later: Task[] = [];
    const terugkerend: Task[] = [];

    for (const t of filteredTasks) {
      if (t.status === 'done') continue;
      if (t.recurrence_rule) {
        terugkerend.push(t);
      } else if (t.due_date && new Date(t.due_date) < now) {
        nuDoen.push(t); // overdue
      } else if (t.due_date && new Date(t.due_date) <= todayEnd) {
        nuDoen.push(t); // today
      } else if (t.due_date && new Date(t.due_date) <= weekEnd) {
        binnenkort.push(t);
      } else if (!t.due_date) {
        binnenkort.push(t); // no date = soon-ish
      } else {
        later.push(t);
      }
    }

    return { nuDoen, binnenkort, later, terugkerend };
  }, [filteredTasks, filter, now]);

  const filters: { key: Filter; label: string }[] = [
    { key: 'open', label: 'Open' },
    { key: 'done', label: 'Afgerond' },
    { key: 'baby_care', label: 'Babyzorg' },
    { key: 'household', label: 'Huishouden' },
    { key: 'all', label: 'Alle' },
  ];

  const renderSection = (title: string, tasks: Task[], urgencyClass?: string) => {
    if (tasks.length === 0) return null;
    return (
      <div>
        <h3 className={`text-xs font-semibold uppercase tracking-wide mb-2 ${urgencyClass || 'text-text-muted'}`}>
          {title} ({tasks.length})
        </h3>
        <div className="space-y-1.5">
          {tasks.map((task) => (
            <SwipeableTaskCard
              key={task.id}
              task={task}
              onClick={() => router.push(`/tasks/${task.id}`)}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-display font-semibold">Taken</h2>
        <Button size="sm" variant="secondary" onClick={() => setShowForm(true)}>Formulier</Button>
      </div>

      <AISuggestionBar page="tasks" maxItems={2} compact />

      <SmartTaskInput onCreated={() => fetchTasks()} />

      <div className="flex gap-2 overflow-x-auto pb-1">
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors
              ${filter === f.key
                ? 'bg-primary text-white'
                : 'bg-surface-alt text-text-muted hover:bg-border'
              }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-text-muted text-center py-8">Taken laden...</p>
      ) : filter === 'done' ? (
        <div className="space-y-1.5">
          {(grouped.done || []).length === 0 ? (
            <p className="text-sm text-text-muted text-center py-8">Geen afgeronde taken</p>
          ) : (
            (grouped.done || []).map((task) => (
              <SwipeableTaskCard key={task.id} task={task} onClick={() => router.push(`/tasks/${task.id}`)} />
            ))
          )}
        </div>
      ) : (
        <div className="space-y-5">
          {renderSection('Nu doen', grouped.nuDoen || [], 'text-danger')}
          {renderSection('Binnenkort', grouped.binnenkort || [], 'text-accent')}
          {renderSection('Later', grouped.later || [])}
          {renderSection('Terugkerend', grouped.terugkerend || [], 'text-primary')}
          {filteredTasks.length === 0 && (
            <p className="text-sm text-text-muted text-center py-8">Geen taken gevonden</p>
          )}
        </div>
      )}

      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title="Nieuwe taak">
        <TaskForm onClose={() => setShowForm(false)} />
      </Modal>
    </div>
  );
}
