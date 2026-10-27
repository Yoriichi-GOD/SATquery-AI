"""Runtime locations shared by services and setup tools; no model imports."""
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent


def location(name, default):
    return Path(os.environ.get(name, str(default))).expanduser().resolve()


def asset_root():
    """Respect an explicit root; inaccessible legacy installs are unavailable."""
    fallback = Path.home() / '.local/share/satquery'
    if 'SATQUERY_ASSET_ROOT' in os.environ:
        return location('SATQUERY_ASSET_ROOT', fallback)
    legacy = Path('/root/satquery')
    try:
        if legacy.is_dir():
            return legacy
    except PermissionError:
        pass
    return fallback.resolve()


# Preserve accessible existing installs without requiring root privileges.
ASSET_ROOT = asset_root()
PAIRED = location('SATQUERY_PAIRED_DIR', ASSET_ROOT / 'paired-lab')
GROUNDING = location('SATQUERY_GROUNDING_DIR', ASSET_ROOT / 'grounding-lab')
APP_DATA = location('SATQUERY_APP_DATA', ASSET_ROOT / 'app-data')
ADAPTER = location('SATQUERY_VQA_ADAPTER', ASSET_ROOT / 'experiments/lora-pilot-v1/adapter')
CDVQA = location('SATQUERY_CDVQA_MODEL_DIR', ASSET_ROOT / 'cdvqa')
ENCODER = location('SATQUERY_CDVQA_ENCODER', Path(os.environ.get('TORCH_HOME', str(Path.home() / '.cache/torch')))
                   / 'hub/checkpoints/resnet50-11ad3fa6.pth')
WATER = location('SATQUERY_WATER_CHECKPOINT', REPO / 'paired_lab/checkpoints/water-v1.pt')
VQA_REPO = 'AdaptLLM/remote-sensing-Qwen2-VL-2B-Instruct'
VQA_REVISION = '7f5dd71bf0f40c282193d50160e848a387a08ffe'


def read_manifest(path):
    path = Path(path)
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'Cannot read runtime manifest {path}. Run python scripts/preflight.py '
                         'and follow docs/ASSETS.md; no model was substituted.') from exc


def manifest_path(record, manifest):
    """New manifests may use relative paths; historical absolute paths still work."""
    path = Path(record['path']).expanduser()
    return path if path.is_absolute() else Path(manifest).parent / path


def vqa_path():
    explicit = os.environ.get('SATQUERY_VQA_MODEL')
    if not explicit and (ASSET_ROOT/'models/vqa').is_dir():
        explicit = str(ASSET_ROOT/'models/vqa')
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_dir():
            raise ValueError(f'Missing VQA snapshot: {path}. See docs/ASSETS.md.')
        receipt=path/'satquery-source.json'
        if receipt.exists():
            if read_manifest(receipt)!={'repo':VQA_REPO,'revision':VQA_REVISION}:
                raise ValueError('VQA snapshot provenance differs from the pinned model; restore the documented release.')
        elif path.name!=VQA_REVISION:
            raise ValueError('VQA snapshot provenance is unknown. Use scripts/provision_assets.py --workflow vqa or a pinned Hugging Face snapshot directory.')
        return str(path)
    from huggingface_hub import snapshot_download
    return snapshot_download(VQA_REPO, revision=VQA_REVISION, local_files_only=True)
