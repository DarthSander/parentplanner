'use client';

import { useEffect, useRef, useState } from 'react';
import api from '@/lib/api';
import ChatMessage from '@/components/chat/ChatMessage';
import ChatInput from '@/components/chat/ChatInput';
import { toast } from '@/components/ui/Toast';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.get('/chat/history')
      .then(({ data }) => setMessages(data))
      .catch(() => {})
      .finally(() => setLoading(false));
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
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      toast('Kon bericht niet versturen', 'error');
    } finally {
      setSending(false);
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
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessage key={msg.id} role={msg.role} content={msg.content} timestamp={msg.created_at} />
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
