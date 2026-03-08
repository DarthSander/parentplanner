'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTaskStore, Task } from '@/store/tasks';
import { useInventoryStore } from '@/store/inventory';
import { useHouseholdStore } from '@/store/household';
import AISuggestionBar from '@/components/ai/AISuggestionBar';
import TaskCard from '@/components/tasks/TaskCard';
import TaskDistributionBar from '@/components/tasks/TaskDistributionBar';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import api from '@/lib/api';

export default function DashboardPage() {
  const router = useRouter();
  const { tasks, fetchTasks } = useTaskStore();
  const { items, fetchItems } = useInventoryStore();
  const { currentMember, members } = useHouseholdStore();
  const [distribution, setDistribution] = useState<
    { member_id: string; display_name: string; completed_count: number; open_count: number; percentage: number }[]
  >([]);
  const [weekEvents, setWeekEvents] = useState<{ date: string; count: number }[]>([]);
  const [activeDevices, setActiveDevices] = useState<{ id: string; label: string; device_type: string; is_running: boolean; total_cycles: number }[]>([]);
  const [picknickRecs, setPicknickRecs] = useState<{ urgent_count: number; connected: boolean }>({ urgent_count: 0, connected: false });

  useEffect(() => {
    fetchTasks();
    fetchItems();
    api.get('/tasks/distribution').then(({ data }) => setDistribution(data)).catch(() => {});
    // Fetch week events for mini overview
    // Fetch SmartThings devices (ignore errors — feature may not be available)
    api.get('/smartthings/devices').then(({ data }) => setActiveDevices(data)).catch(() => {});
    // Picknick status — check urgency without loading full recommendations
    api.get('/picknick/status').then(({ data }) => {
      if (data.connected) {
        api.get('/picknick/recommendations').then(({ data: recs }) => {
          const urgent = (recs.items || []).filter((i: any) => i.priority === 'urgent').length;
          setPicknickRecs({ urgent_count: urgent, connected: true });
        }).catch(() => setPicknickRecs({ urgent_count: 0, connected: true }));
      }
    }).catch(() => {});
    api.get('/calendar/events').then(({ data }) => {
      const counts: Record<string, number> = {};
      for (const e of data) {
        const d = e.start_time?.split('T')[0];
        if (d) counts[d] = (counts[d] || 0) + 1;
      }
      setWeekEvents(Object.entries(counts).map(([date, count]) => ({ date, count })));
    }).catch(() => {});
  }, [fetchTasks, fetchItems]);

  const now = new Date();
  const todayStr = now.toISOString().split('T')[0];

  // Categorize tasks
  const openTasks = useMemo(() => tasks.filter((t) => t.status !== 'done'), [tasks]);
  const overdueTasks = useMemo(
    () => openTasks.filter((t) => t.due_date && new Date(t.due_date) < now).sort(
      (a, b) => new Date(a.due_date!).getTime() - new Date(b.due_date!).getTime()
    ),
    [openTasks, now]
  );
  const todayTasks = useMemo(
    () => openTasks.filter((t) => t.due_date && t.due_date.startsWith(todayStr) && !overdueTasks.includes(t)),
    [openTasks, todayStr, overdueTasks]
  );
  const myTasks = useMemo(
    () => openTasks.filter((t) => t.assigned_to === currentMember?.id),
    [openTasks, currentMember]
  );
  const lowStockItems = useMemo(
    () => items.filter((i) => i.current_quantity <= i.threshold_quantity),
    [items]
  );

  const firstName = currentMember?.display_name?.split(' ')[0] ?? '';
  const hour = now.getHours();
  const greeting = hour < 12 ? 'Goedemorgen' : hour < 18 ? 'Goedemiddag' : 'Goedenavond';

  // Week overview: next 7 days
  const weekDays = useMemo(() => {
    const days = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(now);
      d.setDate(d.getDate() + i);
      const dateStr = d.toISOString().split('T')[0];
      const taskCount = openTasks.filter((t) => t.due_date?.startsWith(dateStr)).length;
      const eventCount = weekEvents.find((e) => e.date === dateStr)?.count || 0;
      days.push({
        date: d,
        dateStr,
        label: d.toLocaleDateString('nl-NL', { weekday: 'short' }),
        dayNum: d.getDate(),
        isToday: i === 0,
        taskCount,
        eventCount,
        total: taskCount + eventCount,
      });
    }
    return days;
  }, [openTasks, weekEvents, now]);

  const attentionCount = overdueTasks.length + lowStockItems.filter((i) => i.current_quantity === 0).length;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-display font-semibold mb-0.5">
          {greeting}{firstName ? `, ${firstName}` : ''}
        </h2>
        <p className="text-sm text-text-muted">
          {now.toLocaleDateString('nl-NL', { weekday: 'long', day: 'numeric', month: 'long' })}
          {todayTasks.length > 0 && ` \u2014 ${todayTasks.length} taken vandaag`}
        </p>
      </div>

      {/* AI Proactive Suggestions Bar */}
      <AISuggestionBar page="dashboard" maxItems={3} />

      {/* Invite prompt */}
      {members.length === 1 && (
        <Card className="border-dashed border-primary/30 bg-primary/5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium">Je gezin is nog niet compleet</p>
              <p className="text-xs text-text-muted mt-0.5">Voeg je partner toe zodat de AI taken kan verdelen</p>
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

      {/* Attention needed — consolidated red section */}
      {attentionCount > 0 && (
        <Card className="border-danger/40 bg-danger/5">
          <h3 className="text-sm font-semibold text-danger mb-2 flex items-center gap-1.5">
            <span className="w-5 h-5 rounded-full bg-danger/15 flex items-center justify-center text-xs">!</span>
            Aandacht nodig ({attentionCount})
          </h3>
          <div className="space-y-1.5">
            {overdueTasks.slice(0, 3).map((t) => (
              <div
                key={t.id}
                onClick={() => router.push(`/tasks/${t.id}`)}
                className="flex items-center justify-between text-sm cursor-pointer hover:bg-danger/5 rounded px-1 py-0.5 -mx-1"
              >
                <span className="truncate">{t.title}</span>
                <span className="text-xs text-danger shrink-0 ml-2">
                  {t.snooze_count > 0 ? `${t.snooze_count}x uitgesteld` : 'verlopen'}
                </span>
              </div>
            ))}
            {lowStockItems.filter((i) => i.current_quantity === 0).slice(0, 2).map((i) => (
              <div
                key={i.id}
                onClick={() => router.push('/inventory')}
                className="flex items-center justify-between text-sm cursor-pointer hover:bg-danger/5 rounded px-1 py-0.5 -mx-1"
              >
                <span className="truncate">{i.name}</span>
                <span className="text-xs text-danger shrink-0 ml-2">op</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Active SmartThings devices */}
      {activeDevices.filter((d) => d.is_running).length > 0 && (
        <Card className="bg-accent/5 border-accent/20">
          <h3 className="text-sm font-semibold mb-1.5 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            Apparaten actief
          </h3>
          <div className="space-y-1">
            {activeDevices.filter((d) => d.is_running).map((d) => {
              const labels: Record<string, string> = {
                washer: 'Wasmachine draait', dryer: 'Droger draait',
                dishwasher: 'Vaatwasser draait', robot_vacuum: 'Robotstofzuiger zuigt',
              };
              return (
                <p key={d.id} className="text-xs text-text-muted">
                  {labels[d.device_type] || `${d.label} is actief`}
                </p>
              );
            })}
          </div>
        </Card>
      )}

      {/* Picknick shopping widget */}
      {picknickRecs.connected && (
        <button
          onClick={() => router.push('/shopping')}
          className="w-full text-left"
        >
          <Card className={picknickRecs.urgent_count > 0 ? 'bg-primary/5 border-primary/20' : ''}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🛒</span>
                <div>
                  <p className="text-sm font-medium">Boodschappen</p>
                  <p className="text-xs text-text-muted">
                    {picknickRecs.urgent_count > 0
                      ? `${picknickRecs.urgent_count} item(s) dringend nodig`
                      : 'Bekijk aanbevelingen'}
                  </p>
                </div>
              </div>
              <svg className="w-4 h-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </Card>
        </button>
      )}

      {/* Today's tasks */}
      <Card>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold">Vandaag</h3>
          <span className="text-xs text-text-muted">{todayTasks.length} taken</span>
        </div>
        {todayTasks.length === 0 ? (
          <p className="text-sm text-text-muted text-center py-4">Geen taken voor vandaag</p>
        ) : (
          <div className="space-y-1.5">
            {todayTasks.map((task) => (
              <TaskCard key={task.id} task={task} onClick={() => router.push(`/tasks/${task.id}`)} />
            ))}
          </div>
        )}
      </Card>

      {/* Quick actions */}
      <div className="grid grid-cols-3 gap-2">
        <button
          onClick={() => router.push('/tasks')}
          className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-surface border border-border hover:shadow-sm transition-shadow"
        >
          <span className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
          </span>
          <span className="text-[11px] font-medium text-text-main">Taak</span>
        </button>
        <button
          onClick={() => {
            sessionStorage.setItem('chat_prefill', '');
            router.push('/chat');
          }}
          className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-surface border border-border hover:shadow-sm transition-shadow"
        >
          <span className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </span>
          <span className="text-[11px] font-medium text-text-main">Chat AI</span>
        </button>
        <button
          onClick={() => router.push('/inventory')}
          className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-surface border border-border hover:shadow-sm transition-shadow"
        >
          <span className="w-8 h-8 rounded-full bg-warning/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          </span>
          <span className="text-[11px] font-medium text-text-main">Voorraad</span>
        </button>
      </div>

      {/* My tasks */}
      {myTasks.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold">Mijn taken</h3>
            <button onClick={() => router.push('/tasks')} className="text-xs text-primary">Alles bekijken</button>
          </div>
          <div className="space-y-1.5">
            {myTasks.slice(0, 4).map((task) => (
              <TaskCard key={task.id} task={task} onClick={() => router.push(`/tasks/${task.id}`)} />
            ))}
          </div>
        </Card>
      )}

      {/* Week overview */}
      <Card>
        <h3 className="text-sm font-semibold mb-3">Weekoverzicht</h3>
        <div className="flex justify-between">
          {weekDays.map((day) => (
            <div key={day.dateStr} className="flex flex-col items-center gap-1">
              <span className={`text-[10px] font-medium uppercase ${day.isToday ? 'text-primary' : 'text-text-muted'}`}>
                {day.label}
              </span>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium
                ${day.isToday ? 'bg-primary text-white' : day.total > 3 ? 'bg-warning/15 text-warning' : 'bg-surface-alt text-text-main'}`}
              >
                {day.dayNum}
              </div>
              {day.total > 0 && (
                <div className="flex gap-0.5">
                  {day.taskCount > 0 && <span className="w-1 h-1 rounded-full bg-primary" />}
                  {day.eventCount > 0 && <span className="w-1 h-1 rounded-full bg-accent" />}
                </div>
              )}
              {day.total === 0 && <div className="h-1" />}
            </div>
          ))}
        </div>
      </Card>

      {/* Distribution */}
      {distribution.length > 0 && (
        <Card>
          <h3 className="text-sm font-semibold mb-3">Taakverdeling deze week</h3>
          <TaskDistributionBar distribution={distribution} />
        </Card>
      )}

      {/* Low stock */}
      {lowStockItems.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold">
              Voorraad <Badge variant="warning">{lowStockItems.length} laag</Badge>
            </h3>
            <button onClick={() => router.push('/inventory')} className="text-xs text-primary">Bekijk alles</button>
          </div>
          <div className="space-y-1.5">
            {lowStockItems.slice(0, 5).map((item) => (
              <div key={item.id} className="flex items-center gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between text-sm">
                    <span className="truncate">{item.name}</span>
                    <span className={`font-medium shrink-0 ml-2 ${item.current_quantity === 0 ? 'text-danger' : 'text-warning'}`}>
                      {item.current_quantity} {item.unit}
                    </span>
                  </div>
                  {/* Progress bar */}
                  <div className="w-full h-1.5 bg-surface-alt rounded-full mt-1">
                    <div
                      className={`h-full rounded-full transition-all ${
                        item.current_quantity === 0 ? 'bg-danger' : item.current_quantity <= item.threshold_quantity ? 'bg-warning' : 'bg-success'
                      }`}
                      style={{ width: `${Math.min(100, (item.current_quantity / Math.max(item.threshold_quantity * 2, 1)) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
