#!/usr/bin/env python3
"""perfect-srt — CLI driver for the mechanical stages of a subtitle
correction job. The correction itself (stage 3) is agent judgment;
this driver runs everything around it and keeps the job auditable.

Job workdir layout (created by `init`):
  job.json          manifest: input paths, names pack, created-at
  source.json       source-language cues (the timing skeleton)
  source_index.txt  idx / start / end / text, for eyeballing ranges
  interleave/       partNN.txt — source+draft interleaved reading view
  cues.json         the corrected cue store (block builders append here)
  report.txt        last validation report

Commands:
  init      JOBDIR --source SRC.srt --draft DRF.srt [--names PACK.json]
  checklist JOBDIR            coverage: source ranges with no built cue
  repair    JOBDIR            mechanical split/trim pass on cues.json
  assemble  JOBDIR --out FINAL.srt [--force]   gates + write + report
  validate  --srt FINAL.srt [--names PACK.json] [--source SRC.srt]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import interleave as interleave_mod
import source_index as source_index_mod
import repair as repair_mod
import validate as validate_mod
from srt_lib import parse_srt


def _manifest(jobdir):
    with open(os.path.join(jobdir, 'job.json'), encoding='utf-8') as f:
        return json.load(f)


def cmd_init(a):
    os.makedirs(a.jobdir, exist_ok=True)
    src_json = os.path.join(a.jobdir, 'source.json')
    src_idx = os.path.join(a.jobdir, 'source_index.txt')
    source_index_mod.dump(a.source, src_json, src_idx)
    interleave_mod.main([a.source, a.draft, '--out-dir',
                         os.path.join(a.jobdir, 'interleave')])
    cues_path = os.path.join(a.jobdir, 'cues.json')
    if not os.path.exists(cues_path):
        with open(cues_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
    manifest = {
        'source_srt': os.path.abspath(a.source),
        'draft_srt': os.path.abspath(a.draft),
        'names_pack': os.path.abspath(a.names) if a.names else None,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'stage': 'prepared — stage 3 (block building) is next',
    }
    with open(os.path.join(a.jobdir, 'job.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print("job initialised:", a.jobdir)
    print("next: read interleave/part*.txt, write block builders against "
          "source.json, append corrected cues to cues.json")


def cmd_checklist(a):
    man = _manifest(a.jobdir)
    with open(os.path.join(a.jobdir, 'source.json'), encoding='utf-8') as f:
        source = json.load(f)
    with open(os.path.join(a.jobdir, 'cues.json'), encoding='utf-8') as f:
        built = json.load(f)
    ranges = validate_mod.coverage_report(source, built)
    print("source cues: %d | built cues: %d" % (len(source), len(built)))
    if built:
        built_sorted = sorted(built, key=lambda c: c[0])
        print("built span: %.2f -> %.2f (source ends %.2f)"
              % (built_sorted[0][0], built_sorted[-1][1], source[-1][1]))
    if not ranges:
        print("coverage: COMPLETE — every source cue is covered "
              "(dialogue or a deliberate ♪ cue)")
    else:
        print("coverage: %d uncovered source range(s):" % len(ranges))
        for i, j in ranges:
            print("  source idx %d-%d  (%.2fs -> %.2fs)  first text: %s"
                  % (i, j, source[i][0], source[j][1], source[i][2][:60]))
    if man.get('names_pack'):
        print("names pack:", man['names_pack'])


def cmd_repair(a):
    cues_path = os.path.join(a.jobdir, 'cues.json')
    with open(cues_path, encoding='utf-8') as f:
        cues = json.load(f)
    cues, trimmed, splits = repair_mod.repair(cues)
    with open(cues_path, 'w', encoding='utf-8') as f:
        json.dump(cues, f, ensure_ascii=False, indent=1)
    print("repaired: %d cues (%d overlaps trimmed, %d splits)"
          % (len(cues), trimmed, splits))


def cmd_assemble(a):
    man = _manifest(a.jobdir)
    with open(os.path.join(a.jobdir, 'cues.json'), encoding='utf-8') as f:
        cues = json.load(f)
    canonical, banned = [], []
    names = a.names or man.get('names_pack')
    if names:
        _p, canonical, banned = validate_mod.load_names(names)
    source = None
    if man.get('source_srt') and os.path.exists(man['source_srt']):
        source = parse_srt(man['source_srt'])
    problems, stats = validate_mod.validate_cues(cues, canonical, banned, source)
    lines = []
    import io
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    ok = validate_mod.print_report(problems, stats)
    if man.get('draft_srt') and os.path.exists(man['draft_srt']):
        old_text = open(man['draft_srt'], encoding='utf-8-sig').read()
        census = validate_mod.variant_census(old_text, banned)
        print("old-draft mangled variant census:",
              json.dumps(census, ensure_ascii=False))
    sys.stdout = old
    report = buf.getvalue()
    print(report, end='')
    with open(os.path.join(a.jobdir, 'report.txt'), 'w', encoding='utf-8') as f:
        f.write(report)
    if ok or a.force:
        from srt_lib import write_srt
        write_srt(sorted(cues, key=lambda c: c[0]), a.out)
        print("WROTE", a.out)
    else:
        print("NOT WRITTEN — gates failed")
    return 0 if ok else 1


def cmd_validate(a):
    return validate_mod.main(['--srt', a.srt] +
                             (['--names', a.names] if a.names else []) +
                             (['--source', a.source] if a.source else []))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('init')
    p.add_argument('jobdir')
    p.add_argument('--source', required=True)
    p.add_argument('--draft', required=True)
    p.add_argument('--names')
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser('checklist')
    p.add_argument('jobdir')
    p.set_defaults(fn=cmd_checklist)

    p = sub.add_parser('repair')
    p.add_argument('jobdir')
    p.set_defaults(fn=cmd_repair)

    p = sub.add_parser('assemble')
    p.add_argument('jobdir')
    p.add_argument('--out', required=True)
    p.add_argument('--names')
    p.add_argument('--force', action='store_true')
    p.set_defaults(fn=cmd_assemble)

    p = sub.add_parser('validate')
    p.add_argument('--srt', required=True)
    p.add_argument('--names')
    p.add_argument('--source')
    p.set_defaults(fn=cmd_validate)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == '__main__':
    sys.exit(main())
