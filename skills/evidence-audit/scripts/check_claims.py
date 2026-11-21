#!/usr/bin/env python3
"""Cross-check the numbers on a deck against evidence/claims.json.

Reports:
  * UNSUPPORTED   a number shown on a slide that no claim for that slide contains
  * ELSEWHERE     the number exists in a claim, but the claim is mapped to another slide
  * QUOTE         a claim value that does not appear in the claim's own verbatim quote
  * SOURCE        a claim whose source id is not in references.json
  * UNVERIFIED    claims whose status is 'unverified'
  * LABEL         a number bound to one endpoint sits on a slide that names only a different
                  endpoint (an RFS hazard ratio under a DMFS title)
  * HANDTYPED     with --src: a number typed into the slide source instead of a {{claim.key}}
                  placeholder (blocking with --require-placeholders)

Usage:
  python check_claims.py deck.html claims.json [--refs references.json] [--include-notes]
                         [--src build/slides.html [--require-placeholders]] [--skip-small]

Exit code 1 when there is any UNSUPPORTED, QUOTE, SOURCE or LABEL finding (and HANDTYPED
with --require-placeholders).
Numbers are matched after normalising decimal commas (0,58 = 0.58) and thousands
separators (1.137 = 1,137 = 1137). Years, page counters ("3 / 8"), CI level labels and
small integers that only number things ("Fig. 2", "Table 3", "step 1") are ignored. Other
integers 0-10 ARE checked (grade 4, 3 doses, NNT 7, 2 deaths); --skip-small restores the
old behaviour of ignoring all of them. Text inside inline <svg> figures is skipped unless
--include-figures: figures are traced through figures/manifest.json instead.

Claim values may be plain strings or objects bound to an endpoint (see claim_values.py).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claim_values import _rx as term_rx, load_endpoints, value_strings, values  # noqa: E402
from deck_text import html_slides, load_slides  # noqa: E402

NUM = re.compile(r"(?<![\w.,])[-−–]?\d+(?:[.,]\d+)*(?:\s?%)?")
STRIP = [
    re.compile(r"\b10\.\d{4,9}/\S+", re.I),                    # DOI
    re.compile(r"https?://\S+"),
    re.compile(r"\b(?:PMID|PMCID|NCT)\s*:?\s*\w+", re.I),
    re.compile(r"\b(?:19|20)\d{2}\s*;\s*\d+(?:\s*\(\s*\d+\s*\))?(?::\s*[\w-]+)?"),  # 2024;403(10427):632-644
    re.compile(r"\b\d+\s*/\s*\d+\s*$"),                        # page counter at end
    re.compile(r"(?:\b(?:KTC|CI)\s*)?\b(?:90|95|99)\s?%\s*(?:CI|KTC|confidence)?", re.I),  # CI level label
    re.compile(r"\bCC[\s-]?(?:BY|0)(?:[\s-](?:SA|NC|ND))*(?:[\s-]?\d\.\d)?", re.I),  # licence names: CC BY 4.0
    # numbering, not data: "Fig. 2", "Table 3", "Hình 1", "slide 4", "step 2", "Q3", "S01"
    re.compile(r"\b(?:fig(?:ure)?s?\.?|tables?|bảng|hình|biểu đồ|slides?|steps?|bước|panels?|phụ lục|"
               r"appendix|supplement(?:ary)?|ref\.?|q|s)\s*\d{1,2}[a-z]?\b", re.I),
    re.compile(r"\{\{[^}]*\}\}"),                                  # unresolved placeholders
    # names with a hyphenated number: PD-1, PD-L1, IL-23, NOVA-1, COVID-19, anti-TNF-α is unaffected
    re.compile(r"\b[A-Za-z][A-Za-z0-9]{0,9}-\d{1,3}\b(?![.,]\d)"),
]


def canon(token: str) -> float | None:
    """Turn '82,2%', '1.137', '1,137', '0.58', '−0,45' into a float."""
    t = token.replace("−", "-").replace("–", "-").replace("%", "").strip()
    neg = t.startswith("-")
    t = t.lstrip("-")
    if not t:
        return None
    seps = re.findall(r"[.,]", t)
    if len(seps) > 1:  # 1.234.567 or 1,234,567 (or 1.234,5)
        last = t[-4] if len(t) > 4 and t[-4] in ".," else None
        if last and len(set(seps)) == 1:
            t = t.replace(seps[0], "")
        else:
            dec = seps[-1]
            t = t.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif len(seps) == 1:
        head, tail = re.split(r"[.,]", t)
        if len(tail) == 3 and head not in ("0", "") and len(head) <= 3:
            t = head + tail  # thousands separator
        else:
            t = head + "." + tail
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def numbers(text: str, keep_small: bool = True) -> list[tuple[str, float]]:
    for rx in STRIP:
        text = rx.sub(" ", text)
    out = []
    for m in NUM.finditer(text):
        tok = m.group(0).strip()
        v = canon(tok)
        if v is None:
            continue
        is_pct = tok.endswith("%")
        is_int = re.fullmatch(r"[-−–]?\d+", tok) is not None
        if is_int and 1900 <= abs(v) <= 2100:
            continue  # year
        if is_int and abs(v) <= 10 and not is_pct and not keep_small:
            continue  # --skip-small: ignore small integers altogether (old behaviour)
        out.append((tok, v))
    return out


LABEL_WINDOW = 250


def endpoint_spans(text: str, vocab: dict) -> list[tuple[int, int, str]]:
    """(start, end, endpoint) for every endpoint term in text, in order; overlaps keep the longer term."""
    hits = []
    for name, terms in vocab.items():
        for t in terms:
            for m in term_rx(t).finditer(text):
                hits.append((m.start(), m.end(), name))
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    out, last_end = [], -1
    for h in hits:
        if h[0] >= last_end:
            out.append(h)
            last_end = h[1]
    return out


def close(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("claims")
    ap.add_argument("--refs")
    ap.add_argument("--include-notes", action="store_true", help="also check numbers in speaker notes")
    ap.add_argument("--include-figures", action="store_true",
                    help="also check numbers inside inline <svg> figures (axis ticks will need claims too)")
    ap.add_argument("--skip-small", action="store_true", help="ignore integers 0-10 without %% (old behaviour)")
    ap.add_argument("--src", help="slide source with {{claim.key}} placeholders (build/slides.html)")
    ap.add_argument("--require-placeholders", action="store_true",
                    help="with --src: hand-typed numbers are blocking")
    ap.add_argument("--talk", help="talk folder, for evidence/endpoints.json (default: above evidence/)")
    a = ap.parse_args(argv)
    keep_small = not a.skip_small
    talk = Path(a.talk) if a.talk else Path(a.claims).resolve().parent.parent
    vocab = load_endpoints(talk)

    slides = load_slides(a.deck)
    claims = json.loads(Path(a.claims).read_text(encoding="utf-8")).get("claims", [])
    refs = None
    if a.refs:
        refs = {r["id"] for r in json.loads(Path(a.refs).read_text(encoding="utf-8")).get("references", [])}

    by_slide: dict[int | None, list[float]] = {}
    for c in claims:
        vals = []
        for v in value_strings(c):
            vals += [n for _, n in numbers(v, keep_small=True)]
        by_slide.setdefault(c.get("slide"), []).extend(vals)
    unmapped = by_slide.get(None, [])

    findings: list[tuple[str, str]] = []
    for s in slides:
        text = (s["text"] if a.include_figures else s.get("text_nosvg", s["text"])) +             (" " + s["notes"] if a.include_notes else "")
        own = by_slide.get(s["index"], []) + unmapped
        for tok, v in numbers(text, keep_small):
            if any(close(v, x) for x in own):
                continue
            other = [k for k, xs in by_slide.items() if k not in (s["index"], None) and any(close(v, x) for x in xs)]
            if other:
                findings.append(("ELSEWHERE", f"slide {s['index']}: '{tok}' is in a claim for slide(s) {other}"))
            else:
                findings.append(("UNSUPPORTED", f"slide {s['index']}: '{tok}' has no claim"))

    # LABEL: a value bound to endpoint X shown where the slide names a different endpoint:
    # either the nearest endpoint named before the number (within LABEL_WINDOW characters,
    # so two-panel slides are judged panel by panel), or, with no endpoint before it, the
    # only endpoint the slide names at all.
    slide_by_index = {s["index"]: s for s in slides}
    for c in claims:
        s = slide_by_index.get(c.get("slide"))
        if not s:
            continue
        stext = s.get("text_nosvg", s["text"])
        spans = endpoint_spans(stext, vocab)
        named = {n for _, _, n in spans}
        for v in values(c):
            ep = v.get("endpoint")
            if not ep or not named:
                continue
            if re.fullmatch(r"\s*\d+\s*(?:months?|weeks?|years?|tháng|tuần|năm)\s*", v["v"]):
                continue  # a time point, not a result
            want = [n for _, n in numbers(v["v"], keep_small=True)][:1]
            if not want:
                continue
            labels = []  # endpoint each occurrence of this number sits under
            for m in NUM.finditer(stext):
                x = canon(m.group(0))
                if x is None or not close(x, want[0]):
                    continue
                before = [n for st, e, n in spans if e <= m.start() and m.start() - e <= LABEL_WINDOW]
                labels.append(before[-1] if before else (next(iter(named)) if len(named) == 1 else None))
            # The same number may appear twice (an RFS CI bound equal to the OS HR): flag only
            # when no occurrence sits under the value's own endpoint.
            if labels and ep not in labels and None not in labels:
                findings.append(("LABEL", f"slide {s['index']}: '{v['v']}' (claim {c.get('id')}) is {ep}, "
                                          f"but on the slide it sits under {', '.join(sorted(set(labels)))}"))

    # HANDTYPED: numbers written into the slide source instead of placeholders.
    if a.src:
        for s in html_slides(Path(a.src).read_text(encoding="utf-8", errors="replace")):
            for tok, _ in numbers(s.get("text_nosvg", s["text"]), keep_small):
                findings.append(("HANDTYPED", f"source slide {s['index']}: '{tok}' is typed, not a {{{{claim.key}}}} placeholder"))

    for c in claims:
        cid = c.get("id", "?")
        if c.get("kind") != "derived" and c.get("quote"):
            qnums = [n for _, n in numbers(c["quote"], keep_small=True)]
            for v in value_strings(c):
                for tok, n in numbers(v, keep_small=True):
                    if not any(close(n, q) for q in qnums):
                        findings.append(("QUOTE", f"claim {cid}: value '{tok}' is not in its quote"))
        if c.get("kind") == "derived" and not c.get("derivation"):
            findings.append(("QUOTE", f"claim {cid}: derived value without 'derivation'"))
        if refs is not None and c.get("source") not in refs:
            findings.append(("SOURCE", f"claim {cid}: source '{c.get('source')}' not in references"))
        if c.get("status") == "unverified":
            findings.append(("UNVERIFIED", f"claim {cid}: {c.get('text', '')}"))

    order = ["UNSUPPORTED", "LABEL", "QUOTE", "SOURCE", "HANDTYPED", "ELSEWHERE", "UNVERIFIED"]
    findings.sort(key=lambda f: order.index(f[0]))
    print(f"# check_claims: {Path(a.deck).name}, {len(slides)} slides, {len(claims)} claims")
    if not findings:
        print("No findings.")
    for kind, msg in findings:
        print(f"- [{kind}] {msg}")
    block = {"UNSUPPORTED", "QUOTE", "SOURCE", "LABEL"} | ({"HANDTYPED"} if a.require_placeholders else set())
    blocking = any(k in block for k, _ in findings)
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
