#!/bin/bash

# Step 1: Take down existing Docker containers and volumes
docker-compose down -v

# Step 2: Build and launch the Docker containers
docker-compose -f docker-compose.prod.yml up -d --build

# Step 3: Run database migrations
#docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

# Step 4: Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear

# Step 5: Sync the static and media files to ubuntu_b
#rsync -azP -e "ssh -i ~/.ssh/id_rsa_rsync" /home/dj_dastore/web/static_cdn/ amethyste@192.168.0.6:/home/amethyste/web/static_cdn/
#rsync -azP -e "ssh -i ~/.ssh/id_rsa_rsync" /home/dj_dastore/web/media_cdn/ amethyste@192.168.0.6:/home/amethyste/web/media_cdn/

