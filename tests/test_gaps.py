import io
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import unittest
from unittest import mock

from foundation_film import tools
from foundation_film.tools import BOUNDARY, TOOL_NAMES, input_sha256, run
from foundation_film_bridge import server
from foundation_film_bridge.schemas import tool_definitions
from foundation_film_bridge.server import LIMITS, PROTOCOL, Bridge, encode_response, serve
from tests import test_tools as fixtures

ROOT = Path(__file__).resolve().parents[1]
INIT = {"jsonrpc": "2.0", "id": "init", "method": "initialize", "params": {"protocolVersion": PROTOCOL}}
SHOT = {"start_ms": 0, "end_ms": 1000, "camera": "pan",
        "metrics": {"sharp": 65020, "black": 350, "subject_motion": 800, "luma": 158}}
DRIFT = {"frames": {"edge_f1": [980, 700, 80], "mask_iou": [840, 700, 0]}}
BANDS, BEATS, look_frame, random_film = fixtures.BANDS, fixtures.BEATS, fixtures.look_frame, fixtures.random_film
GOOD_AUDIO = fixtures.AudioGateTests.GOOD
PROVIDED = fixtures.CueVocabularyTests.PROVIDED
LANES = [{"lane": "a", "references": ["b4:w:heat"]}]
LOOK_GOOD = look_frame("k", (2, 3, 1, 4, 0, 0, 0.99, 1.05))

REFUSED = (("cinematic_gate", {"shots": [SHOT]}), ("cinematic_gate", {"shots": [SHOT], "path": "/tmp/f.mp4"}),
           ("reference_bands", {"shots": []}), ("audio_gate", {"cuts": 1}), ("drift_verdict", {}),
           ("drift_verdict", {"frames": {"edge_f1": [1001]}}),
           ("drift_verdict", {"frames": {"edge_f1": [900], "depth_error": [3]}}),
           ("cue_vocabulary_check", {"provided": [], "lanes": []}), ("look_gate", {"frames": []}),
           ("look_gate", {"frames": [{"id": "k", "path": "a.png"}]}))


def request(method, params=None, ident=1):
    message = {"jsonrpc": "2.0", "id": ident, "method": method}
    if params is not None:
        message["params"] = params
    return message


def call(name, arguments, ident=1):
    return request("tools/call", {"name": name, "arguments": arguments}, ident)


def ready():
    bridge = Bridge()
    reply = bridge.dispatch(INIT)
    if "result" not in reply:
        raise RuntimeError(reply)
    return bridge


def tool_cases():
    rng = random.Random(2026)
    films = [random_film(rng, n) for n in (1, 7, 40, 400)]
    end = films[2][-1]["end_ms"]
    long_edge = [200 if i % 3 else 900 for i in range(2048)]
    return {
        "cinematic_gate": [{"shots": [SHOT], "bands": BANDS},
                           {"shots": [dict(SHOT, metrics=dict(SHOT["metrics"], sharp=1))], "bands": BANDS},
                           {"shots": films[2], "bands": BANDS, "segments": [
                               {"id": "b1", "start_ms": 0, "end_ms": end // 2},
                               {"id": "b2", "start_ms": end // 2, "end_ms": end}]},
                           {"shots": [SHOT], "rules": [{"metric": "luma", "op": ">=", "target": 1}],
                            "segments": [{"id": "late", "start_ms": 20000, "end_ms": 21000}]},
                           {"shots": films[3], "bands": BANDS}],
        "reference_bands": [{"shots": film} for film in films],
        "audio_gate": [GOOD_AUDIO, dict(GOOD_AUDIO, integrated_lufs=-34000, heard=["Speech", "Sine wave"]),
                       dict(GOOD_AUDIO, line_wer=None, heard=None), dict(GOOD_AUDIO, cuts=0, cuts_with_hit=0),
                       dict(GOOD_AUDIO, contract={"forbidden_heard": ["Thunder"], "wer_max": 10}),
                       {"integrated_lufs": None, "true_peak_dbtp": None, "voice_over_bed_db": None, "cuts": None,
                        "cuts_with_hit": None, "heard": None, "line_wer": None}],
        "drift_verdict": [DRIFT, {"frames": {"edge_f1": [980] * 100 + [80] * 21}},
                          {"frames": {"edge_f1": [900, 800], "mask_iou": [700, 650]}},
                          {"frames": {"edge_f1": [900, None], "mask_iou": [None, 700], "depth_error": [100, 260],
                                      "identity_similarity": [None, 800]},
                           "thresholds": {"depth_error_max": 250, "identity_similarity_min": 700}},
                          {"frames": {"edge_f1": [None]}},
                          {"frames": {"edge_f1": long_edge}, "thresholds": {"edge_f1_min": 450}}],
        "cue_vocabulary_check": [
            {"provided": PROVIDED, "aliases": {"b4:heat-in": "b4:w:heat"},
             "lanes": [{"lane": "scene-b04", "references": ["b4:heat-in", "b4:w:vapor"]}],
             "orders": [{"beat": "b4", "sequence": ["b4:heat-in", "b4:w:vapor"]}],
             "min_gaps": [{"rule": "b11", "after": "b11:w:plant", "next": "b12:w:and", "min_ms": 2600}]},
            {"provided": PROVIDED, "aliases": {"slam-9": "b13:w:loop"},
             "lanes": [{"lane": "scene-b04", "references": ["b4:heat", "b4:w:vapor"]}],
             "orders": [{"beat": "b4", "sequence": ["b4:w:vapor", "b4:w:heat"]},
                        {"beat": "b9", "sequence": ["nope", "b4:w:heat"]}],
             "min_gaps": [{"rule": "back", "after": "b12:w:and", "next": "b4:w:heat", "min_ms": 0},
                          {"rule": "unknown", "after": "nope", "next": "b4:w:heat", "min_ms": 0}]},
            {"provided": PROVIDED, "lanes": [{"lane": "empty", "references": []}]}],
        "look_gate": [{"frames": [look_frame(k, v) for k, v in BEATS.items()]},
                      {"frames": [LOOK_GOOD, look_frame("k01", (2, 3, 1, 4, 0, None, 1, 1))]},
                      {"frames": [look_frame("k", (7, 3, 1, 4, 0, 0, 1, 1))],
                       "thresholds": {"palette_ab": 7500, "detail_min": 500, "detail_max": 2000}},
                      {"frames": [look_frame("n", (None,) * 8)]}],
    }


SUPPORTED = {"$schema", "type", "properties", "required", "additionalProperties", "propertyNames", "minProperties",
             "maxProperties", "items", "minItems", "maxItems", "uniqueItems", "enum", "const", "anyOf", "oneOf",
             "pattern", "maxLength", "minimum", "maximum"}
TYPES = {"null": lambda v: v is None, "boolean": lambda v: type(v) is bool, "integer": lambda v: type(v) is int,
         "string": lambda v: type(v) is str, "array": lambda v: type(v) is list, "object": lambda v: type(v) is dict}


def same(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def violations(schema, value, path="$"):
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise ValueError(f"schema keyword {sorted(unknown)} at {path} is not checked by this validator")
    kinds = schema.get("type")
    if kinds is not None and not any(TYPES[k](value) for k in ([kinds] if type(kinds) is str else kinds)):
        return [f"{path}: {value!r:.60} is not {kinds}"]
    found = []
    if "const" in schema and not same(value, schema["const"]):
        found.append(f"{path}: {value!r:.60} is not the constant {schema['const']!r}")
    if "enum" in schema and not any(same(value, option) for option in schema["enum"]):
        found.append(f"{path}: {value!r:.60} is not one of {schema['enum']}")
    if "anyOf" in schema and all(violations(s, value, path) for s in schema["anyOf"]):
        found.append(f"{path}: matches no anyOf branch")
    if "oneOf" in schema and sum(not violations(s, value, path) for s in schema["oneOf"]) != 1:
        found.append(f"{path}: does not match exactly one oneOf branch")
    if type(value) is str:
        if len(value) > schema.get("maxLength", len(value)):
            found.append(f"{path}: longer than {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            found.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if type(value) is int:
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            found.append(f"{path}: {value} outside [{schema.get('minimum')}, {schema.get('maximum')}]")
    if type(value) is list:
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", len(value)):
            found.append(f"{path}: {len(value)} items outside [{schema.get('minItems')}, {schema.get('maxItems')}]")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            found.append(f"{path}: items are not unique")
        for i, item in enumerate(value):
            found += violations(schema.get("items", {}), item, f"{path}[{i}]")
    if type(value) is dict:
        if not schema.get("minProperties", 0) <= len(value) <= schema.get("maxProperties", len(value)):
            found.append(f"{path}: {len(value)} properties outside the bounds")
        found += [f"{path}: missing {key}" for key in schema.get("required", []) if key not in value]
        properties, extra = schema.get("properties", {}), schema.get("additionalProperties", {})
        for key, item in value.items():
            found += violations(schema.get("propertyNames", {}), key, f"{path}<{key}>")
            if key in properties:
                found += violations(properties[key], item, f"{path}.{key}")
            elif extra is False:
                found.append(f"{path}: unexpected property {key}")
            else:
                found += violations(extra, item, f"{path}.{key}")
    return found


class GapFilmTests(unittest.TestCase):
    def test_gap_film_01_oversized_response_is_withheld_with_32002(self):
        """GAP-FILM-01: a response over 1048576 bytes is replaced by a -32002 Result withheld error."""
        empty = {"jsonrpc": "2.0", "id": 7, "result": {"pad": ""}}
        base = len(json.dumps(empty, sort_keys=True, separators=(",", ":")))
        fits = {"jsonrpc": "2.0", "id": 7, "result": {"pad": "x" * (LIMITS["outputFrameBytes"] - base)}}
        raw = encode_response(fits)
        self.assertEqual(len(raw), LIMITS["outputFrameBytes"] + 1)
        self.assertEqual(json.loads(raw), fits)
        over = {"jsonrpc": "2.0", "id": 7, "result": {"pad": "x" * (LIMITS["outputFrameBytes"] - base + 1)}}
        raw = encode_response(over)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertLess(len(raw), 256)
        self.assertEqual(json.loads(raw), {"jsonrpc": "2.0", "id": 7,
                                           "error": {"code": -32002, "message": "Result withheld"}})
        huge = (False, "thresholds_met", {"pad": "x" * LIMITS["outputFrameBytes"]})
        frames = [INIT, call("drift_verdict", DRIFT, 9), request("ping", ident=10)]
        sink = io.BytesIO()
        with mock.patch.object(server, "run", return_value=huge):
            status = serve(io.BytesIO(b"".join(json.dumps(f).encode() + b"\n" for f in frames)), sink)
        replies = [json.loads(line) for line in sink.getvalue().splitlines()]
        self.assertEqual(status, 0)
        self.assertEqual(replies[1:], [{"jsonrpc": "2.0", "id": 9, "error": {"code": -32002, "message": "Result withheld"}},
                                       {"jsonrpc": "2.0", "id": 10, "result": {}}])

    def test_gap_film_02_second_initialize_and_wrong_protocol_are_refused(self):
        """GAP-FILM-02: a second initialize returns -32000; a wrong protocolVersion returns -32001."""
        bridge = Bridge()
        for version in ("2024-11-05", "foundation-film-jsonrpc/2", 1):
            reply = bridge.dispatch(request("initialize", {"protocolVersion": version}, 3))
            self.assertEqual((reply["id"], reply["error"]["code"]), (3, -32001), version)
            self.assertNotIn("result", reply)
        self.assertEqual(bridge.dispatch(request("tools/list", ident=4))["error"]["code"], -32000)
        self.assertEqual(bridge.dispatch(INIT)["result"]["protocolVersion"], PROTOCOL)
        reply = bridge.dispatch(INIT)
        self.assertEqual((reply["id"], reply["error"]["code"]), ("init", -32000))
        self.assertNotIn("result", reply)
        reply = bridge.dispatch(request("initialize", {"protocolVersion": "2024-11-05"}, 5))
        self.assertEqual(reply["error"]["code"], -32001)
        self.assertEqual(bridge.dispatch(request("tools/list", ident=6))["result"]["tools"], tool_definitions())

    def test_gap_film_03_notifications_get_no_reply_and_are_not_executed(self):
        """GAP-FILM-03: a message without id gets no reply and is not executed."""
        bridge = Bridge()
        self.assertIsNone(bridge.dispatch({"jsonrpc": "2.0", "method": "initialize",
                                           "params": {"protocolVersion": PROTOCOL}}))
        self.assertEqual(bridge.dispatch(request("tools/list"))["error"]["code"], -32000)
        bridge = ready()
        with mock.patch.object(server, "run", side_effect=AssertionError("executed")) as tool:
            for method, params in (("tools/call", {"name": "drift_verdict", "arguments": DRIFT}), ("ping", None),
                                   ("tools/list", None), ("initialize", {"protocolVersion": PROTOCOL})):
                message = {"jsonrpc": "2.0", "method": method}
                if params is not None:
                    message["params"] = params
                self.assertIsNone(bridge.dispatch(message), method)
                self.assertIsNone(bridge.handle(json.dumps(message).encode()), method)
            tool.assert_not_called()
        sink = io.BytesIO()
        frames = [INIT, {"jsonrpc": "2.0", "method": "ping"}, request("ping", ident=2)]
        self.assertEqual(serve(io.BytesIO(b"".join(json.dumps(f).encode() + b"\n" for f in frames)), sink), 0)
        self.assertEqual([json.loads(line)["id"] for line in sink.getvalue().splitlines()], ["init", 2])

    def test_gap_film_04_invalid_envelopes_methods_and_arguments(self):
        """GAP-FILM-04: invalid envelopes return -32600, unknown methods -32601, non-object arguments -32602."""
        ping = request("ping")
        envelopes = ([ping], [], "ping", 5, None, dict(ping, extra=1), dict(ping, jsonrpc="1.0"), dict(ping, jsonrpc=2),
                     {k: v for k, v in ping.items() if k != "jsonrpc"}, dict(ping, method=""), dict(ping, method=5),
                     {k: v for k, v in ping.items() if k != "method"}, dict(ping, id=None),
                     dict(ping, id="x" * (LIMITS["idCharacters"] + 1)), dict(ping, id=True), dict(ping, id=[1]),
                     dict(ping, id={"n": 1}))
        for bridge in (Bridge(), ready()):
            for message in envelopes:
                reply = bridge.handle(json.dumps(message).encode())
                self.assertEqual((reply["id"], reply["error"]["code"]), (None, -32600), message)
                self.assertNotIn("result", reply)
            self.assertEqual(bridge.dispatch(dict(ping, id="x" * LIMITS["idCharacters"]))["result"], {})
            for method in ("tools/delete", "resources/list", "shutdown", "Ping"):
                reply = bridge.dispatch(request(method, ident=8))
                self.assertEqual((reply["id"], reply["error"]["code"]), (8, -32601), method)
        bridge = ready()
        for arguments in ([], "x", None, 5, True, [DRIFT]):
            reply = bridge.dispatch(request("tools/call", {"name": "drift_verdict", "arguments": arguments}, 9))
            self.assertEqual((reply["id"], reply["error"]["code"]), (9, -32602), arguments)
            self.assertNotIn("result", reply)

    def test_gap_film_05_unexpected_tool_exception_returns_32603_without_result(self):
        """GAP-FILM-05: an unexpected exception inside a tool returns -32603 with no result."""
        def broken(arguments):
            raise KeyError("private detail")

        bridge = ready()
        for name in TOOL_NAMES:
            with mock.patch.dict(tools.TOOLS, {name: broken}):
                reply = bridge.dispatch(call(name, {}, 11))
            self.assertEqual(set(reply), {"jsonrpc", "id", "error"})
            self.assertEqual((reply["id"], reply["error"]["code"]), (11, -32603))
            self.assertNotIn("private detail", reply["error"]["message"])
        self.assertFalse(bridge.dispatch(call("drift_verdict", DRIFT))["result"]["isError"])

    def test_gap_film_06_error_receipts_carry_input_sha256(self):
        """GAP-FILM-06: error receipts carry the input_sha256 of the refused arguments."""
        bridge, digests = ready(), set()
        for name, arguments in REFUSED:
            failed, _, receipt = run(name, arguments)
            self.assertTrue(failed)
            self.assertEqual(receipt["status"], "error")
            self.assertRegex(receipt["input_sha256"], "^[0-9a-f]{64}$")
            self.assertEqual(receipt["input_sha256"], input_sha256(arguments))
            wire = json.loads(encode_response(bridge.dispatch(call(name, arguments))))
            self.assertEqual(wire["result"]["structuredContent"]["receipt"]["input_sha256"], input_sha256(arguments))
            digests.add((name, receipt["input_sha256"]))
        self.assertEqual(len({d for _, d in digests}), len(REFUSED))

    def test_gap_film_07_results_conform_to_each_output_schema(self):
        """GAP-FILM-07: every tool's results, success and error, conform to its published outputSchema."""
        schemas = {t["name"]: t for t in tool_definitions()}
        bridge, cases = ready(), tool_cases()
        self.assertEqual(set(cases), set(TOOL_NAMES))
        for name in TOOL_NAMES:
            seen = set()
            for arguments in cases[name] + [a for n, a in REFUSED if n == name]:
                if not run(name, arguments)[0]:
                    self.assertEqual(violations(schemas[name]["inputSchema"], arguments), [], (name, arguments))
                reply = json.loads(encode_response(bridge.dispatch(call(name, arguments))))
                content = reply["result"]["structuredContent"]
                self.assertEqual(violations(schemas[name]["outputSchema"], content), [], (name, arguments))
                seen.add(content["assessment"])
            expected = {"reference_bands": {"bands_measured"},
                        "cue_vocabulary_check": {"thresholds_met", "thresholds_not_met"}}.get(
                name, {"thresholds_met", "thresholds_not_met", "not_scored"})
            self.assertEqual(seen, expected | {"tool_error"}, name)

    def test_gap_film_07_schema_check_rejects_nonconforming_results(self):
        """GAP-FILM-07: the schema check itself rejects results that break the outputSchema."""
        schema = {t["name"]: t for t in tool_definitions()}["drift_verdict"]["outputSchema"]
        content = ready().dispatch(call("drift_verdict", DRIFT))["result"]["structuredContent"]
        self.assertEqual(violations(schema, content), [])
        receipt = content["receipt"]
        mutations = (dict(content, formal_proof=True), dict(content, assessment="accepted"), dict(content, extra=1),
                     {k: v for k, v in content.items() if k != "receipt"},
                     dict(content, receipt=dict(receipt, boundary=dict(BOUNDARY, observation_only=False))),
                     dict(content, receipt=dict(receipt, input_sha256="A" * 64)),
                     dict(content, receipt=dict(receipt, evidence=[])),
                     dict(content, receipt=dict(receipt, result=dict(receipt["result"], frames=0))),
                     dict(content, receipt=dict(receipt, result=dict(receipt["result"], first_failing_frame=2.0))),
                     dict(content, receipt=dict(receipt, result=dict(receipt["result"], first_failing_frame=True))))
        for mutated in mutations:
            self.assertNotEqual(violations(schema, mutated), [], mutated)
        with self.assertRaises(ValueError):
            violations({"type": "string", "format": "uri"}, "x")

    def test_gap_film_08_caller_drift_thresholds_are_labelled_and_cited(self):
        """GAP-FILM-08: drift_verdict labels caller thresholds caller and adds a caller Evidence entry."""
        frames = {"edge_f1": [900, 300], "mask_iou": [900, 900]}
        failed, assessment, receipt = run("drift_verdict", {"frames": frames, "thresholds": {"edge_f1_min": 200}})
        result, kinds = receipt["result"], [(e["applies_to"], e["evidence"]["basis"]["kind"]) for e in receipt["evidence"]]
        self.assertEqual((failed, assessment), (False, "thresholds_met"))
        self.assertEqual(result["threshold_sources"], {"edge_f1_min": "caller", "mask_iou_min": "driftgate_default"})
        self.assertEqual(result["thresholds"], {"edge_f1_min": 200, "mask_iou_min": 600})
        self.assertIn(("arguments.thresholds", "caller"), kinds)
        self.assertIn(("result.thresholds", "cited"), kinds)
        caller = [e for e in receipt["evidence"] if e["evidence"]["basis"]["kind"] == "caller"]
        self.assertEqual(caller, [{"applies_to": "arguments.thresholds", "evidence": {"basis": {
            "kind": "caller", "source": "the caller's input", "note": "Thresholds supplied by the caller."},
            "status": "CHECK"}}])
        _, _, receipt = run("drift_verdict", {"frames": frames, "thresholds": {"edge_f1_min": 200, "mask_iou_min": 950}})
        self.assertEqual(set(receipt["result"]["threshold_sources"].values()), {"caller"})
        self.assertEqual(receipt["result"]["first_failing_frame"], 0)
        kinds = [(e["applies_to"], e["evidence"]["basis"]["kind"]) for e in receipt["evidence"]]
        self.assertIn(("arguments.thresholds", "caller"), kinds)
        self.assertNotIn(("result.thresholds", "cited"), kinds)
        _, _, receipt = run("drift_verdict", {"frames": frames})
        self.assertEqual(set(receipt["result"]["threshold_sources"].values()), {"driftgate_default"})
        self.assertNotIn("caller", [e["evidence"]["basis"]["kind"] for e in receipt["evidence"]])

    def test_gap_film_09_environment_changes_evidence_citations(self):
        """GAP-FILM-09: FOUNDATION_FILM_PLAYBOOK and FOUNDATION_FILM_PRODUCERS change the Evidence citation text."""
        cases = {"cinematic_gate": {"shots": [SHOT], "bands": BANDS}, "reference_bands": {"shots": [SHOT]},
                 "audio_gate": GOOD_AUDIO, "drift_verdict": DRIFT,
                 "cue_vocabulary_check": {"provided": PROVIDED, "lanes": LANES}, "look_gate": {"frames": [LOOK_GOOD]}}
        templates = {"cinematic_gate": ["{p}filmgate.py (default rules); {b}"],
                     "reference_bands": ["{p}filmstats.py; {b}"], "audio_gate": ["{b} (the mix gate)"],
                     "drift_verdict": ["{b} (drift gate, I20)", "{p}driftgate.py (defaults)"],
                     "cue_vocabulary_check": ["AGENTS.md I18; {b} (lessons 66-67)"],
                     "look_gate": ["{b} (the look gate; the prep-stage decision)", "{p}lookgate.py (defaults)"]}
        script = ("import json, sys; from foundation_film.tools import run; cases = json.loads(sys.stdin.read()); "
                  "print(json.dumps({n: [e['evidence']['basis']['source'] for e in run(n, a)[2]['evidence'] "
                  "if e['evidence']['basis']['kind'] == 'cited'] for n, a in cases.items()}))")
        base = {k: v for k, v in os.environ.items() if k not in ("FOUNDATION_FILM_PLAYBOOK", "FOUNDATION_FILM_PRODUCERS")}
        for extra, playbook, producers in (({}, "docs/PLAYBOOK-film.md", "tools/film/"),
                                           ({"FOUNDATION_FILM_PLAYBOOK": "runbooks/film.md",
                                             "FOUNDATION_FILM_PRODUCERS": "vendor/producers"},
                                            "runbooks/film.md", "vendor/producers/"),
                                           ({"FOUNDATION_FILM_PRODUCERS": "vendor/producers/"},
                                            "docs/PLAYBOOK-film.md", "vendor/producers/")):
            proc = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, env={**base, **extra},
                                  input=json.dumps(cases), capture_output=True, text=True, timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            expected = {n: [t.format(p=producers, b=playbook) for t in ts] for n, ts in templates.items()}
            self.assertEqual(json.loads(proc.stdout), expected, extra)

    def test_gap_film_10_gap_without_end_ms_is_measured_from_t_ms(self):
        """GAP-FILM-10: a minimum gap is measured from the earlier marker's t_ms when it has no end_ms."""
        provided = [{"id": "a", "t_ms": 1000}, {"id": "b", "t_ms": 1500, "end_ms": 1700}, {"id": "c", "t_ms": 4000}]
        _, _, receipt = run("cue_vocabulary_check", {
            "provided": provided, "aliases": {"a-alias": "a"}, "lanes": [{"lane": "l", "references": ["a"]}],
            "min_gaps": [{"rule": "a-c", "after": "a", "next": "c", "min_ms": 3000},
                         {"rule": "a-b", "after": "a", "next": "b", "min_ms": 501},
                         {"rule": "alias", "after": "a-alias", "next": "b", "min_ms": 500},
                         {"rule": "b-c", "after": "b", "next": "c", "min_ms": 2301},
                         {"rule": "c-a", "after": "c", "next": "a", "min_ms": 0}]})
        self.assertEqual([(g["rule"], g["gap_ms"], g["status"]) for g in receipt["result"]["gaps"]],
                         [("a-c", 3000, "pass"), ("a-b", 500, "fail"), ("alias", 500, "pass"), ("b-c", 2300, "fail"),
                          ("c-a", -3000, "fail")])


if __name__ == "__main__":
    unittest.main()
