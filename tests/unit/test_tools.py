"""Unit tests for the MedSlides scripts. Run from the repo root:

    python -m unittest discover -s tests/unit -v

Network is never used. Tests that need PyMuPDF or python-pptx are skipped when those
packages are missing.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SK = ROOT / "skills"


def load(rel: str, name: str):
    path = SK / rel
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def has(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


SLOP_HTML = """<html><body><div id="stage">
<section class="slide title"><h1>Title</h1></section>
<section class="slide" data-name="Efficacy">
  <div class="eyebrow">03 · RESULTS · ITT</div>
  <span class="trial">Hình 1 nguyên bản NEJM, đổi màu</span>
  <h2>Curves separate — and keep widening — not just a vaccine — a therapy</h2>
  <div class="hint">▸ Bấm tiếp: mốc 24 tháng → HR từng giai đoạn</div>
  <p>Key takeaways 🚀 Lorem ipsum</p>
  <aside class="notes">[click] Bấm tiếp is fine here</aside>
</section></div></body></html>"""

CLEAN_HTML = """<html><body><div id="stage">
<section class="slide title"><h1>Vaccine plus anti-PD-1 lowered recurrence</h1></section>
<section class="slide" data-name="Efficacy">
  <h2>Recurrence-free survival at 24 months was 79,1% vs 67,0%</h2>
  <p>HR 0,62 (95% CI 0,47–0,81); 1.204 screened</p>
  <svg><text>0</text><text>25</text><text>50</text></svg>
  <aside class="notes">[click] 24-month marker</aside>
</section></div></body></html>"""


class TestDeckText(unittest.TestCase):
    def test_copies_are_identical(self):
        a = (SK / "evidence-audit/scripts/deck_text.py").read_bytes()
        b = (SK / "slop-audit/scripts/deck_text.py").read_bytes()
        self.assertEqual(a, b, "keep the two deck_text.py copies identical")

    def test_slides_text_notes_svg(self):
        dt = load("evidence-audit/scripts/deck_text.py", "deck_text_a")
        s = dt.html_slides(CLEAN_HTML)
        self.assertEqual(len(s), 2)
        self.assertIn("79,1%", s[1]["text"])
        self.assertNotIn("24-month", s[1]["text"])
        self.assertIn("24-month marker", s[1]["notes"])
        self.assertIn("25", s[1]["text"])
        self.assertNotIn("25", s[1]["text_nosvg"].split())


class TestLintSlop(unittest.TestCase):
    def setUp(self):
        self.mod = load("slop-audit/scripts/lint_slop.py", "lint_slop")
        self.tmp = Path(tempfile.mkdtemp())

    def lint(self, html):
        p = self.tmp / "d.html"
        p.write_text(html, encoding="utf-8")
        return self.mod.lint_html(p, "auto", None)

    def test_catches_the_baseline_patterns(self):
        ids = {f["id"] for f in self.lint(SLOP_HTML)}
        for rule in ("S01", "S02", "S03", "S04", "S14", "S15", "S16"):
            self.assertIn(rule, ids, rule)

    def test_notes_are_not_linted(self):
        found = [f for f in self.lint(SLOP_HTML) if f["id"] == "S02"]
        self.assertTrue(all("fine here" not in f["text"] for f in found))

    def test_clean_deck_has_no_blocking(self):
        self.assertFalse([f for f in self.lint(CLEAN_HTML) if f["severity"] == "blocking"])

    def test_large_inline_data_is_fast(self):
        import time
        big = "<style>.a{background:url(data:image/png;base64," + "A" * 400000 + ")} .b{font-size:10px}</style>"
        t = time.time()
        res = self.lint(big + CLEAN_HTML)
        self.assertLess(time.time() - t, 5)
        self.assertTrue(any(f["id"] == "S19" for f in res))


class TestCheckClaims(unittest.TestCase):
    def setUp(self):
        self.mod = load("evidence-audit/scripts/check_claims.py", "check_claims")

    def test_canon(self):
        c = self.mod.canon
        self.assertEqual(c("82,2%"), 82.2)
        self.assertEqual(c("0.58"), 0.58)
        self.assertEqual(c("1.137"), 1137)
        self.assertEqual(c("1,137"), 1137)
        self.assertEqual(c("0,450"), 0.45)
        self.assertEqual(c("−0,45"), -0.45)
        self.assertEqual(c("1.234.567"), 1234567)

    def test_numbers_skip_years_pages_ci_label(self):
        nums = [v for _, v in self.mod.numbers("In 2026, HR 0,62 (95% CI 0,47–0,81) 3 / 8")]
        self.assertIn(0.62, nums)
        self.assertNotIn(2026, nums)
        self.assertNotIn(95, nums)

    def run_check(self, claims):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "d.html").write_text(CLEAN_HTML, encoding="utf-8")
        (tmp / "c.json").write_text(json.dumps({"claims": claims}), encoding="utf-8")
        (tmp / "r.json").write_text(json.dumps({"references": [{"id": "src"}]}), encoding="utf-8")
        return self.mod.main([str(tmp / "d.html"), str(tmp / "c.json"), "--refs", str(tmp / "r.json")])

    def test_supported_deck_passes(self):
        claims = [{"id": "c1", "slide": 2, "values": ["24 months", "79.1%", "67.0%", "0.62", "0.47", "0.81", "1204"],
                   "source": "src", "quote": "at 24 months 79.1% vs 67.0% (HR 0.62; 95% CI 0.47 to 0.81); 1204 screened",
                   "kind": "observed", "status": "verified-fulltext"}]
        self.assertEqual(self.run_check(claims), 0)

    def test_unsupported_number_and_bad_quote_fail(self):
        claims = [{"id": "c1", "slide": 2, "values": ["79.1%", "0.62"], "source": "src",
                   "quote": "79.1% vs 67.0%", "kind": "observed", "status": "verified-fulltext"}]
        self.assertEqual(self.run_check(claims), 1)


class TestVerifyRefs(unittest.TestCase):
    def setUp(self):
        self.mod = load("evidence-audit/scripts/verify_refs.py", "verify_refs")
        self.rec = {"id": "w", "title": "Individualised neoantigen therapy mRNA-4157 plus pembrolizumab in resected melanoma",
                    "authors": ["Weber JS"], "year": 2024, "pmid": "1", "doi": "10.1/x"}
        self.found = {"title": "Individualised neoantigen therapy mRNA-4157 plus pembrolizumab in resected melanoma.",
                      "year": 2024, "first_author": "Weber JS", "doi": "10.1/X"}

    def test_verified(self):
        self.assertEqual(self.mod.verify(self.rec, pubmed=lambda p: self.found)[0], "VERIFIED")

    def test_mismatch_year_and_doi(self):
        st, notes = self.mod.verify({**self.rec, "year": 2023, "doi": "10.9/other"}, pubmed=lambda p: self.found)
        self.assertEqual(st, "MISMATCH")
        self.assertEqual(len(notes), 2)

    def test_not_found_no_identifier_error(self):
        self.assertEqual(self.mod.verify(self.rec, pubmed=lambda p: None)[0], "NOT_FOUND")
        self.assertEqual(self.mod.verify({"id": "x", "title": "t"})[0], "NO_IDENTIFIER")

        def boom(_):
            raise OSError("offline")
        self.assertEqual(self.mod.verify(self.rec, pubmed=boom)[0], "ERROR")


class TestPhiScan(unittest.TestCase):
    def test_hits(self):
        mod = load("evidence-audit/scripts/phi_scan.py", "phi_scan")
        kinds = {k for k, _ in mod.scan("Bệnh nhân Nguyễn Văn An, mã BN: 2024001234, nhập viện 12/03/2025, "
                                        "SĐT 0903 123 456, phường Bến Nghé")}
        self.assertTrue({"name", "record-id", "date", "phone", "address"} <= kinds, kinds)

    def test_axis_ticks_are_not_a_phone(self):
        mod = load("evidence-audit/scripts/phi_scan.py", "phi_scan2")
        self.assertFalse([k for k, _ in mod.scan("0 25 50 75 100 0") if k == "phone"])


class TestBuildDeck(unittest.TestCase):
    def test_inlines_assets(self):
        mod = load("html-deck-building/scripts/build_deck.py", "build_deck")
        tmp = Path(tempfile.mkdtemp())
        (tmp / "f.svg").write_text('<?xml version="1.0"?><svg viewBox="0 0 1 1"></svg>', encoding="utf-8")
        (tmp / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 20)
        (tmp / "s.css").write_text(".x{color:red}", encoding="utf-8")
        (tmp / "j.js").write_text("var k=1;", encoding="utf-8")
        (tmp / "src.html").write_text('<link rel="stylesheet" href="s.css"><!--include: f.svg--><img src="a.png">'
                                      '<script src="j.js"></script><img src="https://x.org/r.png">', encoding="utf-8")
        r = mod.build(tmp / "src.html", tmp / "out.html")
        out = (tmp / "out.html").read_text(encoding="utf-8")
        self.assertIn("<svg", out)
        self.assertNotIn("<?xml", out)
        self.assertIn("data:image/png;base64", out)
        self.assertIn(".x{color:red}", out)
        self.assertIn("var k=1;", out)
        self.assertEqual(r["missing"], [])
        self.assertEqual(r["remote"], ["https://x.org/r.png"])


@unittest.skipUnless(has("pymupdf") or has("fitz"), "PyMuPDF not installed")
class TestPdfFigures(unittest.TestCase):
    def test_extract_recolor_split(self):
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        mod = load("medical-figures/scripts/pdf_figures.py", "pdf_figures")
        tmp = Path(tempfile.mkdtemp())
        doc = fitz.open()
        page = doc.new_page(width=400, height=400)
        page.draw_line((50, 50), (300, 50), color=(0, 0.435, 0.6), width=1.5)   # #006f99 "curve"
        page.draw_line((50, 80), (300, 80), color=(0.58, 0.58, 0.6), width=1.5)  # grey "curve"
        page.draw_line((50, 300), (300, 300), color=(0, 0, 0), width=0.5)        # axis
        page.draw_line((50, 380), (300, 380), color=(0, 0, 0), width=0.5)        # outside the crop
        doc.save(tmp / "p.pdf")
        svg = tmp / "f.svg"
        mod.main(["extract", str(tmp / "p.pdf"), "--page", "1", "--rect", "20,20,350,340", "-o", str(svg),
                  "--recolor", "#006f99=#d7262e", "--prefix", "k"])
        text = svg.read_text(encoding="utf-8")
        self.assertIn("#d7262e", text)
        self.assertNotIn('width="', text.split(">")[0].replace("stroke-width", ""))
        rc = mod.main(["split", str(svg), "--colors", "#d7262e", "--min-width", "1", "-o",
                       str(tmp / "b.svg"), str(tmp / "c.svg")])
        self.assertEqual(rc, 0)
        self.assertIn("#d7262e", (tmp / "c.svg").read_text(encoding="utf-8"))
        self.assertNotIn("#d7262e", (tmp / "b.svg").read_text(encoding="utf-8"))


@unittest.skipUnless(has("pptx"), "python-pptx not installed")
class TestPptx(unittest.TestCase):
    def test_spec_build_check_and_scan(self):
        tmp = Path(tempfile.mkdtemp())
        spec = {"cite": "Source A, 2026", "slides": [
            {"type": "title", "title": "Talk", "presenter": "Presenter", "notes": "n"},
            {"type": "bullets", "title": "Point", "bullets": ["one", {"text": "two", "level": 1}], "notes": "n"},
            {"type": "diagram", "title": "Schema", "notes": "n", "nodes": [
                {"id": "a", "x": 0, "y": 0.3, "w": 0.3, "h": 0.3, "text": "A"},
                {"id": "b", "x": 0.6, "y": 0.3, "w": 0.3, "h": 0.3, "text": "B", "style": "int"}],
             "edges": [{"from": "a", "to": "b"}]},
            {"type": "chart", "title": "AEs", "chart": "bar", "categories": ["x", "y"],
             "series": [{"name": "A", "values": [1.5, 2.5], "color": "intervention"}], "notes": "n"},
            {"type": "table", "title": "T", "columns": ["a", "b"], "rows": [["1", "2"]], "notes": "n"},
            {"type": "figure", "title": "Labelled", "image": "pic.png", "notes": "n",
             "labels": [{"text": "Left", "at": [0.2, 0.3], "side": "left"}, {"text": "Right", "at": [0.8, 0.6], "side": "right"}]}]}
        from PIL import Image
        Image.new("RGB", (400, 300), "white").save(tmp / "pic.png")
        (tmp / "deck.json").write_text(json.dumps(spec), encoding="utf-8")
        build = load("pptx-deck-building/scripts/pptx_from_spec.py", "pptx_from_spec")
        self.assertEqual(build.main([str(tmp / "deck.json"), str(tmp / "o.pptx")]), 0)
        check = load("pptx-deck-building/scripts/check_pptx.py", "check_pptx")
        self.assertEqual(check.main([str(tmp / "o.pptx")]), 0)
        scan = load("template-matching/scripts/scan_template.py", "scan_template")
        res = scan.scan(tmp / "o.pptx", tmp / "theme")
        self.assertEqual(len(res["slides"]), 6)
        self.assertTrue((tmp / "theme" / "scan.json").exists())


class TestSkillLayout(unittest.TestCase):
    USER_INVOKED = {"grill-deck", "audit-deck"}

    def test_every_skill(self):
        import re
        names = set()
        for d in sorted(p for p in SK.iterdir() if p.is_dir()):
            md = (d / "SKILL.md").read_text(encoding="utf-8")
            fm = re.match(r"---\n(.*?)\n---\n", md, re.S)
            self.assertIsNotNone(fm, d.name)
            meta = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", fm.group(1), re.M))
            self.assertEqual(meta["name"], d.name)
            self.assertLessEqual(len(meta["description"]), 1024)
            names.add(d.name)
            yaml = (d / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertIn("display_name", yaml)
            if d.name in self.USER_INVOKED:
                self.assertIn("disable-model-invocation: true", md)
                self.assertIn("allow_implicit_invocation: false", yaml)
            else:
                self.assertTrue(meta["description"].startswith("Use when"), d.name)
        roles = (SK / "medical-deck" / "SKILL.md").read_text(encoding="utf-8")
        for r in re.findall(r"roles/([\w-]+)\.md", roles):
            self.assertTrue((SK / "medical-deck" / "roles" / f"{r}.md").exists(), r)
        self.assertGreaterEqual(len(names), 12)

    def test_manifests_agree(self):
        v = {json.loads((ROOT / f).read_text(encoding="utf-8"))["version"]
             for f in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".antigravity-plugin/plugin.json")}
        self.assertEqual(len(v), 1, v)


if __name__ == "__main__":
    unittest.main()


class TestComposeDeck(unittest.TestCase):
    def test_compose_keeps_engine_and_links_parts(self):
        mod = load("html-deck-building/scripts/compose_deck.py", "compose_deck")
        tmp = Path(tempfile.mkdtemp())
        (tmp / "build").mkdir()
        for n, t in (("slides.html", '<section class="slide"><h2 class="t">A</h2></section>'), ("deck.css", ":root{--primary:#123456}"),
                     ("deck.js", "window.x=1;")):
            (tmp / "build" / n).write_text(t, encoding="utf-8")
        out = tmp / "build" / "index.src.html"
        mod.main(["--slides", str(tmp / "build/slides.html"), "--css", str(tmp / "build/deck.css"), "--js",
                  str(tmp / "build/deck.js"), "--title", "T & P", "--lang", "vi", "--cite", 'Src "A"', "-o", str(out)])
        s = out.read_text(encoding="utf-8")
        self.assertIn("<!--include: slides.html-->", s)
        self.assertIn('<link rel="stylesheet" href="deck.css">', s)
        self.assertIn('<script src="deck.js"></script>', s)
        self.assertIn('<html lang="vi">', s)
        self.assertIn("<title>T &amp; P</title>", s)
        self.assertIn('data-cite="Src &quot;A&quot;"', s)
        self.assertIn("window.deck", s)  # the engine itself is there
        build = load("html-deck-building/scripts/build_deck.py", "build_deck2")
        r = build.build(out, tmp / "out.html")
        self.assertEqual(r["missing"], [])
        self.assertIn("--primary:#123456", (tmp / "out.html").read_text(encoding="utf-8"))


@unittest.skipUnless(has("PIL"), "Pillow not installed")
class TestLabelFigure(unittest.TestCase):
    def setUp(self):
        self.mod = load("medical-figures/scripts/label_figure.py", "label_figure")

    def test_spread_keeps_gap_and_bounds(self):
        ys = self.mod.spread([100, 101, 102, 500], gap=30, lo=20, hi=480)
        s = sorted(ys)
        self.assertTrue(all(b - a >= 29.9 for a, b in zip(s, s[1:])))
        self.assertGreaterEqual(min(ys), 20)
        self.assertLessEqual(max(ys), 480)

    def test_build_svg_with_labels(self):
        from PIL import Image
        tmp = Path(tempfile.mkdtemp())
        Image.new("RGB", (400, 300), (250, 250, 250)).save(tmp / "a.png")
        spec = {"image": "a.png", "whiten": 240, "stagger": 0.1, "labels": [
            {"text": "Right atrium", "at": [0.2, 0.4], "side": "left"},
            {"text": "Left atrium & more", "at": [0.8, 0.4], "side": "right"}]}
        svg = self.mod.build(spec, tmp)
        self.assertIn("data:image/jpeg;base64,", svg)
        self.assertIn("Left atrium &amp; more", svg)
        self.assertEqual(svg.count("<circle"), 2)
        self.assertIn('class="a-in"', svg)


class TestLintCredits(unittest.TestCase):
    def test_ai_disclosure_in_credit_is_not_slop(self):
        mod = load("slop-audit/scripts/lint_slop.py", "lint_slop2")
        tmp = Path(tempfile.mkdtemp()) / "d.html"
        tmp.write_text('<section class="slide"><h2>Title</h2></section><section class="slide"><h2>Heart</h2>'
                       '<div class="credit">Illustration: generated with ChatGPT, anatomy checked</div></section>'
                       '<section class="slide"><h2>Heart</h2><p>Figure redrawn for clarity</p></section>', encoding="utf-8")
        found = [(f["id"], f["slide"]) for f in mod.lint_html(tmp, "en", None)]
        self.assertNotIn(("S03", 2), found)
        self.assertIn(("S03", 3), found)
