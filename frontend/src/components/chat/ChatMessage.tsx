'use client';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] px-4 py-2.5 rounded-lg text-sm ${
        isUser
          ? 'bg-primary text-white rounded-br-none'
          : 'bg-surface-alt text-text-main rounded-bl-none'
      }`}>
        <p className="whitespace-pre-wrap">{content}</p>
        <p className={`text-[10px] mt-1 ${isUser ? 'text-white/60' : 'text-text-muted'}`}>
          {new Date(timestamp).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}
