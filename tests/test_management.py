import sys,re,time,json,tempfile,threading,shutil
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import language_registry as registry,install_models as installer,engine as engine_module,model_lock
from engine import TranslationEngine
from server import build_app
import unittest

class ManagementTests(unittest.TestCase):
 def test_management_lifecycle(self):
  # Use isolated lightweight storage. Never remove the VM's real installed weights.
  with tempfile.TemporaryDirectory() as tmp:
   data=Path(tmp);models=data/'models';archives=data/'archives'
   with patch.object(registry,'DATA',data),patch.object(installer,'DATA',data),patch.object(installer,'MODELS',models),patch.object(installer,'ARCHIVES',archives),patch.object(model_lock,'DATA',data),patch.object(engine_module,'MODELS',models):
    engine=TranslationEngine();engine.reload_languages();app=build_app(engine);client=app.test_client()
    html=client.get('/models').data.decode();token=re.search('data-token="([^"]+)"',html).group(1);headers={'X-Studio-Token':token}
    assert client.post('/studio/models/jobs',json={'action':'remove','languages':['ja']}).status_code==403
    assert client.post('/studio/models/jobs',json={'action':'remove','languages':['ja']},headers={**headers,'Origin':'https://example.com'}).status_code==403
    assert client.post('/studio/models/jobs',json={'action':'remove','languages':['ja']},headers={**headers,'Host':'evil.example'}).status_code==403
    assert client.post('/studio/models/jobs',json={'action':'remove','languages':['en']},headers=headers).status_code==400
    for pair in ['ja_en','en_ja']:
     (models/pair).mkdir(parents=True);(models/pair/'weight').write_text('x')
     archives.mkdir(exist_ok=True);(archives/('translate-'+pair+'-1.9.argosmodel')).write_text('x')
    def wait():
     for _ in range(200):
      job=client.get('/studio/models').json['job']
      if job['status'] in ['complete','error']:return job
      time.sleep(.02)
     raise AssertionError('Job timed out')
    res=client.post('/studio/models/jobs',json={'action':'remove','languages':['ja']},headers=headers);assert res.status_code==202
    assert wait()['status']=='complete'
    assert 'ja' not in registry.configured()[0] and 'ja' not in engine_module.LANGUAGES
    assert not (models/'ja_en').exists() and not list(archives.iterdir())
    assert not any('ja' in [m['from_code'],m['to_code']] for m in registry.configured()[1]['models'])
    entered=threading.Event();release=threading.Event()
    def fake_install(models_to_install,progress=None):
     entered.set();release.wait(3);return []
    with patch.object(installer,'install_collection',side_effect=fake_install):
     assert client.post('/studio/models/jobs',json={'action':'install','languages':['ja']},headers=headers).status_code==202
     entered.wait(1)
     assert client.post('/studio/models/jobs',json={'action':'install','languages':['de']},headers=headers).status_code==409
     release.set();assert wait()['status']=='complete'
    assert 'ja' in registry.configured()[0] and 'ja' in engine_module.LANGUAGES
    assert client.get('/languages').json[0]['code']=='en'
    with model_lock.management_lock():
     try:
      with model_lock.management_lock():pass
     except RuntimeError:pass
     else:raise AssertionError('Competing process lock allowed')
    with patch.object(sys,'argv',['install_models.py','--remove-languages','ja']):installer.main()
    assert 'ja' not in registry.configured()[0]
    with patch.object(installer,'install_collection',return_value=[]) as install:installer.add_languages()
    assert not any('ja' in [m['from_code'],m['to_code']] for m in install.call_args.args[0])
    print('PASS web authorization, required English, background removal, archive cleanup, persisted default removal/reinstall, live registry refresh, concurrent job rejection and cross-process lock')
  # Restore global registry after isolation.
  engine.reload_languages()

if __name__=='__main__':unittest.main()
