'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { useHouseholdStore } from '@/store/household';
import { signOut } from '@/lib/auth';
import { can } from '@/lib/permissions';

const menuItems = [
  { href: '/settings/members', label: 'Leden beheren', description: 'Uitnodigen en rollen wijzigen', permission: 'manage_members' },
  { href: '/settings/notifications', label: 'Notificaties', description: 'Meldingsvoorkeuren instellen', permission: null },
  { href: '/settings/subscription', label: 'Abonnement', description: 'Plan en facturatie', permission: 'view_subscription' },
  { href: '/settings/calendar', label: 'Agenda koppelingen', description: 'Google Calendar en CalDAV koppelen', permission: null },
  { href: '/patterns', label: 'Patronen', description: 'AI-analyse van je gezin', permission: 'view_patterns' },
  { href: '/daycare', label: 'Opvang', description: 'Briefing instellingen', permission: 'manage_settings' },
];

export default function SettingsPage() {
  const router = useRouter();
  const { currentMember, household } = useHouseholdStore();
  const role = currentMember?.role as 'owner' | 'partner' | 'caregiver' | undefined;

  const handleLogout = async () => {
    await signOut();
    router.push('/auth/login');
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-display font-semibold">Instellingen</h2>

      {household && (
        <Card>
          <h3 className="text-sm font-medium mb-1">{household.name}</h3>
          <p className="text-xs text-text-muted">
            {currentMember?.display_name} &middot; {currentMember?.role}
          </p>
        </Card>
      )}

      <div className="space-y-2">
        {menuItems
          .filter((item) => !item.permission || (role && can(role, item.permission)))
          .map((item) => (
            <Link key={item.href} href={item.href}>
              <Card className="hover:shadow-sm transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs text-text-muted">{item.description}</p>
                  </div>
                  <svg className="w-5 h-5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </Card>
            </Link>
          ))}
      </div>

      <div className="pt-4">
        <Button variant="ghost" className="w-full text-danger" onClick={handleLogout}>
          Uitloggen
        </Button>
      </div>
    </div>
  );
}
