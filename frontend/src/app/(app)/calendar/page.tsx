'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useTaskStore } from '@/store/tasks';
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
  event_type: string | null;
  source: string | null;
}

interface LinkedTask {
  id: string;
  title: string;
  status: string;
  due_date: string | null;
  category: string;
}

const EVENT_TYPE_CONFIG: Record<string, { dot: string; label: string; hint: string }> = {
  daycare: { dot: 'bg-accent', label: 'Opvang', hint: 'Luiertas ingepakt? Wisselkleding, eten, slaapzak?' },
  medical: { dot: 'bg-warning', label: 'Medisch', hint: 'Zorgpasje mee? Vaccinatieboekje? Vragen voorbereid?' },
  birthday: { dot: 'bg-pink-400', label: 'Verjaardag', hint: 'Cadeau al gekocht? Kaartje gestuurd?' },
  trip: { dot: 'bg-blue-400', label: 'Daguitje', hint: 'Kaartjes geboekt? Eten ingepakt? Kleding gecheckt?' },
  vacation: { dot: 'bg-purple-400', label: 'Vakantie', hint: 'Paklijst klaar? Paspoorten geldig? Verzekering geregeld?' },
  other: { dot: 'bg-text-muted', label: '', hint: '' },
};

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [integrations, setIntegrations] = useState<CalendarIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [linkedTasks, setLinkedTasks] = useState<LinkedTask[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const { tasks } = useTaskStore();

  useEffect(() => {
    Promise.all([
      api.get('/calendar/events').then(({ data }) => setEvents(data)).catch(() => {}),
      api.get('/calendar/integrations').then(({ data }) => setIntegrations(data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  const openEventDetail = async (event: CalendarEvent) => {
    setSelectedEvent(event);
    setLinkedTasks([]);
    setLoadingTasks(true);
    try {
      const { data } = await api.get(`/calendar/events/${event.id}/tasks`);
      setLinkedTasks(data);
    } catch {
      setLinkedTasks([]);
    } finally {
      setLoadingTasks(false);
    }
  };

  // Generate 21 days for the horizontal scroller
  const days = useMemo(() => {
    const result = [];
    const now = new Date();
    for (let i = 0; i < 21; i++) {
      const d = new Date(now);
      d.setDate(d.getDate() + i);
      const dateStr = d.toISOString().split('T')[0];
      const eventsOnDay = events.filter((e) => e.start_time.startsWith(dateStr));
      result.push({
        date: d,
        dateStr,
        label: d.toLocaleDateString('nl-NL', { weekday: 'short' }),
        dayNum: d.getDate(),
        isToday: i === 0,
        eventCount: eventsOnDay.length,
        hasSpecial: eventsOnDay.some((e) => e.event_type && e.event_type !== 'other'),
      });
    }
    return result;
  }, [events]);

  const selectedEvents = useMemo(
    () => events
      .filter((e) => e.start_time.startsWith(selectedDate))
      .sort((a, b) => a.start_time.localeCompare(b.start_time)),
    [events, selectedDate]
  );

  const selectedTasks = useMemo(
    () => tasks.filter((t) => t.status !== 'done' && t.due_date?.startsWith(selectedDate)),
    [tasks, selectedDate]
  );

  const selectedDateLabel = new Date(selectedDate).toLocaleDateString('nl-NL', {
    weekday: 'long', day: 'numeric', month: 'long',
  });

  const getEventConfig = (event: CalendarEvent) =>
    EVENT_TYPE_CONFIG[event.event_type || 'other'] || EVENT_TYPE_CONFIG.other;

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

      {/* Horizontal day scroller — 21 days */}
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
                day.dateStr === selectedDate ? 'bg-white' : day.hasSpecial ? 'bg-accent' : 'bg-text-muted/40'
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
            {selectedEvents.map((event) => {
              const config = getEventConfig(event);
              return (
                <Card
                  key={event.id}
                  padding="sm"
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => openEventDetail(event)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${config.dot} shrink-0`} />
                        <p className="text-sm font-medium">{event.title}</p>
                        {config.label && (
                          <Badge variant="default" className="text-[10px] px-1.5 py-0.5">{config.label}</Badge>
                        )}
                        {event.source && event.source !== 'manual' && (
                          <span className="text-[10px] text-text-muted bg-surface-alt px-1.5 py-0.5 rounded">
                            {event.source === 'google' ? 'Google' : event.source === 'outlook' ? 'Outlook' : 'CalDAV'}
                          </span>
                        )}
                      </div>
                      {event.location && (
                        <p className="text-xs text-text-muted ml-4 mt-0.5">{event.location}</p>
                      )}
                      {config.hint && (
                        <p className="text-xs text-primary mt-1 ml-4 bg-primary/5 px-2 py-1 rounded">
                          {config.hint}
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

            {selectedTasks.length > 0 && (
              <>
                {selectedEvents.length > 0 && <div className="border-t border-border my-2" />}
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

      {/* Event Detail Panel */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
          <div className="absolute inset-0 bg-black/30" onClick={() => setSelectedEvent(null)} />
          <div className="relative bg-surface rounded-t-2xl sm:rounded-2xl w-full max-w-md max-h-[80vh] overflow-y-auto p-4 space-y-4 shadow-lg">
            {/* Header */}
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`w-3 h-3 rounded-full ${getEventConfig(selectedEvent).dot}`} />
                  <h3 className="font-display font-semibold text-base">{selectedEvent.title}</h3>
                  {getEventConfig(selectedEvent).label && (
                    <Badge>{getEventConfig(selectedEvent).label}</Badge>
                  )}
                </div>
                <p className="text-xs text-text-muted mt-1">
                  {selectedEvent.all_day
                    ? 'Hele dag'
                    : `${new Date(selectedEvent.start_time).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })} – ${new Date(selectedEvent.end_time).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}`}
                  {selectedEvent.location && ` · ${selectedEvent.location}`}
                </p>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="p-1 rounded-lg hover:bg-surface-alt transition-colors ml-2 shrink-0"
              >
                <svg className="w-5 h-5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {selectedEvent.description && (
              <p className="text-sm text-text-muted">{selectedEvent.description}</p>
            )}

            {getEventConfig(selectedEvent).hint && (
              <div className="bg-primary/5 border border-primary/10 rounded-xl p-3">
                <p className="text-xs font-medium text-primary">AI-tip</p>
                <p className="text-sm text-text-main mt-0.5">{getEventConfig(selectedEvent).hint}</p>
              </div>
            )}

            {/* Linked AI tasks */}
            <div>
              <p className="text-xs font-medium text-text-muted uppercase tracking-wide mb-2">
                AI-taken voor dit event
              </p>
              {loadingTasks ? (
                <p className="text-xs text-text-muted">Laden...</p>
              ) : linkedTasks.length === 0 ? (
                <p className="text-xs text-text-muted italic">
                  Geen taken gekoppeld. De AI maakt automatisch taken aan bij het detecteren van dit soort afspraken.
                </p>
              ) : (
                <div className="space-y-2">
                  {linkedTasks.map((t) => (
                    <div
                      key={t.id}
                      className="flex items-center gap-2 p-2 bg-surface-alt rounded-lg"
                    >
                      <span
                        className={`w-4 h-4 rounded-full border-2 flex-shrink-0 ${
                          t.status === 'done'
                            ? 'bg-success border-success'
                            : 'border-text-muted'
                        }`}
                      >
                        {t.status === 'done' && (
                          <svg className="w-3 h-3 text-white m-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </span>
                      <span className={`text-sm flex-1 ${t.status === 'done' ? 'line-through text-text-muted' : ''}`}>
                        {t.title}
                      </span>
                      {t.due_date && (
                        <span className="text-xs text-text-muted shrink-0">
                          {new Date(t.due_date).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' })}
                        </span>
                      )}
                    </div>
                  ))}
                  <p className="text-[10px] text-text-muted mt-1">
                    Afgeronde taken worden automatisch teruggezet in je kalender.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
