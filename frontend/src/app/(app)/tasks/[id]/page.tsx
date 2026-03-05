'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useTaskStore, Task } from '@/store/tasks';
import { useHouseholdStore } from '@/store/household';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import { toast } from '@/components/ui/Toast';

const categoryLabels: Record<string, string> = {
  baby_care: 'Babyzorg',
  household: 'Huishouden',
  work: 'Werk',
  private: 'Prive',
};

const statusLabels: Record<string, string> = {
  open: 'Open',
  in_progress: 'Bezig',
  done: 'Afgerond',
  snoozed: 'Uitgesteld',
};

export default function TaskDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const { tasks, completeTask, snoozeTask, fetchTasks } = useTaskStore();
  const { members } = useHouseholdStore();
  const [task, setTask] = useState<Task | null>(null);

  useEffect(() => {
    if (tasks.length === 0) fetchTasks();
  }, [tasks.length, fetchTasks]);

  useEffect(() => {
    const found = tasks.find((t) => t.id === id);
    if (found) setTask(found);
  }, [tasks, id]);

  if (!task) {
    return <p className="text-text-muted text-center py-8">Taak laden...</p>;
  }

  const assignedMember = members.find((m) => m.id === task.assigned_to);

  const handleComplete = async () => {
    await completeTask(task.id);
    toast('Taak afgerond!', 'success');
    router.back();
  };

  const handleSnooze = async () => {
    await snoozeTask(task.id);
    toast('Taak uitgesteld', 'info');
  };

  return (
    <div className="space-y-4">
      <button onClick={() => router.back()} className="text-sm text-text-muted hover:text-text-main">
        &larr; Terug
      </button>

      <Card padding="lg">
        <div className="space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xl font-display font-semibold">{task.title}</h2>
              {task.ai_generated && <Badge variant="primary">AI</Badge>}
            </div>
            <div className="flex gap-2">
              <Badge>{categoryLabels[task.category]}</Badge>
              <Badge variant={task.status === 'done' ? 'success' : 'default'}>
                {statusLabels[task.status]}
              </Badge>
            </div>
          </div>

          {task.description && (
            <p className="text-sm text-text-muted">{task.description}</p>
          )}

          <div className="grid grid-cols-2 gap-3 text-sm">
            {assignedMember && (
              <div>
                <span className="text-text-muted">Toegewezen aan</span>
                <p className="font-medium">{assignedMember.display_name}</p>
              </div>
            )}
            {task.due_date && (
              <div>
                <span className="text-text-muted">Deadline</span>
                <p className="font-medium">
                  {new Date(task.due_date).toLocaleDateString('nl-NL', {
                    weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit',
                  })}
                </p>
              </div>
            )}
            {task.estimated_minutes && (
              <div>
                <span className="text-text-muted">Geschatte duur</span>
                <p className="font-medium">{task.estimated_minutes} min</p>
              </div>
            )}
            {task.snooze_count > 0 && (
              <div>
                <span className="text-text-muted">Uitgesteld</span>
                <p className="font-medium text-warning">{task.snooze_count}x</p>
              </div>
            )}
          </div>

          {task.status !== 'done' && (
            <div className="flex gap-2 pt-2">
              <Button onClick={handleComplete}>Afronden</Button>
              <Button variant="secondary" onClick={handleSnooze}>Uitstellen</Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
