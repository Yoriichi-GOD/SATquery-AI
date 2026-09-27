"""Software-only checks: new binary hygiene and saved benchmark consistency."""
import collections
import json
import math
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    base = os.environ.get('CI_BASE_SHA', '')
    if not base or set(base) == {'0'}:
        base = 'HEAD^'
    # Include every newly added file in the push/PR, not grandfathered archives.
    paths = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=A', base, 'HEAD'], cwd=ROOT, text=True).splitlines()
    bad = []
    for name in paths:
        p = ROOT / name
        if '__pycache__' in p.parts or p.suffix in {'.pyc', '.pt', '.pth', '.safetensors', '.zip', '.rar', '.7z', '.pem', '.key'} or p.name == '.env':
            bad.append(name)
        elif p.is_file() and p.stat().st_size > 50 * 1024 * 1024:
            bad.append(name)
    if bad:
        raise AssertionError('Unexpected generated/sensitive/oversized files: ' + ', '.join(bad))
    evidence = ROOT / 'paired_lab/evidence/cdvqa-trained-20260928'
    summary = json.loads((evidence / 'final-test-summary.json').read_text())
    for split in ('Test', 'Test2'):
        rows = json.loads((evidence / (split + '-predictions.json')).read_text())
        assert len(rows) == len({r['id'] for r in rows}), 'Duplicate prediction IDs'
        for scope in ('all_official', 'excluding_12_previously_inspected_pairs'):
            selected = rows if scope == 'all_official' else [r for r in rows if not r['previously_inspected']]
            for model in ('paired', 'question_only', 'paired_shuffled_images'):
                expected = summary[split][scope][model]
                assert len(selected) == expected['n']
                assert len({r['image'] for r in selected}) == expected['pairs']
                grouped = collections.defaultdict(list)
                for row in selected:
                    grouped[row['type']].append(row[model] == row['reference'])
                correct = sum(sum(g) for g in grouped.values())
                assert correct == expected['correct']
                assert math.isclose(correct / len(selected), expected['oa'], abs_tol=1e-12)
                assert math.isclose(sum(sum(g)/len(g) for g in grouped.values())/len(grouped), expected['aa'], abs_tol=1e-12)
                for kind, values in grouped.items():
                    assert expected['by_type'][kind]['n'] == len(values)
                    assert expected['by_type'][kind]['correct'] == sum(values)
        print(f'{split}: {len(rows):,} saved predictions; both scopes and all three controls agree with the report.')
    print(f'Publication checks passed; inspected {len(paths)} new files. No GPU inference performed.')

if __name__ == '__main__':
    main()
