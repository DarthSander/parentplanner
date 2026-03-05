'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTaskStore, Task } from '@/store/tasks';
import { useInventoryStore } from '@/store/inventory';
import { useHouseholdStore } from '@/store/household';
import TaskList from '@/components/tasks/TaskList';
import TaskDistributionBar from '@/components/tasks/TaskDistributionBar';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import api from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const { tasks, fetchTasks } = useTaskStore();
  const { items, fetchItems } = useInventoryStore();
  const { currentMember } = useHouseholdStore();
  const [distribution, setDistribution] = useState<
    { member_id: string; display_name: string; completed_count: number; open_count: number; percentage: number }[]
  >([]);

  useEffect(() => {
    fetchTasks();
    fetchItems();
    api.get('/tasks/distribution').then(({ data }) => setDistribution(data)).catch(() => {});
  }, [fetchTasks, fetchItems]);

  const today = new Date().toISOString().split('T')[0];
  const todayTasks = tasks.filter(
    (t) => t.status !== 'done' && t.due_date && t.due_date.startsWith(today),
  );
  const overdueTasks = tasks.filter(
    (t) => t.status !== 'done' && t.due_date && t.due_date < new Date().toISOString(),
  );
  const myTasks = tasks.filter(
    (t) => t.status !== 'done' && t.assigned_to === currentMember?.id,
  );
  const lowStockItems = items.filter((i) => i.current_quantity <= i.threshold_quantity);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-display font-semibold mb-1">
          Hoi{currentMember ? `, ${currentMember.display_name.split(' ')[0]}` : ''}
        </h2>
        <p className="text-sm text-text-muted">
          {new Date().toLocaleDateString('nl-NL', { weekday: 'long', day: 'numeric', month: 'long' })}
        </p>
      </div>

      {overdueTasks.length > 0 && (
        <Card className="border-danger">
          <h3 className="text-sm font-medium text-danger mb-2">
            Verlopen ({overdueTasks.length})
          </h3>
          <TaskList
            tasks={overdueTasks.slice(0, 3)}
            onTaskClick={(t: Task) => router.push(`/tasks/${t.id}`)}
          />
        </Card>
      )}

      <Card>
        <h3 className="text-sm font-medium mb-2">Vandaag ({todayTasks.length})</h3>
        <TaskList
          tasks={todayTasks}
          onTaskClick={(t: Task) => router.push(`/tasks/${t.id}`)}
          emptyMessage="Geen taken voor vandaag"
        />
      </Card>

      {myTasks.length > 0 && (
        <Card>
          <h3 className="text-sm font-medium mb-2">Mijn taken ({myTasks.length})</h3>
          <TaskList
            tasks={myTasks.slice(0, 5)}
            onTaskClick={(t: Task) => router.push(`/tasks/${t.id}`)}
          />
        </Card>
      )}

      {distribution.length > 0 && (
        <Card>
          <h3 className="text-sm font-medium mb-3">Taakverdeling deze week</h3>
          <TaskDistributionBar distribution={distribution} />
        </Card>
      )}

      {lowStockItems.length > 0 && (
        <Card>
          <h3 className="text-sm font-medium mb-2">
            Voorraad <Badge variant="warning">{lowStockItems.length} laag</Badge>
          </h3>
          <div className="space-y-1">
            {lowStockItems.slice(0, 5).map((item) => (
              <div key={item.id} className="flex justify-between text-sm">
                <span>{item.name}</span>
                <span className={`font-medium ${item.current_quantity === 0 ? 'text-danger' : 'text-warning'}`}>
                  {item.current_quantity} {item.unit}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
