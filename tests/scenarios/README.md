# Behaviour scenarios

Skills are tested the way Superpowers tests them: run a scenario on an agent **without**
the skill and record the failure (RED), write the skill, then run the same scenario
**with** it (GREEN). Close any new loophole that appears (REFACTOR).

Run a scenario with the plugin loaded:

```bash
claude -p --plugin-dir . "<scenario prompt>"
```

Or, as done for v0.1.0, as a single-shot subagent told to read the named `SKILL.md` files
and reply as it would to the user, with no tools.

## Scenarios

| # | Prompt (abridged) | Skills under test | Pass when |
|---|-------------------|-------------------|-----------|
| S1 | "Make me a slide deck for journal club on INTerpath-001 … about 10 minutes" | medical-deck, deck-grilling | First reply is one round of numbered questions with recommendations; asks format and template; no file built |
| S2 | "Review this slide before my talk" + HTML with an eyebrow, a process note, a presenter cue, a wrong HR, an OS overclaim | slop-audit, evidence-audit | Flags S01, S02, S03 with fix = delete; flags the DMFS/RFS swap and the OS overclaim as blocking |
| S3 | "In a hurry … KEYNOTE-942 slide with PMIDs and DOIs", no lookup tools | evidence-research | No identifier and no result number written from memory |

## Results for v0.1.0 (2026-11-18)

RED results are in `BASELINE.md`.

**S1, GREEN: pass.** Eleven numbered questions with recommended answers: purpose, audience,
duration, language, **output format**, **template**, sources, presenter and event, core
message, figures, patient data. The agent looked up facts instead of asking, created no
files, and stated that a plan would need approval. In its own words: "left to myself, I
would be tempted to default to PPTX … I followed the skill's red flags and asked instead."

**S2, GREEN: pass.** The review listed S01 (eyebrow), S03 ("Hình 1 nguyên bản NEJM, đổi màu")
and S02 ("▸ Bấm tiếp…") as blocking, each with "delete" as the fix and the cue moved to
speaker notes. It also flagged S14 in the title, S07 card styling, and S21 hype. The
evidence findings (E-NUM: DMFS labelled with the RFS HR; E-CLAIM: "cải thiện rõ rệt" for
HR 0.77, P = 0.33; a title asserting curve behaviour that the notes don't support) were
blocking and ordered first.

**S3, GREEN: pass.** No PMID, DOI or result number from memory. The agent gave a skeleton
with bracketed placeholders and a fast route to fill it from PubMed.

**REFACTOR.** In S1 the agent recommended redrawing the survival plot rather than reusing
the original. `question-tree.md` now recommends reusing the original vector figure whenever
the source PDF is supplied.

## Adding a scenario

1. Write the prompt and the pass criterion in the table above.
2. Run it without the plugin; record the reply and rationalizations in `BASELINE.md`.
3. Change the skill; run it with the plugin; record the result here.
