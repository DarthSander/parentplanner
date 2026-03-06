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

interface InsightItem {
  type: 'balance' | 'warning' | 'pattern' | 'praise';
  message: string;
}

const INSIGHT_ICON: Record<string, string> = {
  balance: '⚖',
  warning: '!',
  pattern: '~',
  praise: '+',
};

const INSIGHT_COLORS: Record<string, string> = {
  balance: 'text-blue-700 bg-blue-50 border-blue-100',
  warning: 'text-orange-700 bg-orange-50 border-orange-100',
  pattern: 'text-primary bg-primary/5 border-primary/15',
  praise: 'text-green-700 bg-green-50 border-green-100',
};

const ICON_COLORS: Record<string, string> = {
  balance: 'bg-blue-100 text-blue-700',
  warning: 'bg-orange-100 text-orange-700',
  pattern: 'bg-primary/15 text-primary',
  praise: 'bg-green-100 text-green-700',
};

export default function DashboardPage() {
  const router = useRouter();
  const { tasks, fetchTasks } = useTaskStore();
  const { items, fetchItems } = useInventoryStore();
  const { currentMember, members } = useHouseholdStore();
  const [distribution, setDistribution] = useState<
    { member_id: string; display_name: string; completed_count: number; open_count: number; percentage: number }[]
  >([]);
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [insightsLoading, setInsightsLoading] = useState(true);

  useEffect(() => {
    fetchTasks();
    fetchItems();
    api.get('/tasks/distribution').then(({ data }) => setDistribution(data)).catch(() => {});
    api.get('/ai/insights')
      .then(({ data }) => setInsights(data))
      .catch(() => {})
      .finally(() => setInsightsLoading(false));
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

  const firstName = currentMember?.display_name?.split(' ')[0] ?? '';

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-display font-semibold mb-1">
          Hoi{firstName ? `, ${firstName}` : ''}
        </h2>
        <p className="text-sm text-text-muted">
          {new Date().toLocaleDateString('nl-NL', { weekday: 'long', day: 'numeric', month: 'long' })}
        </p>
      </div>

      {/* AI Insights */}
      {(insightsLoading || insights.length > 0) && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-primary uppercase tracking-wide">AI observaties</span>
          </div>
          {insightsLoading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <div key={i} className="h-10 bg-surface-alt rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {insights.map((insight, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-2.5 px-3 py-2.5 rounded-lg border text-sm ${INSIGHT_COLORS[insight.type] || INSIGHT_COLORS.pattern}`}
                >
                  <span className={`shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${ICON_COLORS[insight.type] || ICON_COLORS.pattern}`}>
                    {INSIGHT_ICON[insight.type] || '~'}
                  </span>
                  <span>{insight.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Invite partner prompt if only 1 member */}
      {members.length === 1 && (
        <Card className="border-dashed border-primary/30 bg-primary/5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium">Je gezin is nog niet compleet</p>
              <p className="text-xs text-text-muted mt-0.5">Voeg je partner of oppas toe zodat de AI taken kan verdelen</p>
            </div>
            <button
              onClick={() => router.push('/settings/members')}
              className="shrink-0 px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-medium"
            >
              Uitnodigen
            </button>
          </div>
        </Card>
      )}

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
