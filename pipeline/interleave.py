#!/usr/bin/env python3
"""Stage 1 — interleaved working view.

Parses the source-language SRT (timing truth) and the machine-target
SRT (flawed draft) and writes a time-sorted, interleaved reading table
so the correcting agent can read source and draft side by side, in
time order, in chunks small enough to work through.

This view is the agent's reading desk. The correction itself is agent
judgment; this tool only guarantees nothing is skipped silently:
every source cue and every draft cue appears exactly once.

Usage:
  python3 interleave.py SOURCE.srt DRAFT.srt --out-dir DIR [--rows 170]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srt_lib import parse_srt, mmss


def build_rows(source, draft):
    rows = []
    for s, e, t in source:
        rows.append((s, 0, "[%s-%s] SRC: %s" % (mmss(s), mmss(e), t.replace('\n', ' '))))
    for s, e, t in draft:
        rows.append((s, 1, "[%s-%s] DRF: %s" % (mmss(s), mmss(e), t.replace('\n', ' '))))
    rows.sort(key=lambda r: (r[0], r[1]))
    return [r[2] for r in rows]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', help='source-language SRT (timing truth)')
    ap.add_argument('draft', help='machine target-language SRT (flawed draft)')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--rows', type=int, default=170,
                    help='rows per part file (default 170)')
    a = ap.parse_args(argv)

    src = parse_srt(a.source)
    drf = parse_srt(a.draft)
    print("source cues: %d  span %.2f -> %.2f" % (len(src), src[0][0], src[-1][1]))
    print("draft  cues: %d  span %.2f -> %.2f" % (len(drf), drf[0][0], drf[-1][1]))
    same = sum(1 for x, y in zip(src, drf)
               if abs(x[0] - y[0]) < 0.05 and abs(x[1] - y[1]) < 0.05)
    print("index-aligned timings: %d of %d" % (same, min(len(src), len(drf))))

    rows = build_rows(src, drf)
    os.makedirs(a.out_dir, exist_ok=True)
    parts = (len(rows) + a.rows - 1) // a.rows
    for ci in range(0, len(rows), a.rows):
        with open(os.path.join(a.out_dir, 'part%02d.txt' % (ci // a.rows)),
                  'w', encoding='utf-8') as f:
            f.write('\n'.join(rows[ci:ci + a.rows]))
    print("rows: %d  parts: %d -> %s" % (len(rows), parts, a.out_dir))


if __name__ == '__main__':
    main()
