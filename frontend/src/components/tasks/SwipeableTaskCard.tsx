'use client';

import { useRef, useState } from 'react';
import { Task, useTaskStore } from '@/store/tasks';
import { useHouseholdStore } from '@/store/household';
import Badge from '@/components/ui/Badge';
import { toast } from '@/components/ui/Toast';

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

interface SwipeableTaskCardProps {
  task: Task;
  onClick?: () => void;
}

export default function SwipeableTaskCard({ task, onClick }: SwipeableTaskCardProps) {
  const { completeTask, snoozeTask } = useTaskStore();
  const { members } = useHouseholdStore();
  const [offset, setOffset] = useState(0);
  const [swiping, setSwiping] = useState(false);
  const startX = useRef(0);
  const startY = useRef(0);
  const isHorizontal = useRef<boolean | null>(null);

  const assignedMember = members.find((m) => m.id === task.assigned_to);
  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';
  const daysOverdue = isOverdue ? Math.floor((Date.now() - new Date(task.due_date!).getTime()) / 86400000) : 0;

  // Urgency coloring based on how overdue
  const urgencyBorder = isOverdue
    ? daysOverdue >= 3 ? 'border-danger' : 'border-warning'
    : task.status === 'done' ? 'border-border opacity-50' : 'border-border';

  const handleTouchStart = (e: React.TouchEvent) => {
    startX.current = e.touches[0].clientX;
    startY.current = e.touches[0].clientY;
    isHorizontal.current = null;
    setSwiping(true);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!swiping) return;
    const dx = e.touches[0].clientX - startX.current;
    const dy = e.touches[0].clientY - startY.current;

    // Determine swipe direction on first significant move
    if (isHorizontal.current === null && (Math.abs(dx) > 5 || Math.abs(dy) > 5)) {
      isHorizontal.current = Math.abs(dx) > Math.abs(dy);
    }

    if (isHorizontal.current) {
      e.preventDefault();
      setOffset(Math.max(-80, Math.min(80, dx)));
    }
  };

  const handleTouchEnd = async () => {
    setSwiping(false);
    if (offset > 50 && task.status !== 'done') {
      // Swipe right = complete
      try {
        await completeTask(task.id);
        toast('Taak afgerond', 'success');
      } catch {
        toast('Kon taak niet afronden', 'error');
      }
    } else if (offset < -50 && task.status !== 'done') {
      // Swipe left = snooze
      try {
        await snoozeTask(task.id);
        toast('Taak uitgesteld', 'success');
      } catch {
        toast('Kon taak niet uitstellen', 'error');
      }
    }
    setOffset(0);
  };

  const handleComplete = (e: React.MouseEvent) => {
    e.stopPropagation();
    completeTask(task.id);
  };

  return (
    <div className="relative overflow-hidden rounded-md">
      {/* Swipe backgrounds */}
      <div className="absolute inset-0 flex">
        <div className={`flex-1 flex items-center pl-3 rounded-l-md transition-colors ${
          offset > 30 ? 'bg-success/20' : 'bg-transparent'
        }`}>
          {offset > 20 && <span className="text-success text-xs font-medium">Klaar</span>}
        </div>
        <div className={`flex-1 flex items-center justify-end pr-3 rounded-r-md transition-colors ${
          offset < -30 ? 'bg-warning/20' : 'bg-transparent'
        }`}>
          {offset < -20 && <span className="text-warning text-xs font-medium">Snooze</span>}
        </div>
      </div>

      {/* Card */}
      <div
        onClick={onClick}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{ transform: `translateX(${offset}px)`, transition: swiping ? 'none' : 'transform 0.2s ease' }}
        className={`relative flex items-start gap-3 p-3 bg-surface border cursor-pointer
          hover:shadow-sm transition-shadow rounded-md ${urgencyBorder}
          ${task.ai_generated ? 'ring-1 ring-primary/20' : ''}`}
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
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className={`text-sm font-medium ${task.status === 'done' ? 'line-through text-text-muted' : ''}`}>
              {task.title}
            </span>
            {task.ai_generated && (
              <span className="text-[9px] font-semibold text-primary bg-primary/10 px-1.5 py-0.5 rounded">AI</span>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs text-text-muted">
            <Badge variant={categoryColors[task.category]}>{categoryLabels[task.category]}</Badge>

            {assignedMember && (
              <span className="flex items-center gap-1">
                <span className="w-4 h-4 rounded-full bg-primary/15 text-primary text-[9px] font-bold flex items-center justify-center">
                  {assignedMember.display_name[0]}
                </span>
                {assignedMember.display_name.split(' ')[0]}
              </span>
            )}

            {task.due_date && (
              <span className={isOverdue ? 'text-danger font-medium' : ''}>
                {isOverdue
                  ? `${daysOverdue}d verlopen`
                  : new Date(task.due_date).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' })
                }
              </span>
            )}

            {task.estimated_minutes && (
              <span>{task.estimated_minutes}min</span>
            )}

            {task.snooze_count > 0 && (
              <span className="text-warning">{task.snooze_count}x</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
