# Using recordings as evidence

Start with a concrete habitat question. For a claim about seasonal food, search a resource such as **acorns**. For a question about disturbance, search an activity such as **exit** or **walk**. Short, ordinary terms work across transcripts with different captioning conventions. Use the source ID to revisit one recording.

Run the helper from the skill directory with Python 3.9 or later.

```sh
python3 scripts/search_archive.py "pure timber" --platform Podcast
python3 scripts/search_archive.py "acorns" --id TVvuY4wU26Y
python3 scripts/search_archive.py "food plot" --library "/path/to/LaPratt-Archive"
```

A sibling directory named `LaPratt-Archive` is detected automatically. In a different installation, set `LAPRATT_ARCHIVE` to the library folder or pass `--library`. The library includes `catalog.csv` and `transcripts/`. A shared checkout without these files searches the public publisher index and [topic cues](topic-cues.csv). These cues point to timestamped mentions of ten habitat subjects in the recordings. A topic cue identifies a place to listen. Open the recording to verify the speaker and meaning.

Results show the type of match, the speaker-attribution evidence, and the first cue time of a short passage when the source provides timing. YouTube links open at that cue. A null time means the result has no verified timestamp. A metadata match helps locate a source. Only a speech match or a direct review of the recording supports a claim about what someone said.

For a project recommendation, use the full interview when available. Listen around a match, especially in panel episodes. A guest’s name in a post can refer to someone who speaks elsewhere in the episode. Record the lesson in original words, connect it to an observable feature, and state what local evidence would change the decision. Count cross-posts of one interview as one example. Keep product promotions, announcements, entertainment and unverified machine recognition out of management recommendations.

## Bringing new material into the skill

The lookup reads the live local catalog, so a newly archived transcript becomes searchable on the next invocation. To refresh the portable publisher index and timestamp pointers after adding recordings, run the command below from the skill checkout.

```sh
python3 scripts/index_archive.py "/path/to/LaPratt-Archive" --output references
```

The generated files contain publisher metadata, topic terms, timestamps and URLs. Listen around relevant cues before revising the original lessons. Add a lesson when the source changes a field decision or supplies a useful counterexample. Update the coverage report when a channel or feed has been rechecked.
