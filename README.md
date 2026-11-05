# lesson-builder

An offline CLI that turns a simple bullet list of what a beginner should
learn into a friendly lesson plan: sessions paced from gentle starters to
bigger stretches, printable one-page lesson cards, a supply list per
session, and progress checkboxes you can actually tick with a pen.

Built the way a friend would explain it: plain English, step by step,
never condescending.

## Who it is for

Anyone teaching themselves (or someone else) something new — including
the beginner-friendly AI education tools published by **Asdale
Dynamics, LLC**, the company behind *The Massive AI Manual* by Dylan
Asdale. It is deliberately distinct from broader workshop guides: this is
a small, local, private tool for turning "what should I learn?" into
"here is what we do this week."

## Features

- **Graded pacing across sessions** — the tool sorts your bullet topics
  into friendly starters, everyday ideas, and bigger stretches, then
  spreads them across sessions so early sessions feel easy and later
  ones carry more weight.
- **Printable one-page lesson cards** — a fixed-width text card per
  session with the checklist, supplies, and a gentle "before you start"
  nudge. Print with `lp card.txt` or a plain `lpr`.
- **Supply list per session** — sensible defaults (notebook, pen, a
  snack) plus smart hints from your topics (computer, printer, etc.)
  and any extras you pass with `--supplies`.
- **Progress checkboxes** — every topic is a `[ ]` you can tick off,
  on paper or in Markdown.
- **Optional drafting help (off by default)** — with `--draft`, the CLI
  asks an OpenAI-compatible chat endpoint (local Ollama by default) for
  short "first things first" blurbs and tucks them into the cards.
  Without that flag, nothing ever touches the network. No API keys are
  stored or looked up in files; pass `--api-key` only if your endpoint
  requires one.

## Install

No dependencies. Python 3.8+.

```bash
# from this folder
python3 -m lesson_builder --help
# or install the script
pip install .
lesson-builder --help
```

## Usage

Start from an ordinary bullet list, one topic per line (`sample-topics.txt`
is included):

```
- what is AI (in plain words)
- getting started with a chat assistant
- asking better questions (prompts)
...
```

Then:

```bash
# auto-paced plan (sessions suggested from ~45 minutes per session)
python3 -m lesson_builder sample-topics.txt

# exactly 3 sessions, markdown checkboxes, written to a file
python3 -m lesson_builder sample-topics.txt --sessions 3 \
  --title "AI for Beginners, Week by Week" \
  --format markdown --output plan.md

# extra supplies in every card, topic cap per session
python3 -m lesson_builder topics.txt --supplies "Tea,Sticky notes" --max-topics 4
```

### Optional drafting help (off by default)

```bash
# local Ollama with some small model — no key needed
pip install ollama  # or: ollama pull llama3.2
python3 -m lesson_builder topics.txt --draft --model llama3.2

# any other OpenAI-compatible endpoint
python3 -m lesson_builder topics.txt --draft \
  --api-base https://example.internal/v1 --model my-model --api-key "$MY_KEY"
```

If the endpoint is unreachable, drafting steps aside with a friendly
note and your lesson plan is still complete — pacing, cards, supplies,
and checkboxes are always computed locally.

## Output formats

- `--format text` (default): bordered one-page cards, printed region
  width 74 characters, with checkboxes and supplies.
- `--format markdown`: headings per session, `- [ ]` checkboxes, supply
  bullets — handy for note apps that support checklists.

## How pacing works (short version)

Every topic gets a rough time weight: friendly starters ~20 min,
everyday ideas ~30 min, bigger stretches ~45 min (guessed from your
wording — "what is…" vs "advanced/deploy/automate…"). Sessions are
filled in order to a near-equal minute budget, gentle topics first, so
the plan stays encouraging instead of front-loading the hard stuff.

## Developing

```bash
python3 -m unittest discover -s tests   # 67 tests, all offline
```

There are no runtime dependencies, so tests run anywhere Python runs.

## License & credits

MIT — see `LICENSE` (Copyright (c) 2026 Asdale Dynamics, LLC).
Made with care by **Asdale Dynamics, LLC** — Dylan Asdale's beginner-first
AI education company. Presented plainly and warmly, like the book does.
