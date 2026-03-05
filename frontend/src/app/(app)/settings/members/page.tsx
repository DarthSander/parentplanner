'use client';

import { useState } from 'react';
import { useHouseholdStore } from '@/store/household';
import Avatar from '@/components/ui/Avatar';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import Card from '@/components/ui/Card';
import { toast } from '@/components/ui/Toast';
import api from '@/lib/api';

export default function MembersPage() {
  const { members, fetchMembers } = useHouseholdStore();
  const [showInvite, setShowInvite] = useState(false);
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [role, setRole] = useState('partner');
  const [inviting, setInviting] = useState(false);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviting(true);
    try {
      await api.post('/members/invite', { email, display_name: displayName, role });
      toast('Uitnodiging verstuurd!', 'success');
      setShowInvite(false);
      setEmail('');
      setDisplayName('');
    } catch {
      toast('Kon uitnodiging niet versturen', 'error');
    } finally {
      setInviting(false);
    }
  };

  const handleRemove = async (memberId: string) => {
    try {
      await api.delete(`/members/${memberId}`);
      toast('Lid verwijderd', 'success');
      fetchMembers();
    } catch {
      toast('Kon lid niet verwijderen', 'error');
    }
  };

  const roleLabels: Record<string, string> = {
    owner: 'Eigenaar',
    partner: 'Partner',
    caregiver: 'Oppas',
    daycare: 'Opvang',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-display font-semibold">Leden</h2>
        <Button size="sm" onClick={() => setShowInvite(true)}>+ Uitnodigen</Button>
      </div>

      <div className="space-y-2">
        {members.map((member) => (
          <Card key={member.id}>
            <div className="flex items-center gap-3">
              <Avatar name={member.display_name} url={member.avatar_url} />
              <div className="flex-1">
                <p className="text-sm font-medium">{member.display_name}</p>
                <div className="flex items-center gap-2">
                  <Badge>{roleLabels[member.role]}</Badge>
                  {member.email && <span className="text-xs text-text-muted">{member.email}</span>}
                </div>
              </div>
              {member.role !== 'owner' && (
                <button
                  onClick={() => handleRemove(member.id)}
                  className="text-xs text-text-muted hover:text-danger"
                >
                  Verwijder
                </button>
              )}
            </div>
          </Card>
        ))}
      </div>

      <Modal isOpen={showInvite} onClose={() => setShowInvite(false)} title="Lid uitnodigen">
        <form onSubmit={handleInvite} className="flex flex-col gap-4">
          <Input label="Naam" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required autoFocus />
          <Input label="E-mail" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-text-main">Rol</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-border bg-surface text-text-main"
            >
              <option value="partner">Partner</option>
              <option value="caregiver">Oppas</option>
            </select>
          </div>
          <div className="flex gap-2 pt-2">
            <Button type="submit" loading={inviting}>Verstuur uitnodiging</Button>
            <Button type="button" variant="secondary" onClick={() => setShowInvite(false)}>Annuleren</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
