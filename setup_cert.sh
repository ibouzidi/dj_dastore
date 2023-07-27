#!/bin/bash

# Check if 'certs' directory exists. If not, create it.
if [ ! -d "/home/topaze/certs" ]; then
  mkdir /home/topaze/certs
fi

# Generate a new private key and self-signed certificate.
# You should replace '/CN=localhost' with your own domain.
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /home/topaze/certs/dastore.key \
    -out /home/topaze/certs/dastore.pem \
    -subj "/C=US/ST=California/L=San Francisco/O=Your Organization/OU=Your Unit/CN=localhost"

# Change ownership of the 'certs' directory to topaze
chown -R topaze:topaze /home/topaze/certs

# Adjust permissions for the private key
chmod 400 /home/topaze/certs/dastore.key

