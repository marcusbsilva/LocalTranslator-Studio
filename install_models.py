"""Download, verify and install portable translation weights without a wrapper engine."""
import argparse,threading,concurrent.futures,hashlib,json,shutil,tempfile,time,urllib.request,zipfile
from pathlib import Path, PurePosixPath
import ctranslate2
from paths import ROOT,DATA,MODELS,ARCHIVES
from language_registry import available,configured,canonical,enable,disable,atomic_json,RAW
RECEIPT_LOCK=threading.Lock()
LOCAL_RECEIPTS=DATA/'download-receipts.json'

RECEIPTS={m['code']:m for m in json.loads((ROOT/'model-downloads.json').read_text(encoding='utf-8'))}

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()

def validate(folder):
    if not ((folder/'sentencepiece.model').exists() or (folder/'bpe.model').exists()):raise ValueError('Tokenizer missing')
    translator=ctranslate2.Translator(str(folder/'model'),device='cpu');del translator

def download(model,progress=None):
    report=progress or (lambda event:None)
    ARCHIVES.mkdir(parents=True,exist_ok=True)
    file=ARCHIVES/(model['code']+'-'+model['package_version']+'.argosmodel')
    pinned=RECEIPTS.get(model['code'],{})
    expected=pinned.get('sha256') if str(pinned.get('version'))==str(model['package_version']) else None
    key=model['code']+':'+str(model['package_version'])
    with RECEIPT_LOCK:
        local=json.loads(LOCAL_RECEIPTS.read_text(encoding='utf-8')) if LOCAL_RECEIPTS.exists() else {}
        if expected is None:expected=local.get(key,{}).get('sha256')
    if expected and file.exists() and digest(file)==expected:
        report({'model':model['code'],'stage':'cached','message':'Using cached '+model['code']});return model,file
    for attempt in range(3):
        try:
            print('Downloading '+model['code'],flush=True)
            report({'model':model['code'],'stage':'downloading','message':'Downloading '+model['code']})
            req=urllib.request.Request(model['links'][0]+'?download=1&full=1',headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=120) as response,file.with_suffix('.part').open('wb') as out:
                received=0;total=int(response.headers.get('Content-Length',0) or 0)
                while block:=response.read(1024*1024):
                    out.write(block);received+=len(block)
                    report({'model':model['code'],'stage':'downloading','received':received,'total':total,'message':'Downloading '+model['code']})
            checksum=digest(file.with_suffix('.part'))
            if expected and checksum!=expected:raise ValueError('Model checksum mismatch; the download was not installed.')
            file.with_suffix('.part').replace(file)
            if expected is None:
                # Upstream does not publish hashes for these optional archives. Record the
                # first HTTPS download for future integrity checks, not publisher verification.
                with RECEIPT_LOCK:
                    local=json.loads(LOCAL_RECEIPTS.read_text(encoding='utf-8')) if LOCAL_RECEIPTS.exists() else {}
                    local[key]={'sha256':checksum,'url':model['links'][0],'bytes':file.stat().st_size}
                    atomic_json(LOCAL_RECEIPTS,local)
            return model,file
        except Exception:
            if attempt==2:raise
            time.sleep(2*(attempt+1))

def install_archive(model,file):
    MODELS.mkdir(parents=True,exist_ok=True)
    destination=MODELS/(model['from_code']+'_'+model['to_code'])
    with tempfile.TemporaryDirectory(prefix='install-',dir=MODELS) as temporary:
        temp=Path(temporary)/"package";temp.mkdir()
        with zipfile.ZipFile(file) as archive:
            if archive.testzip():raise ValueError('Corrupt model archive')
            for entry in archive.infolist():
                parts=PurePosixPath(entry.filename).parts
                if len(parts)<2:continue
                if any(p in {'.','..'} or ':' in p for p in parts) or '\\' in entry.filename or entry.filename.startswith('/'):
                    raise ValueError('Unsafe archive path')
                relative=Path(*parts[1:])
                if not (parts[1]=='model' or (len(parts)==2 and (parts[1] in {'sentencepiece.model','bpe.model'} or 'readme' in parts[1].lower() or 'license' in parts[1].lower()))):continue
                if entry.is_dir():continue
                path=temp/relative;path.parent.mkdir(parents=True,exist_ok=True)
                with archive.open(entry) as src,path.open('wb') as dst:shutil.copyfileobj(src,dst)
        (temp/'metadata.json').write_text(json.dumps({k:model[k] for k in ['from_code','to_code','package_version']},indent=2),encoding='utf-8')
        validate(temp)
        if destination.exists():shutil.rmtree(destination)
        shutil.move(str(temp),str(destination))

def adopt_previous_installation(model):
    legacy=DATA/'share'/'argos-translate'/'packages'
    name=model['from_code']+'_'+model['to_code'];destination=MODELS/name
    if not legacy.exists():return False
    for path in legacy.iterdir():
        meta=path/'metadata.json'
        if not meta.is_file():continue
        try:
            data=json.loads(meta.read_text(encoding='utf-8'))
            if (data.get('from_code'),data.get('to_code'))!=(model['from_code'],model['to_code']):continue
            if str(data.get('package_version'))!=str(model['package_version']):continue
            validate(path);MODELS.mkdir(parents=True,exist_ok=True)
            # Reuse weights only. Old runtime files and sentence detectors are not copied.
            with tempfile.TemporaryDirectory(prefix='reuse-',dir=MODELS) as temporary:
                temp=Path(temporary)/"package";temp.mkdir();shutil.copytree(path/'model',temp/'model')
                for p in path.iterdir():
                    if p.is_file() and (p.name in {'sentencepiece.model','bpe.model'} or 'readme' in p.name.lower() or 'license' in p.name.lower()):shutil.copyfile(p,temp/p.name)
                (temp/'metadata.json').write_text(json.dumps({k:model[k] for k in ['from_code','to_code','package_version']},indent=2),encoding='utf-8')
                if destination.exists():shutil.rmtree(destination)
                shutil.move(str(temp),str(destination))
            return True
        except (OSError,ValueError,RuntimeError):continue
    return False

def install_collection(models,progress=None):
    report=progress or (lambda event:None)
    missing=[];failures=[]
    for m in models:
        path=MODELS/(m['from_code']+'_'+m['to_code'])
        try:
            validate(path);report({'model':m['code'],'stage':'ready','message':'Ready '+m['code']});continue
        except (OSError,ValueError,RuntimeError):pass
        if adopt_previous_installation(m):print('Reused '+m['code'],flush=True)
        else:missing.append(m)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(download,m,report):m for m in missing}
        for future in concurrent.futures.as_completed(futures):
            m=futures[future]
            try:
                m,file=future.result();report({'model':m['code'],'stage':'validating','message':'Validating '+m['code']});install_archive(m,file);print('Installed '+m['code'],flush=True)
                report({'model':m['code'],'stage':'ready','message':'Installed '+m['code']})
            except Exception as e:
                failures.append({'model':m['code'],'error':str(e)});print('FAILED '+m['code']+': '+str(e),flush=True)
                report({'model':m['code'],'stage':'error','message':str(e)})
    return failures

def add_languages(codes=None,all_languages=False,refresh=False,progress=None):
    options=available(refresh)
    requested=list(options) if all_languages else list(dict.fromkeys(canonical(c) for c in (codes or [])))
    invalid=[c for c in requested if c!='en' and c not in options]
    if invalid:raise ValueError('Unavailable language code(s): '+', '.join(invalid)+'. Use --list-languages.')
    names,catalog=configured()
    additions={code:options[code] for code in requested if code!='en' and code not in names}
    models=list(catalog['models'])
    for entry in additions.values():models.extend(entry['models'])
    failures=install_collection(models,progress)
    failed_codes={f['model'] for f in failures}
    for code,entry in additions.items():
        if not any(m['code'] in failed_codes for m in entry['models']):
            enable(code,entry);print('Enabled '+entry['name']+' ('+code+').',flush=True)
    atomic_json(DATA/'model-status.json',{'failures':failures})
    if failures:raise RuntimeError('Setup incomplete. Repeat the same operation to retry; installed models are preserved. '+ '; '.join(f['model']+': '+f['error'] for f in failures))
    legacy=DATA/'share'/'argos-translate'
    if legacy.exists():shutil.rmtree(legacy)
    _,catalog=configured()
    print(f"All {len(catalog['models'])} configured translation models are ready.",flush=True)

def remove_languages(codes,progress=None):
    report=progress or (lambda event:None)
    requested=list(dict.fromkeys(canonical(c) for c in codes))
    names,_=configured()
    if 'en' in requested:raise ValueError('English is the bridge language and cannot be removed.')
    invalid=[c for c in requested if c not in names]
    if invalid:raise ValueError('Language is not configured: '+', '.join(invalid))
    for code in requested:
        raw=RAW.get(code,code)
        # Disable first: a failed filesystem deletion must not leave an active broken route.
        disable(code)
        for pair in [raw+'_en','en_'+raw]:
            folder=MODELS/pair
            if folder.exists():shutil.rmtree(folder)
            if ARCHIVES.exists():
                for archive in ARCHIVES.glob('translate-'+pair+'-*'):
                    if archive.is_file():archive.unlink()
        report({'stage':'removed','message':'Removed '+names[code]+' ('+code+').'})
        print('Removed '+names[code]+' ('+code+').',flush=True)

def main():
    from model_lock import management_lock
    parser=argparse.ArgumentParser(description='Install or remove local translation model pairs.')
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--install-languages',nargs='+',metavar='CODE')
    group.add_argument('--install-all-languages',action='store_true')
    group.add_argument('--remove-languages',nargs='+',metavar='CODE')
    parser.add_argument('--refresh-catalog',action='store_true')
    args=parser.parse_args()
    try:
        with management_lock():
            if args.remove_languages:remove_languages(args.remove_languages)
            else:add_languages(args.install_languages,args.install_all_languages,args.refresh_catalog)
    except (ValueError,RuntimeError,OSError) as error:raise SystemExit(str(error))
if __name__=='__main__':main()
