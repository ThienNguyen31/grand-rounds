#!/usr/bin/env python3
"""Turn every file in <talk>/sources/ into page-numbered text that scripts can check quotes against.

For each PDF, Markdown or text file in sources/ this writes sources/_text/<file>.pages.json:

  {"file": "sources/long2026.pdf", "sha256": "…", "pages": [{"page": 1, "text": "…", "ocr": false}],
   "ids": {"doi": "10.1056/…", "pmid": "…"}, "ocr_pages": [], "empty_pages": []}

and sources/_text/index.json listing every file with its hash, identifiers and OCR pages.

* PDF text comes from PyMuPDF, page by page, so "p. 6" in a locator means PDF page 6.
* A page with almost no text layer but an image is OCR'd when Tesseract is installed and
  marked "ocr": true. Numbers taken from an OCR page must be checked by eye: OCR misreads
  0.58 as 0.38. Without Tesseract the page is listed in "empty_pages".
* Markdown/text: split on "<!-- page N -->" markers, form feeds, or headings carrying
  "(p. N)"; otherwise the whole file is page 1.
* DOI and PMID are read from the first two pages. They are hints for verify_refs.py, not
  verified identifiers.

The SHA-256 pins the version: verify_quotes.py reports STALE if a file changes after ingest.

Usage: python ingest_sources.py <talk> [--ocr-lang eng] [--no-ocr]
Needs PyMuPDF for PDFs (pip install pymupdf).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEXT_EXT = {".md", ".txt", ".markdown"}
DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+?)(?=[\s\"<>]|[.,;)\]]?(?:\s|$))", re.I)
PMID = re.compile(r"\bPMID\s*:?\s*(\d{6,9})\b", re.I)
MIN_TEXT = 40  # characters on a page below which the text layer counts as missing


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def text_pages(src: str) -> list[dict]:
    """Split Markdown/plain text into pages using explicit markers."""
    if re.search(r"<!--\s*page\s+\d+\s*-->", src, re.I):
        parts = re.split(r"<!--\s*page\s+(\d+)\s*-->", src, flags=re.I)
        pages = []
        if parts[0].strip():
            pages.append({"page": 1, "text": parts[0]})
        for n, body in zip(parts[1::2], parts[2::2]):
            pages.append({"page": int(n), "text": body})
        return pages
    if "\f" in src:
        return [{"page": i, "text": t} for i, t in enumerate(src.split("\f"), 1)]
    heads = list(re.finditer(r"^#{1,6} .*?\(p(?:age)?\.?\s*(\d+)[^)]*\).*$", src, re.M | re.I))
    if heads:
        pages = []
        if src[:heads[0].start()].strip():
            pages.append({"page": 1, "text": src[:heads[0].start()]})
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(src)
            n = int(m.group(1))
            if pages and pages[-1]["page"] == n:
                pages[-1]["text"] += src[m.start():end]
            else:
                pages.append({"page": n, "text": src[m.start():end]})
        return pages
    return [{"page": 1, "text": src}]


def pdf_pages(path: Path, ocr: bool, lang: str) -> list[dict]:
    try:
        import pymupdf as fitz  # type: ignore
    except ImportError:
        try:
            import fitz  # type: ignore  # older PyMuPDF
        except ImportError as e:  # pragma: no cover
            raise SystemExit("Reading PDFs needs PyMuPDF: pip install pymupdf") from e
    pages = []
    with fitz.open(str(path)) as doc:
        for i, page in enumerate(doc, 1):
            text = page.get_text("text")
            rec = {"page": i, "text": text, "ocr": False}
            if len(text.strip()) < MIN_TEXT and page.get_images():
                rec["empty"] = True
                if ocr:
                    try:
                        tp = page.get_textpage_ocr(language=lang, dpi=300, full=True)
                        rec["text"] = page.get_text("text", textpage=tp)
                        rec["ocr"] = True
                        rec.pop("empty")
                    except Exception as e:  # Tesseract missing or failed
                        rec["ocr_error"] = f"{type(e).__name__}: {e}"
            pages.append(rec)
    return pages


def find_ids(pages: list[dict]) -> dict:
    head = " ".join(p["text"] for p in pages[:2])
    ids = {}
    m = DOI.search(head)
    if m:
        ids["doi"] = m.group(1).rstrip(".")
    m = PMID.search(head)
    if m:
        ids["pmid"] = m.group(1)
    return ids


def ingest_file(path: Path, talk: Path, ocr: bool = True, lang: str = "eng") -> dict:
    if path.suffix.lower() == ".pdf":
        pages = pdf_pages(path, ocr, lang)
    else:
        pages = [dict(p, ocr=False) for p in text_pages(path.read_text(encoding="utf-8", errors="replace"))]
    rel = path.relative_to(talk).as_posix()
    return {
        "file": rel,
        "sha256": sha256(path),
        "pages": pages,
        "ids": find_ids(pages),
        "ocr_pages": [p["page"] for p in pages if p.get("ocr")],
        "empty_pages": [p["page"] for p in pages if p.get("empty")],
    }


def ingest(talk: Path, ocr: bool = True, lang: str = "eng") -> dict:
    src = talk / "sources"
    out = src / "_text"
    out.mkdir(parents=True, exist_ok=True)
    index = {"files": []}
    for path in sorted(p for p in src.rglob("*") if p.is_file() and "_text" not in p.parts):
        if path.suffix.lower() not in TEXT_EXT | {".pdf"}:
            continue
        rec = ingest_file(path, talk, ocr, lang)
        (out / f"{path.name}.pages.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        index["files"].append({k: rec[k] for k in ("file", "sha256", "ids", "ocr_pages", "empty_pages")}
                              | {"pages": len(rec["pages"]), "text": f"sources/_text/{path.name}.pages.json"})
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return index


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("talk", help="talk folder (contains sources/)")
    ap.add_argument("--ocr-lang", default="eng", help="Tesseract language(s), e.g. eng or eng+vie")
    ap.add_argument("--no-ocr", action="store_true")
    a = ap.parse_args(argv)
    talk = Path(a.talk)
    if not (talk / "sources").is_dir():
        print(f"{talk}/sources not found", file=sys.stderr)
        return 2
    idx = ingest(talk, not a.no_ocr, a.ocr_lang)
    print(f"# ingest_sources: {len(idx['files'])} file(s) → {talk}/sources/_text/")
    for f in idx["files"]:
        ids = ", ".join(f"{k} {v}" for k, v in f["ids"].items()) or "no DOI/PMID found"
        print(f"- {f['file']}: {f['pages']} page(s), {ids}, sha256 {f['sha256'][:12]}…")
        if f["ocr_pages"]:
            print(f"    OCR pages {f['ocr_pages']}: check every number from these pages by eye")
        if f["empty_pages"]:
            print(f"    pages {f['empty_pages']} have no text layer and were not OCR'd: quotes there cannot be checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
