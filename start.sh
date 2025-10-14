#!/bin/bash
echo "Starting Work Management Application..."
gunicorn --bind 0.0.0.0:$PORT app:app