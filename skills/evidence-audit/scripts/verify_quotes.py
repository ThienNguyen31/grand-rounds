#!/usr/bin/env python3
"""Check every claim's verbatim quote against the source text itself, not against the ledger.

check_claims.py confirms that a claim's numbers appear in its quote. That says nothing
about whether the quote appears in the paper: the same agent wrote both. This script closes
the loop. It needs the text layer written by evidence-research/scripts/ingest_sources.py
(sources/_text/) and a "file" field on each reference that points at its source file.

For each claim:

  EXACT            quote found verbatim on the locator page                       ok
  FUZZY            ≥ 97 % of the wording matches and every number matches          advisory
  OCR              found, but on an OCR'd page: check the numbers by eye          advisory
  LOCATOR          found verbatim, but not on the page the locator names           blocking
  NUMBER_MISMATCH  the wording matches the source but a number differs             blocking
  PARAPHRASE       the passage exists but the quote is not verbatim (< 97 %)       blocking
  NOT_FOUND        no passage in the source resembles the quote                    blocking
  ENDPOINT         a value is bound to an endpoint the quote never names           blocking
  STALE            the source file changed after ingest; re-run ingest_sources.py  blocking
  NOT_CHECKED      no ingested text for this claim's source (reported, not blocking;
                   a claim marked verified-fulltext without checkable text is blocking)

Wording is compared after normalising Unicode (NFKC, ligatures), line-break hyphens,
dashes and minus signs, the Lancet decimal point (0·62), quotes and whitespace. Numbers
are never compared loosely: a quote that matches 99 % of the text but says 0.38 where the
source says 0.58 is a NUMBER_MISMATCH.

Table values: instead of "quote", a claim may give "quote_cells": ["Grade ≥3", "21.4",
"19.5"]. Every cell must appear on the locator page within 600 characters of the others.

Usage: python verify_quotes.py <talk>/evidence/claims.json --refs <talk>/evidence/references.json
           [--talk <talk>] [--json]
Exit 1 when any finding is blocking.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claim_values import load_endpoints, mentions, terms_for, values  # noqa: E402

BLOCKING = {"LOCATOR", "NUMBER_MISMATCH", "PARAPHRASE", "NOT_FOUND", "ENDPOINT", "STALE", "UNCHECKABLE"}
FUZZY_OK = 0.97
SIMILAR = 0.80
CELL_WINDOW = 600
NUM = re.compile(r"\d+(?:[.,]\d+)*")
DASHES = "‐‑‒–—―−﹣－"
INVISIBLE = dict.fromkeys(map(ord, "­​‌‍⁠﻿"), None)


def normalize(text: str, join_hyphens: bool = True) -> str:
    t = unicodedata.normalize("NFKC", text or "").translate(INVISIBLE)
    if join_hyphens:  # "recur-\nrence" → "recurrence"
        t = re.sub(r"(\w)[-" + DASHES + r"]\s*\n\s*(?=[a-z])", r"\1", t)
    t = re.sub("[" + DASHES + "]", "-", t)
    t = re.sub(r"(?<=\d)\s*[·•∙]\s*(?=\d)", ".", t)            # 0·62 → 0.62
    t = re.sub(r"[‘’‚‛′`]", "'", t)
    t = re.sub(r"[“”„‟″]", '"', t)
    t = re.sub(r"\s*-\s*", "-", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip().casefold()


def nums(text: str) -> list[str]:
    return NUM.findall(text)


def locator_pages(locator: str) -> list[int]:
    pages: list[int] = []
    for m in re.finditer(r"\b(?:pp?\.?|pages?|trang)\s*(\d+)(?:\s*[-–]\s*(\d+))?", locator or "", re.I):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        pages += list(range(a, min(b, a + 50) + 1))
    return pages


def best_window(q: str, page: str) -> tuple[float, str]:
    """Best fuzzy alignment of quote q inside page text: (share of q matched, aligned source span)."""
    if not q or not page:
        return 0.0, ""
    L = len(q)
    anchors = set()
    sm = difflib.SequenceMatcher(None, page, q, autojunk=False)
    m = sm.find_longest_match(0, len(page), 0, L)
    if m.size:
        anchors.add(m.a - m.b)
    for tok in sorted(set(nums(q)) | set(w for w in q.split() if len(w) > 6), key=len, reverse=True)[:6]:
        k = q.find(tok)
        for hit in re.finditer(re.escape(tok), page):
            anchors.add(hit.start() - k)
    best = (0.0, "")
    for a in anchors:
        start = max(0, a - L // 5)
        window = page[start:start + L + 2 * (L // 5)]
        s2 = difflib.SequenceMatcher(None, q, window, autojunk=False)
        blocks = [b for b in s2.get_matching_blocks() if b.size]
        if not blocks:
            continue
        score = sum(b.size for b in blocks) / L
        span = window[blocks[0].b: blocks[-1].b + blocks[-1].size]
        if score > best[0]:
            best = (score, span)
    return best


def check_quote(quote: str, locator: str, pages: list[dict]) -> dict:
    variants = [normalize(quote), normalize(quote, join_hyphens=False)]
    want = locator_pages(locator)
    norm_pages = [(p["page"], normalize(p["text"]), normalize(p["text"], False), p.get("ocr", False)) for p in pages]
    order = sorted(norm_pages, key=lambda p: (p[0] not in want, p[0]))
    for n, a, b, ocr in order:
        if any(v and (v in a or v in b) for v in variants):
            if want and n not in want:
                return {"status": "LOCATOR", "page": n, "detail": f"found on page {n}, locator says {locator!r}"}
            return {"status": "OCR" if ocr else "EXACT", "page": n,
                    "detail": "OCR page: check every number by eye" if ocr else ""}
    q = variants[0]
    best = (0.0, "", None, False)
    for n, a, _b, ocr in order:
        score, span = best_window(q, a)
        if score > best[0] + 1e-9 or (abs(score - best[0]) < 1e-9 and want and n in want and best[2] not in want):
            best = (score, span, n, ocr)
    score, span, n, ocr = best
    if score < SIMILAR:
        return {"status": "NOT_FOUND", "page": n, "detail": f"closest passage matches {score:.0%}"}
    qn, sn = nums(q), nums(span)
    missing = [x for x in qn if x not in sn]
    if missing:
        extra = [x for x in sn if x not in qn]
        return {"status": "NUMBER_MISMATCH", "page": n,
                "detail": f"quote has {missing}, source passage has {extra or sn}: “{span[:160]}”"}
    if score < FUZZY_OK:
        return {"status": "PARAPHRASE", "page": n, "detail": f"{score:.0%} match; source says “{span[:160]}”"}
    if want and n not in want:
        return {"status": "LOCATOR", "page": n, "detail": f"near-verbatim on page {n}, locator says {locator!r}"}
    return {"status": "OCR" if ocr else "FUZZY", "page": n,
            "detail": f"{score:.0%} match; source says “{span[:160]}”"}


def check_cells(cells: list[str], locator: str, pages: list[dict]) -> dict:
    want = locator_pages(locator) or [p["page"] for p in pages]
    ncells = [normalize(c) for c in cells if str(c).strip()]
    for p in pages:
        if p["page"] not in want:
            continue
        text = normalize(p["text"])
        first = [m.start() for m in re.finditer(re.escape(ncells[0]), text)] if ncells else []
        for pos in first:
            window = text[max(0, pos - CELL_WINDOW): pos + CELL_WINDOW]
            if all(re.search(r"(?<![\d.])" + re.escape(c) + r"(?![\d])" if NUM.fullmatch(c) else re.escape(c), window)
                   for c in ncells):
                return {"status": "OCR" if p.get("ocr") else "EXACT", "page": p["page"], "detail": "table cells found together"}
    return {"status": "NOT_FOUND", "page": None, "detail": f"cells {cells} not found together on page(s) {want}"}


def load_sources(talk: Path, refs: list[dict]) -> dict[str, dict]:
    """reference id → {"pages": [...], "stale": bool, "file": str} for references with ingested text."""
    idx_path = talk / "sources" / "_text" / "index.json"
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"files": []}
    by_file = {f["file"]: f for f in index["files"]}
    out = {}
    for r in refs:
        f = r.get("file")
        if not f:
            continue
        f = Path(f).as_posix()
        entry = by_file.get(f) or by_file.get(f"sources/{Path(f).name}")
        if not entry:
            out[r["id"]] = {"missing": f}
            continue
        src = talk / entry["file"]
        digest = hashlib.sha256(src.read_bytes()).hexdigest() if src.exists() else ""
        rec = json.loads((talk / entry["text"]).read_text(encoding="utf-8"))
        out[r["id"]] = {"pages": rec["pages"], "stale": digest != entry["sha256"], "file": entry["file"]}
    return out


def audit(claims: list[dict], refs: list[dict], talk: Path) -> list[dict]:
    sources = load_sources(talk, refs)
    vocab = load_endpoints(talk)
    results = []
    for c in claims:
        cid, kind = c.get("id", "?"), c.get("kind")
        if kind == "derived":
            continue
        src = sources.get(c.get("source"))
        quote, cells = c.get("quote", ""), c.get("quote_cells")
        res: dict
        if not src or "missing" in src:
            why = f"no ingested text for {src['missing']}" if src else f"reference '{c.get('source')}' has no 'file'"
            status = "UNCHECKABLE" if c.get("status") == "verified-fulltext" else "NOT_CHECKED"
            res = {"status": status, "page": None,
                   "detail": why + (" but the claim is marked verified-fulltext" if status == "UNCHECKABLE" else "")}
        elif src["stale"]:
            res = {"status": "STALE", "page": None, "detail": f"{src['file']} changed after ingest"}
        elif cells:
            res = check_cells(cells, c.get("locator", ""), src["pages"])
        elif quote:
            res = check_quote(quote, c.get("locator", ""), src["pages"])
        else:
            res = {"status": "NOT_FOUND", "page": None, "detail": "claim has neither 'quote' nor 'quote_cells'"}
        res["claim"] = cid
        results.append(res)

        evidence = quote or " ".join(map(str, cells or []))
        for v in values(c):
            ep = v.get("endpoint")
            if ep and evidence and not mentions(evidence, terms_for(ep, vocab, c.get("endpoint_terms"))):
                results.append({"claim": cid, "status": "ENDPOINT", "page": res.get("page"),
                                "detail": f"value {v['v']!r} is bound to {ep}, but the quote never names {ep} "
                                          f"(add the endpoint's words to the quote, or 'endpoint_terms')"})
                break
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("claims")
    ap.add_argument("--refs", required=True)
    ap.add_argument("--talk", help="talk folder (default: the folder above evidence/)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    claims_path = Path(a.claims)
    talk = Path(a.talk) if a.talk else claims_path.resolve().parent.parent
    claims = json.loads(claims_path.read_text(encoding="utf-8")).get("claims", [])
    refs = json.loads(Path(a.refs).read_text(encoding="utf-8")).get("references", [])
    results = audit(claims, refs, talk)
    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        order = ["STALE", "UNCHECKABLE", "NOT_FOUND", "NUMBER_MISMATCH", "PARAPHRASE", "LOCATOR", "ENDPOINT",
                 "OCR", "FUZZY", "NOT_CHECKED", "EXACT"]
        results.sort(key=lambda r: order.index(r["status"]))
        n_block = sum(r["status"] in BLOCKING for r in results)
        print(f"# verify_quotes: {len(claims)} claims, {n_block} blocking")
        for r in results:
            if r["status"] == "EXACT":
                continue
            page = f" (p. {r['page']})" if r.get("page") else ""
            print(f"- [{r['status']}] claim {r['claim']}{page}: {r['detail']}")
        exact = sum(r["status"] == "EXACT" for r in results)
        print(f"{exact} quote(s) found verbatim on their locator page.")
    return 1 if any(r["status"] in BLOCKING for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
