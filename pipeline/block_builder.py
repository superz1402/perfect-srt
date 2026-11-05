"""Stage 3 helper — the block builder.

The translation correction itself is agent judgment and is NOT
automated. What this module automates is the bookkeeping around it:
an agent writes one builder script per time block of the video,
authoring corrected cues as (time-span, text) pairs, where every
time-span comes from the source skeleton:

    from block_builder import BlockBuilder
    b = BlockBuilder('job/source.json', 'job/cues.json')
    b.add(b.R(0, 1),  "Their tremendous skill is already proven —\n"
                      "the most talented girl group out there.")
    b.add(b.R(24, 24), 'Give it up for "MOON"!')
    b.music(b.A(85.0, 92.0), '"MOON" — live')   # unrecoverable span -> ♪ cue
    b.save()   # appends this block's cues to the shared cue store

Rules the builder enforces mechanically:
  - R(i, j) returns (source[i].start, source[j].end); indices are
    checked, so a typo'd range fails loudly instead of drifting timing.
  - music() is the ONLY sanctioned way to cover a span whose words
    cannot be recovered from the source captions. Never invent lyrics
    or dialogue for such a span (see AGENTS.md, hard rules).
  - The cue store is a JSON list shared across block scripts; each
    block script appends its block and saves. Order does not matter —
    repair/assemble sort by start time.
"""
import json
import os


class BlockBuilder:
    def __init__(self, source_json, store_path):
        with open(source_json, encoding='utf-8') as f:
            self.source = json.load(f)
        self.store_path = store_path
        self.cues = []

    # -- time spans -------------------------------------------------
    def R(self, i, j):
        """(start of source cue i, end of source cue j)."""
        if not (0 <= i <= j < len(self.source)):
            raise IndexError("R(%d, %d) outside source 0..%d"
                             % (i, j, len(self.source) - 1))
        return (self.source[i][0], self.source[j][1])

    def A(self, s, e):
        """Absolute span in seconds — for ♪ coverage and clean air
        where no source cue boundary fits. Use sparingly; prefer R()."""
        if not (0 <= s < e):
            raise ValueError("bad absolute span %r-%r" % (s, e))
        return (s, e)

    # -- authoring --------------------------------------------------
    def add(self, span, text):
        s, e = span
        self.cues.append([float(s), float(e), text])
        return self

    def music(self, span, label=None):
        """Cover an unrecoverable span with a ♪ cue instead of
        invented words. label examples: '"MOON" — live', '(opening)'."""
        text = "♪ %s ♪" % label if label else "♪"
        return self.add(span, text)

    # -- persistence ------------------------------------------------
    def save(self):
        existing = []
        if os.path.exists(self.store_path):
            with open(self.store_path, encoding='utf-8') as f:
                existing = json.load(f)
        existing.extend(self.cues)
        existing.sort(key=lambda c: c[0])
        with open(self.store_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=1)
        n, self.cues = len(self.cues), []
        print("block saved: +%d cues (store total %d)" % (n, len(existing)))
