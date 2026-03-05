'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';

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

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/calendar/events')
      .then(({ data }) => setEvents(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Group by date
  const groupedByDate = events.reduce<Record<string, CalendarEvent[]>>((acc, event) => {
    const date = event.start_time.split('T')[0];
    if (!acc[date]) acc[date] = [];
    acc[date].push(event);
    return acc;
  }, {});

  const sortedDates = Object.keys(groupedByDate).sort();

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-display font-semibold">Agenda</h2>

      {loading ? (
        <p className="text-sm text-text-muted text-center py-8">Agenda laden...</p>
      ) : sortedDates.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-8">Geen afspraken gepland</p>
      ) : (
        sortedDates.map((date) => (
          <div key={date}>
            <h3 className="text-sm font-medium text-text-muted mb-2">
              {new Date(date).toLocaleDateString('nl-NL', { weekday: 'long', day: 'numeric', month: 'long' })}
            </h3>
            <div className="space-y-2">
              {groupedByDate[date].map((event) => (
                <Card key={event.id} padding="sm">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium">{event.title}</p>
                      {event.location && (
                        <p className="text-xs text-text-muted">{event.location}</p>
                      )}
                    </div>
                    <div className="text-right">
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
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
