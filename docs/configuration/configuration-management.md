# Configuration management

- Versioning: SemVer. Current version 0.1.0, recorded in `SOURCE-MANIFEST.json`.
- Baseline: the initial commit on `main`.
- Change control: pull requests only, one concern, about 400 changed lines. Refrigeration.AI merges after checking the head SHA. Branches are kept.
- Pins: after any change run `python -B tools/build_manifest.py` and commit the new `SOURCE-MANIFEST.json`. Consumers repin from its output.
- Releases and tags: none yet. A tag is created only with owner approval.
- Secret scanning: gitleaks and trufflehog run before every push.
- Visual producer provenance: Endoforge main at `819fa8a6b3eea9cae5f1388eb67a78556ad65727`, `tools/film/filmstats.py`; adapted into `foundation_film/filmstats.py` under the shared GPL-3.0-only license. No Endoforge runtime imports are required.
- Optional producer dependencies are installed separately with the README's `uv` commands; the bridge inventory remains unchanged. Regenerate the source manifest after producer changes; consumers must repin it.
- `PR_BODY.md` is an uncommitted review artifact, excluded from the shipped-file manifest and its inventory check.
