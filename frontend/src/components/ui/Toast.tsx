'use client';

import { useEffect, useState } from 'react';

type ToastType = 'success' | 'error' | 'info';

interface ToastData {
  id: string;
  message: string;
  type: ToastType;
}

let addToast: (message: string, type?: ToastType) => void;

const typeClasses: Record<ToastType, string> = {
  success: 'bg-success text-white',
  error: 'bg-danger text-white',
  info: 'bg-primary text-white',
};

export function toast(message: string, type: ToastType = 'info') {
  addToast?.(message, type);
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  addToast = (message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  return (
    <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 w-[90%] max-w-sm">
      {toasts.map((t) => (
        <div key={t.id} className={`px-4 py-3 rounded-md shadow-md text-sm font-medium animate-fade-in ${typeClasses[t.type]}`}>
          {t.message}
        </div>
      ))}
    </div>
  );
}
