#!/usr/bin/env python3
"""Stage 5 — the gates. Assemble a cue store into a final SRT only if
every gate passes; otherwise print the full problem list and write
nothing (unless --force).

Gates (pass/fail, never vibes):
  G1 at least one cue; starts monotonic
  G2 zero overlaps
  G3 every cue duration within [min-dur, max-dur]   (default 0.8–7.5 s)
  G4 at most max-lines lines per cue, each line <= max-chars (default 2 / 62)
  G5 first cue starts within first-window of 0      (default 2.0 s)
  G6 last cue ends within end-tol of the source track's final end
  G7 no banned name variant from the names pack appears anywhere

Also reports, for the job log: canonical-name counts in the output,
and a census of mangled variants in the OLD machine draft — the
before/after evidence that the name sweep actually did something.

Usage:
  python3 validate.py CUES.json --names names/pack.json \
      [--source SOURCE.srt] [--draft OLD.srt] [--out FINAL.srt] [--force]
  python3 validate.py --srt FINAL.srt --names names/pack.json [--source SOURCE.srt]
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srt_lib import parse_srt, write_srt


def load_names(path):
    with open(path, encoding='utf-8') as f:
        pack = json.load(f)
    banned, canonical = [], []
    for section in ('group', 'fandom'):
        node = pack.get(section) or {}
        if node.get('canonical'):
            canonical.append(node['canonical'])
        banned.extend(node.get('variants', []))
    for m in pack.get('members', []):
        if m.get('canonical'):
            canonical.append(m['canonical'])
        banned.extend(m.get('variants', []))
    banned.extend(pack.get('song_variants', []))
    return pack, canonical, [b for b in banned if b]


def validate_cues(cues, canonical=(), banned=(), source=None,
                  min_dur=0.8, max_dur=7.5, max_lines=2, max_chars=62,
                  first_window=2.0, end_tol=5.0):
    cues = sorted((list(c) for c in cues), key=lambda c: c[0])
    problems = []
    stats = {'cues': len(cues), 'max_dur': 0.0, 'max_line': 0,
             'first_start': None, 'last_end': None}
    if not cues:
        return ['G1: no cues'], stats
    stats['first_start'] = cues[0][0]
    stats['last_end'] = cues[-1][1]
    prev_end = -1.0
    for i, (s, e, txt) in enumerate(cues):
        dur = e - s
        stats['max_dur'] = max(stats['max_dur'], dur)
        if dur > max_dur:
            problems.append("G3 cue %d: duration %.2fs > %.1f  [%s]"
                            % (i, dur, max_dur, txt[:40]))
        if dur < min_dur:
            problems.append("G3 cue %d: duration %.2fs < %.1f  [%s]"
                            % (i, dur, min_dur, txt[:40]))
        if s < prev_end - 0.001:
            problems.append("G2 cue %d: overlap (start %.2f < prev end %.2f)"
                            % (i, s, prev_end))
        prev_end = max(prev_end, e)
        lines = txt.split('\n')
        if len(lines) > max_lines:
            problems.append("G4 cue %d: %d lines" % (i, len(lines)))
        for ln in lines:
            stats['max_line'] = max(stats['max_line'], len(ln))
            if len(ln) > max_chars:
                problems.append("G4 cue %d: line %d chars: %s"
                                % (i, len(ln), ln))
        for b in banned:
            if b in txt:
                problems.append("G7 cue %d: banned variant %r in: %s"
                                % (i, b, txt[:60]))
    if cues[0][0] > first_window:
        problems.append("G5: first cue starts at %.2fs (> %.1fs)"
                        % (cues[0][0], first_window))
    if source:
        delta = cues[-1][1] - source[-1][1]
        stats['end_delta'] = delta
        if abs(delta) > end_tol:
            problems.append("G6: last cue ends %.2fs vs source end %.2fs "
                            "(delta %.2fs > %.1fs)"
                            % (cues[-1][1], source[-1][1], delta, end_tol))
    stats['canonical_counts'] = {
        name: sum(c[2].count(name) for c in cues) for name in canonical}
    return problems, stats


def variant_census(text, banned):
    return {b: len(re.findall(re.escape(b), text))
            for b in banned if b in text}


def coverage_report(source, built, min_overlap_frac=0.5):
    """Checklist evidence: which source cues no built cue covers.
    A source cue counts as covered when built cues overlap at least
    min_overlap_frac of its duration (♪ cues count — covering an
    unrecoverable span with ♪ is a decision, not a skip)."""
    built = sorted((list(c) for c in built), key=lambda c: c[0])
    uncovered = []
    for idx, (s, e, _t) in enumerate(source):
        dur = max(e - s, 0.001)
        covered = 0.0
        for bs, be, _bt in built:
            if be <= s:
                continue
            if bs >= e:
                break
            covered += min(e, be) - max(s, bs)
        if covered / dur < min_overlap_frac:
            uncovered.append(idx)
    ranges = []
    for idx in uncovered:
        if ranges and idx == ranges[-1][1] + 1:
            ranges[-1][1] = idx
        else:
            ranges.append([idx, idx])
    return ranges


def print_report(problems, stats):
    print("cues: %s" % stats.get('cues'))
    if stats.get('first_start') is not None:
        print("span: %.2f -> %.2f" % (stats['first_start'], stats['last_end']))
    print("max duration: %.2fs | max line: %d chars"
          % (stats.get('max_dur', 0), stats.get('max_line', 0)))
    if 'end_delta' in stats:
        print("end delta vs source: %+.2fs" % stats['end_delta'])
    if stats.get('canonical_counts'):
        print("canonical name counts:",
              json.dumps(stats['canonical_counts'], ensure_ascii=False))
    print("problems: %d" % len(problems))
    for p in problems:
        print(" -", p)
    return not problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cues', nargs='?', help='cue store JSON (omit with --srt)')
    ap.add_argument('--srt', help='validate an existing SRT instead of a cue store')
    ap.add_argument('--names', help='names pack JSON')
    ap.add_argument('--source', help='source-language SRT (span gates)')
    ap.add_argument('--draft', help='old machine draft SRT (variant census)')
    ap.add_argument('--out', help='write assembled SRT here if gates pass')
    ap.add_argument('--force', action='store_true',
                    help='write --out even if gates fail (job log must say why)')
    ap.add_argument('--max-dur', type=float, default=7.5)
    ap.add_argument('--min-dur', type=float, default=0.8)
    ap.add_argument('--max-lines', type=int, default=2)
    ap.add_argument('--max-chars', type=int, default=62)
    a = ap.parse_args(argv)

    canonical, banned = [], []
    if a.names:
        _pack, canonical, banned = load_names(a.names)
    source = parse_srt(a.source) if a.source else None

    if a.srt:
        cues = parse_srt(a.srt)
    else:
        with open(a.cues, encoding='utf-8') as f:
            cues = json.load(f)
    cues = sorted(cues, key=lambda c: c[0])

    problems, stats = validate_cues(
        cues, canonical, banned, source,
        min_dur=a.min_dur, max_dur=a.max_dur,
        max_lines=a.max_lines, max_chars=a.max_chars)
    ok = print_report(problems, stats)

    if a.draft:
        old = open(a.draft, encoding='utf-8-sig').read()
        census = variant_census(old, banned)
        print("old-draft mangled variant census:",
              json.dumps(census, ensure_ascii=False))

    if a.out and (ok or a.force):
        write_srt(cues, a.out)
        print("WROTE", a.out)
    elif a.out:
        print("NOT WRITTEN — gates failed (see problems above)")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
