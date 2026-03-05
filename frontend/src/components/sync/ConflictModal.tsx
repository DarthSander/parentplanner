'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { ConflictData } from '@/store/sync';

interface ConflictModalProps {
  conflict: ConflictData;
  onResolve: (resolution: 'keep_local' | 'keep_server') => void;
  onDismiss: () => void;
}

export default function ConflictModal({ conflict, onResolve, onDismiss }: ConflictModalProps) {
  const [selected, setSelected] = useState<'keep_local' | 'keep_server' | null>(null);

  const changedFields = Object.keys(conflict.localVersion).filter(
    (key) =>
      key !== 'version' &&
      key !== 'updated_at' &&
      JSON.stringify(conflict.localVersion[key]) !== JSON.stringify(conflict.serverVersion[key]),
  );

  const resourceLabel = conflict.resourceType === 'task' ? 'taak' : 'item';

  return (
    <Modal isOpen onClose={onDismiss} title="Synchronisatieconflict">
      <p className="text-sm text-text-muted mb-4">
        Deze {resourceLabel} is door iemand anders aangepast terwijl je offline was.
        Welke versie wil je behouden?
      </p>

      <div className="flex flex-col gap-3 mb-4">
        <button
          onClick={() => setSelected('keep_local')}
          className={`text-left p-3 rounded-md border transition-colors ${
            selected === 'keep_local' ? 'border-primary bg-primary/5' : 'border-border'
          }`}
        >
          <h4 className="font-medium text-sm mb-1">Jouw versie (offline)</h4>
          {changedFields.map((field) => (
            <div key={field} className="text-xs text-text-muted">
              <span className="font-medium">{field}:</span>{' '}
              {String(conflict.localVersion[field])}
            </div>
          ))}
        </button>

        <button
          onClick={() => setSelected('keep_server')}
          className={`text-left p-3 rounded-md border transition-colors ${
            selected === 'keep_server' ? 'border-primary bg-primary/5' : 'border-border'
          }`}
        >
          <h4 className="font-medium text-sm mb-1">Huidige versie (server)</h4>
          {changedFields.map((field) => (
            <div key={field} className="text-xs text-text-muted">
              <span className="font-medium">{field}:</span>{' '}
              {String(conflict.serverVersion[field])}
            </div>
          ))}
        </button>
      </div>

      <div className="flex gap-2">
        <Button onClick={() => selected && onResolve(selected)} disabled={!selected}>
          Toepassen
        </Button>
        <Button variant="secondary" onClick={onDismiss}>
          Later beslissen
        </Button>
      </div>
    </Modal>
  );
}
