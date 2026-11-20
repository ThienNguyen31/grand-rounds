# Harness notes

Skills name actions ("load the skill", "dispatch a subagent"), not tools. This table maps
the actions to each harness.

| Action | Claude Code | Codex | Antigravity |
|--------|-------------|-------|-------------|
| Install | `/plugin marketplace add drtranquanghung91-vn/grand-rounds`, then `/plugin install grand-rounds@grand-rounds` | plugin marketplace (`.codex-plugin/`, `.agents/plugins/marketplace.json`) or copy `skills/*` to `~/.agents/skills/` | `agy plugin install https://github.com/drtranquanghung91-vn/grand-rounds` |
| Load a skill | Skill tool | skill picker / implicit invocation | read the skill's `SKILL.md` with the file-read tool |
| User-only skills | `disable-model-invocation: true` | `policy.allow_implicit_invocation: false` in `agents/openai.yaml` | listed; the model is told not to call them itself |
| Dispatch a subagent | Agent/Task tool (general-purpose) | `spawn_agent` / `wait_agent` (needs `[features] multi_agent = true`) | `invoke_subagent` with TypeName `self` |
| Plan gate and slop-on-save hooks | `hooks/hooks.json`, loaded with the plugin | not wired; the skills' gates still apply | not wired; the skills' gates still apply |
| Track stages | `STATUS.md` in the talk folder (plus the harness's own todo tool if any) | same | same; Antigravity's task artifact may mirror it |

No harness gets a session-start hook. Grand Rounds activates only when a request is about a
medical presentation, through the skills' descriptions, so it stays quiet during other
work. The Claude Code hooks act only on files inside a talk folder (one with `STATUS.md`
and `brief.md`): they hold `build/` and `out/` closed until `STATUS.md` records the plan as
approved, and lint each saved slide file for blocking slop.

## Testing a harness port

Install the plugin, then send S1 from `tests/scenarios/README.md`. The first reply must be
a single round of numbered questions that includes output format and template, and the
agent must not create any slides.
