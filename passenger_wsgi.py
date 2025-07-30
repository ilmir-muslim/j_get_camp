import sys
import os

# Путь до директории, где manage.py
project_path = "/home/venvrusla9m5/j_get_camp"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ["DJANGO_SETTINGS_MODULE"] = "jget_crm.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
