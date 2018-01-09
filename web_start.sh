#!/bin/bash

# Get current directory

# Set up any db change
python /usr/src/app/manage.py makemigrations


# Updates/Creates Database
python /usr/src/app/manage.py migrate

# Starts server
python -u /usr/src/app/manage.py runserver 0.0.0.0:8080
