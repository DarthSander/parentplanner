'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import ChatMessage, { ChatActionData } from '@/components/chat/ChatMessage';
import ChatInput from '@/components/chat/ChatInput';
import { useTaskStore } from '@/store/tasks';
import { useInventoryStore } from '@/store/inventory';
import { toast } from '@/components/ui/Toast';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  actions?: ChatActionData[];
}

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<{ prefill: (text: string) => void }>(null);
  const { createTask, completeTask, snoozeTask } = useTaskStore();
  const { createItem } = useInventoryStore();

  useEffect(() => {
    api.get('/chat/history')
      .then(({ data }) => setMessages(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Pick up prefilled message from AISuggestionBar or other pages
  useEffect(() => {
    const prefill = sessionStorage.getItem('chat_prefill');
    if (prefill) {
      sessionStorage.removeItem('chat_prefill');
      // Auto-send the prefilled message
      handleSend(prefill);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (text: string) => {
    const tempId = `temp-${Date.now()}`;
    const userMsg: Message = {
      id: tempId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setSending(true);

    try {
      const { data } = await api.post('/chat', { message: text });
      const assistantMsg: Message = {
        id: data.message_id,
        role: 'assistant',
        content: data.reply,
        created_at: data.created_at,
        actions: data.actions || [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      toast('Kon bericht niet versturen', 'error');
    } finally {
      setSending(false);
    }
  };

  const handleAction = async (action: ChatActionData) => {
    try {
      switch (action.action) {
        case 'create_task':
          await createTask({
            title: action.data.title as string,
            category: (action.data.category as string) || 'household',
            task_type: (action.data.task_type as string) || 'quick',
            description: action.data.description as string | undefined,
          });
          toast('Taak aangemaakt', 'success');
          break;
        case 'add_to_shopping':
          await createItem({
            name: action.data.item as string,
            current_quantity: 0,
            unit: (action.data.unit as string) || 'stuks',
            threshold_quantity: (action.data.quantity as number) || 1,
            category: 'boodschappen',
          } as never);
          toast('Toegevoegd aan boodschappen', 'success');
          break;
        case 'complete_task':
          await completeTask(action.data.task_id as string);
          toast('Taak afgerond', 'success');
          break;
        case 'snooze_task':
          await snoozeTask(action.data.task_id as string);
          toast('Taak uitgesteld', 'success');
          break;
        default:
          toast('Actie niet herkend', 'error');
      }
    } catch {
      toast('Actie mislukt', 'error');
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <h2 className="text-xl font-display font-semibold mb-3">Chat met AI</h2>

      <div className="flex-1 overflow-y-auto space-y-3 pb-2">
        {loading ? (
          <p className="text-sm text-text-muted text-center py-8">Berichten laden...</p>
        ) : messages.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-text-muted text-sm mb-2">
              Stel een vraag over je gezinssituatie, taken of planning.
            </p>
            <p className="text-xs text-text-muted">
              De AI kent je situatie en denkt actief mee.
            </p>
            {/* Quick start suggestions */}
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {['Hoe is de taakverdeling?', 'Wat moet ik vandaag doen?', 'Wat is bijna op?'].map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="px-3 py-1.5 rounded-full bg-surface-alt text-text-muted text-xs hover:bg-border transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              role={msg.role}
              content={msg.content}
              timestamp={msg.created_at}
              actions={msg.actions}
              onAction={handleAction}
            />
          ))
        )}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-surface-alt text-text-muted px-4 py-2.5 rounded-lg rounded-bl-none text-sm">
              Aan het denken...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={sending} />
    </div>
  );
}
