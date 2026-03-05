'use client';

import { Task } from '@/store/tasks';
import TaskCard from './TaskCard';

interface TaskListProps {
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
  emptyMessage?: string;
}

export default function TaskList({ tasks, onTaskClick, emptyMessage = 'Geen taken' }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-8 text-text-muted text-sm">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onClick={() => onTaskClick?.(task)}
        />
      ))}
    </div>
  );
}
