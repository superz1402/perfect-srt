#!/usr/bin/env python3
"""Stage 2 — timing-skeleton dump.

Writes the source-language track to:
  - a JSON cue list ([[start, end, text], ...]) that block builders load
  - a TSV index (idx <TAB> start <TAB> end <TAB> text) for eyeballing

Builders address exact source boundaries by index range:
R(i, j) = (source[i].start, source[j].end). Because rebuilt cues take
their times from this skeleton, the corrected track inherits source
timing exactly and is monotonic by construction.

Usage:
  python3 source_index.py SOURCE.srt --json-out source.json --index-out source_index.txt
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srt_lib import parse_srt


def dump(source_path, json_out, index_out):
    cues = parse_srt(source_path)
    with open(json_out, 'w', encoding='utf-8') as f:
        json.dump(cues, f, ensure_ascii=False)
    with open(index_out, 'w', encoding='utf-8') as f:
        for i, (s, e, t) in enumerate(cues):
            f.write("%d\t%.2f\t%.2f\t%s\n" % (i, s, e, t.replace('\n', ' ')))
    return cues


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', help='source-language SRT (timing truth)')
    ap.add_argument('--json-out', required=True)
    ap.add_argument('--index-out', required=True)
    a = ap.parse_args(argv)
    cues = dump(a.source, a.json_out, a.index_out)
    print("source cues: %d -> %s , %s" % (len(cues), a.json_out, a.index_out))


if __name__ == '__main__':
    main()
