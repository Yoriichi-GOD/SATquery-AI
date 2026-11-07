from pathlib import Path
import json
from huggingface_hub import HfApi,snapshot_download
repo='Qwen/Qwen3-0.6B';info=HfApi().model_info(repo);revision=info.sha
print('Downloading pinned Qwen3-0.6B revision',revision,flush=True)
path=snapshot_download(repo,revision=revision,allow_patterns=['*.json','*.safetensors','*.txt','*.jinja','LICENSE','README.md'],max_workers=2)
Path('docs/copilot-model.json').write_text(json.dumps({'repo':repo,'revision':revision,'path':path,'purpose':'bounded bilingual situation-report question routing; numbers from frozen evidence'},indent=2))
print('Model download complete',flush=True)
