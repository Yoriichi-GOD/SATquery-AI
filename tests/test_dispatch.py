"""Exercise the actual endpoint functions without unavailable FastAPI/GPU imports.

AST loading strips decorators only. Filesystem, executor and HTTP exception are
test doubles; these tests do not claim HTTP transport or raster integration.
"""
import ast
import threading
import time
import unittest
import uuid
import tempfile
import json
from pathlib import Path
from types import SimpleNamespace
from routing import route


class HTTPError(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail


def endpoints():
    tree = ast.parse(Path('server.py').read_text(encoding='utf-8'))
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ['analyze', 'ndvi_run']]
    for node in funcs:
        node.decorator_list = []
    calls = []
    scope = dict(Form=lambda default: default, HTTPException=HTTPError, route=route,
                 images={'rgb': {'geo': None}, 'spectral': {'geo': {'ndvi_supported': True}}},
                 jobs={}, busy=False, lock=threading.Lock(), uuid=uuid, time=time,
                 executor=SimpleNamespace(submit=lambda *args: calls.append(args)),
                 Path=Path, MODEL_ID='test', REVISION='test', run_job='vqa_worker', run_ndvi='ndvi_worker')
    exec(compile(ast.Module(body=funcs, type_ignores=[]), 'server.py', 'exec'), scope)
    return scope, calls


class DispatchTests(unittest.TestCase):
    def test_temporal_refuses_before_scheduling(self):
        for endpoint in ['analyze', 'ndvi_run']:
            scope, calls = endpoints()
            with self.assertRaises(HTTPError) as caught:
                scope[endpoint](image_id='spectral', question='Compare this to last year')
            self.assertEqual(caught.exception.status_code, 422)
            self.assertEqual(caught.exception.detail['rule'], 'temporal_unavailable')
            self.assertEqual(calls, [])
            self.assertFalse(scope['busy'])

    def test_ndvi_worker_keeps_denominators_and_waits_for_views(self):
        tree = ast.parse(Path('server.py').read_text(encoding='utf-8'))
        worker = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_ndvi')
        stats = dict(selected_area_m2=None, selected_percent_of_valid=50., selected_percent_of_crop=25., valid_coverage_percent=50.)
        with tempfile.TemporaryDirectory(dir='.') as tmp:
            job = dict(threshold=.5, started=time.time())
            scope = dict(jobs={'run':job}, busy=True, RUNS=Path(tmp), UPLOADS=Path(tmp), time=time,
                         geo=SimpleNamespace(analyse=lambda *args:stats), json=json, lock=threading.Lock())
            def views(*args):
                self.assertEqual(job['state'], 'running')
                return ['rgb', 'false-colour', 'evidence', 'mask']
            scope['create_stages'] = views
            exec(compile(ast.Module(body=[worker], type_ignores=[]), 'server.py', 'exec'), scope)
            scope['run_ndvi']('run','image')
            self.assertEqual(job['state'], 'complete')
            self.assertIn('50.00% of valid pixels', job['answer'])
            self.assertIn('25.00% of the whole crop', job['answer'])
            self.assertEqual(len(job['processing_stages']), 4)
            self.assertFalse(scope['busy'])
            self.assertTrue((Path(tmp)/'run.json').exists())

    def test_ndvi_dispatch_and_saved_reason(self):
        scope, calls = endpoints()
        result = scope['analyze'](image_id='spectral', question='Calculate NDVI', mode='baseline', threshold=.7)
        self.assertEqual(calls[0][0], 'ndvi_worker')
        job = scope['jobs'][result['id']]
        self.assertEqual(job['threshold'], .7)
        self.assertEqual(job['question'], 'Calculate NDVI')
        self.assertEqual(job['routing']['tool'], 'ndvi')

    def test_vqa_dispatch_and_saved_reason(self):
        scope, calls = endpoints()
        result = scope['analyze'](image_id='rgb', question='Is there a river visible in this image?')
        self.assertEqual(calls[0][0], 'vqa_worker')
        self.assertEqual(scope['jobs'][result['id']]['routing']['tool'], 'vqa')

    def test_rgb_ndvi_and_direct_endpoint_mismatch(self):
        for image_id, question in [('rgb', 'Calculate NDVI'), ('spectral', 'Is there a river visible in this image?')]:
            scope, calls = endpoints()
            with self.assertRaises(HTTPError) as caught:
                scope['ndvi_run'](image_id=image_id, question=question)
            self.assertEqual(caught.exception.status_code, 422)
            self.assertEqual(calls, [])

    def test_busy_guard(self):
        scope, calls = endpoints()
        scope['busy'] = True
        with self.assertRaises(HTTPError) as caught:
            scope['analyze'](image_id='spectral', question='Calculate NDVI')
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(calls, [])

    def test_adapter_cannot_force_wrong_answer_format(self):
        for mode, question in [('pilot_binary', 'Describe the vegetation'), ('pilot_rural', 'Is there a river?'), ('pilot_binary', 'Is this image rural or urban?')]:
            scope, calls = endpoints()
            with self.assertRaises(HTTPError) as caught:
                scope['analyze'](image_id='rgb', question=question, mode=mode)
            self.assertEqual(caught.exception.status_code, 422)
            self.assertEqual(calls, [])
