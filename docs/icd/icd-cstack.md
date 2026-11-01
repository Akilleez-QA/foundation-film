# Interface control: foundation-film and Cstack

| Side | Item |
|---|---|
| Provider | foundation-film, `foundation_film_bridge` |
| Consumer | Cstack host adapter for this Foundation |
| Transport | Child process, stdio, one JSON-RPC 2.0 message per line |
| Start command | `python -B -m foundation_film_bridge`, fixed cwd, minimal fixed environment, no shell |
| Pins | Manifest SHA-256, manifest file count, canonical tool inventory SHA-256, printed by `python -B tools/build_manifest.py` |
| Version | 0.1.0 (`SOURCE-MANIFEST.json`) |

## Methods

`initialize`, `tools/list`, `tools/call`. Tools: `cinematic_gate`, `reference_bands`, `audio_gate`, `drift_verdict`, `cue_vocabulary_check`, `look_gate`.

## Rules

1. The consumer re-verifies the pins before dispatch and after every accepted response.
2. Only integers or bounded decimal strings cross the bridge as the schemas state; floats are rejected where the schema says so.
3. The consumer grants only the `read` effect.
4. A change to any shipped file changes the manifest pin. The consumer repins in the same change that updates its vendored copy.

## Offline measurement interface

`python -B -m foundation_film.filmstats VIDEO [--fps 8] [--width 640]` prints one
JSON object with `shots` on stdout. Each shot has `start_ms`, `end_ms`, `camera`
and `metrics`, validated by the existing cinematic input contract. Seconds and
floating measurements become milliseconds/milli-units with half ties away from zero.
The result can be supplied as `reference_bands` arguments, or extended with `bands`
or `rules` for `cinematic_gate`. The producer is a local CLI, outside JSON-RPC;
it accepts paths, requires NumPy/OpenCV/PySceneDetect, and emits no bridge receipt.
It rejects empty or incomplete decodes and shots without sampled frames. It does
not emit Endoforge's `summary.json`, audio, palette or contact-strip artifacts.

