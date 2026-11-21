"""Unit tests for the evidence-hardening additions: source ingest, quote verification,
structured claim values, endpoint labels, claim placeholders and retraction checks.

Run from the repo root: python -m unittest discover -s tests/unit -v
Network is never used. PDF and OCR tests are skipped without PyMuPDF / Tesseract.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SK = ROOT / "skills"
EX = ROOT / "examples" / "fictional-trial"


def load(rel: str, name: str):
    path = SK / rel
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def has(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


ingest = load("evidence-research/scripts/ingest_sources.py", "ingest_sources")
vq = load("evidence-audit/scripts/verify_quotes.py", "verify_quotes")
cv = load("evidence-audit/scripts/claim_values.py", "claim_values")
cc = load("evidence-audit/scripts/check_claims.py", "check_claims")
vr = load("evidence-audit/scripts/verify_refs.py", "verify_refs")
bd = load("html-deck-building/scripts/build_deck.py", "build_deck")
dt = load("evidence-audit/scripts/deck_text.py", "deck_text")

SOURCE = """# Trial report

## Methods (p. 2)

Patients were randomly assigned in a 2:1 ratio.

## Results (p. 4)

Recurrence-free survival at 24 months was 79.1% and 67.0% (hazard ratio for recurrence or
death, 0.62; 95% CI, 0.47 to 0.81).

## Safety (p. 6)

Adverse events of grade 3 or higher | 21.4% | 19.5%
"""

QUOTE = ("Recurrence-free survival at 24 months was 79.1% and 67.0% (hazard ratio for recurrence or "
         "death, 0.62; 95% CI, 0.47 to 0.81).")


def make_talk(source: str = SOURCE, name: str = "report.md") -> Path:
    talk = Path(tempfile.mkdtemp())
    (talk / "sources").mkdir()
    (talk / "evidence").mkdir()
    (talk / "sources" / name).write_text(source, encoding="utf-8")
    ingest.ingest(talk, ocr=False)
    return talk


REFS = [{"id": "t", "title": "Trial", "authors": ["A"], "file": "sources/report.md"}]


def claim(**kw):
    base = {"id": "c1", "slide": 1, "source": "t", "locator": "p. 4", "quote": QUOTE,
            "values": ["79.1%", "0.62"], "kind": "observed", "status": "verified-fulltext"}
    base.update(kw)
    return base


class TestIngest(unittest.TestCase):
    def test_markdown_pages_hash_and_index(self):
        talk = make_talk()
        idx = json.loads((talk / "sources" / "_text" / "index.json").read_text())
        self.assertEqual(len(idx["files"]), 1)
        rec = json.loads((talk / idx["files"][0]["text"]).read_text())
        self.assertEqual([p["page"] for p in rec["pages"]], [1, 2, 4, 6])
        self.assertEqual(len(rec["sha256"]), 64)

    def test_page_markers_and_ids(self):
        pages = ingest.text_pages("front <!-- page 2 --> two <!-- page 3 --> three")
        self.assertEqual([p["page"] for p in pages], [1, 2, 3])
        ids = ingest.find_ids([{"text": "doi: 10.1056/NEJMoa2400001. PMID: 38246194"}])
        self.assertEqual(ids, {"doi": "10.1056/NEJMoa2400001", "pmid": "38246194"})

    @unittest.skipUnless(has("fitz"), "PyMuPDF not installed")
    def test_pdf_pages_ligature_hyphen_lancet_point(self):
        import pymupdf as fitz
        talk = Path(tempfile.mkdtemp())
        (talk / "sources").mkdir()
        doc = fitz.open()
        doc.new_page().insert_text((72, 72), "Title page. doi:10.1016/S0140-6736(25)00001-1")
        p2 = doc.new_page()
        # base-14 Helvetica has no en-dash glyph (it comes back as "·"); use a Unicode font if installed
        fonts = sorted(Path("/usr/share/fonts").rglob("DejaVuSans.ttf")) if Path("/usr/share/fonts").exists() else []
        kw = {"fontname": "dejavu", "fontfile": str(fonts[0])} if fonts else {}
        dash = "–" if fonts else "-"
        p2.insert_text((72, 72), "The primary end point was recur-", **kw)
        p2.insert_text((72, 86), f"rence-free survival; hazard ratio 0·62 (95% CI 0·47{dash}0·81).", **kw)
        doc.save(str(talk / "sources" / "paper.pdf"))
        ingest.ingest(talk, ocr=False)
        rec = json.loads((talk / "sources" / "_text" / "paper.pdf.pages.json").read_text())
        self.assertEqual(len(rec["pages"]), 2)
        self.assertEqual(rec["ids"]["doi"], "10.1016/S0140-6736(25)00001-1")
        res = vq.check_quote("The primary end point was recurrence-free survival; hazard ratio 0.62 (95% CI 0.47-0.81).",
                             "p. 2", rec["pages"])
        self.assertEqual(res["status"], "EXACT", res)

    @unittest.skipUnless(has("fitz") and shutil.which("tesseract"), "PyMuPDF or Tesseract missing")
    def test_scanned_page_is_ocrd_and_flagged(self):
        import pymupdf as fitz
        talk = Path(tempfile.mkdtemp())
        (talk / "sources").mkdir()
        img = fitz.open()
        pg = img.new_page(width=600, height=200)
        pg.insert_text((20, 100), "Overall survival hazard ratio 0.81", fontsize=24)
        pix = pg.get_pixmap(dpi=200)
        doc = fitz.open()
        doc.new_page(width=600, height=200).insert_image(fitz.Rect(0, 0, 600, 200), pixmap=pix)
        doc.save(str(talk / "sources" / "scan.pdf"))
        ingest.ingest(talk, ocr=True)
        rec = json.loads((talk / "sources" / "_text" / "scan.pdf.pages.json").read_text())
        self.assertEqual(rec["ocr_pages"], [1])
        res = vq.check_quote("Overall survival hazard ratio 0.81", "p. 1", rec["pages"])
        self.assertIn(res["status"], ("OCR",), res)


class TestVerifyQuotes(unittest.TestCase):
    def setUp(self):
        self.talk = make_talk()

    def run_one(self, c):
        return [r["status"] for r in vq.audit([c], REFS, self.talk)]

    def test_exact(self):
        self.assertEqual(self.run_one(claim()), ["EXACT"])

    def test_number_changed_is_caught_even_when_text_matches(self):
        self.assertEqual(self.run_one(claim(quote=QUOTE.replace("0.62", "0.68"))), ["NUMBER_MISMATCH"])

    def test_wrong_page(self):
        self.assertEqual(self.run_one(claim(locator="p. 2")), ["LOCATOR"])

    def test_invented_quote(self):
        self.assertEqual(self.run_one(claim(quote="Distant metastasis-free survival improved, HR 0.58.")), ["NOT_FOUND"])

    def test_near_verbatim_is_advisory(self):
        res = self.run_one(claim(quote=QUOTE.replace("was 79.1%", "was  79.1 %").replace("(hazard", "( hazard")))
        self.assertIn(res[0], ("EXACT", "FUZZY"))

    def test_paraphrase_blocks(self):
        q = ("Recurrence-free survival at 24 months was 79.1% versus 67.0% (HR for recurrence "
             "or death 0.62; 95% CI 0.47 to 0.81).")
        self.assertIn(self.run_one(claim(quote=q))[0], ("PARAPHRASE", "NOT_FOUND"))
        self.assertIn(self.run_one(claim(quote=q))[0], vq.BLOCKING)

    def test_table_cells(self):
        c = claim(quote="", quote_cells=["grade 3 or higher", "21.4%", "19.5%"], locator="p. 6", values=["21.4%"])
        self.assertEqual(self.run_one(c), ["EXACT"])
        c["quote_cells"] = ["grade 3 or higher", "21.4%", "18.5%"]
        self.assertEqual(self.run_one(c), ["NOT_FOUND"])

    def test_endpoint_must_be_named_in_quote(self):
        c = claim(values=[{"key": "hr", "v": "0.62", "endpoint": "DMFS"}])
        self.assertEqual(self.run_one(c), ["EXACT", "ENDPOINT"])
        c["values"][0]["endpoint"] = "RFS"
        self.assertEqual(self.run_one(c), ["EXACT"])

    def test_stale_and_uncheckable(self):
        (self.talk / "sources" / "report.md").write_text(SOURCE + "\nedited", encoding="utf-8")
        self.assertEqual(self.run_one(claim()), ["STALE"])
        refs = [{"id": "t", "title": "Trial"}]
        self.assertEqual([r["status"] for r in vq.audit([claim()], refs, self.talk)], ["UNCHECKABLE"])
        self.assertEqual([r["status"] for r in vq.audit([claim(status="verified-abstract")], refs, self.talk)],
                         ["NOT_CHECKED"])

    def test_example_talk_passes(self):
        claims = json.loads((EX / "evidence" / "claims.json").read_text())["claims"]
        refs = json.loads((EX / "evidence" / "references.json").read_text())["references"]
        res = vq.audit(claims, refs, EX)
        self.assertFalse([r for r in res if r["status"] in vq.BLOCKING], res)


class TestClaimValues(unittest.TestCase):
    def test_values_lookup_and_defaults(self):
        c = {"id": "c7", "endpoint": "RFS", "values": ["24 months", {"key": "hr", "v": "0.62", "measure": "HR"}]}
        self.assertEqual(cv.value_strings(c), ["24 months", "0.62"])
        self.assertEqual(cv.lookup([c], "c7.hr")["endpoint"], "RFS")
        self.assertEqual(cv.lookup([c], "c7.0")["v"], "24 months")
        self.assertIsNone(cv.lookup([c], "c7.nope"))

    def test_endpoints_in_text_vi_and_case(self):
        vocab = cv.load_endpoints(None)
        self.assertEqual(cv.endpoints_in("Sống còn toàn bộ ở tháng 24", vocab), {"OS"})
        self.assertEqual(cv.endpoints_in("thermos bottle", vocab), set())
        self.assertIn("clinical-remission", cv.endpoints_in("Clinical remission at week 52", vocab))


DECK = """<html><body>
<section class="slide"><h2>{title}</h2>
<p><span data-count="79.1" data-dec="1" data-suf="%">0</span> vs 67.0%; HR 0.62 (0.47–0.81)</p>
<p>Grade 4 events: 3 vs 1; PD-1 blockade; Fig. 2</p></section></body></html>"""


class TestCheckClaimsHardening(unittest.TestCase):
    def run_check(self, title, claims, extra=()):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "evidence").mkdir()
        (tmp / "d.html").write_text(DECK.format(title=title), encoding="utf-8")
        (tmp / "evidence" / "claims.json").write_text(json.dumps({"claims": claims}), encoding="utf-8")
        return cc.main([str(tmp / "d.html"), str(tmp / "evidence" / "claims.json"), *extra])

    def claims(self, endpoint="RFS"):
        return [{"id": "c1", "slide": 1, "endpoint": endpoint, "quote": "", "kind": "derived", "derivation": "test",
                 "values": [{"key": "a", "v": "79.1%"}, "67.0%", {"key": "hr", "v": "0.62"}, "0.47", "0.81"]},
                {"id": "c2", "slide": 1, "kind": "derived", "derivation": "test", "values": ["4", "3", "1"]}]

    def test_count_up_value_is_read(self):
        s = dt.html_slides(DECK.format(title="x"))[0]
        self.assertIn("79.1%", s["text"])
        self.assertNotRegex(s["text"], r"(?<![\d.])0(?![\d.])")

    def test_small_integers_now_checked(self):
        c = self.claims()[:1]
        self.assertEqual(self.run_check("Recurrence-free survival", c), 1)        # grade 4, 3, 1 have no claim
        self.assertEqual(self.run_check("Recurrence-free survival", c, ["--skip-small"]), 0)
        self.assertEqual(self.run_check("Recurrence-free survival", self.claims()), 0)

    def test_endpoint_swap_is_a_label_finding(self):
        self.assertEqual(self.run_check("Distant metastasis-free survival", self.claims()), 1)
        self.assertEqual(self.run_check("Sống còn không tái phát", self.claims()), 0)

    def test_handtyped_numbers_with_src(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "src.html").write_text('<section class="slide"><p>HR {{c1.hr}} vs 0.70</p></section>', encoding="utf-8")
        args = ["--src", str(tmp / "src.html"), "--require-placeholders"]
        self.assertEqual(self.run_check("Recurrence-free survival", self.claims(), args), 1)


class TestBuildPlaceholders(unittest.TestCase):
    CLAIMS = [{"id": "c7", "values": [{"key": "hr", "v": "HR 0.62"}, "79.1%", "1,204"]}]

    def test_fill_and_filters(self):
        out = bd.fill_claims("{{c7.hr}}|{{c7.hr|num}}|{{c7.1|vi}}|{{c7.2|vi}}", self.CLAIMS, [])
        self.assertEqual(out, "HR 0.62|0.62|79,1%|1.204")

    def test_unknown_or_missing_fails_the_build(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "s.html").write_text("<p>{{c7.hr}} {{c9.x}}</p>", encoding="utf-8")
        r = bd.build(tmp / "s.html", tmp / "o.html", self.CLAIMS)
        self.assertEqual(len(r["unresolved"]), 1)
        r = bd.build(tmp / "s.html", tmp / "o.html", None)
        self.assertEqual(len(r["unresolved"]), 2)

    def test_example_deck_builds_from_ledger(self):
        tmp = Path(tempfile.mkdtemp())
        out = tmp / "deck.html"
        claims = json.loads((EX / "evidence" / "claims.json").read_text())["claims"]
        r = bd.build(EX / "build" / "index.src.html", out, claims)
        self.assertEqual(r["unresolved"], [])
        self.assertEqual(out.read_text(encoding="utf-8"),
                         (EX / "out" / "nova1-journal-club.html").read_text(encoding="utf-8"))


PUBMED_XML = b"""<PubmedArticleSet><PubmedArticle><MedlineCitation><Article>
<PublicationTypeList><PublicationType>Journal Article</PublicationType>{pt}</PublicationTypeList></Article>
<CommentsCorrectionsList>{cc}</CommentsCorrectionsList></MedlineCitation></PubmedArticle></PubmedArticleSet>"""


class TestVerifyRefsHardening(unittest.TestCase):
    REC = {"id": "w", "title": "A trial", "authors": ["Weber JS"], "year": 2024, "pmid": "1"}
    FOUND = {"title": "A trial.", "year": 2024, "first_author": "Weber JS", "doi": ""}

    def xml(self, pt="", cc=""):
        return PUBMED_XML.replace(b"{pt}", pt.encode()).replace(b"{cc}", cc.encode())

    def test_parse_notices(self):
        n = vr.parse_pubmed_notices(self.xml(
            pt="<PublicationType>Retracted Publication</PublicationType>",
            cc='<CommentsCorrections RefType="RetractionIn"><RefSource>J. 2025</RefSource><PMID>9</PMID></CommentsCorrections>'
               '<CommentsCorrections RefType="CommentIn"><RefSource>x</RefSource></CommentsCorrections>'))
        self.assertEqual([x["kind"] for x in n], ["retraction", "retraction"])

    def test_retracted_concern_corrected(self):
        def run(kind):
            return vr.verify(self.REC, pubmed=lambda p: self.FOUND,
                             pubmed_notices=lambda p: [{"kind": kind, "ref": "x"}])[0]
        self.assertEqual(run("retraction"), "RETRACTED")
        self.assertEqual(run("concern"), "CONCERN")
        self.assertEqual(run("correction"), "CORRECTED")
        self.assertIn("RETRACTED", vr.BLOCKING)
        self.assertNotIn("CORRECTED", vr.BLOCKING)

    def test_incomplete_record_is_not_verified(self):
        st, _ = vr.verify({"id": "w", "pmid": "1"}, pubmed=lambda p: self.FOUND, pubmed_notices=lambda p: [])
        self.assertEqual(st, "INCOMPLETE")

    def test_crossref_path_uses_updated_by_and_notices(self):
        rec = {"id": "d", "title": "A trial", "authors": ["Weber JS"], "year": 2024, "doi": "10.1/x"}
        found = dict(self.FOUND, notices=[])
        st, _ = vr.verify(rec, crossref=lambda d: found,
                          crossref_notices=lambda d: [{"kind": "retraction", "ref": "notice 10.1/r"}])
        self.assertEqual(st, "RETRACTED")

    def test_guidelines_fictional_manual(self):
        import datetime
        old = {"type": "guideline", "year": 2017}
        self.assertTrue(vr.guideline_note(old, 5, datetime.date(2026, 11, 21)))
        self.assertFalse(vr.guideline_note({"type": "guideline", "year": 2024}, 5, datetime.date(2026, 11, 21)))
        self.assertEqual(vr.verify({"id": "f", "fictional": True})[0], "FICTIONAL")
        st, _ = vr.verify({"id": "g", "type": "guideline", "year": 2025, "url": "https://x", "checked_on": "2026-11-21"})
        self.assertEqual(st, "MANUAL")


class TestSharedHelpersSingleCopy(unittest.TestCase):
    def test_claim_values_single_copy(self):
        copies = [p for p in ROOT.rglob("claim_values.py") if ".git" not in p.parts]
        self.assertEqual([str(p.relative_to(ROOT)) for p in copies],
                         [str(Path("skills/evidence-audit/scripts/claim_values.py"))])


if __name__ == "__main__":
    unittest.main()
