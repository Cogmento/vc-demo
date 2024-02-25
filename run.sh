#!/bin/bash 
gunicorn --conf conf.py --bind 0.0.0.0:8000 main:app 