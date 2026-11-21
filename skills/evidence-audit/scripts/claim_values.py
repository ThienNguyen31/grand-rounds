"""Shared helper: structured claim values and endpoint vocabulary.

This is the only copy. check_claims.py, verify_quotes.py and html-deck-building's
build_deck.py load it from here.

A claim value may be a plain string (old style) or an object that binds the number to what
it measures:

  {"key": "hr", "v": "0.62", "measure": "HR", "endpoint": "RFS",
   "population": "ITT", "timepoint": "24 months", "arm": "vaccine vs placebo"}

Claim-level "endpoint", "population", "timepoint" fill in fields a value leaves out. "key"
names the value for slide placeholders: {{c07.hr}}. A value without a key is reachable by
its position: {{c07.0}}.

Endpoint names are canonical (RFS, OS, clinical-remission, ...). ENDPOINTS maps each to the
words a source or a slide uses for it, in English and Vietnamese. A talk can add or extend
entries in <talk>/evidence/endpoints.json: {"RFS": ["thời gian sống không tái phát"]}.
A claim can add its own with "endpoint_terms".
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ENDPOINTS: dict[str, list[str]] = {
    "RFS": ["recurrence-free survival", "relapse-free survival", "recurrence or death", "RFS",
            "sống còn không tái phát", "sống thêm không tái phát"],
    "DFS": ["disease-free survival", "DFS", "sống còn không bệnh", "sống thêm không bệnh"],
    "EFS": ["event-free survival", "EFS", "sống còn không biến cố", "sống thêm không biến cố"],
    "DMFS": ["distant metastasis-free survival", "distant-metastasis-free survival", "DMFS",
             "sống còn không di căn xa", "sống thêm không di căn xa"],
    "PFS": ["progression-free survival", "progression or death", "PFS",
            "sống còn không bệnh tiến triển", "sống thêm không tiến triển"],
    "OS": ["overall survival", "death from any cause", "hazard ratio for death", "OS",
           "sống còn toàn bộ", "sống thêm toàn bộ", "tử vong do mọi nguyên nhân"],
    "ORR": ["objective response", "overall response rate", "ORR", "tỉ lệ đáp ứng khách quan"],
    "pCR": ["pathological complete response", "pathologic complete response", "pCR",
            "đáp ứng hoàn toàn trên mô bệnh học"],
    "clinical-remission": ["clinical remission", "lui bệnh lâm sàng", "thuyên giảm lâm sàng"],
    "clinical-response": ["clinical response", "đáp ứng lâm sàng"],
    "steroid-free-remission": ["corticosteroid-free remission", "steroid-free remission",
                               "corticosteroid-free clinical remission", "steroid-free clinical remission",
                               "lui bệnh không corticosteroid", "lui bệnh không steroid"],
    "endoscopic-remission": ["endoscopic remission", "lui bệnh nội soi", "thuyên giảm nội soi"],
    "endoscopic-response": ["endoscopic response", "đáp ứng nội soi"],
    "endoscopic-improvement": ["endoscopic improvement", "cải thiện nội soi"],
    "mucosal-healing": ["mucosal healing", "lành niêm mạc"],
    "histologic-remission": ["histologic remission", "histological remission", "lui bệnh mô học"],
    "grade3-AE": ["grade 3 or higher", "grade ≥3", "grade ≥ 3", "grade 3 or worse", "độ 3 trở lên", "độ ≥3"],
    "SAE": ["serious adverse event", "biến cố bất lợi nghiêm trọng", "biến cố nghiêm trọng"],
}

FIELDS = ("measure", "endpoint", "population", "timepoint", "arm")


def load_endpoints(talk: Path | None) -> dict[str, list[str]]:
    """ENDPOINTS merged with <talk>/evidence/endpoints.json, if present."""
    merged = {k: list(v) for k, v in ENDPOINTS.items()}
    if talk:
        f = Path(talk) / "evidence" / "endpoints.json"
        if f.exists():
            for k, terms in json.loads(f.read_text(encoding="utf-8")).items():
                merged.setdefault(k, [])
                merged[k] += [t for t in terms if t not in merged[k]]
    return merged


def values(claim: dict) -> list[dict]:
    """Every value of a claim as a dict with 'v', 'key', 'index' and the binding fields."""
    out = []
    for i, raw in enumerate(claim.get("values", [])):
        rec = {"v": str(raw.get("v", "")), "key": raw.get("key")} if isinstance(raw, dict) else {"v": str(raw), "key": None}
        rec["index"] = i
        for f in FIELDS:
            val = raw.get(f) if isinstance(raw, dict) else None
            rec[f] = val if val else claim.get(f)
        out.append(rec)
    return out


def value_strings(claim: dict) -> list[str]:
    return [v["v"] for v in values(claim)]


def lookup(claims: list[dict], ref: str) -> dict | None:
    """'c07.hr' or 'c07.3' → that value record, or None."""
    cid, _, key = ref.partition(".")
    claim = next((c for c in claims if c.get("id") == cid), None)
    if claim is None or not key:
        return None
    vals = values(claim)
    hit = next((v for v in vals if v["key"] == key), None)
    if hit is None and key.isdigit() and int(key) < len(vals):
        hit = vals[int(key)]
    return hit


def _rx(term: str) -> re.Pattern:
    # Abbreviations (all capitals, short) match case-sensitively; words match case-insensitively.
    flags = 0 if (term.isupper() and len(term) <= 6) or term in ("pCR",) else re.I
    return re.compile(r"(?<![\w-])" + re.escape(term).replace(r"\ ", r"\s+") + r"(?![\w-])", flags)


def terms_for(endpoint: str, vocab: dict[str, list[str]], extra: list[str] | None = None) -> list[str]:
    return [endpoint] + vocab.get(endpoint, []) + list(extra or [])


def mentions(text: str, terms: list[str]) -> bool:
    return any(_rx(t).search(text) for t in terms if t)


def endpoints_in(text: str, vocab: dict[str, list[str]]) -> set[str]:
    """Canonical endpoints a piece of text names."""
    return {name for name, terms in vocab.items() if mentions(text, [name] + terms)}
