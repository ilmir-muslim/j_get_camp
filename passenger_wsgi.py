from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
import os, sys
activate_this = '/home/r/rusla9m5/j_get_camp/venv/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})
sys.path.insert(0, '/home/r/rusla9m5/j_get_camp')
sys.path.insert(1, '/home/r/rusla9m5/j_get_camp/venv/lib/python3.11/site-packages')
os.environ['DJANGO_SETTINGS_MODULE'] = 'jget_crm.settings'
application = StaticFilesHandler(get_wsgi_application())
