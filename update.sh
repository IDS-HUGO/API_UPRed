#!/bin/bash
# Script de actualización rápida (después del primer deploy)

cd ~/red-social-api
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart red-social-api
echo "✅ API actualizada!"
sudo journalctl -u red-social-api -n 50
