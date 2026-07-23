#!/bin/sh
set -e
python setup_db.py
exec gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 8 --timeout 120 --preload "run:app"
