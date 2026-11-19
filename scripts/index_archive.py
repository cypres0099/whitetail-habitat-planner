#!/usr/bin/env python3
"""Rebuild the shareable media index and timestamp pointers from a local LaPratt library."""
import argparse
import csv
import re
from pathlib import Path

from search_archive import citation, cues, tokens

TOPICS = {
    "Seasonal mast and forage": "acorns, mast crop, white oak, red oak, oak ridge",
    "Field establishment": "soil test, seed bed, soil sample, germination, planting depth, soil ph",
    "Browse and understory": "woody browse, native browse, woody vegetation, understory, regeneration, browse line, native grasses, switchgrass",
    "Field shape and sightlines": "field edge, field edges, field shape, visual barrier, line of sight, screening cover, sight lines",
    "Cropping and forage": "food plot, food plots, clover, soybeans, alfalfa",
    "Wet ground and water": "floodplain, river bottom, creek crossing, high water, standing water, river bank, water source",
    "Woodland and edges": "pure timber, big woods, timber edge, timber management, logging road, timber stand",
    "Human disturbance": "human pressure, human intrusion, human scent, human activity, human traffic, foot traffic, access route, entrance and exit, entry and exit",
    "Observing change": "trail camera, trail cameras, camera survey, trail cam, camera data, observation stand",
    "Cover and resting habitat": "security cover, bedding cover, thick cover, bedding area, bedding areas, sanctuary, sanctuaries",
}
PROMOTION = re.compile(r"sponsor|promo code|brought to you by|use code|discount code")


def topic_rows(row, library):
    if not row["transcript"]:
        return
    path = (library / row["transcript"]).resolve()
    if not path.is_relative_to((library / "transcripts").resolve()):
        raise ValueError(f"Unexpected transcript path for {row['id']}")
    timed = [(time, " " + " ".join(tokens(" ".join(words))) + " ")
             for time, words in cues(path.read_text(encoding="utf-8")) if time]
    for topic, phrases in TOPICS.items():
        for term in phrases.split(", "):
            marker = " " + term + " "
            found = next((t for t, line in timed if marker in line and not PROMOTION.search(line)), None)
            if found:
                yield topic, term, row["platform"], row["id"], found, citation(row, found)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library", type=Path, help="Private library containing catalog.csv and transcripts/")
    parser.add_argument("--output", type=Path, required=True, help="Destination for the two public CSV files")
    args = parser.parse_args()
    library = args.library.resolve()
    with (library / "catalog.csv").open(encoding="utf-8", newline="") as file:
        rows = sorted(csv.DictReader(file), key=lambda r: (r["platform"], r["publisher"], r["id"]))
    args.output.mkdir(parents=True, exist_ok=True)
    pointers = []
    with (args.output / "media-index.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["platform", "id", "publisher", "title_or_caption", "source_url", "published_date_if_available",
                         "record_type", "attribution_basis", "speech_source"])
        for row in rows:
            title = row["title"]
            if "shout out to my" in title.lower():
                title = "Community appreciation reel"
            writer.writerow((row["platform"], row["id"], row["publisher"], title, row["url"], row["date"],
                             row["kind"], row["evidence"], row["method"]))
            pointers.extend(topic_rows(row, library))
    with (args.output / "topic-cues.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["topic", "matched_term", "platform", "id", "cue", "source_url"])
        writer.writerows(pointers)
    print(f"Indexed {len(rows)} publisher records and {len(pointers)} timed topic cues.")


if __name__ == "__main__":
    main()
