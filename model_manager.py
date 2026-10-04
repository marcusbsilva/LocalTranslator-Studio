"""Background model jobs for the local management page."""
import copy,threading,uuid
from language_registry import available,configured,canonical,RAW
from model_lock import management_lock
from install_models import add_languages,remove_languages
class BusyError(RuntimeError):pass
class ModelManager:
 def __init__(self,engine):
  self.engine=engine;self.lock=threading.RLock();self.job=None
 def snapshot(self):
  with self.lock:return copy.deepcopy(self.job)
 def collection(self):
  names,_=configured();options=available();state=self.engine.status();installed=set(state['installed'])
  languages=[]
  for code,entry in options.items():
   raw=RAW.get(code,code)
   languages.append({'code':code,'name':entry['name'],'configured':code in names,
    'toEnglish':raw+'_en' in installed,'fromEnglish':'en_'+raw in installed})
  # Previously configured pairs may no longer be listed by a refreshed upstream index.
  for code,name in names.items():
   if code=='en' or code in options:continue
   raw=RAW.get(code,code);languages.append({'code':code,'name':name,'configured':True,
    'toEnglish':raw+'_en' in installed,'fromEnglish':'en_'+raw in installed})
  languages.sort(key=lambda item:(not item['configured'],item['name'].lower()))
  return {'languages':languages,'state':state,'job':self.snapshot()}
 def start(self,action,codes):
  if action not in {'install','remove','refresh'}:raise ValueError('Unknown model action.')
  if not isinstance(codes,list) or any(not isinstance(code,str) for code in codes):raise ValueError('languages must be a list of language codes.')
  codes=list(dict.fromkeys(canonical(code) for code in codes))
  if action!='refresh':
   if not codes:raise ValueError('Select at least one language.')
   options=available();names,_=configured()
   if 'en' in codes:raise ValueError('English is the bridge language and cannot be managed separately.')
   allowed=options if action=='install' else names
   if any(code not in allowed for code in codes):raise ValueError('One or more language codes are unavailable for this action.')
  with self.lock:
   if self.job and self.job['status'] in {'queued','running'}:raise BusyError('Another model operation is running.')
   self.job={'id':uuid.uuid4().hex,'action':action,'languages':codes,'status':'queued',
             'message':'Starting operation…','events':[],'received':0,'total':0}
   threading.Thread(target=self._run,args=(action,codes),daemon=True).start()
   return self.snapshot()
 def report(self,event):
  with self.lock:
   self.job.update({key:event.get(key,0 if key in {'received','total'} else '') for key in ['message','received','total']})
   previous=self.job['events'][-1] if self.job['events'] else None
   if previous and event.get('stage')=='downloading' and previous.get('model')==event.get('model') and previous.get('stage')=='downloading':self.job['events'][-1]=event
   else:self.job['events'].append(event)
   self.job['events']=self.job['events'][-80:]
 def _run(self,action,codes):
  try:
   with self.lock:self.job['status']='running'
   with management_lock():
    if action=='install':add_languages(codes,progress=self.report)
    elif action=='remove':
     self.report({'message':'Waiting for active translations to finish…'})
     with self.engine.lock:
      self.engine.cache.clear();remove_languages(codes,progress=self.report)
    else:
     self.report({'message':'Refreshing the official model catalogue…'});available(refresh=True)
   self.engine.reload_languages()
   with self.lock:self.job.update(status='complete',message='Operation complete. The language collection is up to date.',received=0,total=0)
  except Exception as error:
   self.engine.reload_languages()
   with self.lock:self.job.update(status='error',message=str(error),received=0,total=0)
