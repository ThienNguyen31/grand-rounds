#!/usr/bin/env python3
"""Verify that every reference in references.json is real and is the paper it claims to be.

For each record with a PMID, look it up on PubMed (E-utilities esummary); with a DOI, on
Crossref. Compare title (fuzzy), year and first-author surname, and check that the PMID's
DOI equals the record's DOI.

It also asks whether the paper has been retracted or corrected since: PubMed's linked
notices (CommentsCorrections: RetractionIn, ExpressionOfConcernIn, ErratumIn, UpdateIn …)
and publication type "Retracted Publication"; for DOI-only records, Crossref's
"updated-by" field and the notices that name the DOI in "update-to" (Retraction Watch data
is in Crossref since 2023).

Statuses
  blocking:     MISMATCH (exists, metadata differs) · NOT_FOUND · NO_IDENTIFIER · ERROR (network)
                RETRACTED · CONCERN (expression of concern) · INCOMPLETE (record has no title
                or first author to compare, so existence is all that was checked)
  not blocking: VERIFIED · CORRECTED (erratum or update published: re-check the numbers you
                use against it) · MANUAL (a guideline with no PMID/DOI, checked by hand: "url"
                and "checked_on" given) · FICTIONAL (demo data, "fictional": true)
A guideline ("type": "guideline") older than --max-age years (default 5) gets an advisory
note: look for a newer version on the issuing society's site and record "checked_on".

Usage: python verify_refs.py references.json [--json] [--max-age 5]
"""
from __future__ import annotations

import argparse
import datetime
import difflib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = "grand-rounds/0.1 (+https://github.com/drtranquanghung91-vn/grand-rounds)"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_pubmed(pmid: str) -> dict | None:
    time.sleep(0.34)
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "retmode": "json", "tool": "grand-rounds"})
    res = json.loads(_get(url)).get("result", {})
    s = res.get(str(pmid))
    if not s or "error" in s:
        return None
    ids = {a.get("idtype"): a.get("value") for a in s.get("articleids", [])}
    year = re.match(r"\d{4}", s.get("pubdate", "") or "")
    return {"title": s.get("title", ""), "year": int(year.group(0)) if year else None,
            "first_author": s.get("sortfirstauthor", ""), "doi": ids.get("doi", ""),
            "journal": s.get("source", "")}


# PubMed CommentsCorrections RefType → our notice kind (only the ones that concern this paper)
PUBMED_NOTICES = {
    "RetractionIn": "retraction", "PartialRetractionIn": "retraction",
    "RetractedandRepublishedIn": "retraction",
    "ExpressionOfConcernIn": "concern",
    "ErratumIn": "correction", "CorrectedandRepublishedIn": "correction", "UpdateIn": "update",
}


def fetch_pubmed_notices(pmid: str) -> list[dict]:
    """Retractions, concerns, errata and updates linked to a PMID (efetch XML)."""
    time.sleep(0.34)
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": pmid, "retmode": "xml", "tool": "grand-rounds"})
    return parse_pubmed_notices(_get(url))


def parse_pubmed_notices(xml: bytes) -> list[dict]:
    root = ET.fromstring(xml)
    out = []
    for pt in root.iter("PublicationType"):
        if (pt.text or "").strip() == "Retracted Publication":
            out.append({"kind": "retraction", "ref": "publication type: Retracted Publication"})
    for cc in root.iter("CommentsCorrections"):
        kind = PUBMED_NOTICES.get(cc.get("RefType", ""))
        if kind:
            out.append({"kind": kind, "ref": f"{cc.get('RefType')}: {(cc.findtext('RefSource') or '').strip()}"
                                              + (f" (PMID {cc.findtext('PMID')})" if cc.findtext("PMID") else "")})
    return out


CROSSREF_KINDS = {"retraction": "retraction", "partial_retraction": "retraction", "withdrawal": "retraction",
                  "removal": "retraction", "expression_of_concern": "concern",
                  "correction": "correction", "corrigendum": "correction", "erratum": "correction",
                  "addendum": "update", "clarification": "update", "new_version": "update"}


def fetch_crossref_notices(doi: str) -> list[dict]:
    """Notices whose 'update-to' names this DOI. Assumes Crossref's 'updates' filter; verify live."""
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"filter": f"updates:{doi}", "rows": 20})
    items = json.loads(_get(url)).get("message", {}).get("items", [])
    out = []
    for it in items:
        for u in it.get("update-to", []):
            if str(u.get("DOI", "")).lower() == doi.lower():
                kind = CROSSREF_KINDS.get(str(u.get("type", "")).lower().replace("-", "_"), "update")
                out.append({"kind": kind, "ref": f"{u.get('type')} notice {it.get('DOI')} (source: {u.get('source', 'publisher')})"})
    return out


def fetch_crossref(doi: str) -> dict | None:
    try:
        m = json.loads(_get("https://api.crossref.org/works/" + urllib.parse.quote(doi)))["message"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    year = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    authors = m.get("author", [])
    notices = [{"kind": CROSSREF_KINDS.get(str(u.get("type", "")).lower().replace("-", "_"), "update"),
                "ref": f"updated-by {u.get('type')} {u.get('DOI', '')}".strip()} for u in m.get("updated-by", [])]
    return {"title": (m.get("title") or [""])[0], "year": year,
            "first_author": authors[0].get("family", "") if authors else "", "doi": m.get("DOI", doi),
            "journal": (m.get("short-container-title") or m.get("container-title") or [""])[0],
            "notices": notices}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def surname(author: str) -> str:
    a = norm(author)
    return a.split(" ")[0] if a else ""


def compare(rec: dict, found: dict) -> list[str]:
    problems = []
    if rec.get("title"):
        ratio = difflib.SequenceMatcher(None, norm(rec["title"]), norm(found["title"])).ratio()
        if ratio < 0.85:
            problems.append(f"title differs ({ratio:.2f}): found '{found['title'][:90]}'")
    if rec.get("year") and found.get("year") and int(rec["year"]) != int(found["year"]):
        problems.append(f"year {rec['year']} ≠ {found['year']}")
    first = (rec.get("authors") or [""])[0]
    if first and found.get("first_author") and surname(first) != surname(found["first_author"]):
        problems.append(f"first author '{first}' ≠ '{found['first_author']}'")
    return problems


BLOCKING = {"MISMATCH", "NOT_FOUND", "NO_IDENTIFIER", "ERROR", "RETRACTED", "CONCERN", "INCOMPLETE"}


def notice_status(notices: list[dict]) -> tuple[str | None, list[str]]:
    kinds = {n["kind"] for n in notices}
    notes = [f"{n['kind'].upper()}: {n['ref']}" for n in notices]
    for kind, status in (("retraction", "RETRACTED"), ("concern", "CONCERN")):
        if kind in kinds:
            return status, notes
    if kinds & {"correction", "update"}:
        return "CORRECTED", notes + ["re-check every number you use from this paper against the notice"]
    return None, notes


def guideline_note(rec: dict, max_age: int, today: datetime.date | None = None) -> list[str]:
    if rec.get("type") != "guideline":
        return []
    today = today or datetime.date.today()
    year = rec.get("version_date", "")[:4] if rec.get("version_date") else rec.get("year")
    try:
        age = today.year - int(year)
    except (TypeError, ValueError):
        return ["guideline without year or version_date: record which version you used"]
    if age > max_age:
        return [f"guideline is {age} years old: search the issuing society's site for a newer version "
                f"and record 'checked_on'"]
    return []


def verify(rec: dict, pubmed=fetch_pubmed, crossref=fetch_crossref,
           pubmed_notices=fetch_pubmed_notices, crossref_notices=fetch_crossref_notices,
           max_age: int = 5) -> tuple[str, list[str]]:
    if rec.get("fictional"):
        return "FICTIONAL", ["demonstration data: nothing to verify"]
    pmid, doi = str(rec.get("pmid") or "").strip(), str(rec.get("doi") or "").strip()
    gnotes = guideline_note(rec, max_age)
    if not pmid and not doi:
        if rec.get("type") == "guideline" and rec.get("url") and rec.get("checked_on"):
            return "MANUAL", [f"checked by hand at {rec['url']} on {rec['checked_on']}"] + gnotes
        return "NO_IDENTIFIER", ["no PMID or DOI: cannot be checked automatically"] + gnotes
    try:
        notes: list[str] = []
        if pmid:
            found = pubmed(pmid)
            if not found:
                return "NOT_FOUND", [f"PMID {pmid} not found on PubMed"]
            notes += compare(rec, found)
            if doi and found.get("doi") and found["doi"].lower() != doi.lower():
                notes.append(f"PMID {pmid} has DOI {found['doi']}, record says {doi}")
            notices = pubmed_notices(pmid)
        else:
            found = crossref(doi)
            if not found:
                return "NOT_FOUND", [f"DOI {doi} not found on Crossref"]
            notes += compare(rec, found)
            notices = list(found.get("notices", []))
            seen = {n["ref"] for n in notices}
            notices += [n for n in crossref_notices(doi) if n["ref"] not in seen]
        if notes:
            return "MISMATCH", notes + gnotes
        missing = [f for f, ok in (("title", rec.get("title")), ("first author", (rec.get("authors") or [""])[0]))
                   if not ok]
        nstatus, nnotes = notice_status(notices)
        if nstatus in ("RETRACTED", "CONCERN"):
            return nstatus, nnotes + gnotes
        if missing:
            return "INCOMPLETE", [f"record has no {' or '.join(missing)}: only existence was checked"] + nnotes + gnotes
        return (nstatus or "VERIFIED"), nnotes + gnotes
    except Exception as e:  # network or parse problem: never report as verified
        return "ERROR", [f"{type(e).__name__}: {e}"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("references")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-age", type=int, default=5, help="years after which a guideline gets a recheck note")
    a = ap.parse_args(argv)
    refs = json.loads(Path(a.references).read_text(encoding="utf-8")).get("references", [])
    results = []
    for r in refs:
        status, notes = verify(r, max_age=a.max_age)
        results.append({"id": r.get("id"), "status": status, "notes": notes})
    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"# verify_refs: {len(results)} references")
        for x in results:
            print(f"- {x['id']}: {x['status']}" + "".join(f"\n    · {n}" for n in x["notes"]))
    return 1 if any(x["status"] in BLOCKING for x in results) else 0


if __name__ == "__main__":
    sys.exit(main())
