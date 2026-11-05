#!/usr/bin/env python3
"""Stage 4 — mechanical repair of the built cue store.

Does only what needs no judgment:
  1. Sorts cues by start time.
  2. Trims micro-overlaps: if a cue starts before the previous cue
     ends, the previous cue's end is pulled back to the next start —
     but only when the trimmed cue still meets the minimum duration.
     Anything it cannot fix safely is left for the validator to fail.
  3. Splits any cue longer than --max-dur or with more than
     --max-lines lines at the most balanced line/sentence break,
     splitting time in proportion to text length. ♪ music cues are
     split by time with the same text.

It never rewrites wording. If a cue cannot be split into legal
pieces it is left untouched and validation will report it.

Usage:
  python3 repair.py CUES.json [--max-dur 7.5] [--max-lines 2] [--min-dur 0.8]
"""
import argparse
import json
import re


def is_music(txt):
    return txt.startswith('♪') or txt.strip() in ('(applause)',)


def split_once(cue, max_lines, min_dur):
    s, e, txt = cue
    dur = e - s
    if is_music(txt):
        mid = (s + e) / 2
        second = '♪ ♪' if txt.startswith('♪') else txt
        return [[s, mid, txt], [mid, e, second]]
    lines = txt.split('\n')
    if len(lines) >= 2:
        best = None
        for k in range(1, len(lines)):
            a = '\n'.join(lines[:k])
            b = '\n'.join(lines[k:])
            if len(a.split('\n')) <= max_lines and len(b.split('\n')) <= max_lines:
                bal = abs(len(a) - len(b))
                if best is None or bal < best[0]:
                    best = (bal, a, b)
        if best:
            _, a, b = best
            frac = len(a) / float(len(a) + len(b))
            mid = min(max(s + dur * frac, s + min_dur + 0.1), e - min_dur - 0.1)
            if s + min_dur <= mid <= e - min_dur:
                return [[s, mid, a], [mid, e, b]]
    t = lines[0]
    m = len(t) // 2
    cands = [mm.start() + 1 for mm in re.finditer(r'[.,;:—-] ', t)] + \
            [i for i, ch in enumerate(t) if ch == ' ']
    if not cands:
        return [cue]
    pos = min(cands, key=lambda p: abs(p - m))
    a, b = t[:pos].strip(), t[pos:].strip()
    if not a or not b:
        return [cue]
    frac = len(a) / float(len(t))
    mid = min(max(s + dur * frac, s + min_dur + 0.1), e - min_dur - 0.1)
    if not (s + min_dur <= mid <= e - min_dur):
        return [cue]
    return [[s, mid, a], [mid, e, b]]


def repair(cues, max_dur=7.5, max_lines=2, min_dur=0.8):
    cues = sorted((list(c) for c in cues), key=lambda c: c[0])
    trimmed = 0
    for i in range(len(cues) - 1):
        cur, nxt = cues[i], cues[i + 1]
        if nxt[0] < cur[1] and nxt[0] - cur[0] >= min_dur:
            cur[1] = nxt[0]
            trimmed += 1
    changed = True
    splits = 0
    while changed:
        changed = False
        new = []
        for cue in cues:
            if (cue[1] - cue[0]) > max_dur or len(cue[2].split('\n')) > max_lines:
                parts = split_once(cue, max_lines, min_dur)
                if len(parts) > 1:
                    changed = True
                    splits += 1
                new.extend(parts)
            else:
                new.append(cue)
        cues = new
    cues.sort(key=lambda c: c[0])
    return cues, trimmed, splits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cues', help='cue store JSON to repair in place')
    ap.add_argument('--max-dur', type=float, default=7.5)
    ap.add_argument('--max-lines', type=int, default=2)
    ap.add_argument('--min-dur', type=float, default=0.8)
    a = ap.parse_args(argv)
    with open(a.cues, encoding='utf-8') as f:
        cues = json.load(f)
    cues, trimmed, splits = repair(cues, a.max_dur, a.max_lines, a.min_dur)
    with open(a.cues, 'w', encoding='utf-8') as f:
        json.dump(cues, f, ensure_ascii=False, indent=1)
    print("repaired: %d cues (%d overlaps trimmed, %d splits)"
          % (len(cues), trimmed, splits))


if __name__ == '__main__':
    main()
