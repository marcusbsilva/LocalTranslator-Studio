"""Native setup and startup; the isolated runtime is rebuilt once during upgrade."""
import argparse,hashlib,os,shutil,subprocess,sys,venv
from browser_startup import start_server
from pathlib import Path
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Install models and start Local Translator Studio.')
parser.add_argument('--setup-only',action='store_true');parser.add_argument('--skip-install',action='store_true');parser.add_argument('--port',type=int,default=5000);language_options=parser.add_mutually_exclusive_group()
language_options.add_argument('--list-languages',action='store_true',help='List optional languages and exit.')
language_options.add_argument('--install-languages',nargs='+',metavar='CODE',help='Add languages by code, then exit (e.g. de it ko).')
language_options.add_argument('--remove-languages',nargs='+',metavar='CODE',help='Remove language models and their cached archives, then exit.')
language_options.add_argument('--install-all-languages',action='store_true',help='Install every available English bidirectional pair, then exit.')
parser.add_argument('--refresh-catalog',action='store_true',help='Refresh the official model catalogue before listing or installation.')
parser.add_argument('--open-browser',action=argparse.BooleanOptionalAction,default=False,help='Open the app once the local server is ready.')
args=parser.parse_args()
if not 1<=args.port<=65535:parser.error('Port must be between 1 and 65535.')
if args.skip_install and (args.list_languages or args.install_languages or args.install_all_languages or args.remove_languages or args.refresh_catalog):parser.error('--skip-install cannot be combined with language management.')
if args.refresh_catalog and not (args.list_languages or args.install_languages or args.install_all_languages):parser.error('--refresh-catalog requires a language management option.')
if args.list_languages:
    from language_registry import available,configured
    names,_=configured()
    try:
        for code,entry in available(args.refresh_catalog).items():print(f"{code:8} {entry['name']:24} {'Configured' if code in names else 'Available'}")
    except Exception as error:raise SystemExit('Could not read the model catalogue: '+str(error))
    raise SystemExit(0)
if not (3,10)<=sys.version_info[:2]<=(3,12) or sys.maxsize<=2**32:
    raise SystemExit('Use 64-bit Python 3.10, 3.11 or 3.12.')
folder=ROOT/'.venv';python=folder/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
marker=folder/'studio-runtime-v2';fingerprint=hashlib.sha256((ROOT/'requirements.txt').read_bytes()).hexdigest()
try:
    if args.skip_install:
        if not python.exists() or not marker.exists():raise SystemExit('Setup has not completed. Run the launcher without --skip-install first.')
    else:
        if folder.exists() and not marker.exists():
            print('Rebuilding the isolated Python runtime. Model files are preserved.',flush=True)
            shutil.rmtree(folder)
        if not python.exists():venv.EnvBuilder(with_pip=True).create(folder)
        if not marker.exists() or marker.read_text()!=fingerprint:
            print('Installing application dependencies...',flush=True)
            subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)
            marker.write_text(fingerprint)
        install_options=[]
        if args.install_languages:install_options=['--install-languages',*args.install_languages]
        elif args.install_all_languages:install_options=['--install-all-languages']
        elif args.remove_languages:install_options=['--remove-languages',*args.remove_languages]
        if args.refresh_catalog:install_options.append('--refresh-catalog')
        subprocess.run([str(python),'-u',str(ROOT/'install_models.py'),*install_options],cwd=ROOT,check=True)
    if not (args.setup_only or args.install_languages or args.install_all_languages or args.remove_languages):start_server(python,ROOT,args.port,args.open_browser)
except subprocess.CalledProcessError as e:raise SystemExit(e.returncode)
except KeyboardInterrupt:pass
