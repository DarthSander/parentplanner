'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTaskStore, Task } from '@/store/tasks';
import TaskList from '@/components/tasks/TaskList';
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

  const filteredTasks = tasks.filter((t) => {
    if (filter === 'open') return t.status !== 'done';
    if (filter === 'done') return t.status === 'done';
    if (filter === 'baby_care') return t.category === 'baby_care' && t.status !== 'done';
    if (filter === 'household') return t.category === 'household' && t.status !== 'done';
    return true;
  });

  const filters: { key: Filter; label: string }[] = [
    { key: 'open', label: 'Open' },
    { key: 'done', label: 'Afgerond' },
    { key: 'baby_care', label: 'Babyzorg' },
    { key: 'household', label: 'Huishouden' },
    { key: 'all', label: 'Alle' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-display font-semibold">Taken</h2>
        <Button size="sm" variant="secondary" onClick={() => setShowForm(true)}>Formulier</Button>
      </div>

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
      ) : (
        <TaskList
          tasks={filteredTasks}
          onTaskClick={(t: Task) => router.push(`/tasks/${t.id}`)}
        />
      )}

      <Modal isOpen={showForm} onClose={() => setShowForm(false)} title="Nieuwe taak">
        <TaskForm onClose={() => setShowForm(false)} />
      </Modal>
    </div>
  );
}
