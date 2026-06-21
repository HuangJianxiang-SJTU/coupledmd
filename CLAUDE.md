<!-- better-model:start -->
<!-- better-model block version: 0.10 -->
## Model Routing (better-model)

**CRITICAL**: When spawning subagents via the Agent tool, ALWAYS set the `model` parameter (and `effort` for Sonnet/Opus — Haiku 4.5 does not support effort):
- `model: "haiku"` — search, grep, file reading, exploration, status checks (no effort field — Haiku 4.5 does not support it)
- `model: "sonnet", effort: "medium"` — code generation, tests, refactoring, bug fixes (1-2 files)
- `model: "opus", effort: "xhigh"` — multi-file refactoring (3+ files), code review, migrations, cross-file debugging
- `model: "opus", effort: "max"` — architecture design, security audits, novel algorithm design

Default to `model: "sonnet", effort: "medium"` when unsure.
Avoid Opus on >500K context — known lost-in-the-middle regression.
See [full decision matrix](docs/BETTER-MODEL.md).
<!-- better-model:end -->
