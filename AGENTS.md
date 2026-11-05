# AGENTS.md — perfect-srt operator contract

## Mission

Take a source-language auto-caption SRT and a machine-generated
target-language SRT, and ship a corrected target-language SRT whose
timing is exact, whose names are right, and whose every line the
source can support. Any agent following this file alone must be
able to run a job end-to-end without asking the owner anything.

## The contract

- You are the editor, not a filter. The machine draft is a hint
  layer; the source track is the text of record.
- You report results with the validation report, not with
  impressions. A job is done when the gates say so (see
  *Definition of done*).
- You never ship a file the gates rejected. `--force` exists for
  genuine emergencies and its use must be justified in the job log.

## Hard rules

1. **Source timing is the skeleton of truth.** Every corrected cue
   takes its start/end from source-cue index ranges
   (`R(i, j)` in `pipeline/block_builder.py`). Never re-time from
   the draft; never hand-type timestamps you could have taken from
   the skeleton.
2. **Never invent words.** If a span's words cannot be recovered
   from the source captions — garbled live lyrics, chanting,
   overlapping speech, pure noise — cover the span with a ♪ cue
   (labelled when the content is known, e.g. `♪ "MOON" — live ♪`).
   A track may be silent about what was sung; it may never put
   words in a performer's mouth that the source cannot support.
3. **Names come from the names pack, exactly.** Canonical forms as
   written in the pack (capitalisation included — it is the house
   style). Apply `source_substitutions` to source text before any
   translation step. Every known variant is banned from the output;
   the variant sweep is counted and reported, never eyeballed.
4. **Negations and subjects are guilty until proven innocent.**
   Machine drafts drop negations and flip speakers while reading
   smoothly. Check them against the source line by line,
   especially in fast talk segments.
5. **Gates are pass/fail, never vibes.** "Looks clean" is not a
   result. The assemble stage's report is the only acceptance
   evidence.
6. **Copyright discipline.** Do not commit the input caption files
   (broadcast captions) to this repository. The finished,
   corrected SRT of a worked example may be committed, as in
   `examples/`.

## Pipeline stages

0. **Acquire** — source-language SRT + machine target draft.
   Fetch the source track itself; never depend on a platform
   auto-translate endpoint for the draft of record (see README,
   *Getting inputs*).
1. **Prepare** — `perfect_srt.py init JOBDIR --source … --draft …
   --names …`. Produces the timing skeleton (`source.json`,
   `source_index.txt`) and the interleaved reading view
   (`interleave/part*.txt`).
2. **Build** — you, with `pipeline/block_builder.py`. Read the
   interleaved view in time order; author one builder script per
   time block; every cue's span comes from `R(i, j)` (or `A(s, e)`
   for ♪ coverage); unrecoverable spans get `music()`. Append each
   block to `cues.json`.
3. **Checklist** — `perfect_srt.py checklist JOBDIR`. Every source
   cue must be covered by a built cue — dialogue or a deliberate
   ♪. An uncovered range is unfinished work, not a rounding error.
4. **Repair** — `perfect_srt.py repair JOBDIR`. Mechanical only:
   sort, trim micro-overlaps, split over-long cues. If repair
   cannot fix something without changing words, it leaves it —
   the validator will name it and you fix it in the builder.
5. **Assemble + validate** — `perfect_srt.py assemble JOBDIR --out
   FINAL.srt`. Writes the SRT only if all gates pass; saves
   `report.txt` in the job folder.

## Quality gates

| Gate | Rule | Default |
|---|---|---|
| G1 | cues exist; starts monotonic | — |
| G2 | overlaps | 0 |
| G3 | cue duration | 0.8–7.5 s |
| G4 | lines per cue / chars per line | ≤ 2 / ≤ 62 |
| G5 | first cue start | ≤ 2.0 s |
| G6 | last cue end vs source final end | within 5 s |
| G7 | banned name variants in output | 0 |

Thresholds are CLI parameters, not constants — tighten them per
job if the delivery spec demands it, and record what you used.

## Definition of done

- [ ] Checklist reports **coverage complete**.
- [ ] Assemble passes **all gates** and writes the SRT.
- [ ] `report.txt` shows: 0 problems, canonical-name counts sane
      for the runtime, and the old draft's variant census recorded
      (the before-picture).
- [ ] Any ♪-covered span is a genuine unrecoverable span, listed
      in the job log with its time range and reason.
- [ ] Any new name mangles discovered during the job are folded
      back into the names pack.

## State

- Reference job: `examples/cultwo-show-you-deserve-it.md`
  (BABYMONSTER, Cultwo Show — 472 cues, all gates green).
- Names packs: `names/babymonster.json` (reference). Packs are
  living files; see `names/README.md` to author one.
