'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useTaskStore, Task } from '@/store/tasks';
import AISuggestionBar from '@/components/ai/AISuggestionBar';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';

interface CalendarIntegration {
  id: string;
  provider: string;
  last_synced_at: string | null;
}

interface CalendarEvent {
  id: string;
  title: string;
  description: string | null;
  location: string | null;
  start_time: string;
  end_time: string;
  all_day: boolean;
  member_id: string | null;
}

const DAYCARE_KEYWORDS = ['opvang', 'dagopvang', 'kinderopvang', 'creche', 'bso'];
const MEDICAL_KEYWORDS = ['consultatieburo', 'huisarts', 'prikken', 'vaccinatie', 'dokter'];

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [integrations, setIntegrations] = useState<CalendarIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const { tasks } = useTaskStore();

  useEffect(() => {
    Promise.all([
      api.get('/calendar/events').then(({ data }) => setEvents(data)).catch(() => {}),
      api.get('/calendar/integrations').then(({ data }) => setIntegrations(data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  // Generate 14 days for the horizontal scroller
  const days = useMemo(() => {
    const result = [];
    const now = new Date();
    for (let i = 0; i < 14; i++) {
      const d = new Date(now);
      d.setDate(d.getDate() + i);
      const dateStr = d.toISOString().split('T')[0];
      const eventCount = events.filter((e) => e.start_time.startsWith(dateStr)).length;
      result.push({
        date: d,
        dateStr,
        label: d.toLocaleDateString('nl-NL', { weekday: 'short' }),
        dayNum: d.getDate(),
        isToday: i === 0,
        eventCount,
      });
    }
    return result;
  }, [events]);

  // Events for selected day
  const selectedEvents = useMemo(
    () => events
      .filter((e) => e.start_time.startsWith(selectedDate))
      .sort((a, b) => a.start_time.localeCompare(b.start_time)),
    [events, selectedDate]
  );

  // Tasks for selected day
  const selectedTasks = useMemo(
    () => tasks
      .filter((t) => t.status !== 'done' && t.due_date?.startsWith(selectedDate)),
    [tasks, selectedDate]
  );

  const getEventHint = (event: CalendarEvent): string | null => {
    const lower = event.title.toLowerCase();
    if (DAYCARE_KEYWORDS.some((kw) => lower.includes(kw))) {
      return 'Luiertas ingepakt? Wisselkleding, eten, slaapzak?';
    }
    if (MEDICAL_KEYWORDS.some((kw) => lower.includes(kw))) {
      return 'Vaccinatieboekje mee? Vragen voorbereid?';
    }
    return null;
  };

  const selectedDateLabel = new Date(selectedDate).toLocaleDateString('nl-NL', {
    weekday: 'long', day: 'numeric', month: 'long',
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-display font-semibold">Agenda</h2>
        <Link
          href="/settings/calendar"
          className="flex items-center gap-1.5 text-xs text-text-muted hover:text-primary transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          {integrations.length > 0 ? `${integrations.length} gekoppeld` : 'Koppelen'}
        </Link>
      </div>

      <AISuggestionBar page="calendar" maxItems={2} compact />

      {/* Horizontal day scroller */}
      <div className="flex gap-1 overflow-x-auto pb-1 -mx-1 px-1">
        {days.map((day) => (
          <button
            key={day.dateStr}
            onClick={() => setSelectedDate(day.dateStr)}
            className={`flex flex-col items-center gap-0.5 px-2.5 py-2 rounded-xl shrink-0 transition-colors min-w-[3rem]
              ${day.dateStr === selectedDate
                ? 'bg-primary text-white'
                : day.isToday
                  ? 'bg-primary/10 text-primary'
                  : 'bg-surface-alt text-text-main hover:bg-border'
              }`}
          >
            <span className="text-[10px] font-medium uppercase">{day.label}</span>
            <span className="text-sm font-semibold">{day.dayNum}</span>
            {day.eventCount > 0 && (
              <span className={`w-1.5 h-1.5 rounded-full ${
                day.dateStr === selectedDate ? 'bg-white' : 'bg-accent'
              }`} />
            )}
          </button>
        ))}
      </div>

      {/* Selected day content */}
      <div>
        <h3 className="text-sm font-medium text-text-muted mb-3 capitalize">{selectedDateLabel}</h3>

        {loading ? (
          <p className="text-sm text-text-muted text-center py-8">Laden...</p>
        ) : selectedEvents.length === 0 && selectedTasks.length === 0 ? (
          <p className="text-sm text-text-muted text-center py-8">Niets gepland voor deze dag</p>
        ) : (
          <div className="space-y-2">
            {/* Events */}
            {selectedEvents.map((event) => {
              const hint = getEventHint(event);
              return (
                <Card key={event.id} padding="sm">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-accent shrink-0" />
                        <p className="text-sm font-medium">{event.title}</p>
                      </div>
                      {event.location && (
                        <p className="text-xs text-text-muted ml-4">{event.location}</p>
                      )}
                      {/* AI hint */}
                      {hint && (
                        <p className="text-xs text-primary mt-1 ml-4 bg-primary/5 px-2 py-1 rounded">
                          {hint}
                        </p>
                      )}
                    </div>
                    <div className="text-right shrink-0 ml-2">
                      {event.all_day ? (
                        <Badge>Hele dag</Badge>
                      ) : (
                        <span className="text-xs text-text-muted">
                          {new Date(event.start_time).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}
                          {' - '}
                          {new Date(event.end_time).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}

            {/* Tasks for this day */}
            {selectedTasks.length > 0 && (
              <>
                {selectedEvents.length > 0 && (
                  <div className="border-t border-border my-2" />
                )}
                <p className="text-xs font-medium text-text-muted uppercase tracking-wide">
                  Taken ({selectedTasks.length})
                </p>
                {selectedTasks.map((task) => (
                  <Card key={task.id} padding="sm">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-primary shrink-0" />
                      <span className="text-sm">{task.title}</span>
                      <Badge variant={task.category === 'baby_care' ? 'primary' : 'default'}>
                        {task.category === 'baby_care' ? 'Baby' : task.category === 'household' ? 'Huis' : task.category}
                      </Badge>
                    </div>
                  </Card>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
