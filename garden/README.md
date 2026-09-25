# Garden

A writing workspace for discovery writers. You bring a scene; Claude writes it
in your voice, makes up the world as it goes, and remembers what it invented.

## How to use

Open Claude Code **inside this folder** (so it picks up `CLAUDE.md` and the
skills in `.claude/skills/`). Then just talk:

- **Give a beat** → *"A tax auditor finds out the dragon has been filing jointly."*
  Claude writes the scene, saves it to `scenes/`, and updates `ledger.md`.
- **Keep going** → *"next"* or *"continue"*.
- **Stuck** → *"I'm stuck"* / *"this is boring"*. You get three doors to pick
  from, then the scene gets written.
- **React** → *"this line is perfect"* or *"too wordy"*. Claude revises and
  records the lesson in `voice.md`, so the voice gets closer to yours over time.

## What's in here

| File | What it is | Who edits it |
|---|---|---|
| `voice.md` | Your style, plus what you liked and rejected | Claude, from your reactions (you can too) |
| `ledger.md` | Characters, places, world facts, open threads | Claude, after every scene |
| `scenes/` | The story, one file per scene | Claude writes, you can rewrite |
| `.claude/skills/seed` | Beat → scene | — |
| `.claude/skills/unstick` | Stuck → three doors → scene | — |

To use the skills in every project, copy the two folders in `.claude/skills/`
into `~/.claude/skills/`. They expect `voice.md` and `ledger.md` in whatever
folder you're writing in; copy those too.
