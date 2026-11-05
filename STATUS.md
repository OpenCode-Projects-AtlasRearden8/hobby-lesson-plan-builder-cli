# STATUS — lesson-builder

Built and verified: November 5, 2026.

## What was built

`lesson-builder`, an offline Python CLI in this folder that turns a
bullet list of what a beginner should learn into a friendly, paced
lesson plan.

- `lesson_builder/pacing.py` — graded pacing: keyword-tiered topics
  (starter / everyday / stretch with 20/30/45-minute weights), stable
  sort, near-equal minute-budget session distribution (gentle topics
  first), session-count auto-suggestion, per-session supply lists.
- `lesson_builder/cards.py` — printable one-page lesson cards
  (fixed 74-character bordered text cards, wrapped topics, checklist
  checkboxes, supplies block, gentle framing) and a markdown plan with
  `- [ ]` checkboxes.
- `lesson_builder/drafting.py` — optional drafting help via any
  OpenAI-compatible `chat/completions` endpoint. Default endpoint is a
  local Ollama (`http://localhost:11434/v1`, model `llama3.2`). Off by
  default (`--draft` to enable); no key is read from the environment or
  files (`--api-key` is the only key path), and failures degrade
  gracefully to the fully local plan.
- `lesson_builder/cli.py` — `argparse` entry point (`python -m
  lesson_builder` or `lesson-builder` after `pip install .`): bullet
  file or stdin, `--sessions`, `--minutes`, `--max-topics`, `--supplies`,
  `--format text|markdown`, `--output`, `--draft`, `--api-base`,
  `--model`, `--api-key`, `--version`.
- `tests/` — 67 unit tests covering pacing math (tiering, stable graded
  sort, session suggestion, distribution invariants: full topic coverage,
  no empty sessions,   cap handling and overflow survival, near-balance of session loads)
  and card rendering (width at every line, border integrity, checkbox
  counts, supplies, markdown parity, notes section), plus CLI and
  drafting tests (all network calls mocked; no real network in tests).
- `sample-topics.txt` — example input; `sample-plan.md` — example output
  (markdown) and the same plan rendered as text cards.
- Docs/legal: `README.md` crediting Asdale Dynamics, LLC; `LICENSE`
  MIT with "Copyright (c) 2026 Asdale Dynamics, LLC"; `pyproject.toml`
  (stdlib-only, `lesson-builder` console script).

## How to run it

```bash
python3 -m lesson_builder sample-topics.txt --sessions 3 \
  --title "AI for Beginners, Week by Week" --format markdown --output plan.md
python3 -m lesson_builder sample-topics.txt            # text cards to stdout
python3 -m lesson_builder sample-topics.txt --draft    # optional; local Ollama
# pip install . installs the `lesson-builder` command
python3 -m lesson_builder --help                       # all flags
```

## Verification results

- `python3 -m unittest discover -s tests` — **67 tests, all passing**
  (pacing math, card rendering, parsing, CLI behaviors, drafting with
  all network access mocked).
- `pyflakes lesson_builder tests` — no warnings; all sources compile.
- End-to-end runs verified manually:
  - text cards to stdout with graded pacing (starters first, API/
    automation topics in later sessions);
  - markdown plan to `--output` file;
  - drafting **off by default** (confirmed the drafting function is not
    called without `--draft`);
  - `--draft` against a fake OpenAI-compatible server: blurbs fetched
    and rendered into cards (mocked real HTTP server, locally spawned
    during manual verification only);
  - `--draft` against an unreachable endpoint: clear "Drafting
    unavailable" note, plan still complete, exit code 0;
  - error paths: missing file / empty input → exit code 2 with a
    friendly hint.

## Known gaps / next ideas

- Pacing tiers are English-keyword heuristics (no NLP); unusual wording
  just defaults to the middle tier.
- Card height is not yet fitted to exactly one physical page for very
  long topic lists (text is complete; a very packed card may take two
  printed pages).
- Drafting blurbs come back as plain lines; no streaming, no token
  limits beyond a 120-second timeout.
- Markdown mode carries the auto-suggested session minutes but no
  per-session "before you start" nudge; the text card carries the
  gentle framing.
- No `--stdin` flag name beyond the `-` convention; make that explicit
  in help copy if publishing further.
