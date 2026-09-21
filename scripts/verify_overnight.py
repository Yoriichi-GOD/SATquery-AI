"""Local-only verification; no model inference, training, installs or network."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import evaluation
from routing import route
sys.path.insert(0, str(ROOT/'tests'))
from test_routing import CASES


def main():
    result_dir = ROOT/'results'
    report = dict(scope='Code verification and saved prediction re-scoring; no fresh model evaluation', checks=[])
    commands = [
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_routing.py', '-v'],
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_dispatch.py', '-v'],
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_evaluation.py', '-v'],
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
        [sys.executable, '-m', 'py_compile', 'server.py', 'routing.py', 'stages.py', 'evaluation.py'],
        ['node', '--check', 'web/app.js'],
        ['node', 'tests/test_ui.cjs'],
    ]
    (result_dir/'overnight-development-rescore.json').write_text(json.dumps(evaluation.development(), indent=2)+'\n', encoding='utf-8')
    for command in commands:
        completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        report['checks'].append(dict(command=command, exit_code=completed.returncode, output=completed.stdout.decode('utf-8', errors='replace')))
    report['routing_examples'] = [dict(question=q, expected_with_calibration=e,
                                      calibrated=route(q, ndvi_supported=True), rgb_only=route(q)) for q, e in CASES]
    backup = ROOT/'backups'/'20260907-000855'
    protected = ['geo.py', 'start.ps1']
    protected += [str(p.relative_to(backup)) for name in ['results', 'scripts'] for p in (backup/name).rglob('*') if p.is_file()]
    report['protected_files'] = [dict(path=name, sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),
                                          unchanged=(ROOT/name).read_bytes() == (backup/name).read_bytes()) for name in protected]
    with zipfile.ZipFile(ROOT/'SATquery-evidence-pack.zip') as archive:
        entries = [name for name in archive.namelist() if not name.endswith('/')]
        report['handoff_archive_check'] = dict(files=len(entries),
            mismatches=[name for name in entries if not (ROOT/name).is_file() or (ROOT/name).read_bytes() != archive.read(name)])
    (result_dir/'overnight-verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    for check in report['checks']:
        print(('PASS' if check['exit_code'] == 0 else 'FAIL/BLOCKED'), ' '.join(check['command']))
    print('Protected files unchanged:', all(r['unchanged'] for r in report['protected_files']))
    print('Handoff archive:', report['handoff_archive_check'])
    return 1 if any(c['exit_code'] for c in report['checks']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
