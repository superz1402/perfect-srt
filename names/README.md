# Names packs

A names pack is the job's single source of truth for every proper
noun that must survive correction exactly: the artist/group, members,
fandom, song titles, organisations, shows. Machine drafts mangle
these more than any other content — in the reference job the group
name alone was mangled 19+ times, once into "a snake" — so the system
treats names as protected data, not as text.

`babymonster.json` in this folder is the reference pack. Copy its
shape for any other artist or show.

## Format

```json
{
  "pack_name": "babymonster",
  "version": 1,
  "group":   {"canonical": "BABYMONSTER", "variants": ["Baby Monster", "..."]},
  "fandom":  {"canonical": "MONSTIEZ",    "variants": ["Monstiez"]},
  "members": [
    {"canonical": "AHYEON", "variants": ["A-yeon", "Ayeon", "Ahyun"]},
    {"canonical": "RUKA",   "variants": ["Luca", "Leuka"]}
  ],
  "songs_title_case": ["You Deserve It", "SHEESH", "DRIP"],
  "song_variants": ["Devove"],
  "orgs_and_shows": ["YG Entertainment", "Cultwo Show"],
  "source_substitutions": [
    {"source": "베이비몬스터", "canonical": "BABYMONSTER"},
    {"source": "아연", "canonical": "AHYEON",
     "note": "ASR mishearing; verify context before applying"}
  ],
  "cautions": ["..."]
}
```

Field rules:

- **canonical** — the exact display form required in the output.
  Whatever capitalisation the canonical form uses *is* the house
  style (BABYMONSTER's members display in ALL CAPS; another artist's
  pack might use Title Case — the pack decides, the agent obeys).
- **variants** — literal wrong strings seen in machine drafts or
  source ASR. The validator **bans** every variant in the output
  (gate G7) and **counts** them in the old draft as before/after
  evidence. Keep variants distinctive: a variant that is a substring
  of an ordinary word will false-positive. When a mangle is too
  generic to ban safely, leave it out and fix it by eye in the block
  pass.
- **songs_title_case** — reference list for the block pass; song
  titles are written exactly as listed. **song_variants** are
  garbled title strings and are banned like name variants.
- **source_substitutions** — source-language strings that must be
  replaced by the canonical form *before* any translation step, so
  no translator (machine or model) ever gets the chance to mangle
  them. Include ASR mishearings of names — in the MBC Radio job the
  source ASR heard AHYEON's name as the Korean word for "zinc" 17
  times. Always attach a `note` when a substitution is
  context-dependent.
- **cautions** — known traps for this artist/show. Read them before
  the block pass. (Example from the reference pack's sibling job:
  a source substring that looks like a song title was actually a
  verb ending in every occurrence — blind substitution would have
  corrupted four good lines.)

## Authoring a pack for a new artist/show

1. Start from the official spellings: agency/label pages, official
   channel names, album tracklists. Canonical forms come from the
   artist's own sources, never from the machine draft.
2. Skim the machine draft once, harvesting every mangled rendering
   of every protected name into `variants`. Drafts are inventive;
   expect homophones, wrong people with similar names, and at least
   one absurd mistranslation.
3. Skim the source-language track for ASR mishearings of the names
   and add them to `source_substitutions` with context notes.
4. List every song title likely to be mentioned (full discography
   for an interview/performance show) in `songs_title_case`.
5. Run a job. Afterwards, fold any NEW mangles the validator census
   or your own reading surfaced back into the pack — packs are
   living files, versioned with the system.
