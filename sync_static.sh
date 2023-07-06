#!/bin/bash

# Variables
STATIC_LOCAL_PATH="/home/topaze/dj_dastore_docker/dj_dastore/static_cdn/"
MEDIA_LOCAL_PATH="/home/topaze/dj_dastore_docker/dj_dastore/media_cdn/"
REMOTE_USER="amethyste"
REMOTE_IP="192.168.0.6"
STATIC_REMOTE_PATH="/home/amethyste/web/static_cdn/"
MEDIA_REMOTE_PATH="/home/amethyste/web/media_cdn/"

# Sync files
rsync -azP -e "ssh -i ~/.ssh/id_rsa_rsync" "${STATIC_LOCAL_PATH}" "${REMOTE_USER}@${REMOTE_IP}:${STATIC_REMOTE_PATH}"
rsync -azP -e "ssh -i ~/.ssh/id_rsa_rsync" "${MEDIA_LOCAL_PATH}" "${REMOTE_USER}@${REMOTE_IP}:${MEDIA_REMOTE_PATH}"
echo "Sync completed at $(date)"

