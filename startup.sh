#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Run a case command
case $1 in
    server)
    # Pull in Docker env
    BASE_PATH=/home/dj_dastore/web

    # Check if requirements.txt exists, and there is no env already built
    if [ -e $BASE_PATH/requirements.txt ] && [ ! -d $BASE_PATH/venv ]; then
        python3 -m venv $BASE_PATH/venv
        source $BASE_PATH/venv/bin/activate
        pip install -r $BASE_PATH/requirements.txt
        pip install opencv-python-headless
        pip uninstall python-decouple && pip install python-decouple
    else
        source $BASE_PATH/venv/bin/activate
    fi
    # Change to $BASE_PATH
    cd $BASE_PATH
    # Make django migrations
    python manage.py makemigrations
    python manage.py migrate
    echo "Made Migrations..."
    # Add collect static
    python manage.py collectstatic --noinput
    # Startup apache2 server
    apache2ctl -D FOREGROUND
    ;;

esac

