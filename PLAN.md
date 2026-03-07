# Verbeterplan: GezinsAI → Centrale AI Ouder-Hub

## Probleemanalyse huidige staat

### Wat er mis is

1. **Chat kent de context niet** — De chat endpoint gebruikt GEEN vector retrieval. Hij ziet alleen de laatste 10 chatberichten. Geen taken, geen voorraad, geen patronen uit het geheugen.

2. **AI zit verstopt** — AI is alleen zichtbaar op 3 plekken: dashboard (2 insights), taak-formulier (suggesties), en chat. Op voorraad, agenda, patronen en instellingen is de AI afwezig.

3. **Geen proactieve AI** — De AI reageert alleen als je er om vraagt. Geen "luiers raken op over 3 dagen", geen "morgen opvang, is de tas ingepakt?", geen "je partner heeft 80% van de babytaken gedaan deze week".

4. **Te veel losse pagina's, te veel klikken** — Dashboard, taken, voorraad, agenda, patronen, chat, daycare, settings = 8+ pagina's. Een ouder met een huilende baby wil niet door menu's navigeren.

5. **Data wordt saai weergegeven** — Platte lijsten overal. Geen visuele prioritering, geen slimme groepering, geen "dit is urgent" vs "dit kan later".

6. **Onboarding genereert niks nuttigs** — Na onboarding wordt er een AI-summary gemaakt maar er worden geen taken of voorraadlijsten aangemaakt. De gebruiker begint met een lege app.

---

## Visie: De AI als co-ouder

De app moet aanvoelen alsof er een derde persoon meekijkt die alles onthoudt, patronen ziet, en op het juiste moment het juiste zegt. Niet een chatbot die je moet opzoeken, maar een assistent die *overal* aanwezig is.

---

## Plan in 8 blokken

### Blok 1: Chat wordt de slimste in de kamer

**Backend — `routers/chat.py` + `services/ai/chat_service.py`**

Probleem: Chat gebruikt geen vector context, geen live taken/voorraad data.

Wijzigingen:
- Chat system prompt krijgt ALTIJD mee:
  - Alle open taken (niet alleen vandaag, ALLE open taken)
  - Alle voorraad items met huidige hoeveelheid + drempel
  - Agenda komende 7 dagen
  - Laatste 5 patronen
  - Onboarding situatie (kind leeftijd, werksituatie, pijnpunten)
  - Vector retrieval op basis van het chatbericht (top 12 relevante herinneringen)
- Chat kan ACTIES voorstellen als gestructureerde JSON-blokken in zijn antwoord:
  - `{"action": "create_task", "title": "Luiers kopen", "category": "baby_care", "due_date": "..."}`
  - `{"action": "add_to_shopping", "item": "Luiers", "quantity": 2, "unit": "pakken"}`
  - `{"action": "complete_task", "task_id": "..."}`
  - `{"action": "snooze_task", "task_id": "..."}`
- Frontend toont deze acties als klikbare knoppen onder het chatbericht
- Eén klik = actie uitgevoerd, geen formulieren

**Nieuw schema: `ChatResponseWithActions`**
```python
class ChatAction(BaseModel):
    action: str  # create_task | add_to_shopping | complete_task | snooze_task
    label: str   # Wat de knop zegt: "Luiers toevoegen aan boodschappen"
    data: dict   # De data voor de actie

class ChatResponseWithActions(BaseModel):
    reply: str
    actions: list[ChatAction]  # 0-3 voorgestelde acties
    message_id: UUID
    created_at: datetime
```

---

### Blok 2: AI-strip op elke pagina

**Nieuw component: `<AIBar />`**

Een compacte, contextbewuste AI-balk die bovenaan elke pagina verschijnt met 1-2 relevante inzichten + actieknoppen. Geen lange teksten, maar korte zinnen met directe acties.

**Per pagina:**

| Pagina | AI-bar inhoud | Actieknoppen |
|--------|---------------|--------------|
| Dashboard | "Morgen opvang — luiertas checklist staat klaar" | [Bekijk checklist] |
| Dashboard | "Partner heeft 75% babytaken deze week. Wissel voor balans?" | [Herverdeel] |
| Taken | "3 taken al 4x uitgesteld. Wil je ze toewijzen of verwijderen?" | [Toewijzen] [Verwijderen] |
| Taken | "Op basis van jullie patroon: was doen past beter bij [partner]" | [Toewijzen aan partner] |
| Voorraad | "Luiers gaan 4 dagen mee. Over 2 dagen op. Toevoegen?" | [Toevoegen aan boodschappen] |
| Voorraad | "Flesvoeding verbruik stijgt — gemiddeld 2 per dag nu" | [Drempel aanpassen] |
| Agenda | "Woensdag consultatieburo — vaccinatieboekje + vragen voorbereid?" | [Checklist maken] |
| Agenda | "Vrijdag geen opvang maar beide werken — oppas regelen?" | [Taak aanmaken] |

**Backend — nieuw endpoint: `GET /ai/page-context?page={page}`**

```python
@router.get("/ai/page-context")
async def get_page_context(
    page: str,  # dashboard | tasks | inventory | calendar
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    # Bouwt specifieke context per pagina
    # Retourneert 1-3 inzichten met optionele acties
```

Response:
```json
[
  {
    "message": "Luiers gaan nog ~3 dagen mee. Toevoegen aan boodschappen?",
    "type": "suggestion",
    "actions": [
      {"action": "add_to_shopping", "label": "Toevoegen", "data": {"item": "Luiers", "quantity": 1}}
    ]
  }
]
```

---

### Blok 3: Dashboard wordt command center

**Huidige staat:** Platte lijst met taken + 2 AI insights + voorraadbalk.

**Nieuwe staat:** Eén scherm dat alles toont wat je moet weten.

Structuur van boven naar beneden:

1. **AI-bar** (Blok 2) — 1-2 proactieve suggesties met actieknoppen
2. **Vandaag blok** — Compacte timeline van wat er vandaag moet gebeuren:
   - Taken gegroepeerd: ochtend / middag / avond (op basis van due_date of AI-schatting)
   - Agenda items inline met taken (niet op aparte pagina)
   - Swipe-to-complete op taken (geen checkbox, geen detail pagina nodig)
3. **Aandacht nodig** — Rode sectie, alleen als er iets urgens is:
   - Verlopen taken (>2 dagen over deadline)
   - Voorraad op (onder drempel)
   - Onbeantwoorde uitnodigingen
4. **Quick actions** — 3-4 grote knoppen:
   - "Snel taak toevoegen" (SmartTaskInput, maar inline, niet op aparte pagina)
   - "Chat met AI" (opent chat als overlay/drawer, niet navigatie)
   - "Boodschappenlijst" (gefilterde voorraad items die onder drempel zijn)
5. **Weekoverzicht mini** — Compacte 7-daagse balk die laat zien welke dagen druk zijn

---

### Blok 4: Slimme knoppen, minder formulieren

**Principe:** Elke actie maximaal 1-2 tikken. Geen modals met 8 velden.

Wijzigingen:

1. **SmartTaskInput wordt de standaard overal** — Geen apart formulier meer. Type "luiers kopen morgen" → AI parsed → preview → 1 tik bevestigen. Het formulier met dropdowns wordt een "geavanceerd" optie.

2. **Swipe acties op taken:**
   - Swipe rechts = klaar
   - Swipe links = snooze
   - Geen detail pagina nodig voor simpele acties

3. **Quick-add op voorraad:**
   - "-" en "+" knoppen direct op elk voorraad item
   - Geen modal nodig om hoeveelheid aan te passen
   - Bij 0: automatisch "wil je dit op de boodschappenlijst?" prompt

4. **AI-actieknoppen:**
   - Elke AI suggestie heeft een directe actieknop
   - 1 tik = actie uitgevoerd + toast bevestiging
   - Geen bevestigingsmodal tenzij destructief

5. **Boodschappenlijst als apart concept:**
   - Nieuw: `shopping_list` veld op inventory items (boolean)
   - Items onder drempel worden automatisch voorgesteld
   - Afvinkbaar als "gekocht" → restock + van lijst af
   - Bereikbaar via quick action op dashboard

---

### Blok 5: Data weergave herontwerp

**Taken:**
- Niet meer één platte lijst. Groepering:
  - "Nu doen" (vandaag, verlopen)
  - "Binnenkort" (deze week)
  - "Later" (volgende week+)
  - "Terugkerend" (automatische taken)
- Kleurcodering op urgentie, niet op categorie
- Toewijzing als avatar-icoontje, niet als tekst
- AI-gegenereerde taken krijgen subtiel ander design (licht pulserende rand of AI-icoontje)

**Voorraad:**
- Visuele voortgangsbalk per item (current/threshold ratio)
- Rood = op, oranje = bijna op, groen = voldoende
- "Dagen resterend" berekening prominent (niet verstopt)
- Groepering per categorie met emoji: 🍼 Baby, 🧹 Schoonmaak, 🍎 Eten

**Agenda:**
- Horizontale dagscroller bovenaan (Ma Di Wo Do Vr Za Zo)
- Geselecteerde dag toont events + gekoppelde taken
- AI-waarschuwingen inline bij events ("Opvang — tas ingepakt?")

**Patronen:**
- Niet als losse pagina, maar als inzichten in de AI-bar en dashboard
- Confidence score als visuele indicator (niet als getal)
- "Wat betekent dit?" uitleg per patroon als je erop tikt

---

### Blok 6: Onboarding genereert echte startdata

**Huidige staat:** Onboarding slaat antwoorden op en maakt een AI-summary. Gebruiker begint met lege app.

**Nieuwe staat:** Na onboarding heeft de gebruiker direct:

1. **Starttaken** (AI-gegenereerd op basis van intake):
   - Kind 8 weken? → Voedingsschema taken, slaapregistratie, consultatieburo afspraak
   - Co-ouderschap? → Wisselmoment taken, communicatie check-in
   - Pijnpunt boodschappen? → Wekelijkse boodschappenlijst taak
   - Opvang op ma/wo/vr? → Luiertas inpakken taken op zo/di/do avond

2. **Startvoorraad** (AI-gegenereerd):
   - Baby basics: luiers, doekjes, flesvoeding/moedermelk zakjes, sudocrem
   - Op basis van leeftijd: vast voedsel items als kind > 16 weken

3. **Eerste patronen seeds:**
   - Op basis van werksituatie: "Partner werkt voltijd, owner parttime → owner doet 60% babytaken overdag"

**Backend wijziging:**
- `POST /onboarding` triggert Celery task `generate_onboarding_starter`
- Celery task genereert taken + voorraad + patronen via Claude
- Alles wordt opgeslagen en geëmbed in vectoren
- Frontend toont "Je persoonlijke planner wordt ingericht..." (langer dan 5 sec, realtime updates via SSE)

---

### Blok 7: Vector geheugen wordt echt gebruikt

**Huidige staat:** Embeddings worden aangemaakt maar nauwelijks gebruikt. Chat gebruikt ze niet. Context engine gebruikt ze beperkt.

**Nieuwe staat:**

1. **Chat gebruikt ALTIJD vector retrieval:**
   - Query = laatste chatbericht
   - Top 12 relevante vectoren worden meegestuurd als context
   - "Herinner je dat we vorige week zeiden dat..." → AI vindt het terug

2. **AI-bar gebruikt vector retrieval:**
   - Per pagina wordt een relevante query gedaan
   - Voorraadpagina: "voorraad verbruik patronen" → haalt historische consumptiedata op
   - Takenpagina: "taken verdeling eerlijkheid" → haalt vergelijkingsdata op

3. **Alle acties worden geëmbed:**
   - Taak aangemaakt/afgerond/gesnoozed
   - Voorraad bijgevuld/leeg gemeld
   - Chat berichten (user + assistant)
   - Patronen gedetecteerd
   - Onboarding antwoorden
   - Dit gebeurt al grotendeels, maar chat berichten worden nu pas echt embedded

4. **Maandelijkse samenvatting wordt beter:**
   - Niet alleen per source_type, maar ook een overall gezinssamenvatting
   - "In maart heeft het gezin 45 taken afgerond, waarvan 60% door owner. Luierverbruik stabiel op 6/dag."

---

### Blok 8: Navigatie vereenvoudigen

**Huidige bottom nav:** Home | Taken | Voorraad | Chat | Menu (5 items)

**Nieuwe bottom nav:** Home | Planner | Chat | Profiel (4 items)

Wijzigingen:
- **Home** = het nieuwe command center dashboard (Blok 3)
- **Planner** = gecombineerde view van taken + agenda + voorraad in tabs of swipeable sections
- **Chat** = chat met AI (met acties, Blok 1). Chat opent als full-screen overlay zodat je snel terug kunt
- **Profiel** = instellingen, leden, abonnement, patronen

Waarom:
- Voorraad als aparte tab is overkill — het is een sub-view van "wat moet er geregeld worden"
- Patronen als aparte pagina bezoekt niemand — integreer in AI-bar en dashboard
- Minder navigatie = sneller = beter met baby op arm

---

## Implementatievolgorde

| # | Blok | Impact | Complexiteit |
|---|------|--------|--------------|
| 1 | Blok 1: Chat context + acties | Hoogste — dit is de kern | Gemiddeld |
| 2 | Blok 6: Onboarding starter data | Hoog — eerste indruk | Gemiddeld |
| 3 | Blok 7: Vector geheugen activeren | Hoog — AI wordt slimmer | Laag |
| 4 | Blok 2: AI-bar component | Hoog — AI overal zichtbaar | Gemiddeld |
| 5 | Blok 3: Dashboard redesign | Hoog — dagelijks gebruik | Hoog |
| 6 | Blok 5: Data weergave | Gemiddeld — UX verbetering | Gemiddeld |
| 7 | Blok 4: Quick actions | Gemiddeld — minder frictie | Gemiddeld |
| 8 | Blok 8: Navigatie | Gemiddeld — structuurwijziging | Laag |

---

## Samenvatting: wat verandert er fundamenteel

| Aspect | Nu | Straks |
|--------|-----|--------|
| AI op chat pagina | Ja (maar zonder context) | Ja, met volledige context + actieknoppen |
| AI op andere pagina's | Alleen dashboard (2 insights) | Elke pagina heeft AI-bar met suggesties |
| Proactieve AI | Nee | Ja — "luiers bijna op", "morgen opvang" |
| Acties vanuit AI | Nee | Ja — 1-klik knoppen voor taken/voorraad |
| Na onboarding | Lege app | Gevuld met taken, voorraad, patronen |
| Navigatie | 5 tabs, 8+ pagina's | 4 tabs, alles bereikbaar in 1-2 tikken |
| Data weergave | Platte lijsten | Gegroepeerd, visueel, urgentie-gestuurd |
| Vector geheugen | Aangemaakt, niet gebruikt | Actief in chat + AI-bar + context engine |
| Taak toevoegen | Formulier met 8 velden | Type zin → AI parsed → 1 tik bevestigen |
| Voorraad bijwerken | Modal → velden invullen | +/- knoppen direct op item |
