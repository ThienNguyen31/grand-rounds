# Changelog

## 0.3.0 (2026-11-21)

Evidence hardening: the checks that matter most no longer rest on the agent's own ledger.

### Added

- `evidence-research/scripts/ingest_sources.py`: page-numbered text for every PDF,
  Markdown or text source in `sources/`, with SHA-256 (version pin), OCR for pages without a
  text layer (flagged for checking by eye), and DOI/PMID read from the paper.
- `evidence-audit/scripts/verify_quotes.py`: finds each claim's quote in the source text.
  Wording may match loosely (Unicode, ligatures, line-break hyphens, dashes, Lancet
  decimal point); numbers must match exactly. NUMBER_MISMATCH, LOCATOR, PARAPHRASE,
  NOT_FOUND, STALE and ENDPOINT block. `quote_cells` checks table values.
- Structured claim values (`evidence-audit/scripts/claim_values.py`, single copy): each
  number can carry its measure, endpoint, population, time point and arm, with an
  English–Vietnamese endpoint vocabulary (oncology and IBD end points) that a talk can
  extend in `evidence/endpoints.json`.
- `check_claims.py`: LABEL (a number shown under a different endpoint than its claim,
  judged panel by panel), HANDTYPED with `--src` (numbers typed instead of placeholders).
- `build_deck.py --claims`: `{{c07.hr}}`, `{{c07.hr|vi}}`, `{{c07.rfs|num}}` placeholders
  filled from the ledger; unknown or unfilled placeholders fail the build.
- `verify_refs.py`: retraction and correction check (PubMed CommentsCorrections and
  publication type; Crossref `updated-by` and update notices), INCOMPLETE for records with
  nothing to compare, guideline age note, MANUAL and FICTIONAL statuses.
- `tests/unit/test_evidence_hardening.py` (29 tests, offline).

### Fixed

- Count-up numbers (`data-count`) were read as "0" by `check_claims.py`, so the headline
  numbers of a slide were never checked. `deck_text.py` now reads their final value.
- Integers 0–10 were never checked (grade 4, 3 doses, NNT 7); they are now, except where
  they only number things (Fig. 2, Table 3, step 1). `--skip-small` restores the old rule.
  Names such as PD-1, IL-23, NOVA-1 no longer count as numbers.

### Changed

- The fictional-trial example: its source is ingested, its reference points at the file,
  slide 5 is built from placeholders (byte-identical output), and the deck was rebuilt with
  the current engine.

## 0.2.1 (2026-11-20)

### Fixed

- **A one-line request skipped the interview.** For example: "5 slides on belantamab,
  HTML, lots of charts".
  - Where many plugins are installed, Claude Code drops the descriptions of rarely used
    skills, so the request could go straight to `html-deck-building`.
  - Even when it reached the orchestrator, the agent asked its questions and kept working
    in the same turn.
  - Fixes:
    - A `UserPromptSubmit` hook (`route_prompt.py`) reminds the agent to start from
      `medical-deck` and to open with the interview.
    - `medical-deck` now makes the first reply the interview only, and creates the talk
      folder after the brief is confirmed.
    - In `deck-grilling`, each round of questions ends the turn.
    - `html-deck-building` and `pptx-deck-building` send the agent back to `medical-deck`
      when no approved plan or claim ledger exists.
- The HTML render check states that `pip install playwright` is enough when Edge or Chrome
  is installed. If the check cannot run, the agent must say so in the delivery report
  rather than skip it silently.

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
