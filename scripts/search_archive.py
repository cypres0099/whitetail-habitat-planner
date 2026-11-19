#!/usr/bin/env python3
"""Find attributable passages in the local library, or publisher links in a shared skill checkout."""
import argparse
import csv
from collections import defaultdict
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
STAMP = re.compile(r"^(\d\d:\d\d:\d\d)\s+")
WORDS = re.compile(r"[a-z0-9]+")
PLATFORMS = ("YouTube", "Podcast", "Facebook", "Instagram", "TikTok")


def tokens(text):
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return WORDS.findall(plain)


def cues(text):
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = STAMP.match(line)
        start = m[1] if m else None
        words = line[m.end() if m else 0:].split()
        # Some platforms supply only one untimed paragraph. Keep windows comparable.
        for i in range(0, len(words), 36):
            yield start, words[i:i + 36]


def passages(text):
    lines = list(cues(text))
    for i, (stamp, words) in enumerate(lines):
        chunk = list(words)
        for offset in range(1, 7):
            if len(chunk) >= 40 or i + offset >= len(lines):
                break
            chunk.extend(lines[i + offset][1])
        yield stamp, " ".join(chunk)


def relevance(query, text):
    words = tokens(text)
    needed = set(query)
    if not needed.issubset(words):
        return 0
    phrase = " " + " ".join(query) + " "
    exact = phrase in (" " + " ".join(words) + " ")
    return (50 if exact else 15) + len(needed) + min(5, sum(w in needed for w in words)) + 1 / max(1, len(words))


def citation(row, stamp):
    url = row.get("url") or row["source_url"]
    if row["platform"] == "YouTube" and stamp:
        h, m, s = map(int, stamp.split(":"))
        return f"{url}&t={3600*h+60*m+s}s"
    return url


def matches(rows, query, library, args):
    public_cues = defaultdict(list)
    if not library:
        with (SKILL / "references" / "topic-cues.csv").open(encoding="utf-8", newline="") as file:
            for cue in csv.DictReader(file):
                public_cues[(cue["platform"], cue["id"])].append(cue)
    results = []
    for row in rows:
        if args.platform and row["platform"] != args.platform:
            continue
        if args.id and row["id"] != args.id:
            continue
        title = row.get("title") or row.get("title_or_caption", "")
        metadata = " ".join([title, row["publisher"], row.get("kind") or row.get("record_type", "")])
        weight = relevance(query, metadata)
        best = None
        if library and row.get("transcript"):
            p = (library / row["transcript"]).resolve()
            if p.is_relative_to((library / "transcripts").resolve()) and p.is_file():
                for stamp, text in passages(p.read_text(encoding="utf-8")):
                    score = relevance(query, text)
                    if score and (best is None or score > best[0]):
                        best = score, stamp, text
        cue = None
        cue_score = 0
        for item in public_cues[(row["platform"], row["id"])]:
            score = relevance(query, item["matched_term"] + " " + item["topic"])
            if score > cue_score:
                cue, cue_score = item, score
        if best is None and not weight and cue is None:
            continue
        score, stamp, excerpt = best or (weight, None, None)
        match_type = "speech" if best else "metadata"
        if cue and cue_score >= weight:
            score, stamp, match_type = cue_score, cue["cue"], "topic cue"
        results.append((score + (100 if best else 0), {
            "platform": row["platform"], "id": row["id"], "publisher": row["publisher"],
            "title": title, "match": match_type, "time": stamp,
            "topic": cue["topic"] if cue and match_type == "topic cue" else None,
            "source": citation(row, stamp), "excerpt": excerpt,
            "transcript_method": row.get("method") or row.get("speech_source"),
            "attribution_basis": row.get("evidence") or row.get("attribution_basis"),
        }))
    results.sort(key=lambda item: (-item[0], item[1]["publisher"], item[1]["id"]))
    return [r for _, r in results[:args.limit]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Short topic phrase. All terms must appear in one passage or record.")
    parser.add_argument("--library", type=Path, help="Local LaPratt-Archive directory")
    parser.add_argument("--platform", choices=PLATFORMS)
    parser.add_argument("--id", help="Restrict to one platform item ID from the index")
    parser.add_argument("--limit", type=int, default=6)
    args = parser.parse_args()
    query = tokens(args.query)
    if not query or args.limit < 1:
        parser.error("Enter a searchable phrase and a positive result limit.")
    explicit = args.library or os.environ.get("LAPRATT_ARCHIVE")
    library = Path(explicit or SKILL.parent / "LaPratt-Archive").expanduser().resolve()
    catalog = library / "catalog.csv"
    if not catalog.is_file():
        if explicit:
            parser.error(f"No catalog.csv found in {library}")
        library = None
        catalog = SKILL / "references" / "media-index.csv"
    with catalog.open(encoding="utf-8", newline="") as file:
        rows = matches(csv.DictReader(file), query, library, args)
    json.dump({"mode": "local_library" if library else "publisher_index", "results": rows},
              sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
