#!/bin/sh
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
#python manage.py makemigrations phonenumber --fake-initial
echo "Make Migrations files done."
python manage.py migrate

exec "$@"
