'use client';

import { Task, useTaskStore } from '@/store/tasks';
import Badge from '@/components/ui/Badge';
import { useHouseholdStore } from '@/store/household';

const categoryLabels: Record<string, string> = {
  baby_care: 'Babyzorg',
  household: 'Huishouden',
  work: 'Werk',
  private: 'Prive',
};

const categoryColors: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'default'> = {
  baby_care: 'primary',
  household: 'success',
  work: 'warning',
  private: 'default',
};

interface TaskCardProps {
  task: Task;
  onClick?: () => void;
}

export default function TaskCard({ task, onClick }: TaskCardProps) {
  const { completeTask } = useTaskStore();
  const { members } = useHouseholdStore();

  const assignedMember = members.find((m) => m.id === task.assigned_to);
  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';

  const handleComplete = (e: React.MouseEvent) => {
    e.stopPropagation();
    completeTask(task.id);
  };

  return (
    <div
      onClick={onClick}
      className={`flex items-start gap-3 p-3 rounded-md bg-surface border border-border
        cursor-pointer hover:shadow-sm transition-shadow
        ${task.status === 'done' ? 'opacity-50' : ''}`}
    >
      <button
        onClick={handleComplete}
        className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded-full border-2 transition-colors
          ${task.status === 'done'
            ? 'bg-success border-success'
            : 'border-border hover:border-primary'
          }`}
      >
        {task.status === 'done' && (
          <svg className="w-full h-full text-white p-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        )}
      </button>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-sm font-medium ${task.status === 'done' ? 'line-through' : ''}`}>
            {task.title}
          </span>
          {task.ai_generated && (
            <Badge variant="primary">AI</Badge>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-text-muted">
          <Badge variant={categoryColors[task.category]}>{categoryLabels[task.category]}</Badge>
          {assignedMember && <span>{assignedMember.display_name}</span>}
          {task.due_date && (
            <span className={isOverdue ? 'text-danger font-medium' : ''}>
              {new Date(task.due_date).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' })}
            </span>
          )}
          {task.snooze_count > 0 && (
            <span className="text-warning">{task.snooze_count}x uitgesteld</span>
          )}
        </div>
      </div>
    </div>
  );
}
