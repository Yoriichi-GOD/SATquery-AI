import requests,json,time
from pathlib import Path
cases=[('How many buildings intersect the water candidates?','buildings'),('What area is newly observed water?','water'),('How much road length is exposed?','roads'),('Which settlements lost access to their nearest hospital?','connectivity'),('Write a situation report.','summary'),('How many people died?','limitations'),('कति भवन प्रभावित छन्?','buildings'),('बाढीको क्षेत्रफल कति छ?','water'),('सडकको अवस्था के छ?','roads'),('कुन बस्तीको अस्पताल जाने बाटो बन्द छ?','connectivity'),('स्थिति प्रतिवेदन लेख्नुहोस्।','summary'),('के यो नतिजा निश्चित छ?','limitations')]
results=[]
for question,expected in cases:
 r=requests.post('http://127.0.0.1:8771/route',json={'question':question},timeout=120);r.raise_for_status();d=r.json();results.append({'question':question,'expected':expected,**d,'correct':d['intent']==expected});print(expected,d['intent'],flush=True)
p=Path('docs/copilot-routing-evaluation.json');p.write_text(json.dumps({'scope':'development question-routing smoke test, not independent language or disaster accuracy','correct':sum(r['correct'] for r in results),'count':len(results),'cases':results},indent=2,ensure_ascii=False))
