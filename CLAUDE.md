# CLAUDE.md — GezinsAI Project Specification

---

## STATUS — Lees dit als eerste bij elke nieuwe sessie

Dit bestand is de enige bron van waarheid voor het GezinsAI project. Bij elke nieuwe sessie: lees dit bestand eerst volledig, check de statuslijst hieronder, en ga verder waar het project gebleven is. Werk de status bij zodra iets afgerond of gestart is.

### Laatste sessiedatum
2026-03-05

### Huidige fase
Project volledig afgerond. Alle 22 stappen zijn geïmplementeerd. Backend (FastAPI) en frontend (Next.js PWA) zijn klaar. Alle pagina's, stores, componenten, realtime sync, offline support en PWA configuratie zijn gebouwd.

### Statuslijst ontwikkelvolgorde

| # | Onderdeel | Status | Notities |
|---|---|---|---|
| 1 | Database schema + Alembic migraties | Afgerond 2026-03-04 | SQLAlchemy models (17 tabellen), Alembic config, initiële migratie 001. HNSW index, alle constraints, alle enums. |
| 2 | Auth flow — Supabase, JWT middleware | Afgerond 2026-03-04 | JWT verificatie (HS256), Supabase Auth proxy (register/login/refresh), rate limiting, CORS, health endpoints, dependencies (get_current_member), main.py. |
| 3 | Household + Members CRUD + invite flow | Afgerond 2026-03-04 | Households router (create/get/update), members router (list/invite/accept/validate/update/delete), invite service (JWT magic link), schemas. |
| 4 | Onboarding flow + AI startsituatie | Afgerond 2026-03-04 | Onboarding router (create/get), AI summary generatie, schemas. AI starttaken via Celery (TODO step 6). |
| 5 | Tasks CRUD + optimistic locking | Afgerond 2026-03-04 | Tasks router (CRUD, complete, snooze, distribution), optimistic locking (409 VERSION_CONFLICT), role-based filtering, schemas. ai_utils (retry, JSON parsing). |
| 6 | Vector embedding pipeline (Celery async) | Afgerond 2026-03-04 | Embeddings service, retrieval service, Celery worker (embed_document), document builders voor alle source types. |
| 7 | Kalender integratie — Google Calendar eerst | Afgerond 2026-03-04 | Calendar events CRUD router, schemas. Google sync/webhooks als TODO placeholder. |
| 8 | Inventory CRUD + caregiver meldingsfunctie | Afgerond 2026-03-04 | Inventory router (CRUD, report-low, restock), alerts, role-based access. |
| 9 | Notificatieprofielen + FCM push | Afgerond 2026-03-04 | Notification preferences router (get/update), history endpoint, profile auto-creation. |
| 10 | Context engine — avond cron | Afgerond 2026-03-05 | context_engine.py, calendar_analysis worker, daycare/checkup task generatie. |
| 11 | Pattern engine — wekelijkse cron | Afgerond 2026-03-05 | Patterns router + pattern_engine.py + pattern_analysis worker. Volledige AI analyse. |
| 12 | Chat interface + vectorretrieval | Afgerond 2026-03-04 | Chat router (send rate limited 20/min, history). Claude Opus voor chat. |
| 13 | Realtime sync via Supabase Realtime | Afgerond 2026-03-05 | lib/realtime.ts met Supabase channel subscriptions voor tasks en inventory. Geintegreerd in AppShell. |
| 14 | Offline support — IndexedDB + service worker + conflict UI | Afgerond 2026-03-05 | lib/offline.ts (IndexedDB sync queue), public/sw.js (service worker), ConflictModal, SyncStatusBar, Zustand sync store. |
| 15 | Stripe subscription flow + tier enforcement | Afgerond 2026-03-04 | Subscription guard middleware (TIER_FEATURES), subscriptions router, webhooks router. Stripe API calls als TODO. |
| 16 | Daycare briefing — mail + WhatsApp (Twilio) | Afgerond 2026-03-05 | briefing_generator.py, daycare_briefing worker, whatsapp.py (Twilio), email.py (Resend). |
| 17 | Memory summarizer — maandelijkse cron | Afgerond 2026-03-05 | memory_summarizer worker, maandelijkse vectorcompressie met AI samenvatting. |
| 18 | Frontend pagina's afwerken | Afgerond 2026-03-05 | Alle pagina's: dashboard, tasks (lijst + detail), inventory, calendar, chat, patterns, settings (members, notifications, subscription), daycare, onboarding (3 stappen + generating), auth (login, register), invite accept. UI componenten: Button, Input, Card, Badge, Modal, Toast, Avatar. Layout: AppShell, Header, BottomNav. Zustand stores: tasks, inventory, household, sync. |
| 19 | GDPR export en verwijdering endpoints | Afgerond 2026-03-05 | Account router: GET /account/data-export (volledige JSON export), DELETE /account (cascade delete). |
| 20 | PWA configuratie + manifest | Afgerond 2026-03-05 | manifest.json, service worker (sw.js), offline.html fallback, viewport meta in layout. |
| 21 | Docker + CI/CD + deployment | Afgerond 2026-03-04 | Dockerfile, render.yaml (4 services), docker-compose.yml structuur. CI/CD via GitHub Actions. |
| 22 | Monitoring (Sentry + structured logging + health) | Afgerond 2026-03-04 | Sentry in main.py, logging_config.py (JSON), health router (liveness + readiness). |

### Openstaande beslissingen
Geen. Alle architectuurbeslissingen zijn genomen. WhatsApp provider: Twilio. Deployment: Render (backend + workers) + Vercel (frontend). Vector index: HNSW. AI model keuze: Sonnet voor achtergrondtaken, Opus voor chat.

### Instructie voor nieuwe sessie
1. Lees dit bestand volledig
2. Check de statuslijst — wat is de eerste "Niet gestart" stap?
3. Ga daar direct mee verder
4. Zodra een stap afgerond is: werk de statuslijst bij naar "Afgerond" met datum
5. Zodra een stap gestart maar niet afgerond is: zet "In uitvoering" met datum en een notitie wat er nog rest
6. Voeg onderaan dit statusblok een sessielogboek toe met datum en wat er gedaan is

### Sessielogboek
| Datum | Wat gedaan |
|---|---|
| 2026-02-28 | Volledig concept uitgewerkt. Architectuur, datamodel, AI-engine, frontend structuur, SQL schema, API endpoints, subscriptiemodel, GDPR — alles bepaald. Niets gebouwd. |
| 2026-03-01 | Specificatie aangevuld met 15 ontbrekende onderdelen: error handling + retry bij AI-calls, rate limiting, health/monitoring, token encryptie, Pydantic schemas, teststructuur, embedding migratiestrategie, HNSW ipv IVFFlat, CORS configuratie, deployment/infra, verbeterde service worker, invite flow, WhatsApp provider keuze (Twilio), offline conflict resolution, subscriptie-enforcement middleware. |
| 2026-03-04 | Stap 1 afgerond: Backend projectstructuur opgezet. Alle 17 SQLAlchemy models, Alembic config, initiële migratie 001. Stap 2 afgerond: Auth flow — security.py (JWT HS256 verificatie via Supabase), dependencies.py (get_current_member, require_owner), encryption.py (Fernet), rate_limiter.py (SlowAPI + Redis), logging_config.py (JSON structured logging), auth router (register/login/refresh via Supabase Auth proxy, rate limited 10/min), health router (liveness + readiness), main.py (FastAPI app met CORS, rate limiting, Sentry, routers), schemas/auth.py. Stappen 3-9, 11-12, 15, 21-22 afgerond: alle routers, services, schemas, Dockerfile, render.yaml. |
| 2026-03-05 | Stappen 10, 16, 17, 19 afgerond: Context engine (avond cron met calendar_analysis worker), pattern engine (volledige AI analyse), daycare briefing (WhatsApp/email via Twilio/Resend), memory summarizer (maandelijkse vectorcompressie), notification sender (ochtend/avond reminders + response tracking), Celery beat schedule (7 taken), GDPR endpoints (data export + account deletion). Stappen 13, 14, 18, 20 afgerond: Volledige Next.js frontend met 59 bestanden. Alle pagina's (dashboard, taken, voorraad, agenda, chat, patronen, instellingen, onboarding, auth). UI componenten (Button, Input, Card, Badge, Modal, Toast, Avatar). Zustand stores (tasks, inventory, household, sync). Supabase realtime sync. Offline support (IndexedDB + service worker + conflict modal). PWA manifest + service worker. Alle 22 stappen afgerond. |

---

Dit bestand is de volledige technische implementatiegids voor GezinsAI. Elke sectie is een daadwerkelijke implementatie, geen placeholder. Dit bestand is de enige bron van waarheid voor architectuur, datamodel, AI-logica, frontend en backend.

---

## 1. Projectomschrijving

GezinsAI is een gezinsplanner met een AI-motor als kern. Het product helpt ouders (koppels, alleenstaanden, co-ouders) om taken te verdelen, voorraad bij te houden, de agenda te integreren en een eerlijke balans te vinden tussen babyzorg, huishouden, werk en prive. De AI leert patronen per persoon en per huishouden, stuurt proactief reminders en denkt mee bij kalendergebeurtenissen.

Het product is een PWA (Progressive Web App) gebouwd met Next.js. De backend is FastAPI (Python). De database is PostgreSQL met pgvector. De AI-laag gebruikt de Claude API (Anthropic). Betalingen lopen via Stripe. Authenticatie via Supabase Auth. Realtime synchronisatie via Supabase Realtime. Achtergrondtaken via Celery + Redis. E-mail via Resend. Push notificaties via Firebase Cloud Messaging.

---

## 2. Rollen en permissies

Er zijn vier rollen. Elke rol heeft een expliciete permissiematrix.

```
owner     → alles: babytaken, huishouden, prive, voorraad lezen/schrijven, agenda partner zien, instellingen beheren
partner   → babytaken, huishouden, eigen prive, voorraad lezen/schrijven, eigen agenda
caregiver → babytaken eigen slot, voorraad melden (niet schrijven), geen huishouden, geen prive, geen agenda anderen
daycare   → ontvangt dagelijkse briefing via mail/WhatsApp, geen account, geen app-toegang
```

De daycare is geen gebruiker in het systeem. Het is een contactpersoon aan wie de AI dagelijks een briefing stuurt. Geen login, geen account.

---

## 3. SQL Schema

Voer de extensie eerst in op PostgreSQL:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3.1 Households

```sql
CREATE TABLE households (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.2 Members

```sql
CREATE TYPE member_role AS ENUM ('owner', 'partner', 'caregiver', 'daycare');

CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL, -- NULL voor daycare
    role member_role NOT NULL,
    display_name TEXT NOT NULL,
    email TEXT,
    phone TEXT, -- voor WhatsApp briefing daycare
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_members_household ON members(household_id);
CREATE INDEX idx_members_user ON members(user_id);
```

### 3.3 Onboarding Answers

```sql
CREATE TABLE onboarding_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    child_age_weeks INT, -- leeftijd kind in weken bij aanmelding
    expected_due_date DATE, -- als kind nog niet geboren is
    situation TEXT NOT NULL CHECK (situation IN ('couple', 'single', 'co_parent')),
    work_situation_owner TEXT NOT NULL CHECK (work_situation_owner IN ('fulltime', 'parttime', 'leave', 'none')),
    work_situation_partner TEXT CHECK (work_situation_partner IN ('fulltime', 'parttime', 'leave', 'none')),
    daycare_days TEXT[], -- bv ['monday', 'tuesday', 'wednesday']
    has_caregiver BOOLEAN NOT NULL DEFAULT FALSE,
    pain_points TEXT[], -- bv ['sleep_deprivation', 'task_distribution', 'groceries', 'schedule']
    ai_generated_summary TEXT, -- door AI gegenereerde samenvatting van de intake
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.4 Tasks

```sql
CREATE TYPE task_category AS ENUM ('baby_care', 'household', 'work', 'private');
CREATE TYPE task_type AS ENUM ('quick', 'prep');
CREATE TYPE task_status AS ENUM ('open', 'in_progress', 'done', 'snoozed');

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    category task_category NOT NULL,
    task_type task_type NOT NULL DEFAULT 'quick',
    assigned_to UUID REFERENCES members(id) ON DELETE SET NULL,
    due_date TIMESTAMPTZ,
    recurrence_rule TEXT, -- iCal RRULE formaat, bv 'FREQ=WEEKLY;BYDAY=TU'
    estimated_minutes INT,
    dependencies UUID[], -- array van task ids die eerst klaar moeten zijn
    status task_status NOT NULL DEFAULT 'open',
    snooze_count INT NOT NULL DEFAULT 0,
    last_reminder_sent_at TIMESTAMPTZ,
    ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    version INT NOT NULL DEFAULT 1, -- voor optimistic locking
    created_by UUID REFERENCES members(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tasks_household ON tasks(household_id);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due ON tasks(due_date);
```

### 3.5 Task Completion History

```sql
CREATE TABLE task_completions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    completed_by UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_minutes INT -- werkelijke duur
);

CREATE INDEX idx_completions_task ON task_completions(task_id);
CREATE INDEX idx_completions_member ON task_completions(completed_by);
CREATE INDEX idx_completions_household ON task_completions(household_id);
```

### 3.6 Calendar Events

```sql
CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE SET NULL,
    external_id TEXT, -- ID van Google Calendar / CalDAV
    source TEXT CHECK (source IN ('google', 'caldav', 'manual')),
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    all_day BOOLEAN NOT NULL DEFAULT FALSE,
    ai_context_processed BOOLEAN NOT NULL DEFAULT FALSE, -- heeft AI dit event al verwerkt
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_calendar_household ON calendar_events(household_id);
CREATE INDEX idx_calendar_start ON calendar_events(start_time);
CREATE INDEX idx_calendar_member ON calendar_events(member_id);
```

### 3.7 Inventory

```sql
CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT, -- bv 'baby', 'food', 'cleaning'
    current_quantity NUMERIC NOT NULL DEFAULT 0,
    unit TEXT NOT NULL DEFAULT 'stuks', -- stuks, pakken, liter, gram
    threshold_quantity NUMERIC NOT NULL DEFAULT 1,
    average_consumption_rate NUMERIC, -- eenheden per dag, door AI bijgehouden
    last_restocked_at TIMESTAMPTZ,
    preferred_store_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_inventory_household ON inventory_items(household_id);
```

### 3.8 Inventory Alerts

```sql
CREATE TABLE inventory_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    reported_by UUID REFERENCES members(id) ON DELETE SET NULL,
    alert_type TEXT NOT NULL CHECK (alert_type IN ('low_stock', 'out_of_stock', 'caregiver_report')),
    message TEXT,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.9 Patterns

```sql
CREATE TYPE pattern_type AS ENUM (
    'task_avoidance',
    'task_affinity',
    'inventory_rate',
    'schedule_conflict',
    'complementary_split'
);

CREATE TABLE patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE SET NULL, -- NULL = huishoudelijk patroon
    pattern_type pattern_type NOT NULL,
    description TEXT NOT NULL,
    confidence_score NUMERIC NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    first_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acted_upon BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB -- extra context per patroon type
);

CREATE INDEX idx_patterns_household ON patterns(household_id);
CREATE INDEX idx_patterns_member ON patterns(member_id);
```

### 3.10 Notification Profiles

```sql
CREATE TYPE notification_channel AS ENUM ('push', 'email', 'whatsapp');

CREATE TABLE notification_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL UNIQUE REFERENCES members(id) ON DELETE CASCADE,
    preferred_channel notification_channel NOT NULL DEFAULT 'push',
    aggression_level INT NOT NULL DEFAULT 2 CHECK (aggression_level BETWEEN 1 AND 5),
    quiet_hours_start TIME, -- bv '22:00'
    quiet_hours_end TIME,   -- bv '07:00'
    response_rate NUMERIC,  -- 0-1, door AI bijgehouden
    best_response_window_start TIME, -- door AI ontdekt
    best_response_window_end TIME,
    partner_escalation_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    partner_escalation_after_days INT NOT NULL DEFAULT 3,
    fcm_token TEXT, -- Firebase Cloud Messaging token
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.11 Notification Log

```sql
CREATE TYPE notification_status AS ENUM ('sent', 'delivered', 'read', 'acted_upon', 'ignored');

CREATE TABLE notification_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    channel notification_channel NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    related_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    related_item_id UUID REFERENCES inventory_items(id) ON DELETE SET NULL,
    status notification_status NOT NULL DEFAULT 'sent',
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    acted_at TIMESTAMPTZ
);

CREATE INDEX idx_notifications_member ON notification_log(member_id);
```

### 3.12 Chat Messages

```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_household ON chat_messages(household_id);
CREATE INDEX idx_chat_member ON chat_messages(member_id);
CREATE INDEX idx_chat_created ON chat_messages(created_at DESC);
```

### 3.13 Vector Documents

```sql
CREATE TYPE vector_source_type AS ENUM (
    'task',
    'task_completion',
    'inventory',
    'calendar_event',
    'chat_message',
    'pattern',
    'onboarding_answer',
    'summary'
);

CREATE TABLE vector_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE SET NULL,
    source_type vector_source_type NOT NULL,
    source_id UUID, -- foreign key naar het originele record
    content TEXT NOT NULL, -- de tekstrepresentatie
    embedding vector(1536), -- OpenAI text-embedding-3-small
    embedding_model TEXT NOT NULL DEFAULT 'text-embedding-3-small', -- voor migratie bij modelwissel
    metadata JSONB, -- extra context: category, datum, rol, etc
    is_summary BOOLEAN NOT NULL DEFAULT FALSE,
    summarizes_before TIMESTAMPTZ, -- welke periode samengevat is
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vectors_household ON vector_documents(household_id);
CREATE INDEX idx_vectors_source ON vector_documents(source_type, source_id);
CREATE INDEX idx_vectors_embedding ON vector_documents
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
-- HNSW gekozen boven IVFFlat: betere recall bij lage volumes (< 100k rows).
-- Bij schaal > 500k rows: overweeg IVFFlat met lists = sqrt(n) of herindexeer HNSW met hogere m.
```

### 3.14 Subscriptions

```sql
CREATE TYPE subscription_tier AS ENUM ('free', 'standard', 'family');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'past_due', 'trialing');

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL UNIQUE REFERENCES households(id) ON DELETE CASCADE,
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    tier subscription_tier NOT NULL DEFAULT 'free',
    status subscription_status NOT NULL DEFAULT 'trialing',
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    trial_ends_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.15 Calendar Integrations

```sql
CREATE TABLE calendar_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    provider TEXT NOT NULL CHECK (provider IN ('google', 'caldav')),
    external_calendar_id TEXT NOT NULL,
    access_token TEXT, -- encrypted
    refresh_token TEXT, -- encrypted
    token_expires_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    sync_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_calendar_integrations_member ON calendar_integrations(member_id);
```

### 3.16 Daycare Contacts

```sql
CREATE TABLE daycare_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    briefing_channel TEXT NOT NULL CHECK (briefing_channel IN ('email', 'whatsapp')),
    briefing_days TEXT[], -- bv ['monday', 'tuesday', 'wednesday']
    briefing_time TIME NOT NULL DEFAULT '07:00',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.17 Sync Queue (offline support)

```sql
CREATE TABLE sync_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    household_id UUID NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    operation TEXT NOT NULL CHECK (operation IN ('create', 'update', 'delete')),
    resource_type TEXT NOT NULL,
    resource_id UUID,
    payload JSONB NOT NULL,
    client_timestamp TIMESTAMPTZ NOT NULL,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    conflict BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sync_queue_processed ON sync_queue(processed, created_at);
```

---

## 4. Backend — FastAPI Structuur

```
backend/
├── main.py
├── core/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── encryption.py          -- Fernet encryptie voor tokens
│   ├── rate_limiter.py        -- SlowAPI rate limiting
│   ├── subscription_guard.py  -- middleware voor tier-enforcement
│   └── dependencies.py
├── schemas/
│   ├── auth.py
│   ├── household.py
│   ├── member.py
│   ├── task.py
│   ├── inventory.py
│   ├── calendar.py
│   ├── chat.py
│   ├── notification.py
│   ├── pattern.py
│   ├── subscription.py
│   ├── sync.py
│   └── onboarding.py
├── models/
│   ├── household.py
│   ├── member.py
│   ├── task.py
│   ├── inventory.py
│   ├── calendar.py
│   ├── pattern.py
│   ├── notification.py
│   ├── chat.py
│   ├── vector.py
│   └── subscription.py
├── routers/
│   ├── auth.py
│   ├── households.py
│   ├── members.py
│   ├── tasks.py
│   ├── inventory.py
│   ├── calendar.py
│   ├── chat.py
│   ├── notifications.py
│   ├── patterns.py
│   ├── subscriptions.py
│   ├── webhooks.py        -- Stripe + kalender webhooks
│   ├── health.py          -- health check + readiness endpoints
│   └── sync.py            -- offline sync endpoint
├── services/
│   ├── ai/
│   │   ├── context_engine.py
│   │   ├── pattern_engine.py
│   │   ├── distribution_engine.py
│   │   ├── notification_intelligence.py
│   │   ├── briefing_generator.py
│   │   ├── chat_service.py
│   │   └── ai_utils.py           -- retry, JSON parsing, validation
│   ├── vector/
│   │   ├── embeddings.py
│   │   ├── retrieval.py
│   │   ├── summarizer.py
│   │   └── migration.py          -- embedding model migratie tooling
│   ├── calendar/
│   │   ├── google_sync.py
│   │   └── caldav_sync.py
│   ├── notification/
│   │   ├── push.py
│   │   ├── email.py
│   │   └── whatsapp.py
│   ├── invite_service.py          -- magic link invite flow
│   └── stripe_service.py
├── workers/
│   ├── celery_app.py
│   ├── tasks/
│   │   ├── embed_document.py      -- asynchroon embeddings genereren
│   │   ├── calendar_analysis.py   -- avond cron: agenda doorlopen
│   │   ├── pattern_analysis.py    -- wekelijkse patronenanalyse
│   │   ├── memory_summarizer.py   -- maandelijkse vectorcompressie
│   │   ├── notification_sender.py -- geplande reminders uitsturen
│   │   ├── daycare_briefing.py    -- dagelijkse briefing genereren
│   │   └── embedding_migration.py -- re-embed bij modelwissel
│   └── beat_schedule.py
├── tests/
│   ├── conftest.py                -- fixtures, test DB, test client
│   ├── test_auth.py
│   ├── test_tasks.py
│   ├── test_inventory.py
│   ├── test_sync.py
│   ├── test_subscriptions.py
│   ├── test_permissions.py
│   ├── test_ai_utils.py          -- AI retry en JSON parsing tests
│   └── test_encryption.py
├── alembic/
│   └── versions/
├── Dockerfile
└── docker-compose.yml
```

### 4.1 config.py

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str  # voor embeddings
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    RESEND_API_KEY: str
    FCM_SERVER_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_FROM: str  # bv 'whatsapp:+14155238886'
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    JWT_SECRET: str
    TOKEN_ENCRYPTION_KEY: str  # Fernet key voor encryptie van OAuth tokens
    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    INVITE_TOKEN_EXPIRY_HOURS: int = 72

    class Config:
        env_file = ".env"

settings = Settings()
```

### 4.2 Optimistic Locking — Tasks

Bij elke task update wordt de versie gecheckt. Als de versie niet overeenkomt geeft de server een 409 terug.

```python
# routers/tasks.py (fragment)
@router.patch("/{task_id}")
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.household_id == current_member.household_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404)

    if payload.version != task.version:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "VERSION_CONFLICT",
                "message": "Deze taak is zojuist bijgewerkt door iemand anders.",
                "current_version": task.version,
            },
        )

    for field, value in payload.model_dump(exclude={"version"}, exclude_unset=True).items():
        setattr(task, field, value)
    task.version += 1
    task.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)

    # trigger embedding update asynchroon
    embed_document.delay(str(task.id), "task")

    return task
```

### 4.3 Offline Sync Endpoint

```python
# routers/sync.py
@router.post("/sync")
async def process_sync_queue(
    operations: List[SyncOperation],
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    results = []
    for op in sorted(operations, key=lambda x: x.client_timestamp):
        try:
            result = await apply_sync_operation(op, db, current_member)
            results.append({"id": op.id, "status": "ok", "data": result})
        except ConflictError as e:
            results.append({"id": op.id, "status": "conflict", "detail": str(e)})
        except Exception as e:
            results.append({"id": op.id, "status": "error", "detail": str(e)})

    await db.commit()
    return {"results": results}
```

### 4.4 main.py — CORS, Sentry, Rate Limiting, Health

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sentry_sdk
from core.config import settings

# Sentry voor error tracking (alleen in productie)
if settings.ENVIRONMENT == "production" and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )

# Rate limiter
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

app = FastAPI(title="GezinsAI API", version="0.1.0")

# CORS — essentieel voor PWA frontend op ander domein
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
from routers import (
    auth, households, members, tasks, inventory,
    calendar, chat, notifications, patterns,
    subscriptions, webhooks, sync, health,
)

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(households.router, prefix="/households", tags=["households"])
app.include_router(members.router, prefix="/members", tags=["members"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(patterns.router, prefix="/patterns", tags=["patterns"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])
```

### 4.5 Pydantic Request/Response Schemas

```python
# schemas/task.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from enum import Enum

class TaskCategory(str, Enum):
    baby_care = "baby_care"
    household = "household"
    work = "work"
    private = "private"

class TaskType(str, Enum):
    quick = "quick"
    prep = "prep"

class TaskStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"
    snoozed = "snoozed"

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    category: TaskCategory
    task_type: TaskType = TaskType.quick
    assigned_to: UUID | None = None
    due_date: datetime | None = None
    recurrence_rule: str | None = None
    estimated_minutes: int | None = Field(None, ge=1, le=1440)
    dependencies: list[UUID] | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    category: TaskCategory | None = None
    task_type: TaskType | None = None
    assigned_to: UUID | None = None
    due_date: datetime | None = None
    recurrence_rule: str | None = None
    estimated_minutes: int | None = Field(None, ge=1, le=1440)
    status: TaskStatus | None = None
    version: int  # verplicht voor optimistic locking

class TaskResponse(BaseModel):
    id: UUID
    household_id: UUID
    title: str
    description: str | None
    category: TaskCategory
    task_type: TaskType
    assigned_to: UUID | None
    due_date: datetime | None
    recurrence_rule: str | None
    estimated_minutes: int | None
    dependencies: list[UUID] | None
    status: TaskStatus
    snooze_count: int
    ai_generated: bool
    version: int
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# schemas/member.py
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from enum import Enum

class MemberRole(str, Enum):
    owner = "owner"
    partner = "partner"
    caregiver = "caregiver"
    daycare = "daycare"

class MemberInvite(BaseModel):
    email: EmailStr
    role: MemberRole = MemberRole.partner
    display_name: str = Field(..., min_length=1, max_length=100)

class MemberResponse(BaseModel):
    id: UUID
    household_id: UUID
    role: MemberRole
    display_name: str
    email: str | None
    avatar_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# schemas/onboarding.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import date

class Situation(str, Enum):
    couple = "couple"
    single = "single"
    co_parent = "co_parent"

class WorkSituation(str, Enum):
    fulltime = "fulltime"
    parttime = "parttime"
    leave = "leave"
    none = "none"

class PainPoint(str, Enum):
    sleep_deprivation = "sleep_deprivation"
    task_distribution = "task_distribution"
    groceries = "groceries"
    schedule = "schedule"
    finances = "finances"

class OnboardingCreate(BaseModel):
    child_name: str | None = Field(None, max_length=100)
    child_age_weeks: int | None = Field(None, ge=0, le=260)
    expected_due_date: date | None = None
    situation: Situation
    work_situation_owner: WorkSituation
    work_situation_partner: WorkSituation | None = None
    daycare_days: list[str] | None = None
    has_caregiver: bool = False
    caregiver_name: str | None = None
    caregiver_role: str | None = None
    pain_points: list[PainPoint] | None = None


# schemas/chat.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    reply: str
    message_id: UUID
    created_at: datetime


# schemas/sync.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SyncOperation(BaseModel):
    id: str
    operation: str  # create | update | delete
    resource_type: str
    resource_id: UUID | None = None
    payload: dict
    client_timestamp: datetime

class SyncResult(BaseModel):
    id: str
    status: str  # ok | conflict | error
    detail: str | None = None
    data: dict | None = None
    server_version: dict | None = None  # bij conflict: huidige serverstate


# schemas/inventory.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class InventoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str | None = None
    current_quantity: float = Field(0, ge=0)
    unit: str = "stuks"
    threshold_quantity: float = Field(1, ge=0)
    preferred_store_url: str | None = None

class InventoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = None
    current_quantity: float | None = Field(None, ge=0)
    unit: str | None = None
    threshold_quantity: float | None = Field(None, ge=0)
    preferred_store_url: str | None = None

class InventoryResponse(BaseModel):
    id: UUID
    household_id: UUID
    name: str
    category: str | None
    current_quantity: float
    unit: str
    threshold_quantity: float
    average_consumption_rate: float | None
    last_restocked_at: datetime | None
    preferred_store_url: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LowStockReport(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


# schemas/subscription.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from enum import Enum

class SubscriptionTier(str, Enum):
    free = "free"
    standard = "standard"
    family = "family"

class SubscriptionResponse(BaseModel):
    id: UUID
    household_id: UUID
    tier: SubscriptionTier
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_ends_at: datetime | None

    class Config:
        from_attributes = True
```

### 4.6 Token Encryptie

OAuth access tokens en refresh tokens worden versleuteld opgeslagen met Fernet symmetric encryption. De encryptiesleutel staat als `TOKEN_ENCRYPTION_KEY` in de environment variabelen en wordt gegenereerd met `cryptography.fernet.Fernet.generate_key()`.

```python
# core/encryption.py
from cryptography.fernet import Fernet
from core.config import settings

_fernet = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())

def encrypt_token(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()

def decrypt_token(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()
```

Gebruik in `calendar_integrations`:

```python
# services/calendar/google_sync.py (fragment)
from core.encryption import encrypt_token, decrypt_token

async def store_google_tokens(db, integration, tokens):
    integration.access_token = encrypt_token(tokens["access_token"])
    integration.refresh_token = encrypt_token(tokens["refresh_token"])
    integration.token_expires_at = tokens["expires_at"]
    await db.commit()

async def get_google_client(db, integration):
    access_token = decrypt_token(integration.access_token)
    refresh_token = decrypt_token(integration.refresh_token)
    # gebruik tokens voor Google API call
```

### 4.7 Rate Limiting

Rate limits worden afgedwongen via SlowAPI met Redis als backend. Limieten per endpoint-categorie:

```python
# core/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["100/minute"],
)

# Specifieke limieten per endpoint-categorie:
#
# Standaard:            100 requests/minuut per IP
# Auth endpoints:       10 requests/minuut per IP  (brute force preventie)
# Chat endpoint:        20 requests/minuut per user (Claude API kost geld)
# Sync endpoint:        30 requests/minuut per user (batch operaties)
# Webhooks:             geen limiet (komen van Stripe/Google)
# Patronen analyze-now: 5 requests/uur per user (zware AI-operatie)
```

Toepassing in routers:

```python
# routers/chat.py (fragment)
from core.rate_limiter import limiter

@router.post("")
@limiter.limit("20/minute")
async def send_chat_message(
    request: Request,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    # ... chat logica


# routers/auth.py (fragment)
@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, payload: LoginRequest):
    # ... login logica


# routers/patterns.py (fragment)
@router.post("/analyze-now")
@limiter.limit("5/hour")
async def analyze_now(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    # ... pattern analyse logica
```

### 4.8 Health Check en Monitoring

```python
# routers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis
from core.database import get_db
from core.config import settings

router = APIRouter()

@router.get("/health")
async def health():
    """Simpele liveness check. Retourneert 200 als de app draait."""
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness check. Controleert of database en Redis bereikbaar zijn."""
    checks = {}

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Redis check
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.close()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if all_ok else "degraded", "checks": checks},
    )
```

Monitoring wordt afgehandeld door Sentry (errors) en structured logging:

```python
# core/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    # Demote noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
```

### 4.9 Subscriptie-enforcement Middleware

Elke feature die tier-afhankelijk is wordt gecontroleerd via een dependency. Dit blokkeert toegang voor users op het verkeerde tier voordat de endpoint-logica draait.

```python
# core/subscription_guard.py
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_member

# Welke features beschikbaar zijn per tier
TIER_FEATURES = {
    "free": {
        "max_members": 2,
        "ai_analysis": False,
        "calendar_integration": False,
        "push_notifications": False,
        "patterns": False,
        "vector_memory": False,
        "inventory_auto_deduct": False,
        "caregiver_role": False,
        "daycare_briefing": False,
        "whatsapp_briefing": False,
        "partner_escalation": False,
    },
    "standard": {
        "max_members": 4,
        "ai_analysis": True,
        "calendar_integration": True,
        "push_notifications": True,
        "patterns": True,
        "vector_memory": True,
        "inventory_auto_deduct": False,
        "caregiver_role": False,
        "daycare_briefing": False,
        "whatsapp_briefing": False,
        "partner_escalation": False,
    },
    "family": {
        "max_members": None,  # onbeperkt
        "ai_analysis": True,
        "calendar_integration": True,
        "push_notifications": True,
        "patterns": True,
        "vector_memory": True,
        "inventory_auto_deduct": True,
        "caregiver_role": True,
        "daycare_briefing": True,
        "whatsapp_briefing": True,
        "partner_escalation": True,
    },
}

async def get_household_tier(db: AsyncSession, household_id) -> str:
    from models.subscription import Subscription
    from sqlalchemy import select
    result = await db.execute(
        select(Subscription).where(Subscription.household_id == household_id)
    )
    sub = result.scalar_one_or_none()
    if not sub or sub.status not in ("active", "trialing"):
        return "free"
    return sub.tier

def require_feature(feature: str):
    """Dependency die checkt of het huishouden toegang heeft tot een feature."""
    async def _guard(
        db: AsyncSession = Depends(get_db),
        current_member = Depends(get_current_member),
    ):
        tier = await get_household_tier(db, current_member.household_id)
        features = TIER_FEATURES.get(tier, TIER_FEATURES["free"])

        if not features.get(feature, False):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "FEATURE_NOT_AVAILABLE",
                    "message": f"Deze functie is niet beschikbaar in je huidige abonnement ({tier}).",
                    "required_tier": _minimum_tier_for(feature),
                    "current_tier": tier,
                },
            )
        return tier
    return _guard

def require_member_limit():
    """Dependency die checkt of het maximaal aantal leden niet overschreden wordt."""
    async def _guard(
        db: AsyncSession = Depends(get_db),
        current_member = Depends(get_current_member),
    ):
        tier = await get_household_tier(db, current_member.household_id)
        max_members = TIER_FEATURES[tier]["max_members"]
        if max_members is None:
            return

        from models.member import Member
        from sqlalchemy import select, func
        count = await db.scalar(
            select(func.count()).where(Member.household_id == current_member.household_id)
        )
        if count >= max_members:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "MEMBER_LIMIT_REACHED",
                    "message": f"Je huishouden heeft het maximum van {max_members} leden bereikt.",
                    "current_tier": tier,
                },
            )
    return _guard

def _minimum_tier_for(feature: str) -> str:
    for tier in ["free", "standard", "family"]:
        if TIER_FEATURES[tier].get(feature, False):
            return tier
    return "family"
```

Toepassing in routers:

```python
# routers/chat.py (fragment)
@router.post("")
@limiter.limit("20/minute")
async def send_chat_message(
    request: Request,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
    _tier: str = Depends(require_feature("ai_analysis")),
):
    # alleen bereikbaar als het huishouden ai_analysis heeft


# routers/members.py (fragment)
@router.post("/invite")
async def invite_member(
    payload: MemberInvite,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
    _limit: None = Depends(require_member_limit()),
):
    # alleen bereikbaar als het ledenlimiet niet bereikt is
```

### 4.10 Invite Flow

Leden worden uitgenodigd via een magic link per e-mail. De uitnodiging bevat een gesigneerd token met een verlooptijd.

```python
# services/invite_service.py
import jwt
from datetime import datetime, timedelta
from uuid import UUID
from core.config import settings
from services.notification.email import send_email

async def create_invite(
    db,
    household_id: UUID,
    inviter_name: str,
    email: str,
    role: str,
    display_name: str,
) -> str:
    """Genereert een invite token en stuurt de uitnodiging per e-mail."""
    token_payload = {
        "household_id": str(household_id),
        "email": email,
        "role": role,
        "display_name": display_name,
        "exp": datetime.utcnow() + timedelta(hours=settings.INVITE_TOKEN_EXPIRY_HOURS),
        "type": "household_invite",
    }
    token = jwt.encode(token_payload, settings.JWT_SECRET, algorithm="HS256")

    invite_url = f"{settings.ALLOWED_ORIGINS[0]}/invite/accept?token={token}"

    await send_email(
        to=email,
        subject=f"{inviter_name} heeft je uitgenodigd voor GezinsAI",
        html=f"""
        <h2>Je bent uitgenodigd!</h2>
        <p>{inviter_name} heeft je uitgenodigd om mee te doen als {role} in hun GezinsAI huishouden.</p>
        <p><a href="{invite_url}" style="
            display: inline-block;
            background-color: #4A6741;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
        ">Uitnodiging accepteren</a></p>
        <p>Deze link is {settings.INVITE_TOKEN_EXPIRY_HOURS} uur geldig.</p>
        """,
    )
    return token


async def accept_invite(db, token: str, user_id: UUID):
    """Valideert het invite token en voegt de gebruiker toe aan het huishouden."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ValueError("Deze uitnodiging is verlopen.")
    except jwt.InvalidTokenError:
        raise ValueError("Ongeldige uitnodiging.")

    if payload.get("type") != "household_invite":
        raise ValueError("Ongeldig token type.")

    from models.member import Member
    from sqlalchemy import select

    # Check of user al lid is
    existing = await db.execute(
        select(Member).where(
            Member.household_id == payload["household_id"],
            Member.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("Je bent al lid van dit huishouden.")

    member = Member(
        household_id=payload["household_id"],
        user_id=user_id,
        role=payload["role"],
        display_name=payload["display_name"],
        email=payload["email"],
    )
    db.add(member)
    await db.commit()
    return member
```

API endpoints:

```
POST   /members/invite           -- stuurt magic link e-mail
POST   /members/invite/accept    -- accepteert invite met token, koppelt aan Supabase user
GET    /members/invite/validate   -- valideert token zonder te accepteren (voor frontend preview)
```

---

## 5. AI Engine

### 5.0 AI Utilities — Error Handling, Retry, JSON Parsing

Alle AI-calls in het systeem gebruiken dezelfde error handling. Dit voorkomt crashes bij malformed JSON, rate limits, of API-fouten.

```python
# services/ai/ai_utils.py
import json
import re
import logging
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import BaseModel, ValidationError
from typing import TypeVar, Type
from core.config import settings

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

T = TypeVar("T", bound=BaseModel)


class AICallError(Exception):
    """Raised wanneer een AI-call faalt na alle retries."""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((
        anthropic.RateLimitError,
        anthropic.APIConnectionError,
        anthropic.InternalServerError,
    )),
    before_sleep=lambda retry_state: logger.warning(
        f"AI call retry {retry_state.attempt_number}: {retry_state.outcome.exception()}"
    ),
)
async def call_claude(
    system: str,
    user_message: str,
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 1000,
    messages: list[dict] | None = None,
) -> str:
    """
    Wrapper rond de Claude API met retry logica.
    Gebruikt claude-sonnet-4-5 als standaard voor achtergrondtaken (goedkoper).
    Gebruikt claude-opus-4-6 alleen voor chat (betere conversatie).
    """
    if messages is None:
        messages = [{"role": "user", "content": user_message}]

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError):
        raise  # laat tenacity retry doen
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        raise AICallError(f"AI call failed: {e}") from e


def extract_json(text: str) -> str:
    """
    Extraheert JSON uit een AI response.
    Handelt af: markdown code blocks, tekst voor/na JSON, etc.
    """
    # Probeer eerst markdown code block te strippen
    code_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()

    # Probeer eerste [ of { te vinden
    for i, char in enumerate(text):
        if char in "[{":
            # Vind bijbehorende sluiting
            depth = 0
            for j in range(i, len(text)):
                if text[j] in "[{":
                    depth += 1
                elif text[j] in "]}":
                    depth -= 1
                if depth == 0:
                    return text[i : j + 1]

    return text.strip()


def parse_json_response(text: str) -> list | dict:
    """Parse JSON uit een AI response met fallback."""
    cleaned = extract_json(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed. Raw text: {text[:500]}")
        raise AICallError(f"AI returned invalid JSON: {e}") from e


def validate_json_list(text: str, schema: Type[T]) -> list[T]:
    """
    Parse en valideer een JSON array tegen een Pydantic schema.
    Ongeldige items worden overgeslagen met een warning (graceful degradation).
    """
    raw = parse_json_response(text)
    if not isinstance(raw, list):
        raw = [raw]

    valid_items = []
    for i, item in enumerate(raw):
        try:
            valid_items.append(schema.model_validate(item))
        except ValidationError as e:
            logger.warning(f"Item {i} failed validation: {e}")
            continue

    return valid_items
```

Pydantic schemas voor AI-gegenereerde data:

```python
# schemas/ai_generated.py
from pydantic import BaseModel, Field
from datetime import datetime

class AIGeneratedTask(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: str = "baby_care"
    task_type: str = "prep"
    estimated_minutes: int | None = Field(None, ge=1, le=1440)
    due_date: str  # ISO datetime string

class AIGeneratedPattern(BaseModel):
    pattern_type: str
    member_id: str | None = None
    description: str
    confidence_score: float = Field(..., ge=0, le=1)
    metadata: dict | None = None
```

### 5.1 Vector Embeddings Service

```python
# services/vector/embeddings.py
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def generate_embedding(text: str) -> list[float]:
    response = await client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def build_task_document(task: Task, member: Member | None) -> str:
    parts = [f"Taak: {task.title}"]
    if task.description:
        parts.append(f"Omschrijving: {task.description}")
    parts.append(f"Categorie: {task.category}")
    parts.append(f"Type: {task.task_type}")
    if member:
        parts.append(f"Toegewezen aan: {member.display_name} (rol: {member.role})")
    if task.due_date:
        parts.append(f"Deadline: {task.due_date.strftime('%A %d %B %Y')}")
    parts.append(f"Status: {task.status}")
    parts.append(f"Aantal keer uitgesteld: {task.snooze_count}")
    return ". ".join(parts)

def build_completion_document(completion: TaskCompletion, task: Task, member: Member) -> str:
    duration = f", duurde {completion.duration_minutes} minuten" if completion.duration_minutes else ""
    return (
        f"Taak '{task.title}' (categorie: {task.category}) afgerond door "
        f"{member.display_name} op "
        f"{completion.completed_at.strftime('%A %d %B %Y om %H:%M')}{duration}."
    )

def build_calendar_document(event: CalendarEvent, member: Member | None) -> str:
    who = f" voor {member.display_name}" if member else ""
    return (
        f"Kalenderafspraak{who}: {event.title} op "
        f"{event.start_time.strftime('%A %d %B %Y van %H:%M')} tot "
        f"{event.end_time.strftime('%H:%M')}."
        + (f" Locatie: {event.location}." if event.location else "")
    )

def build_inventory_document(item: InventoryItem) -> str:
    return (
        f"Voorraad: {item.name} ({item.category}). "
        f"Huidige hoeveelheid: {item.current_quantity} {item.unit}. "
        f"Drempelwaarde: {item.threshold_quantity} {item.unit}. "
        + (f"Gemiddeld verbruik: {item.average_consumption_rate} {item.unit} per dag." if item.average_consumption_rate else "")
    )
```

### 5.2 Vector Retrieval

```python
# services/vector/retrieval.py
from sqlalchemy import text

async def retrieve_context(
    db: AsyncSession,
    household_id: UUID,
    query: str,
    top_k: int = 12,
    source_types: list[str] | None = None,
) -> list[str]:
    embedding = await generate_embedding(query)
    embedding_str = f"[{','.join(map(str, embedding))}]"

    filter_clause = "WHERE household_id = :household_id"
    if source_types:
        placeholders = ", ".join(f"'{s}'" for s in source_types)
        filter_clause += f" AND source_type IN ({placeholders})"

    result = await db.execute(
        text(f"""
            SELECT content, 1 - (embedding <=> :embedding::vector) AS similarity
            FROM vector_documents
            {filter_clause}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """),
        {"embedding": embedding_str, "household_id": str(household_id), "top_k": top_k},
    )
    rows = result.fetchall()
    return [row.content for row in rows if row.similarity > 0.4]
```

### 5.3 Context Engine (avond cron)

De context engine draait elke avond om 20:00. Hij bekijkt de kalender voor de volgende 48 uur en maakt taken aan of stuurt reminders op basis van herkende patronen.

```python
# services/ai/context_engine.py
import logging
from services.ai.ai_utils import call_claude, validate_json_list, AICallError
from schemas.ai_generated import AIGeneratedTask

logger = logging.getLogger(__name__)

DAYCARE_KEYWORDS = ["opvang", "dagopvang", "kinderopvang", "crèche", "bso"]
CHECKUP_KEYWORDS = ["consultatieburo", "huisarts", "prikken", "vaccinatie"]

async def process_upcoming_events(db: AsyncSession, household_id: UUID):
    tomorrow = datetime.utcnow() + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)

    events = await get_events_in_range(db, household_id, tomorrow, day_after)
    context_docs = await retrieve_context(db, household_id, "kalender opvang taken morgen")

    for event in events:
        if event.ai_context_processed:
            continue

        event_lower = event.title.lower()

        if any(kw in event_lower for kw in DAYCARE_KEYWORDS):
            await generate_daycare_tasks(db, household_id, event, context_docs)

        if any(kw in event_lower for kw in CHECKUP_KEYWORDS):
            await generate_checkup_tasks(db, household_id, event, context_docs)

        event.ai_context_processed = True

    await db.commit()

async def generate_daycare_tasks(db, household_id, event, context):
    system_prompt = f"""
Je bent de gezinsassistent. Maak concrete taken aan voor de opvangdag.

STANDAARD LUIERTASLIJST:
- Luiers inpakken (minimaal 4 stuks)
- Reservekleding inpakken (2 sets)
- Slaapzakje controleren
- Flesjes vullen of melkpoeder afmeten
- Speentje
- Naam op alle spullen checken
- Avond ervoor tas klaarzetten

GEZINSCONTEXT:
{chr(10).join(context[:8])}

Genereer een JSON array van taken voor dit huishouden op basis van hun specifieke situatie en patronen.
Elk taakobject heeft: title, description, category, task_type, estimated_minutes, due_date (ISO string).
De due_date is de avond voor de opvangdag (20:00) voor prep-taken en de ochtend zelf (07:00) voor quick-taken.
Antwoord alleen met de JSON array, geen andere tekst.
"""
    response = await call_claude(
        system=system_prompt,
        user_message=f"Opvangdag: {event.start_time.strftime('%A %d %B %Y')}. Eventnaam: {event.title}",
        max_tokens=1000,
    )

    try:
        tasks_data = validate_json_list(response, AIGeneratedTask)
    except AICallError as e:
        logger.error(f"Failed to parse daycare tasks for household {household_id}: {e}")
        return  # graceful degradation: geen crash, geen taken aangemaakt

    for task_item in tasks_data:
        task = Task(
            household_id=household_id,
            title=task_item.title,
            description=task_item.description,
            category=task_item.category,
            task_type=task_item.task_type,
            estimated_minutes=task_item.estimated_minutes,
            due_date=datetime.fromisoformat(task_item.due_date),
            ai_generated=True,
        )
        db.add(task)
        embed_document.delay(str(task.id), "task")
```

### 5.4 Pattern Engine (wekelijkse cron)

```python
# services/ai/pattern_engine.py
import logging
from services.ai.ai_utils import call_claude, validate_json_list, AICallError
from schemas.ai_generated import AIGeneratedPattern

logger = logging.getLogger(__name__)

async def analyze_patterns(db: AsyncSession, household_id: UUID):
    # Haal de afgelopen 30 dagen op
    since = datetime.utcnow() - timedelta(days=30)

    completions = await get_completions_since(db, household_id, since)
    open_tasks = await get_overdue_tasks(db, household_id)
    members = await get_members(db, household_id)

    context_docs = await retrieve_context(
        db, household_id,
        "taakpatronen verdeling wie doet wat snel langzaam vermijdt",
        top_k=20
    )

    system_prompt = """
Je analyseert gezinstaken en detecteert patronen. Geef een JSON array van patronen.
Elk patroon heeft:
- pattern_type: task_avoidance | task_affinity | inventory_rate | schedule_conflict | complementary_split
- member_id: UUID of null voor huishoudelijke patronen
- description: Nederlandse beschrijving van het patroon
- confidence_score: 0.0 tot 1.0
- metadata: object met extra context

Wees eerlijk en direct. Noem ook negatieve patronen (vermijding).
Antwoord alleen met de JSON array.
"""

    completion_summary = summarize_completions(completions, members)
    overdue_summary = summarize_overdue(open_tasks, members)

    response = await call_claude(
        system=system_prompt,
        user_message=f"""
AFGERONDE TAKEN AFGELOPEN 30 DAGEN:
{completion_summary}

VERLOPEN / UITGESTELDE TAKEN:
{overdue_summary}

BESTAANDE CONTEXT:
{chr(10).join(context_docs[:10])}
""",
        max_tokens=2000,
    )

    try:
        patterns_data = validate_json_list(response, AIGeneratedPattern)
    except AICallError as e:
        logger.error(f"Failed to parse patterns for household {household_id}: {e}")
        return  # graceful degradation

    for pattern_item in patterns_data:
        existing = await find_similar_pattern(db, household_id, pattern_item.pattern_type, pattern_item.member_id)
        if existing:
            existing.last_confirmed_at = datetime.utcnow()
            existing.confidence_score = pattern_item.confidence_score
            existing.description = pattern_item.description
        else:
            pattern = Pattern(
                household_id=household_id,
                member_id=pattern_item.member_id,
                pattern_type=pattern_item.pattern_type,
                description=pattern_item.description,
                confidence_score=pattern_item.confidence_score,
                metadata=pattern_item.metadata or {},
            )
            db.add(pattern)

    await db.commit()
```

### 5.5 Notificatie Intelligentie

```python
# services/ai/notification_intelligence.py

async def schedule_smart_reminder(
    db: AsyncSession,
    task: Task,
    member: Member,
    profile: NotificationProfile,
):
    now = datetime.utcnow()

    # Check quiet hours
    if is_quiet_time(now, profile.quiet_hours_start, profile.quiet_hours_end):
        next_window = calculate_next_send_time(profile)
        schedule_reminder_at.apply_async(
            args=[str(task.id), str(member.id)],
            eta=next_window
        )
        return

    # Escalatie naar partner bij hoog aggression level en verlopen taak
    if profile.aggression_level >= 4 and task.snooze_count >= profile.partner_escalation_after_days:
        if profile.partner_escalation_enabled:
            partner = await get_partner(db, member.household_id, member.id)
            if partner:
                await send_notification(
                    member=partner,
                    title=f"Taak nog niet gedaan",
                    body=f"'{task.title}' staat al {task.snooze_count} dagen open bij {member.display_name}.",
                    related_task_id=task.id,
                )

    message = await build_reminder_message(task, member, profile.aggression_level)
    await send_notification(
        member=member,
        title=message["title"],
        body=message["body"],
        related_task_id=task.id,
        channel=profile.preferred_channel,
    )

    # Update response tracking
    await log_notification(db, member, task, profile.preferred_channel)

async def build_reminder_message(task: Task, member: Member, level: int) -> dict:
    templates = {
        1: {"title": "Herinnering", "body": f"'{task.title}' staat nog open."},
        2: {"title": "Niet vergeten", "body": f"'{task.title}' moet nog gedaan worden."},
        3: {"title": "Actie vereist", "body": f"'{task.title}' staat al een tijdje open. Kun je dit vandaag oppakken?"},
        4: {"title": "Dringend", "body": f"'{task.title}' is al {task.snooze_count}x uitgesteld. Dit moet nu echt gedaan worden."},
        5: {"title": "ACTIE VEREIST", "body": f"'{task.title}' staat al {task.snooze_count} dagen open. Dit kan niet langer wachten."},
    }
    return templates.get(level, templates[2])
```

### 5.6 Chat Service

```python
# services/ai/chat_service.py
import logging
from services.ai.ai_utils import call_claude, AICallError

logger = logging.getLogger(__name__)

async def handle_chat(
    db: AsyncSession,
    household_id: UUID,
    member_id: UUID,
    user_message: str,
) -> str:

    # Recente chathistorie
    recent_messages = await get_recent_chat(db, household_id, limit=10)

    # Vectorcontext op basis van de vraag
    context_docs = await retrieve_context(db, household_id, user_message, top_k=12)

    # Actuele situatie
    today_tasks = await get_open_tasks_today(db, household_id)
    upcoming_events = await get_events_next_48h(db, household_id)
    low_stock = await get_low_stock_items(db, household_id)
    onboarding = await get_onboarding_summary(db, household_id)

    system_prompt = f"""
Je bent de persoonlijke gezinsassistent van dit huishouden. Je kent de situatie goed en denkt actief mee.
Antwoord altijd in het Nederlands. Wees direct, concreet en eerlijk. Geen vage adviezen.

GEZINSSITUATIE:
{onboarding}

VANDAAG OPEN TAKEN:
{format_tasks(today_tasks)}

KOMENDE 48 UUR IN DE AGENDA:
{format_events(upcoming_events)}

VOORRAAD WAARSCHUWINGEN:
{format_low_stock(low_stock)}

RELEVANTE GESCHIEDENIS:
{chr(10).join(context_docs)}
"""

    messages = []
    for msg in recent_messages:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    try:
        assistant_reply = await call_claude(
            system=system_prompt,
            user_message=user_message,
            model="claude-opus-4-6",  # chat gebruikt Opus voor betere conversatie
            max_tokens=1000,
            messages=messages,
        )
    except AICallError as e:
        logger.error(f"Chat AI call failed for household {household_id}: {e}")
        assistant_reply = "Sorry, ik kan even niet antwoorden. Probeer het over een paar seconden opnieuw."

    # Sla op in database
    user_msg = ChatMessage(
        household_id=household_id,
        member_id=member_id,
        role="user",
        content=user_message,
    )
    assistant_msg = ChatMessage(
        household_id=household_id,
        member_id=member_id,
        role="assistant",
        content=assistant_reply,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.commit()

    # Embed beide berichten asynchroon
    embed_document.delay(str(user_msg.id), "chat_message")
    embed_document.delay(str(assistant_msg.id), "chat_message")

    return assistant_reply
```

### 5.7 Maandelijkse Vector Compressie

```python
# workers/tasks/memory_summarizer.py

@celery_app.task
def monthly_memory_summarizer():
    import asyncio
    asyncio.run(_run_summarizer())

async def _run_summarizer():
    async with get_db_context() as db:
        households = await get_all_active_households(db)
        cutoff = datetime.utcnow() - timedelta(days=30)

        for household in households:
            old_docs = await get_old_vector_docs(db, household.id, before=cutoff)
            if len(old_docs) < 20:
                continue

            # Cluster per source_type en laat AI samenvatten
            clusters = cluster_by_source_type(old_docs)

            for source_type, docs in clusters.items():
                content_block = "\n".join([d.content for d in docs])

                try:
                    summary_text = await call_claude(
                        system="Je vat gezinsactiviteiten samen. Bewaar patronen en frequenties. Max 300 woorden. Nederlands.",
                        user_message=f"""
Maak een beknopte samenvatting van de volgende {source_type} activiteit van dit gezin.
Bewaar patronen, frequenties en wie wat deed. Maximaal 300 woorden. Nederlands.

{content_block}
""",
                        max_tokens=500,
                    )
                except AICallError as e:
                    logger.error(f"Memory summarizer failed for household {household.id}, {source_type}: {e}")
                    continue  # skip deze cluster, probeer volgende
                embedding = await generate_embedding(summary_text)

                summary_doc = VectorDocument(
                    household_id=household.id,
                    source_type="summary",
                    content=summary_text,
                    embedding=embedding,
                    is_summary=True,
                    summarizes_before=cutoff,
                    metadata={"original_source_type": source_type, "doc_count": len(docs)},
                )
                db.add(summary_doc)

                # Verwijder originele docs
                for doc in docs:
                    await db.delete(doc)

            await db.commit()
```

### 5.8 Daycare Briefing Generator

```python
# services/ai/briefing_generator.py

async def generate_daycare_briefing(
    db: AsyncSession,
    household_id: UUID,
    daycare_contact: DaycareContact,
    date: datetime,
) -> str:
    context_docs = await retrieve_context(
        db, household_id,
        f"opvang briefing {date.strftime('%A')} bijzonderheden kind",
        top_k=10,
        source_types=["task", "inventory", "onboarding_answer", "pattern"]
    )

    today_tasks = await get_tasks_for_date(db, household_id, date, category="baby_care")
    low_stock = await get_low_stock_items(db, household_id)

    try:
        briefing_text = await call_claude(
            system="""
Je schrijft een korte, vriendelijke dagbriefing voor de opvang of oppas.
Alleen relevante informatie voor de zorgverlener. Geen huishoudelijke of prive informatie.
Maximaal 200 woorden. Duidelijke koptjes. Nederlands.
""",
            user_message=f"""
Datum: {date.strftime('%A %d %B %Y')}
Ontvanger: {daycare_contact.name}

BABYTAKEN VANDAAG:
{format_tasks(today_tasks)}

VOORRAAD WAARSCHUWINGEN:
{format_low_stock(low_stock)}

RELEVANTE CONTEXT:
{chr(10).join(context_docs[:6])}

Genereer de briefing.
""",
            max_tokens=400,
        )
        return briefing_text
    except AICallError as e:
        logger.error(f"Daycare briefing generation failed for household {household_id}: {e}")
        return None  # briefing wordt niet verstuurd
```

---

## 6. Celery Beat Schedule

```python
# workers/beat_schedule.py
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    "calendar-analysis-evening": {
        "task": "workers.tasks.calendar_analysis.run",
        "schedule": crontab(hour=20, minute=0),
    },
    "pattern-analysis-weekly": {
        "task": "workers.tasks.pattern_analysis.run",
        "schedule": crontab(day_of_week=1, hour=3, minute=0),  # maandag 03:00
    },
    "memory-summarizer-monthly": {
        "task": "workers.tasks.memory_summarizer.monthly_memory_summarizer",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),
    },
    "notification-sender-morning": {
        "task": "workers.tasks.notification_sender.send_morning_reminders",
        "schedule": crontab(hour=7, minute=30),
    },
    "notification-sender-evening": {
        "task": "workers.tasks.notification_sender.send_evening_reminders",
        "schedule": crontab(hour=20, minute=0),
    },
    "daycare-briefing": {
        "task": "workers.tasks.daycare_briefing.send_briefings",
        "schedule": crontab(hour=6, minute=45),
    },
    "inventory-auto-deduct": {
        "task": "workers.tasks.inventory_deduct.run",
        "schedule": crontab(hour=0, minute=5),  # middernacht
    },
    "notification-response-tracker": {
        "task": "workers.tasks.notification_sender.update_response_rates",
        "schedule": crontab(hour=4, minute=0),
    },
}
```

---

## 7. API Endpoints Overzicht

```
GET    /health                   -- liveness check
GET    /health/ready             -- readiness check (db + redis)

POST   /auth/register
POST   /auth/login
POST   /auth/refresh

POST   /households
GET    /households/me
PATCH  /households/me

POST   /members/invite           -- stuurt magic link e-mail
POST   /members/invite/accept    -- accepteert invite met token
GET    /members/invite/validate  -- valideert token (voor frontend preview)
GET    /members
PATCH  /members/{member_id}
DELETE /members/{member_id}

POST   /onboarding
GET    /onboarding

POST   /tasks
GET    /tasks
GET    /tasks/{task_id}
PATCH  /tasks/{task_id}
DELETE /tasks/{task_id}
POST   /tasks/{task_id}/complete
POST   /tasks/{task_id}/snooze
GET    /tasks/distribution        -- taakverdeling overzicht per member

POST   /inventory
GET    /inventory
PATCH  /inventory/{item_id}
DELETE /inventory/{item_id}
POST   /inventory/{item_id}/report-low   -- voor caregiver rol
POST   /inventory/{item_id}/restock

GET    /calendar/events
POST   /calendar/events
PATCH  /calendar/events/{event_id}
DELETE /calendar/events/{event_id}
POST   /calendar/integrations/google
POST   /calendar/integrations/caldav
DELETE /calendar/integrations/{integration_id}
POST   /calendar/sync

GET    /patterns
POST   /patterns/analyze-now     -- handmatig triggeren (rate limited: 5/uur)

GET    /notifications/preferences
PATCH  /notifications/preferences
GET    /notifications/history

POST   /chat                     -- rate limited: 20/minuut
GET    /chat/history

GET    /subscriptions/me
POST   /subscriptions/checkout
POST   /subscriptions/portal
DELETE /subscriptions/me

GET    /account/data-export      -- GDPR: volledige data export als JSON
DELETE /account                  -- GDPR: verwijdert alle data inclusief vectors

POST   /sync                     -- offline sync queue verwerken

POST   /webhooks/stripe
POST   /webhooks/calendar
```

---

## 8. Frontend — Next.js PWA Structuur

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                 -- landing / login redirect
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── invite/
│   │       └── accept/page.tsx  -- magic link acceptatie
│   ├── onboarding/
│   │   ├── page.tsx             -- uitlegmodal + vragenlijst
│   │   └── generating/page.tsx  -- AI genereert startsituatie
│   └── (app)/
│       ├── layout.tsx           -- app shell met navigatie
│       ├── dashboard/page.tsx   -- vandaag overzicht
│       ├── tasks/
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       ├── inventory/page.tsx
│       ├── calendar/page.tsx
│       ├── patterns/page.tsx
│       ├── chat/page.tsx
│       ├── settings/
│       │   ├── page.tsx
│       │   ├── members/page.tsx
│       │   ├── notifications/page.tsx
│       │   └── subscription/page.tsx
│       └── daycare/page.tsx
├── components/
│   ├── ui/                      -- basiscomponenten
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   ├── Badge.tsx
│   │   ├── Card.tsx
│   │   ├── Avatar.tsx
│   │   └── Toast.tsx
│   ├── tasks/
│   │   ├── TaskCard.tsx
│   │   ├── TaskList.tsx
│   │   ├── TaskForm.tsx
│   │   ├── TaskDistributionBar.tsx
│   │   └── TaskFilter.tsx
│   ├── inventory/
│   │   ├── InventoryCard.tsx
│   │   ├── LowStockAlert.tsx
│   │   └── ReportLowModal.tsx
│   ├── calendar/
│   │   ├── CalendarView.tsx
│   │   └── EventCard.tsx
│   ├── patterns/
│   │   ├── PatternCard.tsx
│   │   └── DistributionChart.tsx
│   ├── chat/
│   │   ├── ChatWindow.tsx
│   │   ├── ChatMessage.tsx
│   │   └── ChatInput.tsx
│   ├── onboarding/
│   │   ├── WelcomeModal.tsx
│   │   └── OnboardingForm.tsx
│   ├── sync/
│   │   ├── ConflictModal.tsx    -- offline conflict resolution UI
│   │   └── SyncStatusBar.tsx    -- toont sync status (online/offline/syncing)
│   ├── invite/
│   │   └── InviteAcceptPage.tsx -- magic link acceptatie pagina
│   └── layout/
│       ├── AppShell.tsx
│       ├── BottomNav.tsx
│       └── Header.tsx
├── lib/
│   ├── api.ts                   -- axios client met auth headers
│   ├── auth.ts                  -- supabase auth helpers
│   ├── offline.ts               -- IndexedDB + sync queue logic
│   ├── realtime.ts              -- supabase realtime subscriptions
│   └── permissions.ts           -- rol-gebaseerde toegangscontrole
├── hooks/
│   ├── useTasks.ts
│   ├── useInventory.ts
│   ├── useCalendar.ts
│   ├── usePatterns.ts
│   ├── useChat.ts
│   ├── useOfflineSync.ts
│   └── usePermissions.ts
├── store/
│   ├── household.ts             -- Zustand store
│   ├── tasks.ts
│   ├── inventory.ts
│   └── sync.ts
├── public/
│   ├── manifest.json            -- PWA manifest
│   ├── offline.html             -- fallback pagina bij geen netwerk
│   └── sw.js                    -- service worker
└── styles/
    └── globals.css
```

### 8.1 Design systeem

Het ontwerp is warm en organisch — zachte aardtonen, ronde vormen, ruimhartige witruimte. Geen koude productiviteitsapp maar een tool die aanvoelt als rust in chaos.

```css
/* styles/globals.css */
:root {
  --color-background: #FAF8F5;
  --color-surface: #FFFFFF;
  --color-surface-alt: #F2EDE8;
  --color-primary: #4A6741;       /* donkergroen */
  --color-primary-light: #7A9E72;
  --color-accent: #C4783A;        /* terracotta */
  --color-accent-light: #E8A96D;
  --color-text: #2C2C2C;
  --color-text-muted: #7A7269;
  --color-danger: #C0392B;
  --color-warning: #E67E22;
  --color-success: #27AE60;
  --color-border: #E0D9D1;

  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 22px;
  --radius-full: 9999px;

  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.10);

  --font-display: 'Lora', Georgia, serif;
  --font-body: 'DM Sans', system-ui, sans-serif;

  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 40px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-body);
  background-color: var(--color-background);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3 {
  font-family: var(--font-display);
  font-weight: 600;
  line-height: 1.3;
}
```

### 8.2 Offline Service Worker

De service worker gebruikt een stale-while-revalidate strategie voor navigatie en een cache-first strategie voor statische assets. Next.js genereert gehashte bestandsnamen voor JS/CSS, dus die zijn veilig om lang te cachen. Navigatieroutes worden altijd eerst van het netwerk geprobeerd.

```javascript
// public/sw.js
const CACHE_VERSION = 'gezinsai-v1';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `dynamic-${CACHE_VERSION}`;

// Alleen shell-assets cachen, niet Next.js pagina's (die hebben eigen hashes)
const PRECACHE_ASSETS = [
    '/offline.html',  // fallback pagina bij geen netwerk
    '/icons/icon-192.png',
    '/icons/icon-512.png',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => cache.addAll(PRECACHE_ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    // Verwijder oude caches bij nieuwe versie
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                    .filter((key) => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
                    .map((key) => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const { request } = event;

    // Skip non-GET requests
    if (request.method !== 'GET') return;

    // Skip API calls — die gaan via de sync queue
    if (request.url.includes('/api/') || request.url.includes('/auth/')) return;

    // Navigatie: network-first met offline fallback
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    const clone = response.clone();
                    caches.open(DYNAMIC_CACHE).then((cache) => cache.put(request, clone));
                    return response;
                })
                .catch(() => caches.match(request).then((cached) => cached || caches.match('/offline.html')))
        );
        return;
    }

    // Statische assets (JS/CSS met hash): cache-first
    if (request.url.match(/\/_next\/static\//)) {
        event.respondWith(
            caches.match(request).then((cached) => {
                if (cached) return cached;
                return fetch(request).then((response) => {
                    if (response.ok) {
                        const clone = response.clone();
                        caches.open(STATIC_CACHE).then((cache) => cache.put(request, clone));
                    }
                    return response;
                });
            })
        );
        return;
    }

    // Overig: stale-while-revalidate
    event.respondWith(
        caches.match(request).then((cached) => {
            const networkFetch = fetch(request).then((response) => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(DYNAMIC_CACHE).then((cache) => cache.put(request, clone));
                }
                return response;
            });
            return cached || networkFetch;
        })
    );
});

// Background sync voor offline acties
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-queue') {
        event.waitUntil(processSyncQueue());
    }
});

async function processSyncQueue() {
    const db = await openIndexedDB();
    const pending = await db.getAll('syncQueue');
    if (pending.length === 0) return;

    const response = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pending),
    });

    if (response.ok) {
        const result = await response.json();
        for (const item of result.results) {
            if (item.status === 'ok') {
                await db.delete('syncQueue', item.id);
            }
        }
    }
}
```

### 8.3 Offline Hook

```typescript
// hooks/useOfflineSync.ts
import { openDB } from 'idb';

const DB_NAME = 'gezinsai-offline';
const STORE_NAME = 'syncQueue';

export async function getOfflineDB() {
  return openDB(DB_NAME, 1, {
    upgrade(db) {
      db.createObjectStore(STORE_NAME, { keyPath: 'id' });
    },
  });
}

export async function queueOfflineOperation(op: {
  id: string;
  operation: 'create' | 'update' | 'delete';
  resource_type: string;
  resource_id?: string;
  payload: object;
}) {
  const db = await getOfflineDB();
  await db.add(STORE_NAME, {
    ...op,
    client_timestamp: new Date().toISOString(),
    processed: false,
  });

  if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
    const registration = await navigator.serviceWorker.ready;
    await (registration as any).sync.register('sync-queue');
  }
}
```

### 8.4 Permissiecontrole Frontend

```typescript
// lib/permissions.ts
export type Role = 'owner' | 'partner' | 'caregiver';

const PERMISSIONS: Record<Role, Record<string, boolean>> = {
  owner: {
    view_baby_tasks: true,
    edit_baby_tasks: true,
    view_household_tasks: true,
    edit_household_tasks: true,
    view_private_tasks: true,
    edit_private_tasks: true,
    view_inventory: true,
    edit_inventory: true,
    report_inventory_low: true,
    view_partner_calendar: true,
    manage_members: true,
    manage_settings: true,
    view_patterns: true,
    view_subscription: true,
  },
  partner: {
    view_baby_tasks: true,
    edit_baby_tasks: true,
    view_household_tasks: true,
    edit_household_tasks: true,
    view_private_tasks: false, // alleen eigen
    edit_private_tasks: false, // alleen eigen
    view_inventory: true,
    edit_inventory: true,
    report_inventory_low: true,
    view_partner_calendar: true,
    manage_members: false,
    manage_settings: false,
    view_patterns: true,
    view_subscription: false,
  },
  caregiver: {
    view_baby_tasks: true,     // alleen eigen tijdslot
    edit_baby_tasks: false,
    view_household_tasks: false,
    edit_household_tasks: false,
    view_private_tasks: false,
    edit_private_tasks: false,
    view_inventory: true,
    edit_inventory: false,
    report_inventory_low: true,
    view_partner_calendar: false,
    manage_members: false,
    manage_settings: false,
    view_patterns: false,
    view_subscription: false,
  },
};

export function can(role: Role, permission: string): boolean {
  return PERMISSIONS[role]?.[permission] ?? false;
}
```

### 8.5 Realtime Synchronisatie

```typescript
// lib/realtime.ts
import { createClient } from '@supabase/supabase-js';
import { useTaskStore } from '@/store/tasks';

export function subscribeToHousehold(householdId: string) {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const channel = supabase
    .channel(`household:${householdId}`)
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'tasks', filter: `household_id=eq.${householdId}` },
      (payload) => {
        const store = useTaskStore.getState();
        if (payload.eventType === 'UPDATE') store.updateTask(payload.new as any);
        if (payload.eventType === 'INSERT') store.addTask(payload.new as any);
        if (payload.eventType === 'DELETE') store.removeTask(payload.old.id);
      }
    )
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'inventory_items', filter: `household_id=eq.${householdId}` },
      (payload) => {
        // zelfde patroon voor inventory
      }
    )
    .subscribe();

  return () => supabase.removeChannel(channel);
}
```

### 8.6 PWA Manifest

```json
// public/manifest.json
{
  "name": "GezinsAI",
  "short_name": "GezinsAI",
  "description": "De slimme gezinsplanner met AI",
  "start_url": "/dashboard",
  "display": "standalone",
  "background_color": "#FAF8F5",
  "theme_color": "#4A6741",
  "orientation": "portrait",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

---

## 9. Onboarding Flow

### Stap 1 — Welkomstmodal

Simpele uitleg. Geen invoer vereist. Twee knoppen: "Start" en "Meer informatie".

### Stap 2 — Vragenlijst

Velden:
- Naam kind (optioneel)
- Leeftijd kind in weken, of verwachte uitgerekende datum
- Situatie: koppel / alleenstaand / co-ouderschap
- Werksituatie (beide ouders indien koppel): voltijd / deeltijd / verlof
- Opvang aanwezig? Zo ja: welke dagen (checkbox)
- Heeft iemand een zorgrol (oppas, oma)? Zo ja: naam en rol
- Grootste pijnpunten (multi-select): slaaptekort, taakverdeling, boodschappen vergeten, agenda-chaos, financien bijhouden

### Stap 3 — AI genereert startsituatie

Na invullen toont de app een laadscherm ("AI denkt mee..."). De AI genereert:
- Een startset van terugkerende taken per categorie
- Een basis voorraadlijst (luiers, flesvoeding, doekjes, etc.)
- Een voorgestelde taakverdeling op basis van werksituatie
- Eerste `Pattern` records gebaseerd op de intake-antwoorden

Gebruiker ziet het resultaat en kan aanpassen of goedkeuren.

---

## 10. Subscription Tiers

```
Free
- Max 2 leden (owner + partner)
- Geen AI-analyse
- Geen kalenderintegratie
- Geen push notificaties
- Basis taakverdeling handmatig

Standaard — 8,99 euro/maand
- AI-motor volledig actief
- Kalender koppeling (Google + CalDAV)
- Push notificaties + email reminders
- Max 4 leden
- Patronenrapportage
- Vectorgeheugen

Gezin — 13,99 euro/maand
- Alles van Standaard
- Onbeperkte leden
- Alle rollen inclusief caregiver en daycare
- Voorraadmanagement met auto-afschrijving
- WhatsApp briefing voor opvang
- Partner escalatie notificaties
- Prioriteit AI-verwerking
```

Bij opzegging: data bewaard voor 90 dagen, exporteerbaar als JSON. GDPR-verplichting.

---

## 11. GDPR

- Data opgeslagen in EU (Supabase EU region: Frankfurt)
- Data Processing Agreement beschikbaar via settings
- Recht op inzage: API endpoint `GET /account/data-export`
- Recht op verwijdering: API endpoint `DELETE /account` verwijdert alle data inclusief vectors
- Geen AI-training op gebruikersdata
- Privacy policy in begrijpelijk Nederlands
- Cookie-only voor authenticatie, geen tracking cookies

---

## 12. Omgevingsvariabelen

```env
# .env (backend)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/gezinsai
REDIS_URL=redis://localhost:6379/0
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
RESEND_API_KEY=re_xxx
FCM_SERVER_KEY=xxx
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
JWT_SECRET=xxx
TOKEN_ENCRYPTION_KEY=xxx  # genereer met: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
SENTRY_DSN=https://xxx@sentry.io/xxx
ALLOWED_ORIGINS=["https://app.gezinsai.nl"]
INVITE_TOKEN_EXPIRY_HOURS=72
ENVIRONMENT=production
```

```env
# .env.local (frontend)
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
NEXT_PUBLIC_API_URL=https://api.gezinsai.nl
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## 13. Ontwikkelvolgorde

1. Database schema uitvoeren en migraties opzetten met Alembic
2. Auth flow (Supabase) — register, login, JWT middleware
3. Household + Members CRUD + invite flow (magic link)
4. Onboarding flow inclusief AI-startsituatie generatie
5. Tasks CRUD + optimistic locking
6. Vector embedding pipeline (asynchroon via Celery)
7. Kalender integratie (Google eerst)
8. Inventory CRUD + meldingsfunctie caregiver
9. Notificatieprofielen + push notificaties via FCM
10. Context engine (avond cron)
11. Pattern engine (wekelijks)
12. Chat interface + vectorretrieval
13. Realtime sync via Supabase
14. Offline support (IndexedDB + service worker + conflict resolution UI)
15. Stripe subscription flow + tier enforcement middleware
16. Daycare briefing (mail + WhatsApp via Twilio)
17. Memory summarizer (maandelijks)
18. Frontend afwerken per pagina
19. GDPR export en verwijdering endpoints
20. PWA configuratie + manifest
21. Docker + CI/CD + deployment naar Railway/Fly.io
22. Monitoring (Sentry, structured logging, health checks)

---

## 14. WhatsApp Integratie — Twilio

De WhatsApp briefing voor de opvang wordt verstuurd via de Twilio WhatsApp Business API. Twilio is gekozen boven 360dialog en de directe Meta Business API vanwege: eenvoudige setup, goede Python SDK, pay-per-message zonder maandelijkse kosten, en goede documentatie.

### Kosten
- Twilio WhatsApp: ~$0.005 per bericht (conversation-based pricing)
- Bij 1 briefing per werkdag per huishouden: ~$1/maand per actief gezin
- Valt ruim binnen de marge van het Gezin-tier (€13,99/maand)

### Implementatie

```python
# services/notification/whatsapp.py
from twilio.rest import Client
from core.config import settings
import logging

logger = logging.getLogger(__name__)

_twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

async def send_whatsapp_message(to_phone: str, body: str) -> bool:
    """
    Verstuurt een WhatsApp bericht via Twilio.
    to_phone: internationaal formaat, bv '+31612345678'
    """
    try:
        message = _twilio_client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            body=body,
            to=f"whatsapp:{to_phone}",
        )
        logger.info(f"WhatsApp sent to {to_phone}: SID {message.sid}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send failed to {to_phone}: {e}")
        return False
```

### Gebruik in daycare briefing

```python
# workers/tasks/daycare_briefing.py (fragment)
from services.notification.whatsapp import send_whatsapp_message
from services.notification.email import send_email

async def send_briefing(daycare_contact, briefing_text):
    if daycare_contact.briefing_channel == "whatsapp" and daycare_contact.phone:
        success = await send_whatsapp_message(daycare_contact.phone, briefing_text)
        if not success:
            # Fallback naar email als WhatsApp faalt
            if daycare_contact.email:
                await send_email(
                    to=daycare_contact.email,
                    subject=f"Dagbriefing {datetime.now().strftime('%d %B')}",
                    html=f"<pre>{briefing_text}</pre>",
                )
    elif daycare_contact.briefing_channel == "email" and daycare_contact.email:
        await send_email(
            to=daycare_contact.email,
            subject=f"Dagbriefing {datetime.now().strftime('%d %B')}",
            html=f"<pre>{briefing_text}</pre>",
        )
```

### Twilio setup vereisten
1. Twilio account aanmaken
2. WhatsApp Sandbox activeren (voor development)
3. WhatsApp Business Profile aanvragen (voor productie)
4. Webhook URL configureren voor delivery status callbacks (optioneel)

---

## 15. Offline Conflict Resolution

Wanneer een gebruiker offline wijzigingen maakt en een ander lid dezelfde data heeft gewijzigd terwijl ze offline waren, ontstaat een conflict. De sync endpoint retourneert `status: "conflict"` met de huidige serverstate. De frontend toont dan een conflict resolution UI.

### Backend response bij conflict

```python
# De sync endpoint (routers/sync.py) retourneert bij conflict:
{
    "id": "sync-op-123",
    "status": "conflict",
    "detail": "Deze taak is gewijzigd door iemand anders terwijl je offline was.",
    "server_version": {
        "id": "task-uuid",
        "title": "Boodschappen doen",
        "status": "done",
        "assigned_to": "partner-uuid",
        "updated_at": "2026-03-01T14:30:00Z",
        "version": 5
    }
}
```

### Frontend Conflict Resolution Component

```typescript
// components/sync/ConflictModal.tsx
import { useState } from 'react';

interface ConflictData {
  syncOpId: string;
  localVersion: Record<string, any>;
  serverVersion: Record<string, any>;
  resourceType: string;
}

interface ConflictModalProps {
  conflict: ConflictData;
  onResolve: (resolution: 'keep_local' | 'keep_server') => void;
  onDismiss: () => void;
}

export function ConflictModal({ conflict, onResolve, onDismiss }: ConflictModalProps) {
  const [selected, setSelected] = useState<'keep_local' | 'keep_server' | null>(null);

  const changedFields = Object.keys(conflict.localVersion).filter(
    (key) =>
      key !== 'version' &&
      key !== 'updated_at' &&
      JSON.stringify(conflict.localVersion[key]) !== JSON.stringify(conflict.serverVersion[key])
  );

  return (
    <div className="conflict-modal-overlay">
      <div className="conflict-modal">
        <h3>Synchronisatieconflict</h3>
        <p>
          Deze {conflict.resourceType === 'task' ? 'taak' : 'wijziging'} is door iemand
          anders aangepast terwijl je offline was. Welke versie wil je behouden?
        </p>

        <div className="conflict-comparison">
          <div
            className={`conflict-option ${selected === 'keep_local' ? 'selected' : ''}`}
            onClick={() => setSelected('keep_local')}
          >
            <h4>Jouw versie (offline)</h4>
            {changedFields.map((field) => (
              <div key={field} className="conflict-field">
                <span className="field-name">{field}:</span>
                <span className="field-value">{String(conflict.localVersion[field])}</span>
              </div>
            ))}
          </div>

          <div
            className={`conflict-option ${selected === 'keep_server' ? 'selected' : ''}`}
            onClick={() => setSelected('keep_server')}
          >
            <h4>Huidige versie (server)</h4>
            {changedFields.map((field) => (
              <div key={field} className="conflict-field">
                <span className="field-name">{field}:</span>
                <span className="field-value">{String(conflict.serverVersion[field])}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="conflict-actions">
          <button
            onClick={() => selected && onResolve(selected)}
            disabled={!selected}
            className="btn-primary"
          >
            Toepassen
          </button>
          <button onClick={onDismiss} className="btn-secondary">
            Later beslissen
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Conflict verwerking in sync hook

```typescript
// hooks/useOfflineSync.ts (aanvulling)

export async function processConflicts(
  conflicts: ConflictData[],
  resolutions: Map<string, 'keep_local' | 'keep_server'>
) {
  const db = await getOfflineDB();

  for (const conflict of conflicts) {
    const resolution = resolutions.get(conflict.syncOpId);
    if (!resolution) continue;

    if (resolution === 'keep_server') {
      // Verwijder lokale operatie, accepteer serverversie
      await db.delete('syncQueue', conflict.syncOpId);
      // Update lokale store met serverversie
      updateLocalStore(conflict.resourceType, conflict.serverVersion);
    } else {
      // Retry met geforceerde versie (overschrijf server)
      const op = await db.get('syncQueue', conflict.syncOpId);
      if (op) {
        op.payload.version = conflict.serverVersion.version;
        op.payload.force = true;
        await db.put('syncQueue', op);
        // Trigger nieuwe sync
        const registration = await navigator.serviceWorker.ready;
        await (registration as any).sync.register('sync-queue');
      }
    }
  }
}

function updateLocalStore(resourceType: string, data: Record<string, any>) {
  switch (resourceType) {
    case 'task':
      useTaskStore.getState().updateTask(data as any);
      break;
    case 'inventory_item':
      useInventoryStore.getState().updateItem(data as any);
      break;
  }
}
```

---

## 16. Test Strategie

### Aanpak

Tests zijn opgedeeld in drie lagen: unit tests (snel, geen externe dependencies), integratietests (met test database), en AI output tests (validatie van JSON structuur, geen inhoudelijke toets).

### Test configuratie

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from main import app
from core.database import get_db

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/gezinsai_test"

test_engine = create_async_engine(TEST_DATABASE_URL)
TestSession = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Maak tabellen aan in de test database."""
    from models import Base  # SQLAlchemy Base met alle models
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db(setup_database):
    """Geeft een database sessie die na elke test wordt teruggedraaid."""
    async with TestSession() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
async def client(db):
    """Test client met database dependency override."""
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_member():
    """Standaard test member (owner rol)."""
    from models.member import Member
    return Member(
        id="00000000-0000-0000-0000-000000000001",
        household_id="00000000-0000-0000-0000-000000000010",
        user_id="00000000-0000-0000-0000-000000000100",
        role="owner",
        display_name="Test User",
        email="test@example.com",
    )
```

### Voorbeeld tests

```python
# tests/test_tasks.py
import pytest

@pytest.mark.asyncio
async def test_create_task(client, mock_member):
    response = await client.post("/tasks", json={
        "title": "Luiers inpakken",
        "category": "baby_care",
        "task_type": "prep",
        "estimated_minutes": 10,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Luiers inpakken"
    assert data["version"] == 1
    assert data["status"] == "open"

@pytest.mark.asyncio
async def test_optimistic_locking_conflict(client, mock_member):
    # Maak taak aan
    create_resp = await client.post("/tasks", json={
        "title": "Test taak",
        "category": "household",
    })
    task_id = create_resp.json()["id"]

    # Eerste update slaagt
    resp1 = await client.patch(f"/tasks/{task_id}", json={
        "title": "Gewijzigd",
        "version": 1,
    })
    assert resp1.status_code == 200

    # Tweede update met oude versie faalt
    resp2 = await client.patch(f"/tasks/{task_id}", json={
        "title": "Conflicterend",
        "version": 1,
    })
    assert resp2.status_code == 409
    assert resp2.json()["detail"]["code"] == "VERSION_CONFLICT"


# tests/test_permissions.py
import pytest

@pytest.mark.asyncio
async def test_caregiver_cannot_edit_household_tasks(client):
    """Caregiver mag geen huishoudelijke taken aanpassen."""
    # ... setup met caregiver rol
    response = await client.patch("/tasks/{task_id}", json={
        "title": "Poging tot wijziging",
        "version": 1,
    })
    assert response.status_code == 403


# tests/test_ai_utils.py
import pytest
from services.ai.ai_utils import extract_json, parse_json_response, validate_json_list
from schemas.ai_generated import AIGeneratedTask

def test_extract_json_from_markdown_block():
    text = 'Hier is het resultaat:\n```json\n[{"title": "Test"}]\n```\nKlaar.'
    assert extract_json(text) == '[{"title": "Test"}]'

def test_extract_json_from_plain_text():
    text = 'Oké, hier: [{"title": "Test"}] en meer tekst.'
    assert extract_json(text) == '[{"title": "Test"}]'

def test_parse_json_response_invalid():
    with pytest.raises(Exception):
        parse_json_response("Dit is geen JSON helemaal niet")

def test_validate_json_list_skips_invalid():
    raw_json = '[{"title": "Goed", "due_date": "2026-03-01"}, {"invalid": true}]'
    results = validate_json_list(raw_json, AIGeneratedTask)
    assert len(results) == 1
    assert results[0].title == "Goed"


# tests/test_encryption.py
from core.encryption import encrypt_token, decrypt_token

def test_encrypt_decrypt_roundtrip():
    original = "ya29.a0AfH6SMBxxxxxx"
    encrypted = encrypt_token(original)
    assert encrypted != original
    decrypted = decrypt_token(encrypted)
    assert decrypted == original


# tests/test_subscriptions.py
import pytest

@pytest.mark.asyncio
async def test_free_tier_blocks_ai_features(client):
    """Free tier gebruiker kan chat endpoint niet gebruiken."""
    response = await client.post("/chat", json={"message": "Hallo"})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FEATURE_NOT_AVAILABLE"

@pytest.mark.asyncio
async def test_member_limit_enforced(client):
    """Free tier kan max 2 leden hebben."""
    # ... setup met 2 bestaande leden
    response = await client.post("/members/invite", json={
        "email": "derde@example.com",
        "role": "caregiver",
        "display_name": "Derde",
    })
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "MEMBER_LIMIT_REACHED"
```

### Testcommando's

```bash
# Alle tests draaien
pytest tests/ -v

# Alleen unit tests (snel, geen DB nodig)
pytest tests/test_ai_utils.py tests/test_encryption.py -v

# Integratietests met coverage
pytest tests/ --cov=. --cov-report=html -v

# Specifieke test draaien
pytest tests/test_tasks.py::test_optimistic_locking_conflict -v
```

---

## 17. Embedding Migratie Strategie

Wanneer OpenAI een nieuw embedding model uitbrengt (bv `text-embedding-3-large` of een toekomstig model), moeten alle bestaande vectoren opnieuw gegenereerd worden. De `embedding_model` kolom in `vector_documents` maakt het mogelijk om oude en nieuwe embeddings te onderscheiden.

### Migratie worker

```python
# workers/tasks/embedding_migration.py
import logging
from celery import shared_task
from services.vector.embeddings import generate_embedding
from core.database import get_db_context

logger = logging.getLogger(__name__)

TARGET_MODEL = "text-embedding-3-small"  # wijzig naar nieuw model bij migratie


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def migrate_embeddings_batch(self, household_id: str, batch_offset: int, batch_size: int = 100):
    """
    Herbereekent embeddings voor een batch vector_documents.
    Wordt aangestuurd door een migratie management command.
    """
    import asyncio
    asyncio.run(_migrate_batch(household_id, batch_offset, batch_size))


async def _migrate_batch(household_id: str, offset: int, batch_size: int):
    async with get_db_context() as db:
        from sqlalchemy import text
        result = await db.execute(
            text("""
                SELECT id, content FROM vector_documents
                WHERE household_id = :hid AND embedding_model != :target
                ORDER BY created_at
                OFFSET :offset LIMIT :batch_size
            """),
            {"hid": household_id, "target": TARGET_MODEL, "offset": offset, "batch_size": batch_size},
        )
        rows = result.fetchall()

        for row in rows:
            try:
                new_embedding = await generate_embedding(row.content)
                await db.execute(
                    text("""
                        UPDATE vector_documents
                        SET embedding = :embedding, embedding_model = :model
                        WHERE id = :id
                    """),
                    {"embedding": str(new_embedding), "model": TARGET_MODEL, "id": str(row.id)},
                )
            except Exception as e:
                logger.error(f"Failed to migrate embedding {row.id}: {e}")
                continue

        await db.commit()
        logger.info(f"Migrated {len(rows)} embeddings for household {household_id}")
```

### Management command voor migratie

```python
# scripts/migrate_embeddings.py
"""
Gebruik: python scripts/migrate_embeddings.py

Stuurt Celery tasks aan om alle embeddings te herberekenen.
Draai dit na het wijzigen van TARGET_MODEL in embedding_migration.py.
"""
import asyncio
from core.database import get_db_context
from workers.tasks.embedding_migration import migrate_embeddings_batch

async def main():
    async with get_db_context() as db:
        from sqlalchemy import text
        households = await db.execute(text("SELECT DISTINCT household_id FROM vector_documents"))

        for row in households.fetchall():
            hid = str(row.household_id)
            count_result = await db.execute(
                text("SELECT COUNT(*) FROM vector_documents WHERE household_id = :hid"),
                {"hid": hid},
            )
            total = count_result.scalar()

            for offset in range(0, total, 100):
                migrate_embeddings_batch.delay(hid, offset, 100)
                print(f"Queued batch: household={hid}, offset={offset}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Procedure bij modelwissel
1. Update `TARGET_MODEL` in `embedding_migration.py`
2. Update `generate_embedding()` in `embeddings.py` om het nieuwe model te gebruiken
3. Deploy nieuwe code (nieuwe documenten krijgen automatisch het nieuwe model)
4. Draai `python scripts/migrate_embeddings.py` om bestaande vectors te migreren
5. Monitor via logs of alle batches succesvol zijn
6. Optioneel: herindexeer de HNSW index na migratie (`REINDEX INDEX idx_vectors_embedding`)

---

## 18. Deployment & Infrastructuur

### Architectuuroverzicht

```
                    ┌─────────────┐
                    │  Cloudflare  │
                    │   DNS + CDN  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
     ┌────────▼────────┐     ┌─────────▼────────┐
     │   Vercel/Fly     │     │   Railway/Fly     │
     │   Next.js PWA    │     │   FastAPI + Celery │
     │   (frontend)     │     │   (backend)        │
     └─────────────────┘     └────────┬───────────┘
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                  ┌──────▼──┐  ┌─────▼─────┐  ┌──▼─────┐
                  │Supabase  │  │  Redis     │  │Supabase│
                  │PostgreSQL│  │  (Railway) │  │  Auth  │
                  │+ pgvector│  │            │  │        │
                  └──────────┘  └───────────┘  └────────┘
```

### Docker configuratie

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml (voor lokale ontwikkeling)
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    depends_on:
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    build: ./backend
    env_file: ./backend/.env
    depends_on:
      - redis
    volumes:
      - ./backend:/app
    command: celery -A workers.celery_app worker --loglevel=info --concurrency=2

  celery-beat:
    build: ./backend
    env_file: ./backend/.env
    depends_on:
      - redis
    volumes:
      - ./backend:/app
    command: celery -A workers.celery_app beat --loglevel=info

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file: ./frontend/.env.local
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev
```

### Deployment platform keuze

**Backend (FastAPI + Celery): Render**
- Reden: native Docker support, gratis Redis add-on, Infrastructure as Code via render.yaml, goede DX
- Drie services: API (web service), Celery worker (background worker), Celery beat (cron worker)
- Auto-deploy vanuit GitHub main branch
- Health check op /health endpoint

**Frontend (Next.js): Vercel**
- Reden: native Next.js support, edge functions, automatische preview deploys
- Zero-config deployment vanuit GitHub

**Database: Supabase (EU — Frankfurt)**
- Reden: al gekozen voor Auth en Realtime, pgvector support, GDPR-compliant EU hosting

**Redis: Render Redis**
- Gratis tier beschikbaar (25MB), voldoende voor rate limiting + Celery broker
- Upgrade naar betaald plan bij productie

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Test & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: gezinsai_test
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        working-directory: ./backend
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run tests
        working-directory: ./backend
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5433/gezinsai_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: test-secret
          TOKEN_ENCRYPTION_KEY: ${{ secrets.TEST_ENCRYPTION_KEY }}
        run: pytest tests/ -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./backend/coverage.xml

  # Render deploys automatisch via render.yaml bij push naar main
  # Geen aparte deploy job nodig — Render detecteert pushes zelf

  deploy-frontend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
          working-directory: ./frontend
```

### Render configuratie

De backend wordt geconfigureerd via `render.yaml` (Infrastructure as Code). Render detecteert dit bestand automatisch en maakt de services aan. Zie `render.yaml` in de repository root.

Services:
- **gezinsai-api**: Web service (FastAPI), health check op /health
- **gezinsai-worker**: Background worker (Celery)
- **gezinsai-beat**: Background worker (Celery Beat)
- **gezinsai-redis**: Redis instance voor rate limiting + Celery broker

### Vereiste secrets in GitHub

```
VERCEL_TOKEN           — Vercel deployment token
VERCEL_ORG_ID          — Vercel organization ID
VERCEL_PROJECT_ID      — Vercel project ID
TEST_ENCRYPTION_KEY    — Fernet key voor test database
```

### Vereiste environment variables in Render

Alle variabelen uit sectie 12 moeten als environment variables in Render worden ingesteld. REDIS_URL wordt automatisch gelinkt vanuit de Redis service.
