import sys
import os

INTERP = os.path.expanduser('/home/eukefkfs/eukexpress_api/venv/bin/python')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

os.environ['APP_ENV'] = 'production'

from app.main import app as application