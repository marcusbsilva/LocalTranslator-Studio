"""Independent CPU translation pipeline for packaged OpenNMT models."""
from collections import OrderedDict
from pathlib import Path
import json, re, threading, os
import ctranslate2
import sentencepiece
from langdetect import DetectorFactory, detect_langs, LangDetectException
from paths import ROOT, MODELS

DetectorFactory.seed = 0
from language_registry import configured, ALIASES, RAW
LANGUAGES, CATALOG = configured()

class InputError(ValueError): pass
class ModelUnavailable(RuntimeError): pass

def normalize(code):
    if not isinstance(code,str):raise InputError('Language codes must be strings.')
    code=code.strip().replace('_','-').lower()
    result=ALIASES.get(code,code)
    if result not in LANGUAGES and result!='auto':raise InputError('Unsupported language: '+code)
    return result

def detect(text):
    if not text.strip():return {'language':'en','confidence':0.0}
    # Scripts provide reliable signals even for short UI labels.
    if re.search('[\u3040-\u30ff]',text):return {'language':'ja','confidence':99.0}
    if re.search('[\u0e00-\u0e7f]',text):return {'language':'th','confidence':99.0}
    try:
        for candidate in detect_langs(text[:5000]):
            try:code=normalize(candidate.lang)
            except InputError:continue
            return {'language':code,'confidence':round(candidate.prob*100,2)}
    except LangDetectException:pass
    if re.search('[\u0400-\u04ff]',text):return {'language':'ru','confidence':50.0}
    if re.search('[\u4e00-\u9fff]',text):return {'language':'zh-Hans','confidence':50.0}
    return {'language':'en','confidence':0.0}

def pair_name(source,target):return RAW.get(source,source)+'_'+RAW.get(target,target)

def model_ready(path):
    return (path/'model/model.bin').is_file() and ((path/'sentencepiece.model').is_file() or (path/'bpe.model').is_file())

class TranslationEngine:
    def __init__(self,max_cached=3):
        self.lock=threading.RLock();self.cache=OrderedDict();self.max_cached=max_cached
    def reload_languages(self):
        with self.lock:
            names,catalog=configured()
            LANGUAGES.clear();LANGUAGES.update(names);CATALOG.clear();CATALOG.update(catalog)
            self.cache.clear()
    def status(self):
        with self.lock:
            installed=[];missing=[]
            for model in CATALOG['models']:
                name=model['from_code']+'_'+model['to_code']
                (installed if model_ready(MODELS/name) else missing).append(name)
            return {'engine':'CTranslate2','local':True,'ready':not missing,'installed':installed,
                    'missing':missing,'modelCount':len(installed),'expectedModelCount':len(CATALOG['models']),
                    'dailyQuota':None,'maxCharactersPerItem':64000,'maxBatchItems':30,'version':'2.2.0'}
    def _load(self,source,target):
        key=pair_name(source,target)
        if key in self.cache:
            self.cache.move_to_end(key);return self.cache[key]
        folder=MODELS/key
        if not model_ready(folder):raise ModelUnavailable('Missing model '+key+'. Run start.bat --setup-only (Windows) or bash start.sh --setup-only (Linux).')
        if len(self.cache)>=self.max_cached:self.cache.popitem(last=False)
        translator=ctranslate2.Translator(str(folder/'model'),device='cpu',intra_threads=min(os.cpu_count() or 1,4),inter_threads=1)
        if (folder/'sentencepiece.model').is_file():
            tokenizer=sentencepiece.SentencePieceProcessor(model_file=str(folder/'sentencepiece.model'))
            encode=lambda text:tokenizer.encode(text,out_type=str)
            decode=lambda tokens:tokenizer.decode(tokens).replace("▁"," ").strip()
        else:
            from subword_nmt.apply_bpe import BPE
            from sacremoses import MosesTokenizer, MosesDetokenizer
            with (folder/'bpe.model').open(encoding='utf-8') as f:bpe=BPE(f)
            source_tokenizer=MosesTokenizer(lang=source);target_tokenizer=MosesDetokenizer(lang=target)
            encode=lambda text:bpe.process_line(source_tokenizer.tokenize(text,return_str=True)).split()
            decode=lambda tokens:target_tokenizer.detokenize(' '.join(tokens).replace('@@ ','').split())
        value=(translator,encode,decode);self.cache[key]=value;return value
    def _leg(self,text,source,target):
        if source==target or not text.strip():return text
        translator,encode,decode=self._load(source,target)
        output=[]
        # Preserve every newline. Punctuation-based spans are bounded by token count.
        for paragraph in re.split('(\r\n|\r|\n)',text):
            if not paragraph.strip():output.append(paragraph);continue
            spans=re.findall(r'.+?(?:[。！？]+|[.!?]+(?=\s|$)|$)\s*',paragraph)
            if not spans:spans=[paragraph]
            for span in spans:
                lead=re.match(r'^\s*',span).group();tail=re.search(r'\s*$',span).group()
                tokens=encode(span.strip());parts=[tokens[i:i+384] for i in range(0,len(tokens),384)]
                results=translator.translate_batch(parts,beam_size=4,max_input_length=384,max_decoding_length=1024,
                                                   replace_unknowns=True)
                if any(len(result.hypotheses[0])>=1024 for result in results):
                    raise ModelUnavailable('Translation exceeded the model output limit. Split the text into shorter sentences.')
                translated=' '.join(decode(result.hypotheses[0]) for result in results)
                output.append(lead+translated+tail)
        return ''.join(output)
    def translate(self,text,source,target):
        with self.lock:
            source=normalize(source);target=normalize(target)
            if target=='auto':raise InputError('The target language cannot be auto.')
            detected=detect(text) if source=='auto' else None
            actual=detected['language'] if detected else source
            if actual==target:output=text;route=[actual]
            elif actual!='en' and target!='en':
                intermediate=self._leg(text,actual,'en');output=self._leg(intermediate,'en',target);route=[actual,'en',target]
            else:output=self._leg(text,actual,target);route=[actual,target]
            response={'translatedText':output,'route':route}
            if detected:response['detectedLanguage']=detected
            return response
