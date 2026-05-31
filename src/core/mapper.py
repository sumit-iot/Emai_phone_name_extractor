import re
from src.utils.constants import EMAIL_REGEX, URL_REGEX, PHONE_REGEX

_email_re = re.compile(EMAIL_REGEX, re.IGNORECASE)
_phone_re = re.compile(PHONE_REGEX)
_url_re = re.compile(URL_REGEX, re.IGNORECASE)
_sent_split = re.compile(r'(?<=[.!?])\s+|\n+')

# A "digit block" that looks like a phone: 7–15 digits, possibly +/dash/dot separated
_PHONE_TOKEN = re.compile(r'[\+\d][\d\s\-\.\(\)]{5,18}[\d]')


def _extract_phones_broad(text: str) -> list[str]:
    """Accept formatted (US/intl) and plain digit strings (Indian 10-digit etc.)."""
    found: list[str] = []
    for token in re.split(r'[,;\s]+', text):
        token = token.strip()
        if not token:
            continue
        clean = re.sub(r'[\s\-\.\(\)\+]', '', token)
        if clean.isdigit() and 7 <= len(clean) <= 15:
            found.append(token)
        elif _phone_re.search(token):
            found.append(token)
    return found


def _is_tsv(text: str) -> bool:
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return False
    tab_lines = sum(1 for l in lines if '\t' in l)
    return (tab_lines / len(lines)) >= 0.5


def _parse_tsv(text: str) -> list[dict]:
    """
    Parse tab-separated data where:
      col0 = name / label
      col1 = comma-separated emails
      col2 = comma-separated phones (optional)
      col3 = URLs (optional)

    Rows where col0 yields no heuristic name are skipped.
    Multiple rows whose col0 resolves to the same name are merged.
    """
    from src.core.extractor import extract_names_heuristic

    bucket: dict[str, dict] = {}

    for line in text.splitlines():
        if not line.strip():
            continue

        cols = [c.strip() for c in line.split('\t')]
        col0 = cols[0] if len(cols) > 0 else ''
        col1 = cols[1] if len(cols) > 1 else ''
        col2 = cols[2] if len(cols) > 2 else ''
        col3 = cols[3] if len(cols) > 3 else ''

        # Skip rows where col0 is itself an email or looks like an ID/code
        if _email_re.fullmatch(col0) or re.fullmatch(r'[A-Z0-9/\-]{3,}', col0):
            continue

        names = extract_names_heuristic(col0)
        if not names:
            continue

        # Use the longest extracted name as the canonical key
        primary = max(names, key=len)

        emails = [e.lower() for e in _email_re.findall(col1)] if col1 else []
        phones = _extract_phones_broad(col2) if col2 else []
        urls = _url_re.findall(col3) if col3 else []

        if primary not in bucket:
            bucket[primary] = {
                "name": primary,
                "emails": set(),
                "phones": set(),
                "urls": set(),
            }
        bucket[primary]["emails"].update(emails)
        bucket[primary]["phones"].update(phones)
        bucket[primary]["urls"].update(urls)

    return [
        {
            "Name": v["name"],
            "Emails": ", ".join(sorted(v["emails"])),
            "Phones": ", ".join(sorted(v["phones"])),
            "URLs": ", ".join(sorted(v["urls"])),
        }
        for v in bucket.values()
        if v["emails"] or v["phones"] or v["urls"]   # skip name-only rows
    ]


def _associate(segments: list[str], get_entities) -> dict[str, dict]:
    bucket: dict[str, dict] = {}
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        emails = [e.lower() for e in _email_re.findall(seg)]
        phones = _phone_re.findall(seg)
        urls = _url_re.findall(seg)
        if not (emails or phones or urls):
            continue
        entities = get_entities(seg)
        if not entities:
            continue
        for name in entities:
            if name not in bucket:
                bucket[name] = {"name": name, "emails": set(), "phones": set(), "urls": set()}
            bucket[name]["emails"].update(emails)
            bucket[name]["phones"].update(phones)
            bucket[name]["urls"].update(urls)
    return bucket


def build_entity_map(text: str) -> list[dict]:
    """
    TSV input  → row-level parser (col0=name, col1=emails, col2=phones).
    Free text  → sentence-level proximity via spaCy (+ heuristic fallback).
    """
    if _is_tsv(text):
        return _parse_tsv(text)

    # ── Free-text path ───────────────────────────────────────────────────
    from src.core.extractor import _load_nlp, extract_names_heuristic

    nlp = _load_nlp()

    if nlp is not None:
        doc = nlp(text)
        bucket: dict[str, dict] = {}
        for sent in doc.sents:
            s = sent.text.strip()
            emails = [e.lower() for e in _email_re.findall(s)]
            phones = _phone_re.findall(s)
            urls = _url_re.findall(s)
            if not (emails or phones or urls):
                continue
            seen: set[str] = set()
            entities: list[str] = []
            for name in extract_names_heuristic(s):
                if name not in seen:
                    seen.add(name)
                    entities.append(name)
            for ent in sent.ents:
                if ent.label_ in {"PERSON", "ORG"}:
                    name = ent.text.strip()
                    if name not in seen:
                        seen.add(name)
                        entities.append(name)
            for name in entities:
                if name not in bucket:
                    bucket[name] = {"name": name, "emails": set(), "phones": set(), "urls": set()}
                bucket[name]["emails"].update(emails)
                bucket[name]["phones"].update(phones)
                bucket[name]["urls"].update(urls)
    else:
        segments = _sent_split.split(text)
        bucket = _associate(segments, extract_names_heuristic)

    return [
        {
            "Name": v["name"],
            "Emails": ", ".join(sorted(v["emails"])),
            "Phones": ", ".join(sorted(v["phones"])),
            "URLs": ", ".join(sorted(v["urls"])),
        }
        for v in bucket.values()
        if v["emails"] or v["phones"] or v["urls"]
    ]
