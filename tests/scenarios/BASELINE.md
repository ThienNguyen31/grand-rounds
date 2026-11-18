# Baseline behaviour (RED phase)

Recorded 2026-11-18 with a general-purpose agent that had **no Grand Rounds skills loaded**.
Each scenario was run as a single-shot subagent with no tools. These are the failures the
skills were written to fix. Re-run the same prompts with the plugin installed to check that
they now pass (see `README.md` in this folder).

## S1 — Intake: "Make me a journal club deck on INTerpath-001, ~10 minutes"

Baseline reply (abridged):

> What I'm assuming, so you can correct me: … Format: editable PowerPoint (.pptx) …
> Audience: physician or mixed clinical journal club … Otherwise I'll continue with these
> defaults and give you a file to review.

ACTIONS listed: "No questions before starting", pick PPTX, pick a "clean clinical look,
navy title bars and one accent colour", build immediately.

**Failure:** output format, template, audience and purpose were decided by the agent.
The user was told about the assumptions only after the agent had committed to them.
Rationalizations heard: "decide and proceed", "the usual journal club flow", "tell me if
you'd rather have a different template".

**Expected with skills:** one round of numbered questions with a recommended answer each
(deck type, audience, duration, language, HTML vs PPTX, template, sources, presenter),
before any file is created.

## S2 — Review: one slide with eyebrow, presenter hint, process note, wrong numbers

Baseline caught the scientific problems well (DMFS labelled with the RFS hazard ratio;
"overall survival improved markedly" for HR 0.77, P = 0.33).

**Failures on presentation craft:**

- The eyebrow `03 · KẾT QUẢ HIỆU QUẢ · ITT` was discussed only for whether "ITT" was
  correct. It was not recognised as a template-ish AI pattern to delete.
- `Hình 1 nguyên bản NEJM, đổi màu` ("original NEJM Figure 1, recoloured") was treated as a
  caption to reword ("Vẽ lại/điều chỉnh từ Hình 1…"), not as process narration that the
  audience never needs.
- KPI-card styling of every number was not questioned.
- The presenter hint `▸ Bấm tiếp: …` was moved "to speaker notes or hidden" only as an
  afterthought (item 7 of 9).

**Expected with skills:** these are flagged as slop findings with IDs from the catalog,
alongside the evidence findings, and the fix is deletion, not rewording.

## S3 — Hurried request for references with PMIDs/DOIs

The agent declined to give 5-year data it could not cite (good) but still wrote a PMID and
DOI **from memory**, labelled "(verify)".

**Failure:** an identifier that was never retrieved by a tool reached slide text.

**Expected with skills:** identifiers come only from a lookup made in this session (MCP or
`pubmed.py`) and are recorded in `references.json`; anything else is shown as
"[reference pending verification]" and listed as a blocker.
