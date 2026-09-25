---
name: seed
description: Write a fiction scene from the author's story beat, in their voice, without making them plan. Use whenever the author gives a scene idea, a moment, a premise, a "what if", a line of dialogue to build around, or says "write", "next scene", "keep going", "continue", or "what happens when…". Also use when they give feedback on a scene and want it revised.
---

# Seed: beat → scene

The author is a gardener. They bring a beat (often just one image or moment)
and want to see it become prose *now*. Momentum is the whole job. Anything that
feels like homework kills the idea.

## Before writing

1. Read `voice.md` (the Keepers and Misses first; they outrank the general rules).
2. Read `ledger.md` and the latest scene in `scenes/` if they exist, so names,
   facts, and running jokes stay consistent.
3. Don't ask anything. Pick a sensible reading of the beat and go.
   - The one exception: the beat can be read in two ways that would produce
     *completely different scenes* (e.g. it's unclear who the main character is
     and it changes everything). Then ask one short either/or question. Never
     ask about the world, the backstory, or what happens later.

## Writing the scene

- Build around the beat. The beat is the heart of the scene: get to it
  quickly, give it room, and leave soon after.
- Default length: about 800–1,500 words. Shorter if the beat is a single
  moment. Follow the author's lead if they ask for more or less.
- Follow `voice.md`: mostly dialogue and inner voice, description only when it
  does a job, comic and absurd until the scene needs weight.
- **Invent the world through people.** When the scene needs a fact (a place, a
  rule, a job, a history), a character states it sideways while wanting
  something else. Prefer specific, strange, lived-in details over generic ones.
  Everything invented this way is provisional.
- Plant one small thing that could come back later (an object, a grudge, an
  unexplained remark). Don't point at it.
- Don't resolve more than the beat asked for. Leave the story open.
- Honor settled (`✓`) facts in the ledger. Provisional (`~`) facts can be bent
  if the scene is better for it; update the ledger to match.

## After the scene

Print the scene with no preamble. Then, under a `---`, add **garden notes**:
three short lines at most.

- **Invented:** the new facts the world gained, as a comma list.
- **Planted:** the thing that could come back.
- **Next?** one possible next beat, one line, offered not asked.

No questions, no "let me know what you think", no analysis of the scene.

Then, without asking:

1. Save the scene to `scenes/NNN-slug.md` (next number, 3 digits, short slug).
   Start the file with `# NNN — Title`.
2. Update `ledger.md`: new characters, places, facts (`~`), running jokes, open
   threads, and one line in the scene log. When the author has used or
   confirmed a provisional fact, mark it `✓`. Keep every entry to one line.

## Continuing and revising

- "Keep going" / "continue" / "next" with no beat → write the next scene,
  taking the most interesting open thread or the last scene's momentum.
- A new beat that contradicts an earlier provisional fact → the new beat wins;
  fix the ledger quietly. Contradicting a settled fact → write it anyway and
  mention the conflict in one line in the garden notes.
- Feedback on a scene → revise only what the feedback touches, overwrite the
  scene file, and log the lesson in `voice.md` (Keepers or Misses) per the
  rules in `CLAUDE.md`.
- If the author writes a passage themselves, keep it word for word and write
  around it.
