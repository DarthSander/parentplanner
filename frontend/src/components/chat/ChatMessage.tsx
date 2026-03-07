'use client';

export interface ChatActionData {
  action: string;
  label: string;
  data: Record<string, unknown>;
}

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  actions?: ChatActionData[];
  onAction?: (action: ChatActionData) => void;
}

export default function ChatMessage({ role, content, timestamp, actions, onAction }: ChatMessageProps) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className="max-w-[85%]">
        <div className={`px-4 py-2.5 rounded-lg text-sm ${
          isUser
            ? 'bg-primary text-white rounded-br-none'
            : 'bg-surface-alt text-text-main rounded-bl-none'
        }`}>
          <p className="whitespace-pre-wrap">{content}</p>
          <p className={`text-[10px] mt-1 ${isUser ? 'text-white/60' : 'text-text-muted'}`}>
            {new Date(timestamp).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>

        {/* Action buttons */}
        {!isUser && actions && actions.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1.5 ml-1">
            {actions.map((action, i) => (
              <button
                key={i}
                onClick={() => onAction?.(action)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                  ${i === 0
                    ? 'bg-primary text-white hover:bg-primary-light'
                    : 'bg-surface border border-border text-text-main hover:bg-surface-alt'
                  }`}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
