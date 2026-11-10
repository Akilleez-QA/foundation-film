# foundation-film verification matrix

| Field | Value |
|---|---|
| Document ID | FFILM-VM |
| Version | 2.1 |
| Status | Draft |
| Owner | Akilleez-QA |
| Date | 2026-11-10 |
| Baseline commit | 1fb04eab1d174ae0443cd0a7604ea9bcac75d168 |
| Applies to | foundation-film main at baseline commit |
| Classification | Self-assessed Class E analog; not safety-critical (see SMP §1) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

Trace check: performed with an out-of-tree adaptation of foundation-robotics `tools/check_trace.py` (this repository has no trace tool yet; the documentation change was docs-only). Result and command are in the [assurance record](../assurance/assurance-record.md). The check fails on a requirement with no row, a row naming a missing test or path, a `T` row with no test, a test that traces to nothing, an unallocated requirement, or a dead link. A reference `file::Class` covers every test method in that class. Results come from the latest report in [reports/](reports/README.md).

| Requirement | Method | Test (file::Class.method) or inspection target | Acceptance observation / limit | Last result |
|---|---|---|---|---|
| REQ-FILM-001 | T | `tests/test_tools.py::CinematicGateTests` | Parity with filmgate on 60 seeded films; exact default rules; whole film is the default segment; static void fails five rules; uncovered segment not scored | STR (latest) |
| REQ-FILM-002 | T | `tests/test_tools.py::ReferenceBandsTests` | Bands equal the reference weighted percentile on 60 seeded films; moving share within 0.0005; bands feed the gate | STR (latest) |
| REQ-FILM-003 | T | `tests/test_tools.py::AudioGateTests` | A mix inside the contract passes (hit share 813); each of eight breaches names its check | STR (latest) |
| REQ-FILM-004 | T | `tests/test_tools.py::DriftVerdictTests`, `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_a_verdict_with_evidence` | First failing frame 2 over the bridge; a late collapse fails although the mean passes | STR (latest) |
| REQ-FILM-005 | T | `tests/test_tools.py::CueVocabularyTests`, `tests/test_gaps.py::GapFilmTests.test_gap_film_10_gap_without_end_ms_is_measured_from_t_ms` | Closed vocabulary passes with one alias; invented names, broken aliases, order and gap breaches listed; a gap without `end_ms` is measured from `t_ms` (3000 ms passes a 3000 ms minimum, 500 ms fails 501) | STR (latest) |
| REQ-FILM-006 | T | `tests/test_tools.py::LookGateTests` | Target passes against itself; a rendered set fails frame by frame; one failing keyframe fails the set | STR (latest) |
| REQ-FILM-007 | T | `tests/test_bridge.py::BridgeTests.test_source_manifest_lists_every_file` | Manifest file map equals a fresh hash of the tree under the same exclusions | STR (latest) |
| REQ-FILM-008 | T, I | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_a_verdict_with_evidence`, `foundation_film/tools.py` | Test: receipt boundary equals the constant. Inspection: `run` sets `boundary` on every receipt; no tool module writes files, opens sockets or starts processes | STR (latest); inspection in SAR 2026-11-08 |
| REQ-FILM-009 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_a_verdict_with_evidence`, `tests/test_bridge.py::BridgeTests.test_bad_arguments_are_a_tool_error_that_still_carries_evidence` | Evidence present on a verdict and on refusals for all six tools | STR (latest) |
| REQ-FILM-010 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_a_verdict_with_evidence`, `tests/test_gaps.py::GapFilmTests.test_gap_film_06_error_receipts_carry_input_sha256` | `input_sha256` equals `input_sha256(arguments)` on a success receipt and on ten refused argument sets, directly and over the bridge | STR (latest) |
| REQ-FILM-011 | I, T | `foundation_film_bridge/server.py`, `foundation_film/tools.py`, `tests/test_bridge.py::BridgeTests.test_wire_profile_fails_closed`, `tests/test_filmstats.py::FilmstatsBoundaryTests.test_imports_without_optional_dependencies` | Test: `--root /` gives exit 2; tools and producer import with `-S` (no site packages). Inspection: tool modules import only the standard library; the producer imports NumPy, OpenCV and PySceneDetect inside functions | STR (latest); inspection in SAR 2026-11-08 |
| REQ-FILM-012 | T | `tests/test_requirement_limits.py::RequirementLimitsTests` | Each limit accepted at the limit and rejected one past it with `-32002`; an oversized stream line ends the session with status 2 | STR (latest) |
| REQ-FILM-013 | T | `tests/test_filmstats.py::FilmstatsBoundaryTests.test_milli_rounding`, `tests/test_filmstats.py::FilmstatsBoundaryTests.test_scene_times_use_the_seconds_property_not_get_seconds`, `tests/test_filmstats.py::FilmstatsBoundaryTests.test_producer_dependencies_are_present_where_ci_requires_them`, `tests/test_filmstats.py::FilmstatsVisionTests` | Half-up milli rounding; NaN and infinity refused; scene times read through `.seconds` (stand-in modules without `get_seconds()`); uniform frame metrics; pan versus still; a two-shot video through the CLI gives shots 0–3000 and 3000–6000 ms with no deprecation warning from the producer; bad sampling refused. The vision class is skipped without the optional dependencies; the CI `producer` job sets `FOUNDATION_FILM_REQUIRE_PRODUCER=1`, so a missing dependency fails there instead of skipping | STR (latest) states whether it ran |
| REQ-FILM-014 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_a_verdict_with_evidence` | Protocol string echoed; `mcpCompatible` false | STR (latest) |
| REQ-FILM-015 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_a_verdict_with_evidence` | Catalog equals `tool_definitions()`; names in `TOOL_NAMES` order | STR (latest) |
| REQ-FILM-016 | T | `tests/test_bridge.py::BridgeTests.test_bad_arguments_are_a_tool_error_that_still_carries_evidence`, `tests/test_tools.py::CinematicGateTests.test_malformed_films_are_refused`, `tests/test_tools.py::AudioGateTests.test_unmeasured_is_not_scored_and_overrides_are_reported`, `tests/test_tools.py::DriftVerdictTests.test_optional_metrics_need_thresholds_and_nulls_are_not_scored`, `tests/test_tools.py::CueVocabularyTests.test_ambiguous_or_malformed_vocabularies_are_refused`, `tests/test_tools.py::LookGateTests.test_caller_thresholds_are_reported_and_malformed_requests_refused` | `isError` true, assessment `tool_error`, status `error`, result null, evidence present | STR (latest) |
| REQ-FILM-017 | T | `tests/test_bridge.py::BridgeTests.test_wire_profile_fails_closed` | `tools/call` before `initialize` gives `-32000`; `read_file` gives `-32602` | STR (latest) |
| REQ-FILM-018 | T | `tests/test_bridge.py::BridgeTests.test_wire_profile_fails_closed` | Duplicate key, `1.5` and `NaN` give `-32700` | STR (latest) |
| REQ-FILM-019 | T | `tests/test_tools.py::CinematicGateTests.test_a_static_void_fails_and_an_uncovered_segment_is_not_scored`, `tests/test_tools.py::AudioGateTests.test_unmeasured_is_not_scored_and_overrides_are_reported`, `tests/test_tools.py::LookGateTests.test_one_failing_keyframe_fails_the_set_and_nulls_are_not_scored`, `tests/test_tools.py::AudioGateTests.test_a_mix_inside_the_contract_meets_it` | Unmeasured gives `not_scored`; a failing check gives `thresholds_not_met`; all-pass gives `thresholds_met` | STR (latest) |
| REQ-FILM-020 | T | `tests/test_tools.py::CinematicGateTests.test_a_static_void_fails_and_an_uncovered_segment_is_not_scored`, `tests/test_tools.py::AudioGateTests.test_unmeasured_is_not_scored_and_overrides_are_reported`, `tests/test_tools.py::LookGateTests.test_caller_thresholds_are_reported_and_malformed_requests_refused`, `tests/test_gaps.py::GapFilmTests.test_gap_film_08_caller_drift_thresholds_are_labelled_and_cited` | `rule_source` `caller`; `contract_overrides` lists `forbidden_heard`; `threshold_sources.palette_ab` `caller` and a `caller` Evidence entry; `drift_verdict` labels `edge_f1_min` `caller` and adds one `caller` Evidence entry, and none without caller thresholds | STR (latest) |
| REQ-FILM-021 | T | `tests/test_tools.py::CinematicGateTests.test_parity_with_filmgate_on_random_films`, `tests/test_tools.py::ReferenceBandsTests.test_parity_with_the_weighted_percentile_used_for_the_reference_bands`, `tests/test_tools.py::DriftVerdictTests.test_parity_with_driftgate_every_frame_rule`, `tests/test_tools.py::LookGateTests.test_parity_with_lookgate_on_random_frames` | 60, 60, 60 and 200 seeded trials agree with the reference rules | STR (latest) |
| REQ-FILM-022 | T | `tests/test_requirement_limits.py::RequirementLimitsTests.test_req_film_012_stream_frame_limit` | Two `ping` requests without `initialize` each return `{}` | STR (latest) |
| REQ-FILM-023 | T | `tests/test_gaps.py::GapFilmTests.test_gap_film_01_oversized_response_is_withheld_with_32002` | A response of exactly 1048576 bytes plus newline is sent; one byte more becomes `-32002` "Result withheld" with the same id; the next request is answered | STR (latest) |
| REQ-FILM-024 | T | `tests/test_gaps.py::GapFilmTests.test_gap_film_02_second_initialize_and_wrong_protocol_are_refused` | Three wrong versions give `-32001` and leave the session uninitialized; a second `initialize` gives `-32000`; no result in either | STR (latest) |
| REQ-FILM-025 | T | `tests/test_gaps.py::GapFilmTests.test_gap_film_03_notifications_get_no_reply_and_are_not_executed` | No reply to id-less `initialize`, `ping`, `tools/list` and `tools/call`; no tool runs; the session stays uninitialized | STR (latest) |
| REQ-FILM-026 | T | `tests/test_gaps.py::GapFilmTests.test_gap_film_04_invalid_envelopes_methods_and_arguments` | 17 malformed envelopes give `-32600` with `id: null` before and after `initialize`; a 128-character id is accepted; four unknown methods give `-32601`; six non-object `arguments` give `-32602` | STR (latest) |
| REQ-FILM-027 | T | `tests/test_gaps.py::GapFilmTests.test_gap_film_05_unexpected_tool_exception_returns_32603_without_result` | For each of the six tools: `-32603`, no result, no exception text; the next call succeeds | STR (latest) |
| REQ-FILM-028 | T | `tests/test_gaps.py::GapFilmTests.test_gap_film_07_results_conform_to_each_output_schema`, `tests/test_gaps.py::GapFilmTests.test_gap_film_07_schema_check_rejects_nonconforming_results` | Every assessment of every tool, including `tool_error`, validates against its `outputSchema`; accepted arguments validate against `inputSchema`; ten broken results are rejected; an unsupported schema keyword is refused | STR (latest) |
| REQ-FILM-029 | T | `tests/test_gaps.py::GapFilmTests.test_gap_film_09_environment_changes_evidence_citations` | Default, both variables set, and producers only with a trailing `/`: the `cited` sources of all six tools match the expected text | STR (latest) |

## Tests without a requirement

None. Every test method traces to at least one requirement.

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-10-30 | 5c37f74 | Initial matrix | Initial commit |
| 1.1 | 2026-10-30 | 9725403 | Inspection-only rows marked I | PR #4 |
| 1.2 | 2026-11-01 | e6e6405 | REQ-FILM-012 and 013 rows with named tests | PR #5 |
| 2.0 | 2026-11-08 | 852f976 | Family standard. Method-level references. REQ-FILM-002, 003, 005 and 006 no longer cite `tests/test_bridge.py` for their behaviour (the bridge test only refuses their bad arguments; that is REQ-FILM-016). Rows for REQ-FILM-014 to 022. "pass at baseline" replaced by pointers to the generated STR | docs/nasa-standard PR |
| 2.1 | 2026-11-10 | 1fb04ea | Rows for REQ-FILM-023 to 029. REQ-FILM-005, 010, 013 and 020 gained the tests that closed GAP-FILM-10, 06 and 08 and findings F-5 and F-7. REQ-FILM-013 no longer says CI skips the video tests | findings-sweep PR |
