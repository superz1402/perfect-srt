# perfect-srt

A system for turning a **source-language auto-caption SRT** plus a
**machine-generated target-language SRT** into a corrected,
broadcast-quality subtitle file — with the names right, the timing
exact, and every fix verified by gates instead of vibes.

Built for fan-subtitle work on Korean broadcast content (radio and
music shows), where machine drafts reliably mangle artist names,
drop negations, and garble song lyrics — and where a wrong name in
a subtitle is the one error the audience never forgives.

## The core idea

Machine translation of captions fails in predictable places:
proper nouns, negations, idioms, lyrics. A general "fix the file"
pass misses them because the wrong text reads smoothly. This system
instead rebuilds the track under three disciplines:

1. **The source-language track is the skeleton of truth.** Its cue
   timings are inherited exactly, by index range — never re-timed,
   never trusted to the draft.
2. **Names are protected data.** A per-artist *names pack* fixes
   canonical spellings and every known mangled variant. Variants
   are banned from the output by a validator gate and counted in
   the old draft as before/after evidence.
3. **Nothing is invented.** Where the source captions cannot
   support a faithful translation (garbled live lyrics, chanting,
   noise), the span is covered with a **♪ cue** — silence about the
   words, never fabricated words.

## Pipeline

| Stage | Tool | What happens |
|---|---|---|
| 0. Acquire | — | Get the **source-language** caption track and a machine draft in the target language (see *Getting inputs*). |
| 1. Prepare | `perfect_srt.py init` | Parse both SRTs; dump the timing skeleton; write the interleaved source+draft reading view. |
| 2. Build | agent + `pipeline/block_builder.py` | The correction itself: the agent reads the interleaved view block by block and authors corrected cues against the source, referencing skeleton index ranges. Unrecoverable spans get ♪ cues. |
| 3. Checklist | `perfect_srt.py checklist` | Coverage proof: every source cue is covered by a built cue (dialogue or deliberate ♪). Nothing skipped silently. |
| 4. Repair | `perfect_srt.py repair` | Mechanical only: sort, trim micro-overlaps, split over-long/over-line cues at balanced breaks. Never rewrites wording. |
| 5. Assemble + validate | `perfect_srt.py assemble` | Runs all gates; writes the final SRT **only if every gate passes**; saves the validation report into the job folder. |

Stages 1, 3, 4, 5 are fully mechanical. Stage 2 is agent judgment —
deliberately. The tooling's job there is to make the judgment
complete (interleaved view, coverage checklist) and checkable
(gates), not to pretend a script can translate.

## Running a job end-to-end

```bash
# inputs: SOURCE.srt (timing truth), DRAFT.srt (machine target draft),
#         a names pack (see names/)
python3 pipeline/perfect_srt.py init job/ \
    --source SOURCE.srt --draft DRAFT.srt --names names/babymonster.json

# stage 2 (agent): read job/interleave/part*.txt; write one builder
# script per time block against job/source.json, appending corrected
# cues to job/cues.json — helper: pipeline/block_builder.py

python3 pipeline/perfect_srt.py checklist job/   # coverage proof
python3 pipeline/perfect_srt.py repair job/      # mechanical splits
python3 pipeline/perfect_srt.py assemble job/ --out FINAL.srt
```

Any existing SRT can also be gated on its own:

```bash
python3 pipeline/perfect_srt.py validate --srt FINAL.srt \
    --names names/babymonster.json --source SOURCE.srt
```

## Quality gates (pass/fail)

- **G1** cues exist, starts monotonic
- **G2** zero overlaps
- **G3** every cue 0.8–7.5 s
- **G4** ≤ 2 lines per cue, ≤ 62 chars per line
- **G5** first cue starts within 2 s of zero
- **G6** last cue ends at the source track's final end (±5 s)
- **G7** zero banned name variants from the names pack

The assembler writes nothing when a gate fails (a `--force` exists
for emergencies and must be justified in the job log). The
validation report — cue count, span, max duration, max line,
canonical-name counts, and the old draft's mangled-variant census —
is the job's receipt.

## Getting inputs

- Fetch the **source-language** caption track itself. Do **not**
  build on a platform's auto-translate caption endpoint: it
  rate-limits hard from datacenter IPs and its output is exactly
  the class of draft this system exists to correct.
- A machine draft in the target language is a *hint layer* — useful
  for spotting what the source means at a glance, never text to
  keep. If none exists, the block pass works from the source alone;
  if you generate one, apply the names pack's
  `source_substitutions` to the source text **before** translating,
  so names reach the translator already correct.

## Repository layout

```
AGENTS.md          the operator contract — read this first
pipeline/          the tools (srt_lib, interleave, source_index,
                   block_builder, repair, validate, perfect_srt CLI)
names/             names packs + how to author one (babymonster.json
                   is the reference pack)
examples/          a complete worked job: case note + shipped SRT
```

See `examples/cultwo-show-you-deserve-it.md` for a real job: what
the machine draft got wrong (19+ group-name mangles, one "a snake"),
how the system fixed it, and the two lyric spans where the ♪ rule
applied.

---

## Project status

**Completed project** — verified in the portfolio audit of **7 November 2026** (README, codebase and project state reviewed).

_Last verified: 7 November 2026_
