# Changelog

## 0.2.0 (2026-11-20)

The project is now called **Grand Rounds** (repository `grand-rounds`, plugin
`grand-rounds`). It was published as MedSlides. Links to the old repository URL redirect.

### Added

- **Claude Code hooks** (`hooks/`):
  - The plan gate refuses writes to `build/` and `out/`, and the deck-builder scripts,
    until `STATUS.md` records that the user approved `plan.md`.
  - Slop on save lints each slide file saved under `build/` or `out/` and sends blocking
    findings (S01–S04) straight back to the agent.
  - Both hooks act only inside a talk folder and do nothing if they fail. Set
    `GRAND_ROUNDS_NO_GATE=1` to turn the gate off.
- **CI** on every push:
  - unit tests on Linux (Python 3.10 and 3.13), Windows and macOS, with PyMuPDF and
    python-pptx installed;
  - `claude plugin validate` on the plugin and marketplace manifests.
- **Illustrations**, preferring libraries over AI:
  - Servier Medical Art: vector kits exported cleanly from PowerPoint.
  - Bioicons: `bioicons.py` searches, cleans and credits icons.
  - ChatGPT or Gemini images as a last resort, using the account the user has.
  - `label_figure.py` adds editable labels with leader lines, kept clear of each other.
- **Motion graphics** inside the slide instead of a pasted video:
  - looping mechanisms built from Bioicons parts;
  - image sequences (for example the cardiac cycle);
  - poster frames for print and PDF.
- **Examples**:
  - `examples/heart-anatomy`: Servier and AI hearts with labels, and a cardiac-cycle loop.
  - The fictional-trial efficacy slide now shows two Kaplan–Meier panels: recurrence-free
    survival and overall survival.
- A workflow diagram (`assets/workflow.svg` / `.png`) in the README.

### Fixed

- Two skills, `medical-figures` and `template-matching`, had a `: ` in an unquoted
  description. The YAML frontmatter failed to parse, so both loaded with no description and
  could not trigger. They are now quoted, and a test guards against this.
- `deck_text.py` has a single copy, in `evidence-audit`. `lint_slop.py` and the hooks load
  it from there instead of keeping a hand-synced duplicate.
- Mechanism figure: labels no longer overlap, and the highlight circle is no longer
  misplaced.

## 0.1.0 (2026-11-18)

First release, published as MedSlides:

- **Orchestrator** `medical-deck`: eight stages with gates, and subagent role briefs.
- **Interview** `deck-grilling`: one round of questions, each with a recommended answer.
- **Planning, evidence research and figures**: PubMed, Europe PMC, Crossref and
  ClinicalTrials.gov lookups; a claim ledger; vector Kaplan–Meier curves taken from the
  paper's PDF.
- **Deck builds**: HTML (presenter tools) and PPTX (from your template).
- **Audits**: one for AI slop, one for evidence (numbers, references, patient identifiers).
- Behaviour scenarios (RED/GREEN) and unit tests for every script.
