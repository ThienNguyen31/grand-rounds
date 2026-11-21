# Example: NOVA-1 journal club (fictional)

A complete Grand Rounds run on an invented trial. NOVA-1 does not exist; its "paper" is
`sources/nova1-fictional-report.md`. Everything else is what the pipeline produces for a
real talk.

| Stage | File |
|-------|------|
| 1 Interview | `brief.md` |
| 2 Template | none; palette in `build/index.src.html` `:root` |
| 3 Plan | `plan.md` |
| 4 Evidence | `evidence/references.json`, `evidence/claims.json` |
| 5 Figures | `figures/` (KM layers made by `figures/make_km.py`, mechanism SVG) and `figures/manifest.json` |
| 6 Build | `build/slides.html`, `build/deck.css`, `build/deck.js` → `out/nova1-journal-club.html` |
| 7 Audit | `audit/slop-report.md`, `audit/evidence-report.md` |

Open `out/nova1-journal-club.html` in a browser. Use → or a clicker to advance. Slide 2's
mechanism is a looping motion graphic (16 s, four captioned stages); slide 5 reveals a
24-month marker on click. Press `L` for
the laser, `C` to circle, `P` for the pen, `N` for speaker notes and `F` for fullscreen.

Rebuild and re-check from this folder:

```bash
python ../../skills/html-deck-building/scripts/compose_deck.py --slides build/slides.html --css build/deck.css --js build/deck.js --title "NOVA-1 journal club (fictional demo)" --lang en --cite "NOVA-1 trial report (fictional, for demonstration). All data are invented." -o build/index.src.html
python ../../skills/html-deck-building/scripts/build_deck.py build/index.src.html out/nova1-journal-club.html --claims evidence/claims.json
python ../../skills/html-deck-building/scripts/check_render.py out/nova1-journal-club.html --out build/render --smooth 5
python ../../skills/slop-audit/scripts/lint_slop.py build/render/dom.html
python ../../skills/evidence-research/scripts/ingest_sources.py .
python ../../skills/evidence-audit/scripts/verify_quotes.py evidence/claims.json --refs evidence/references.json
python ../../skills/evidence-audit/scripts/check_claims.py build/render/dom.html evidence/claims.json --refs evidence/references.json --src build/slides.html
```

Slide 5 takes its numbers from the ledger (`{{c07.hr}}` and so on in `build/slides.html`);
the other slides still have typed numbers, which `--src` lists as HANDTYPED.

A real deck would lift the Kaplan–Meier figure from the paper's PDF with
`pdf_figures.py`. This demo has no PDF, so it draws the curves from fictional data.
