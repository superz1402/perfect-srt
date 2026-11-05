"""Shared SRT parsing/formatting for the perfect-srt pipeline.

A cue everywhere in this system is a plain list: [start, end, text]
with start/end in float seconds and text possibly containing '\n'
for a second line. Cue stores on disk are JSON lists of these.
"""
import re

_TS_RE = re.compile(
    r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)')


def parse_srt(path):
    """Parse an SRT file into [[start, end, text], ...] sorted by start."""
    txt = open(path, encoding='utf-8-sig').read().replace('\r\n', '\n')
    cues = []
    for block in re.split(r'\n\s*\n', txt.strip()):
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        m = _TS_RE.match(lines[1])
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append([s, e, '\n'.join(lines[2:]) if lines[2:] else ''])
    cues.sort(key=lambda c: c[0])
    return cues


def fmt_ts(t):
    """Float seconds -> 'HH:MM:SS,mmm'."""
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def mmss(t):
    return "%02d:%02d" % (int(t // 60), int(t % 60))


def write_srt(cues, path):
    with open(path, 'w', encoding='utf-8') as f:
        for i, (s, e, txt) in enumerate(cues, 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, fmt_ts(s), fmt_ts(e), txt))
