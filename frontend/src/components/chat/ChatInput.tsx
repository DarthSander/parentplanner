'use client';

import { useState, useRef } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setMessage('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex items-end gap-2 p-3 bg-surface border-t border-border">
      <textarea
        ref={inputRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Stel een vraag..."
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none px-3 py-2 rounded-md border border-border bg-background
          text-sm text-text-main placeholder:text-text-muted
          focus:outline-none focus:ring-2 focus:ring-primary
          max-h-32"
      />
      <button
        onClick={handleSend}
        disabled={!message.trim() || disabled}
        className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-white
          flex items-center justify-center
          disabled:opacity-50 disabled:cursor-not-allowed
          hover:bg-primary-light transition-colors"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m0 0l-7 7m7-7l7 7" />
        </svg>
      </button>
    </div>
  );
}
