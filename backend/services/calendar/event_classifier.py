"""
Calendar event classifier.

Classifies calendar events into semantic types so the context engine
can generate the right tasks for each type.

Classification is keyword-based (fast, no AI call needed) and cached
in calendar_events.event_type to avoid re-classifying every night.
"""
from __future__ import annotations

from datetime import datetime

# ── Keyword lists (all lowercase) ────────────────────────────────────────────

BIRTHDAY_KEYWORDS = [
    "verjaardag", "jarig", "birthday", "bday", "wordt", "jaar oud",
]

DAYCARE_KEYWORDS = [
    "opvang", "dagopvang", "kinderopvang", "crèche", "creche", "bso",
    "gastouder", "naschoolse opvang",
]

MEDICAL_KEYWORDS = [
    "consultatieburo", "consultatiebureau", "huisarts", "prikken", "vaccinatie",
    "dokter", "tandarts", "orthodontist", "specialist", "fysiotherapeut",
    "ziekenhuis", "controle afspraak", "bloedprik",
]

VACATION_KEYWORDS = [
    "vakantie", "reis", "vliegen", "vliegtuig", "hotel", "camping",
    "bungalow", "airbnb", "citytrip", "citybreak", "cruise",
]

# Known Dutch/Belgian attractions and leisure venues
KNOWN_ATTRACTIONS = [
    "efteling", "artis", "beekse bergen", "walibi", "duinrell", "droomvlucht",
    "pretpark", "dolfinarium", "madurodam", "zoo", "dierentuin", "dierenpark",
    "speeltuinen", "avonturenpark", "toverland", "julianatoren", "panorama mesdag",
    "rijksmuseum", "van gogh museum", "anne frank", "nemo", "naturalis",
    "wildlands", "attractiepark", "avonturenboerderij", "kinderboerderij",
    "museon", "tropenmuseum", "stedelijk", "groninger museum",
    "slagharen", "plopsaland", "bobbejaanland", "bellewaerde",
    "disneyland", "centerparcs", "center parcs", "roompot",
    "strand", "zee", "bos", "meer", "dag uit", "dagje uit",
    "museum", "bioscoop", "theater", "concert",
]

DAYTRIP_KEYWORDS = [
    "dagje", "uitje", "dag uit", "dagtocht", "dagtripje",
    "bezoek aan", "uitstapje",
]


# ── Classifier ────────────────────────────────────────────────────────────────

def classify_event(
    title: str,
    description: str | None,
    start_time: datetime,
    end_time: datetime,
    location: str | None = None,
) -> str:
    """
    Return the event type as a string:
      birthday | daycare | medical | vacation | trip | other

    Checks title and description (lowercased). Duration is used to
    distinguish single-day trips from multi-day vacations.
    """
    text = (title + " " + (description or "") + " " + (location or "")).lower()
    duration_days = (end_time.date() - start_time.date()).days

    # Birthday — highest priority
    if any(kw in text for kw in BIRTHDAY_KEYWORDS):
        return "birthday"

    # Daycare
    if any(kw in text for kw in DAYCARE_KEYWORDS):
        return "daycare"

    # Medical
    if any(kw in text for kw in MEDICAL_KEYWORDS):
        return "medical"

    # Vacation — multi-day (≥ 2 nights) with travel keywords
    if duration_days >= 2:
        if any(kw in text for kw in VACATION_KEYWORDS + KNOWN_ATTRACTIONS):
            return "vacation"
        # Any multi-day event with a location is likely a trip/vacation
        if location and duration_days >= 2:
            return "vacation"

    # Day trip — single day, known attraction OR daytrip keyword
    if any(kw in text for kw in DAYTRIP_KEYWORDS):
        return "trip"
    if any(attr in text for attr in KNOWN_ATTRACTIONS):
        return "trip"

    return "other"


def extract_birthday_info(title: str) -> tuple[str | None, int | None]:
    """
    Try to extract person name and age from a birthday event title.

    Examples:
      "Verjaardag Sara 2 jaar" → ("Sara", 2)
      "Sara jarig"             → ("Sara", None)
      "Verjaardag"             → (None, None)
    """
    import re

    lower = title.lower()

    # Remove birthday keyword to get the rest
    for kw in ["verjaardag", "birthday", "bday"]:
        lower = lower.replace(kw, "").strip()

    # Try to extract age: "X jaar" or "X years"
    age_match = re.search(r"(\d+)\s*(?:jaar|years?|j\.)", lower)
    age = int(age_match.group(1)) if age_match else None

    # Remove age from string to find name
    cleaned = re.sub(r"\d+\s*(?:jaar|years?|j\.)", "", lower).strip()
    # Remove "jarig" and "wordt"
    cleaned = re.sub(r"\bjarig\b|\bwordt\b", "", cleaned).strip()

    # What's left (if not empty) is likely the name — capitalize it
    name = cleaned.strip().title() if cleaned.strip() else None

    return name, age


def extract_destination(title: str, description: str | None, location: str | None) -> str:
    """
    Best-effort extraction of the destination for a trip/vacation event.
    Falls back to the raw title.
    """
    # Location field is most reliable
    if location and len(location) > 2:
        return location

    # Check for known attractions in title
    title_lower = title.lower()
    for attr in KNOWN_ATTRACTIONS:
        if attr in title_lower:
            return attr.title()

    # Use the event title itself, stripping common prefixes
    import re
    cleaned = re.sub(
        r"^(dagje|uitje|vakantie|reis naar|trip naar|naar|bezoek aan)\s*",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned or title
