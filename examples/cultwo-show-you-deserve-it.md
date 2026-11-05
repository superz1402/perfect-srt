# Case note — BABYMONSTER, Cultwo Show ("You Deserve It")

**Job:** English subtitles for BABYMONSTER's Cultwo Show appearance
(SBS PowerFM, 2026-11-05), 36 min 48 s of radio talk plus two live
performances.
**Inputs:** Korean auto-generated caption SRT (timing source) + a
machine-generated English SRT (the draft to correct).
**Output:** `BABYMONSTER-You-Deserve-It-EN.srt` in this folder.
**Names pack:** `../names/babymonster.json`.

## What the machine draft got wrong

- **The group name, constantly.** 19+ mangles of BABYMONSTER in one
  draft — "Baby Monster", "Beckmon", "Baekmon", "Bammon", "BB bus
  line" — including one passage where the group was introduced as
  **"a snake"**. A viewer relying on the draft would not know who
  was on the show.
- **Member names.** RUKA appeared as "Luca" and "Leuka", RORA as
  "Laura" and "Lola", PHARITA as "Parita" and "Barita", CHIQUITA as
  "Chikita"/"Chikida", AHYEON as "A-yeon"/"Ayeon".
- **Song titles garbled** — romanised fragments and near-words in
  place of the actual titles ("MOON", "You Deserve It", "SHEESH",
  "PSYCHO", "HOT SAUCE" all took damage).
- **Dropped negations and flipped meanings** in the talk segments —
  the classic machine-translation failure: sentences that read
  smoothly and say the opposite of what was said. Only a
  line-by-line pass against the Korean catches these; no spellcheck
  ever will.

## How the system fixed it

1. **Timing from the Korean skeleton only.** Every corrected cue
   takes its start/end from source-cue index ranges, so the output
   inherits broadcast timing exactly and cannot drift.
2. **Interleaved reading pass.** Source and draft read side by side
   in time order, in ~6 blocks across the runtime; each block's
   corrected cues were authored against the Korean, with the draft
   treated as a hint, never as text to keep.
3. **Names applied from the pack, then proven.** Canonical forms
   written throughout; the validator then banned every known
   variant (gate G7) and counted the variants in the old draft as
   the before/after record.
4. **Mechanical repair, then gates.** Splitter pass for over-long
   cues, then full validation before the file was written.

## The two unrecoverable spans — and the ♪ rule

Twice, the source captions themselves could not support a faithful
translation:

1. **The opening live performance of "MOON"** — the source lyric
   captions for the performance are garbled beyond recovery.
2. **The bridge of the "You Deserve It" live** — same failure;
   the recoverable lyric lines around it were translated and kept.

In both spans the system wrote **♪ cues** (one labelled
`♪ "MOON" — live ♪`) instead of inventing words. This is a hard
rule, not a style choice: **a subtitle track may be silent about
what was sung; it may never put words in a performer's mouth that
the source cannot support.** 36 cues in the finished file carry ♪
markers (performances, applause, music beds).

## Validation summary (shipped file)

| Gate | Result |
|---|---|
| Cues | 472 |
| Overlaps | 0 |
| Cue durations | 0.8–7.5 s (max 7.50 s) |
| Longest line | 54 chars (limit 62) |
| Lines per cue | ≤ 2 |
| Span | 0.50 s → 36:47.60 — last cue ends exactly at the source track's final end |
| Banned name variants in output | 0 |
| Coverage | every source range covered — dialogue or a deliberate ♪ cue |
