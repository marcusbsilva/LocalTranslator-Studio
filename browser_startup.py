"""Open the default browser only after this server becomes ready."""
import json,socket,subprocess,threading,urllib.request,webbrowser

def wait_and_open(process,port,stop,open_url=None):
    url=f'http://127.0.0.1:{port}'
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while not stop.is_set() and process.poll() is None:
        try:
            with opener.open(url+'/health',timeout=1) as response:
                ready=response.status==200 and json.load(response).get('status')=='ok'
            if ready and not stop.is_set() and process.poll() is None:
                try:
                    opened=(open_url or webbrowser.open)(url,new=2)
                    if not opened:print('Open the app in your browser: '+url,flush=True)
                except Exception:print('Open the app in your browser: '+url,flush=True)
                return
        except (OSError,ValueError):pass
        stop.wait(.4)

def start_server(python,root,port,open_browser=False):
    # Avoid opening an unrelated server already listening on this port.
    with socket.socket() as probe:
        probe.settimeout(.3)
        if probe.connect_ex(('127.0.0.1',port))==0:
            raise SystemExit(f'Port {port} is already in use. Stop the existing server or choose --port 5001.')
    stop=threading.Event()
    with subprocess.Popen([str(python),'-u',str(root/'server.py'),'--port',str(port)],cwd=root) as process:
        watcher=None
        if open_browser:
            watcher=threading.Thread(target=wait_and_open,args=(process,port,stop),daemon=True)
            watcher.start()
        try:
            returncode=process.wait()
        except KeyboardInterrupt:
            if process.poll() is None:process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            raise
        finally:
            stop.set()
            if watcher:watcher.join(timeout=2)
        if returncode:raise subprocess.CalledProcessError(returncode,process.args)
