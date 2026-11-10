# Changelog

Format: Keep a Changelog 1.1, SemVer.

## [Unreleased]

### Added

- Tests for the ten behaviours that had none (GAP-FILM-01 to 10) in `tests/test_gaps.py`, including a check of every tool's results against its published output schema. Found by the family findings sweep.
- CI job `producer` runs the full suite with NumPy, opencv-python-headless and `scenedetect>=0.7.2`, and fails if those libraries are missing, so the four video tests no longer skip in CI.
- Initial release: Foundation package, stdio bridge, tests, and NASA-style docs under `docs/`.
- Documentation to the Cstack family standard (organized after NASA NPR 7150.2D and the NASA Software Engineering Handbook; self-assessed Class E analog, not safety-critical): software management plan, compliance matrix, data dictionary, test plan, test report, version description, assurance record, user manual map, tutorial, how-to guides, generated tool catalog and defaults, and explanation pages including limitations.
- Problem-report and change-request issue templates (replacing the bug template) and a peer-review pull request template.

### Changed

- Requirements: added REQ-FILM-023 to 029 for the newly tested behaviour; REQ-FILM-005, 010, 013 and 020 cite their new tests; the untested-behaviour list in SRS §8 is empty.
- Requirements: added REQ-FILM-014 to 022 for tested behaviour; listed untested behaviour as GAP-FILM-01 to 10.

### Fixed

- The video producer read scene times with `get_seconds()`, which scenedetect 0.7.2 deprecates; it now uses the `seconds` property. A test fails on any deprecation warning from the producer.
- The tool catalog lists the fields of nullable array items and nullable objects: `audio_gate` `line_wer[].line` and `line_wer[].wer_permille` (0..10000), and `cue_vocabulary_check` `result.orders[].first_violation.*`. Regenerated with the union-aware generator logic from foundation-robotics. The interface document describes evidence entries with their real nesting (`evidence.basis.kind`, `evidence.status`). Found during the 2026-11-09 backfill review.
- Documentation claims that did not match the code: the verification matrix cited the bridge test for four tools' behaviour; the interface document omitted `ping` and mentioned decimal strings that the bridge never accepts; the configuration document and AGENTS.md claimed trufflehog runs before every push.
- Exclude `.github/` automation and repository metadata from the source manifest so CI-only changes do not invalidate source pins.
