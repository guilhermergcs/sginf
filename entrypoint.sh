#!/bin/sh
set -e
python setup_db.py
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 "run:app"
