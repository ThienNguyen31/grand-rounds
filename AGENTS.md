# Contributing to Grand Rounds (for humans and agents)

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
- Shared code has one copy, in the skill that owns it. `deck_text.py` lives in
  `evidence-audit/scripts/`; `slop-audit/scripts/lint_slop.py` and the hooks load it from
  the sibling folder. Never copy it (a unit test checks there is only one). Installing
  skills one by one therefore needs both `evidence-audit` and `slop-audit`.
- Quote a frontmatter value that contains `: ` (YAML would otherwise drop the whole
  frontmatter at load time; a unit test and `claude plugin validate` catch it).
- Keep `SKILL.md` short (under ~500 words). Move references to sibling `.md` files and
  tools to `scripts/`.

## Changing behaviour: test first

Write the scenario first, run it without the change, and record what goes wrong. Then make
the change and re-run. See `tests/scenarios/`. A skill edit that no scenario exercised is
an untested change.

## Hooks

`hooks/hooks.json` (Claude Code) wires three scripts through `hooks/run-hook.sh`, which picks
whichever Python 3 is installed and does nothing if there is none:

- `route_prompt.py` (UserPromptSubmit): when a prompt asks for slides, a deck or a
  presentation, adds a reminder to start from `medical-deck` and make the first reply the
  interview. Claude Code drops the descriptions of rarely used skills when many plugins are
  installed, so the skill list alone cannot be relied on to route the request.
- `plan_gate.py` (PreToolUse): inside a talk folder (a folder with `STATUS.md` and
  `brief.md`), refuses writes to `build/` and `out/`, and deck-builder commands, until the
  Plan row of `STATUS.md` says `approved`. `GRAND_ROUNDS_NO_GATE=1` turns it off.
- `slop_on_save.py` (PostToolUse): lints saved `.html` slides under `build/` or `out/` and
  reports blocking slop findings (S01–S04) to the agent.

Hooks must stay silent outside a talk folder and fail open on their own errors. Keep them
fast: they run on every prompt and every Write, Edit and Bash call.

## Scripts

- Standard library first. PyMuPDF, python-pptx and Playwright are optional dependencies,
  and each script says which one it needs and exits with an install hint if it is missing.
- Never send user content to third-party services other than the literature APIs (NCBI,
  Europe PMC, Crossref, ClinicalTrials.gov). Never include a user's email or name in API
  requests.
- Every script gets a unit test in `tests/unit/test_tools.py` that runs offline.

```bash
python -m unittest discover -s tests/unit -v
claude plugin validate .claude-plugin/plugin.json
```

CI (`.github/workflows/ci.yml`) runs the unit tests on Linux, Windows and macOS with
PyMuPDF and python-pptx installed, and `claude plugin validate` on both manifests.

## Releases

Bump `version` in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.codex-plugin/plugin.json` and `.antigravity-plugin/plugin.json` together. A test checks that
they agree.

## Examples

Example decks must use fictional or openly licensed data. Never commit a hospital's
template, a patient's data, or a copyrighted figure.
