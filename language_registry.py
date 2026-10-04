"""Bundled upstream catalogue and the user's successfully installed extra routes."""
import json,re
from paths import ROOT,DATA
INDEX_URL='https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json'
DEFAULT_NAMES={'en':'English','zh-Hans':'Chinese (Simplified)','zh-Hant':'Chinese (Traditional)',
 'vi':'Vietnamese','th':'Thai','ru':'Russian','pt':'Portuguese','es':'Spanish','fr':'French','ja':'Japanese'}
ALIASES={'zh':'zh-Hans','zt':'zh-Hant','zh-cn':'zh-Hans','zh-tw':'zh-Hant','zh-hans':'zh-Hans',
 'zh-hant':'zh-Hant','pt-br':'pt','ptbr':'pt','nb-no':'nb','no':'nb'}
RAW={'zh-Hans':'zh','zh-Hant':'zt'}
def public(code):return {'zh':'zh-Hans','zt':'zh-Hant'}.get(code,code)
def canonical(code):return ALIASES.get(code.strip().replace('_','-').lower(),code.strip().lower())
def atomic_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8');temp.replace(path)
def available(refresh=False):
 path=DATA/'available-models.json'
 if refresh:
  import urllib.request
  request=urllib.request.Request(INDEX_URL,headers={'User-Agent':'LocalTranslatorStudio/2.1'})
  with urllib.request.urlopen(request,timeout=60) as response:items=json.load(response)
 else:items=json.loads((path if path.exists() else ROOT/'available-models.json').read_text(encoding='utf-8'))
 pairs={}
 for item in items:
  source,target=item.get('from_code',''),item.get('to_code','')
  if not re.fullmatch('[a-z]{2,3}',source) or not re.fullmatch('[a-z]{2,3}',target):continue
  if 'en' not in {source,target} or source==target:continue
  item=dict(item);item['links']=[url for url in item.get('links',[]) if url.startswith('https://argos-net.com/')]
  if not item['links']:continue
  item['code']='translate-'+source+'_'+target
  version=str(item.get('package_version',''))
  if not re.fullmatch(r'\d+(?:\.\d+)*',version):continue
  old=pairs.get((source,target))
  if old is None or tuple(map(int,version.split('.')))>tuple(map(int,str(old['package_version']).split('.'))):pairs[source,target]=item
 result={}
 for source,target in sorted(pairs):
  if target=='en' and ('en',source) in pairs:
   result[public(source)]={'name':DEFAULT_NAMES.get(public(source),pairs[source,target]['from_name']),
                         'models':[pairs[source,target],pairs['en',source]]}
 if refresh:atomic_json(path,list(pairs.values()))
 return result

def configured():
 base=json.loads((ROOT/'model-catalog.json').read_text(encoding='utf-8'))
 disabled_path=DATA/'disabled-languages.json'
 disabled=set(json.loads(disabled_path.read_text(encoding='utf-8'))) if disabled_path.exists() else set()
 names={c:n for c,n in DEFAULT_NAMES.items() if c not in disabled or c=='en'}
 models=[m for m in base['models'] if public(m['from_code']) not in disabled and public(m['to_code']) not in disabled]
 extra=DATA/'extra-languages.json'
 if extra.exists():
  for code,entry in json.loads(extra.read_text(encoding='utf-8')).items():
   if code in names or code in disabled:continue
   names[code]=entry['name'];models.extend(entry['models'])
 return names,{'models':models,'languages':list(names)}
def enable(code,entry):
 path=DATA/'extra-languages.json';extras=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
 extras[code]=entry;atomic_json(path,extras)
 disabled_path=DATA/'disabled-languages.json'
 disabled=json.loads(disabled_path.read_text(encoding='utf-8')) if disabled_path.exists() else []
 atomic_json(disabled_path,[c for c in disabled if c!=code])

def disable(code):
 path=DATA/'disabled-languages.json'
 disabled=set(json.loads(path.read_text(encoding='utf-8'))) if path.exists() else set()
 disabled.add(code);atomic_json(path,sorted(disabled))
 extras_path=DATA/'extra-languages.json'
 if extras_path.exists():
  extras=json.loads(extras_path.read_text(encoding='utf-8'));extras.pop(code,None);atomic_json(extras_path,extras)
