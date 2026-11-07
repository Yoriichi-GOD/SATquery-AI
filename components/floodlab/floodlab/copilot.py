"""Evidence-only answer rendering. Model output selects a topic, never a number."""
import hashlib,json
from pathlib import Path
INTENTS={'summary','water','buildings','roads','connectivity','limitations'}
def frozen_result(root):
 root=Path(root);freeze=json.loads((root/'freeze.json').read_text())
 for name in ('result.json','manifest.json','connectivity.json'):
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=freeze['files'].get(name):raise ValueError('Frozen evidence mismatch')
 return json.loads((root/'result.json').read_text())
def render(result,intent,language):
 if intent not in INTENTS or language not in ('en','ne'):raise ValueError('Unsupported answer category/language')
 s=result['summary'];ne=language=='ne';sections=[];fields=[]
 def add(text,keys):sections.append(text);fields.extend(keys)
 if intent in ('summary','water'):
  add(f"नयाँ पानीका सम्भावित क्षेत्र: {s['new_water_m2']:,.0f} m² ({s['new_water_pixels']} पिक्सेल)।" if ne else f"New-water candidate area: {s['new_water_m2']:,.0f} m² ({s['new_water_pixels']} pixels).",['new_water_m2','new_water_pixels'])
 if intent in ('summary','buildings'):
  add(f"सम्भावित पानी क्षेत्रसँग जुधेका नक्साङ्कित भवन: {s['exposed_buildings']}।" if ne else f"Mapped buildings intersecting water candidates: {s['exposed_buildings']}.",['exposed_buildings'])
 if intent in ('summary','roads'):
  add(f"पानीका सम्भावित क्षेत्रसँग जुधेको सडक/पुल लम्बाइ: {s['exposed_road_m']:,.2f} m; पुल विशेषता: {s['exposed_bridge_features']}।" if ne else f"Intersected road/bridge length: {s['exposed_road_m']:,.2f} m; intersected bridge features: {s['exposed_bridge_features']}.",['exposed_road_m','exposed_bridge_features'])
 if intent in ('summary','connectivity'):
  if not s.get('connectivity_assessed',False):add('बस्तीको पहुँचबारे निश्चित निष्कर्ष उपलब्ध छैन। अपूर्ण सडक वा अवलोकनका कारण अवस्था अज्ञात छ।' if ne else 'Settlement isolation is unresolved. Network boundaries, snapping or missing observations prevent a definitive access conclusion.',[])
  else:add(f"मोडेलका धारणाअनुसार सम्भावित पहुँच विच्छेद भएका बस्ती: {s['potentially_cut_off']}।" if ne else f"Potentially cut-off settlements under the stated disruption assumptions: {s['potentially_cut_off']}.",['potentially_cut_off'])
 if intent=='limitations':add('यो प्रणालीले मृत्यु संख्या, उद्धार आदेश वा वास्तविक क्षति पुष्टि गर्न सक्दैन। मलबा वर्गीकरण र स्वतन्त्र शुद्धता परीक्षण पूरा भएका छैनन्।' if ne else 'This run cannot establish casualties, evacuation instructions or confirmed damage. Debris classification and independent accuracy validation are incomplete.',[])
 add('यो अप्रमाणित पानी-परिवर्तन अनुमान हो, पुष्टि भएको बाढी क्षति होइन। नेपाली पाठको मानव समीक्षा बाँकी छ।' if ne else 'This is an unvalidated water-change baseline, not confirmed flood damage.',[])
 return {'answer':'\n\n'.join(sections),'language':language,'intent':intent,'run_id':result['run_id'],'synthetic':result['synthetic'],'citations':[{'file':'result.json','pointer':'/summary/'+k,'value':s[k]} for k in dict.fromkeys(fields)],'method':'bilingual evidence templates insert only saved map calculations; routing method reported separately','limitations':result['limitations']}
