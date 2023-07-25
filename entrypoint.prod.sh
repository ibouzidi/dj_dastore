#!/bin/sh

set -e

# Activate the virtual environment
. /home/dj_dastore/web/venv/bin/activate

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

echo "Make migrations files"
python manage.py makemigrations account team extbackup folder log
echo "Make Migrations files done."
python manage.py migrate

exec "$@"

