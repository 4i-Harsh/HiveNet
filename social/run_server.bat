@echo off
set DJANGO_SETTINGS_MODULE=social.settings
set PYTHONPATH=%cd%
daphne -b 127.0.0.1 -p 8000 social.asgi:application