# 🚀 DEPLOYMENT - MANUAL RÁPIDO

## 1️⃣ CREAR INSTANCIA EC2

1. AWS Console → EC2 → Launch Instance
2. Ubuntu 22.04 LTS
3. Tipo: t3.small
4. Storage: 20GB
5. Security Group:
   - Puerto 22 (SSH)
   - Puerto 80 (HTTP)
   - Puerto 443 (HTTPS)
6. Descargar clave `.pem`

## 2️⃣ CONECTAR A EC2

```bash
chmod 400 tu-clave.pem
ssh -i tu-clave.pem ubuntu@tu-ip-elastica
```

## 3️⃣ INSTALAR DEPENDENCIAS

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx postgresql-client
```

## 4️⃣ CLONAR REPO

```bash
git clone https://tu-repo.git /web/upred-api
cd /web/upred-api
```

## 5️⃣ ENTORNO PYTHON

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

## 6️⃣ CONFIGURAR .env

```bash
nano .env
```

Pegar:
```env
DB_HOST=tu-endpoint-rds.amazonaws.com
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=contraseña_fuerte
DB_NAME=upred_db
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
```

## 7️⃣ CONFIGURAR NGINX

```bash
sudo nano /etc/nginx/sites-available/upred
```

Pegar:
```nginx
upstream upred_app {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    server_name _;
    client_max_body_size 10M;

    location / {
        proxy_pass http://upred_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/upred /etc/nginx/sites-enabled/upred
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 8️⃣ CREAR SERVICIO SYSTEMD

```bash
sudo nano /etc/systemd/system/upred.service
```

Pegar:
```ini
[Unit]
Description=UPRed API
After=network.target

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=/web/upred-api
Environment="PATH=/web/upred-api/venv/bin"
ExecStart=/web/upred-api/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable upred
sudo systemctl start upred
```

## 9️⃣ ABRIR FIREWALL

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

## 10️⃣ VERIFICAR

```bash
sudo systemctl status upred
sudo systemctl status nginx
```

Ir a: `http://tu-ip/docs`

## 1️⃣1️⃣ SSL (Opcional, después de apuntar dominio)

```bash
sudo certbot --nginx -d tu-dominio.com
```

---

## 🔄 CREAR Y CONFIGURAR BASE DE DATOS (RDS)

### 1) Crear la BD en RDS

En AWS → RDS → Create Database:
- Engine: PostgreSQL 15
- DB name: `upred_db`
- Master user: `postgres`
- Password: fuerte
- Security Group: abrir puerto 5432 solo para tu EC2

### 2) Conectar y crear la base

```bash
psql -h tu-endpoint.rds.amazonaws.com -U postgres -d postgres

# En psql:
CREATE DATABASE upred_db;
\q
```

### 3) Cargar el script de la BD

El script ya esta en el repo: `database_schema.sql`

```bash
psql -h tu-endpoint.rds.amazonaws.com -U postgres -d upred_db < database_schema.sql
```

### 4) Verificar

```bash
psql -h tu-endpoint.rds.amazonaws.com -U postgres -d upred_db
\dt
\q
```

---

## 📊 COMANDOS ÚTILES

```bash
# Logs de API
sudo journalctl -u upred -f

# Logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Reiniciar
sudo systemctl restart upred nginx

# Status
sudo systemctl status upred

# Ver .env
cat .env
```

---

**¡Listo! API en producción.**
