'use client';

import { useState } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { useTaskStore } from '@/store/tasks';
import { useHouseholdStore } from '@/store/household';
import { toast } from '@/components/ui/Toast';

interface TaskFormProps {
  onClose: () => void;
}

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

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Input
        label="Titel"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Wat moet er gedaan worden?"
        required
        autoFocus
      />

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
