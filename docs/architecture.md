# Architecture

## Three layers

| Layer | Where | What it does |
|-------|-------|--------------|
| Behaviour | `skills/*/SKILL.md` and their references | Tells the agent what to do, when, and what "done" means |
| Orchestration | `skills/medical-deck/` and `roles/` | Order of stages, approval gates, subagent briefs, fix loop |
| Execution | `skills/*/scripts/`, `html-deck-building/assets/deck-engine.html` | Deterministic tools: lookups, figure extraction, builds, render and audit checks |

The agent reasons; scripts measure. Nothing that a script can check (overflow, a number
without a claim, a PMID that doesn't exist) is left to the agent's say-so.

## Data contracts

| File | Written by | Read by |
|------|-----------|---------|
| `brief.md` | deck-grilling | everyone |
| `plan.md` | deck-planning | researcher, figure maker, builder |
| `theme/theme.json`, `theme/scan.json` | template-matching | figure maker, builder |
| `evidence/references.json` | evidence-research (`pubmed.py refs`) | builder, evidence-audit (`verify_refs.py`) |
| `evidence/claims.json` | evidence-research | figure maker, builder, evidence-audit (`check_claims.py`) |
| `figures/manifest.json` | medical-figures | builder, evidence-audit |
| `build/render/dom.html` | `check_render.py` | slop-audit (`lint_slop.py`), evidence-audit |
| `audit/*.md` | the two reviewers | orchestrator (fix loop), user |

### A claim record

```json
{"id": "c07", "slide": 5, "text": "RFS at 24 months, intervention vs control",
 "values": ["24 months", "82.2%", "70.0%", "HR 0.58", "0.45–0.75"],
 "source": "long2026", "locator": "p. 6, Fig. 1A", "quote": "…verbatim…",
 "kind": "observed | planned | derived | recommendation | background",
 "derivation": "only for derived values",
 "status": "verified-fulltext | verified-abstract | unverified"}
```

## Gates

1. **Brief confirmed** by the user (end of interview).
2. **Plan approved** by the user. Nothing is researched or built for slides that are not in
   the plan.
3. **Audit pass**: no blocking slop (S01–S06) and no blocking evidence finding (E-NUM,
   E-SRC, E-REF, E-PHI; E-CLAIM/E-FIG when they change the meaning). After three failed
   loops, the orchestrator stops and shows the user the open findings.

## Why subagents

Stages 4–7 run in fresh contexts. The researcher can't be swayed by the plan's hoped-for
numbers, and the reviewers judge the deck as the audience will see it, without the
builder's intentions. Each role brief ends with a fixed report shape, so the orchestrator
can route findings without reading the subagent's transcript.
