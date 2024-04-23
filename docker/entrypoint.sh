#!/bin/bash
set -ex

# Build the settings_local.py file from the template using environment variables
envsubst < docker/settings_local.py.template > settings_local.py

python manage.py syncdb --all --noinput
python manage.py migrate --fake --noinput

exec "$@"