import os

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'social.settings'
django.setup()

from django.core.cache import cache

cache.set('key', 'value', 60)
value = cache.get('key')

print(value)
