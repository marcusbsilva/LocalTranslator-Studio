"""Local Translator Studio HTTP service and English-only pages."""
import argparse,io,json,zipfile,secrets
from urllib.parse import urlsplit
from model_manager import ModelManager,BusyError
from flask import Flask,request,jsonify,render_template,send_from_directory,send_file
from werkzeug.exceptions import HTTPException
from waitress import serve
from engine import TranslationEngine,LANGUAGES,normalize,detect,InputError,ModelUnavailable
from paths import ROOT

MAX_TEXT=64000;MAX_BATCH=30

def build_app(engine=None):
    app=Flask(__name__,template_folder=str(ROOT/'web/templates'),static_folder=None)
    app.config['MAX_CONTENT_LENGTH']=1024*1024
    translator=engine or TranslationEngine()
    manager=ModelManager(translator);management_token=secrets.token_urlsafe(32)
    app.extensions['model_manager']=manager
    @app.after_request
    def headers(response):
        if request.path in {'/translate','/detect','/languages','/health','/studio/status','/frontend/settings'}:
            response.headers['Access-Control-Allow-Origin']='*'
            response.headers['Access-Control-Allow-Headers']='Content-Type'
            response.headers['Access-Control-Allow-Methods']='GET,POST,OPTIONS'
            response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        return response
    def payload():
        data=request.get_json(silent=True) if request.is_json else request.form.to_dict()
        if not isinstance(data,dict):raise InputError('Send a JSON object or form fields.')
        return data
    def texts(data):
        q=data.get('q');batch=isinstance(q,list);items=q if batch else [q]
        if not items or len(items)>MAX_BATCH:raise InputError('Send between 1 and 30 text items.')
        if any(not isinstance(x,str) for x in items):raise InputError('q must be a string or a list of strings.')
        if any(len(x)>MAX_TEXT for x in items) or sum(map(len,items))>MAX_TEXT:
            raise InputError('A request can contain at most 64,000 text characters in total.')
        return items,batch
    @app.get('/')
    def home():return render_template('index.html',page='translate',title='Translate')
    @app.get('/docs')
    def docs():return render_template('docs.html',page='docs',title='API Guide')
    @app.get('/models')
    def models():return render_template('models.html',page='models',title='Models',state=translator.status(),languages=LANGUAGES,management_token=management_token)
    @app.get('/about')
    def about():return render_template('about.html',page='about',title='About')
    @app.get('/licenses')
    def licenses():return render_template('licenses.html',page='about',title='Licenses',notices=(ROOT/'THIRD-PARTY-NOTICES.md').read_text(encoding='utf-8'))
    @app.get('/studio/assets/<path:name>')
    def assets(name):return send_from_directory(ROOT/'web',name)
    @app.get('/languages')
    def languages():
        with translator.lock:return jsonify([{'code':code,'name':name,'targets':list(LANGUAGES)} for code,name in LANGUAGES.items()])
    def local_management():
        if request.host.split(':')[0] not in {'localhost','127.0.0.1'}:return jsonify(error='Model management is available only on localhost.'),403
        origin=request.headers.get('Origin')
        if origin and urlsplit(origin).netloc!=request.host:return jsonify(error='Cross-origin model management is not allowed.'),403
        return None
    @app.get('/studio/models')
    def model_collection():
        denied=local_management()
        if denied:return denied
        return jsonify(manager.collection())
    @app.post('/studio/models/jobs')
    def model_action():
        denied=local_management()
        if denied:return denied
        if not request.is_json or not secrets.compare_digest(request.headers.get('X-Studio-Token',''),management_token):return jsonify(error='Reload the Models page before managing languages.'),403
        data=payload()
        try:job=manager.start(data.get('action'),data.get('languages',[]))
        except ValueError as error:raise InputError(str(error))
        return jsonify(job),202
    @app.errorhandler(BusyError)
    def busy(error):return jsonify(error=str(error)),409
    @app.get('/studio/status')
    def status():return jsonify(translator.status())
    @app.get('/health')
    def health():return jsonify(status='ok',modelsReady=translator.status()['ready'],version='2.2.0')
    @app.get('/frontend/settings')
    def settings():return jsonify(charLimit=MAX_TEXT,batchLimit=MAX_BATCH,apiKeys=False,defaultSource='auto',defaultTarget='en')
    @app.route('/translate',methods=['POST','OPTIONS'])
    def translate():
        if request.method=='OPTIONS':return '',204
        data=payload();items,batch=texts(data)
        if data.get('format','text')!='text':raise InputError('Only plain-text translation is supported. Use format: text.')
        source=normalize(data.get('source','auto'));target=normalize(data.get('target','en'))
        if target=='auto':raise InputError('Choose a target language; auto is only available as the source.')
        results=[translator.translate(q,source,target) for q in items]
        if not batch:return jsonify(results[0])
        out={'translatedText':[r['translatedText'] for r in results],'routes':[r['route'] for r in results]}
        if source=='auto':out['detectedLanguage']=[r['detectedLanguage'] for r in results]
        return jsonify(out)
    @app.route('/detect',methods=['POST','OPTIONS'])
    def detection():
        if request.method=='OPTIONS':return '',204
        items,batch=texts(payload());results=[[detect(q)] for q in items]
        return jsonify(results if batch else results[0])
    @app.get('/studio/source.zip')
    def source():
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
            for p in ROOT.rglob('*'):
                if p.is_file() and not any(part in {'.venv','data','__pycache__'} for part in p.relative_to(ROOT).parts):z.write(p,p.relative_to(ROOT))
        buffer.seek(0);return send_file(buffer,download_name='local-translator-studio-source.zip',as_attachment=True)
    @app.errorhandler(InputError)
    def bad_input(error):return jsonify(error=str(error)),400
    @app.errorhandler(ModelUnavailable)
    def model_error(error):return jsonify(error=str(error)),503
    @app.errorhandler(HTTPException)
    def http_error(error):
        descriptions={400:'The request could not be read.',404:'This page or endpoint does not exist.',405:'This endpoint does not accept that request method.',413:'The request body is too large.'}
        message=descriptions.get(error.code,'The request could not be completed.')
        if request.path in {'/translate','/detect','/languages','/health','/studio/status','/spec'} or request.method!='GET':return jsonify(error=message),error.code
        return render_template('error.html',title='Request error',page='',code=error.code,message=message),error.code
    @app.errorhandler(Exception)
    def unexpected(error):
        app.logger.exception('Translation service error')
        return jsonify(error='The local engine could not complete this request. Check the model installation and server console.'),500
    return app

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Start Local Translator Studio on this computer.')
    parser.add_argument('--port',type=int,default=5000);args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error('Port must be between 1 and 65535.')
    app=build_app();print(f'Local Translator Studio: http://127.0.0.1:{args.port}',flush=True)
    serve(app,host='127.0.0.1',port=args.port,threads=4,max_request_body_size=1024*1024)
