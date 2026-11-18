# Contributing to MedSlides (for humans and agents)

## Skills

- One folder per skill in `skills/`, with `SKILL.md` (frontmatter `name` = folder name) and
  `agents/openai.yaml` (Codex display name and short description).
- **Model-invoked** skills: the description starts with "Use when…" and lists triggering
  situations only, never the skill's workflow (agents follow a workflow summary instead of
  reading the skill).
- **User-invoked** skills (`grill-deck`, `audit-deck`): `disable-model-invocation: true` in
  `SKILL.md` and `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. Keep the
  two in sync. A user-invoked skill may call model-invoked skills, never the reverse.
- Skills refer to each other by telling the agent to call the Skill tool with the skill's
  name. On harnesses without a Skill tool, the agent reads that skill's `SKILL.md`. Don't link
  across skill folders with relative paths. Shared material lives in the skill that owns
  it.
- `deck_text.py` exists in both `slop-audit/scripts/` and `evidence-audit/scripts/` so that
  each skill is self-contained. Keep the two copies byte-identical (a unit test checks).
- Keep `SKILL.md` short (under ~500 words). Move references to sibling `.md` files and
  tools to `scripts/`.

## Changing behaviour: test first

Write the scenario first, run it without the change, and record what goes wrong. Then make
the change and re-run. See `tests/scenarios/`. A skill edit that no scenario exercised is
an untested change.

## Scripts

- Standard library first. PyMuPDF, python-pptx and Playwright are optional dependencies,
  and each script says which one it needs and exits with an install hint if it is missing.
- Never send user content to third-party services other than the literature APIs (NCBI,
  Europe PMC, Crossref, ClinicalTrials.gov). Never include a user's email or name in API
  requests.
- Every script gets a unit test in `tests/unit/test_tools.py` that runs offline.

```bash
python -m unittest discover -s tests/unit -v
```

## Releases

Bump `version` in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.codex-plugin/plugin.json` and `.antigravity-plugin/plugin.json` together. A test checks that
they agree.

## Examples

Example decks must use fictional or openly licensed data. Never commit a hospital's
template, a patient's data, or a copyrighted figure.
