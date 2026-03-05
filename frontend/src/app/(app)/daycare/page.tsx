'use client';

import { useEffect, useState } from 'react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';

export default function DaycarePage() {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-display font-semibold">Opvang</h2>

      <Card>
        <p className="text-sm text-text-muted">
          De opvangbriefing wordt elke ochtend automatisch verstuurd via WhatsApp of e-mail
          naar je opvangcontact. Stel dit in via de backend.
        </p>
      </Card>

      <Card>
        <h3 className="text-sm font-medium mb-2">Briefing instellingen</h3>
        <div className="space-y-2 text-sm text-text-muted">
          <p>Verstuurmethode: WhatsApp / E-mail</p>
          <p>Tijdstip: 06:45</p>
          <p>Dagen: ingesteld per contactpersoon</p>
        </div>
      </Card>
    </div>
  );
}
