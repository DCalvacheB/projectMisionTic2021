#!/bin/bash
echo "Starting my app"
cd /home/ubuntu/CafBrioche/
source venv/bin/activate
sudo /home/ubuntu/CafBrioche/venv/bin/gunicorn --workers=20 -b 0.0.0.0:443 --certfile=micertificado.pem --keyfile=llaveprivada.pem wsgi:application

