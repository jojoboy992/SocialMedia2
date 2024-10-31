"""
WSGI config for SocialMedia project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append(os.path.join(os.path.dirname(__file__), "SocialMedia"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SocialMedia.settings")

application = get_wsgi_application()


# import os
# import sys
# #
# ## assuming your django settings file is at '/home/joetex/mysite/mysite/settings.py'
# ## and your manage.py is is at '/home/joetex/mysite/manage.py'
# path = '/home/joetex/SocialMedia/'
# if path not in sys.path:
#     sys.path.append(path)

# os.environ['DJANGO_SETTINGS_MODULE'] = 'SocialMedia.settings'
# #
# ## then:
# from django.core.wsgi import get_wsgi_application
# application = get_wsgi_application()
