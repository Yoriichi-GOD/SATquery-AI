import hashlib
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from jai_extension.flood_bridge import BridgeError, FloodBridge, normalize


class Upstream(BaseHTTPRequestHandler):
    payloads = {}
    overrides = {}

    def do_GET(self):
        if self.path in self.overrides:
            code, raw, headers = self.overrides[self.path]
        elif self.path in self.payloads:
            code, raw, headers = 200, self.payloads[self.path], {}
        else:
            code, raw, headers = 404, b"", {}
        self.send_response(code)
        self.send_header("Content-Length", str(len(raw)))
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.bridge = FloodBridge(f"http://127.0.0.1:{cls.server.server_port}")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.result = {"run_id": "fixture", "synthetic": True, "event_name": "SYNTHETIC SOFTWARE TEST",
                       "summary": {"new_water_m2": 3200, "connectivity_assessed": False, "potentially_cut_off": 0},
                       "limitations": ["Invented software fixture"]}
        manifest = {"synthetic": True, "pre": {}, "post": {}, "analysis": {}}
        files = {"result.json": json.dumps(self.result).encode(), "manifest.json": json.dumps(manifest).encode(),
                 "pre.png": b"\x89PNG\r\n\x1a\nfixture", "exposure.csv": b"id,kind,exposed,observed,total,unit,status\nx,road,40,80,80,m,exposed\n"}
        Upstream.payloads = {"/api/health": b'{"service":"satquery-flood-lab"}', "/api/runs": json.dumps([self.result]).encode()}
        Upstream.payloads.update({"/runs/fixture/" + n: raw for n, raw in files.items()})
        self.freeze = {"files": {n: hashlib.sha256(raw).hexdigest() for n, raw in files.items()}}
        Upstream.payloads["/runs/fixture/freeze.json"] = json.dumps(self.freeze).encode()
        Upstream.overrides = {}

    def assert_status(self, status, fn, *args):
        with self.assertRaises(BridgeError) as ctx:
            fn(*args)
        self.assertEqual(ctx.exception.status, status)

    def test_only_literal_loopback_origins(self):
        for url in ["https://127.0.0.1:8770", "http://example.com:8770", "http://localhost:8770",
                    "http://127.0.0.1:8770/x", "http://user:secret@127.0.0.1:8770", "http://10.0.0.1:8770"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                FloodBridge(url)

    def test_health_identifies_real_service(self):
        self.assertTrue(self.bridge.health()["available"])

    def test_stopped_upstream(self):
        bridge = FloodBridge("http://127.0.0.1:1")
        self.assertFalse(bridge.health()["available"])
        self.assert_status(503, bridge.runs)

    def test_redirect_is_not_followed(self):
        Upstream.overrides["/api/runs"] = 302, b"", {"Location": "http://example.com"}
        self.assert_status(503, self.bridge.runs)

    def test_empty_runs(self):
        Upstream.payloads["/api/runs"] = b"[]"
        self.assertEqual(self.bridge.runs()["runs"], [])

    def test_listing_labels_synthetic_population(self):
        item = self.bridge.runs()["runs"][0]
        self.assertEqual(item["population"], "SYNTHETIC_SOFTWARE_TEST")
        self.assertEqual(item["integrity"], "NOT_YET_CHECKED")

    def test_missing_population_withheld(self):
        del self.result["synthetic"]
        Upstream.payloads["/api/runs"] = json.dumps([self.result]).encode()
        self.assertEqual(self.bridge.runs()["rejected_metadata"], 1)

    def test_no_false_zero_for_unassessed_connectivity(self):
        item = normalize(self.result)
        self.assertNotIn("potentially_cut_off", item["summary"])
        self.assertEqual(item["summary"]["connectivity_status"], "NOT_ASSESSED")

    def test_negative_measurement_refused(self):
        self.result["summary"]["new_water_m2"] = -1
        self.assert_status(422, normalize, self.result)

    def test_nonfinite_measurement_refused(self):
        self.result["summary"]["new_water_m2"] = float("nan")
        self.assert_status(422, normalize, self.result)

    def test_nan_upstream_json_refused(self):
        Upstream.payloads["/api/runs"] = b"[NaN]"
        self.assert_status(422, self.bridge.runs)

    def test_unknown_run(self):
        self.assert_status(404, self.bridge.detail, "absent")

    def test_path_traversal_refused(self):
        for value in ["..", "../fixture", "fixture%2f..", "/tmp/data", "file?x=1"]:
            self.assert_status(404, self.bridge.detail, value)
        self.assert_status(404, self.bridge.verified, "fixture", "../secret")

    def test_allowlist_only(self):
        self.assert_status(404, self.bridge.verified, "fixture", ".env.local")

    def test_summary_and_manifest_verified(self):
        value = self.bridge.detail("fixture")
        self.assertEqual(value["integrity"], "RESULT_AND_MANIFEST_VERIFIED")
        self.assertNotIn("path", json.dumps(value["provenance"]))

    def test_modified_result_refused(self):
        Upstream.payloads["/runs/fixture/result.json"] += b" "
        self.assert_status(409, self.bridge.detail, "fixture")

    def test_modified_preview_refused(self):
        Upstream.payloads["/runs/fixture/pre.png"] += b"x"
        self.assert_status(409, self.bridge.verified, "fixture", "pre.png")

    def test_freeze_cannot_allow_arbitrary_path(self):
        self.freeze["files"]["../secret"] = "a" * 64
        Upstream.payloads["/runs/fixture/freeze.json"] = json.dumps(self.freeze).encode()
        self.assert_status(422, self.bridge.freeze, "fixture")

    def test_exposure_keeps_saved_values(self):
        data = self.bridge.exposure("fixture")
        self.assertEqual(data["rows"][0]["exposed"], 40)

    def test_transfer_limit(self):
        self.assert_status(413, self.bridge.read, "/api/runs", 5)

    def test_compressed_response_refused(self):
        Upstream.overrides["/api/runs"] = 200, b"test", {"Content-Encoding": "gzip"}
        self.assert_status(422, self.bridge.runs)


if __name__ == "__main__":
    unittest.main()
