"""
ASGI config for language_learning project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "language_learning.settings")

application = get_asgi_application()
