#!/bin/bash
# Script de despliegue en EC2 Ubuntu

# ⚠️ EDITA ESTAS VARIABLES ANTES DE EJECUTAR
GITHUB_REPO="https://github.com/TU_USUARIO/TU_REPO.git"
DB_PASSWORD="TuPasswordSeguro123!"

echo "🚀 Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y python3-pip python3-venv nginx mysql-server git

echo "📦 Clonando repositorio..."
cd ~
git clone $GITHUB_REPO red-social-api
cd red-social-api

echo "🐍 Configurando entorno Python..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "🗄️ Configurando MySQL..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS red_social_escolar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'apiuser'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
sudo mysql -e "GRANT ALL PRIVILEGES ON red_social_escolar.* TO 'apiuser'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
sudo mysql red_social_escolar < database_schema.sql

echo "⚙️ Configurando .env..."
cat > .env << EOF
DB_HOST=localhost
DB_PORT=3306
DB_USER=apiuser
DB_PASSWORD=$DB_PASSWORD
DB_NAME=red_social_escolar

SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
EOF

echo "🔧 Configurando Systemd..."
sudo tee /etc/systemd/system/red-social-api.service > /dev/null << EOF
[Unit]
Description=Red Social API
After=network.target

[Service]
User=$USER
WorkingDirectory=$HOME/red-social-api
Environment="PATH=$HOME/red-social-api/venv/bin"
ExecStart=$HOME/red-social-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
EOF

echo "🌐 Configurando Nginx..."
sudo tee /etc/nginx/sites-available/red-social-api > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/red-social-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "🚀 Iniciando API..."
sudo systemctl daemon-reload
sudo systemctl enable red-social-api
sudo systemctl start red-social-api

echo "✅ Despliegue completado!"
echo ""
echo "📊 Comandos útiles:"
echo "  Ver logs: sudo journalctl -u red-social-api -f"
echo "  Reiniciar: sudo systemctl restart red-social-api"
echo "  Estado: sudo systemctl status red-social-api"
echo ""
echo "🌐 API disponible en: http://$(curl -s ifconfig.me)"
echo "📚 Docs: http://$(curl -s ifconfig.me)/docs"
