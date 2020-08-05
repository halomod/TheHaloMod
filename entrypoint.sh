#!/usr/bin/env sh

gunicorn --bind :8000 TheHaloMod.wsgi:application

