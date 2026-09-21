import hashlib
import json
from pathlib import Path
import random
import zipfile
from PIL import Image, ImageDraw
root = Path(__file__).resolve().parents[1]
out = root / 'results/reliability-20260907/vqa'
data = Path('/root/satquery/evaluation')
assert not (out / 'fresh-review-cases.json').exists()
used = {json.loads(line)['image_id'] for line in (data/'eval_v1.jsonl').read_text().splitlines()}
used |= {c['image_id'] for c in json.loads((out/'frozen-cases.json').read_text())['cases'] if 'image_id' in c}
images = [r for r in json.loads((data/'LR_split_test_images.json').read_text())['images'] if r.get('active') and r['id'] not in used]
random.Random(9072026).shuffle(images)
cases = []
canvas = Image.new('RGB', (768, 556), 'white')
draw = ImageDraw.Draw(canvas)
with zipfile.ZipFile(data/'Images_LR.zip') as z:
    for index, info in enumerate(images[:6]):
        target=out/f'fresh-{info["id"]}.png'
        with z.open(f'Images_LR/{info["id"]}.tif') as handle:
            im=Image.open(handle).convert('RGB')
            im.save(target)
            x,y=(index%3)*256,(index//3)*278
            canvas.paste(im.resize((256,256)),(x,y+22))
            draw.text((x+4,y+4),f'Image {info["id"]}',fill='black')
        cases.append(dict(id=f'fresh-{info["id"]}',image=str(target),source_image=info['original_name'],
                          sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                          question='Describe the major visible features briefly.'))
(out/'fresh-review-cases.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
canvas.save(out/'fresh-review-contact.png')
print([c['id'] for c in cases])
