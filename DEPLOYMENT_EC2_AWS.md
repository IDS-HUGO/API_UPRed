# 🚀 GUÍA DE DEPLOYMENT EN EC2 AWS - UPRed API

## 📋 TABLA DE CONTENIDOS

1. [Requisitos Previos](#requisitos-previos)
2. [Configuración Inicial EC2](#configuración-inicial-ec2)
3. [Instalación de Dependencias](#instalación-de-dependencias)
4. [Configurar PostgreSQL](#configurar-postgresql)
5. [Desplegar la Aplicación](#desplegar-la-aplicación)
6. [Configurar Gunicorn + Nginx](#configurar-gunicorn--nginx)
7. [SSL con Certbot](#ssl-con-certbot)
8. [Monitoreo y Logs](#monitoreo-y-logs)
9. [Troubleshooting](#troubleshooting)

---

## 📌 REQUISITOS PREVIOS

- Cuenta de AWS
- Dominio (para SSL)
- Clave PEM descargada
- Terminal SSH

---

## 🏗️ CONFIGURACIÓN INICIAL EC2

### 1. Lanzar Instancia EC2

1. **Ve a AWS Console → EC2 → Instances → Launch Instance**

2. **Configuración recomendada:**
   - **AMI**: Ubuntu Server 22.04 LTS (free tier)
   - **Tipo**: t3.small (mínimo recomendado) o t2.micro (free tier)
   - **Storage**: 20-30 GB
   - **VPC**: Default
   - **Security Group**: Ver paso 3

3. **Security Group - Abre estos puertos:**
   ```
   Puerto 22   → SSH (tu IP)
   Puerto 80   → HTTP (0.0.0.0)
   Puerto 443  → HTTPS (0.0.0.0)
   Puerto 5432 → PostgreSQL (solo si DB local, opcional)
   ```

4. **Guarda la clave PEM** en lugar seguro

### 2. Conectar a la Instancia

```bash
# Cambiar permisos de la clave
chmod 400 tu-clave.pem

# Conectar por SSH
ssh -i tu-clave.pem ubuntu@tu-ip-elastica.amazonaws.com
```

### 3. Variables de Entorno AWS (Opcional pero Recomendado)

```bash
# Instalar AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configurar credenciales
aws configure
# Ingresa: Access Key, Secret Key, región (ej: us-east-1), formato JSON
```

---

## 📦 INSTALACIÓN DE DEPENDENCIAS

### 1. Actualizar Sistema

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y curl wget git build-essential libssl-dev libffi-dev python3-dev python3-pip python3-venv
```

### 2. Instalar Python 3.11 (Opcional, para versión más reciente)

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### 3. Clonar Repositorio

```bash
cd /web
sudo mkdir -p upred-api
sudo chown ubuntu:ubuntu upred-api
cd upred-api

# Clonar tu repositorio
git clone https://github.com/IDS-HUGO/WEBSOCKET_REDUP.git .
# O si tienes SSH configurado:
# git clone git@github.com:IDS-HUGO/WEBSOCKET_REDUP.git .
```

### 4. Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🗄️ CONFIGURAR POSTGRESQL

### Opción A: Usar RDS (Recomendado para producción)

1. **Ve a AWS → RDS → Create Database**

2. **Configuración:**
   - Engine: PostgreSQL 15.x
   - Templates: Free tier (si aplica)
   - DB instanceidentifier: `upred-db`
   - Credentials:
     - Username: `postgres`
     - Password: genera una contraseña fuerte
   - Storage: 20 GB
   - VPC: Mismo de tu EC2
   - Security Group: Crear nuevo, abrir 5432 para la instancia EC2

3. **Después de crear:**
   - Anota el **Endpoint** (ej: upred-db.xxxxx.us-east-1.rds.amazonaws.com)
   - Crea la base de datos:

```bash
# Desde tu EC2
psql -h tu-endpoint.rds.amazonaws.com -U postgres -d postgres

# Ejecuta en psql:
CREATE DATABASE upred_db;
\q
```

4. **Ejecuta el script SQL:**

```bash
psql -h tu-endpoint.rds.amazonaws.com -U postgres -d upred_db < database_schema.sql
```

### Opción B: PostgreSQL Local en EC2

```bash
# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Crear usuario y BD
sudo -u postgres psql

# En psql:
CREATE USER upred WITH PASSWORD 'tu_password_segura';
ALTER ROLE upred SET client_encoding TO 'utf8';
ALTER ROLE upred SET default_transaction_isolation TO 'read committed';
ALTER ROLE upred SET default_transaction_deferrable TO on;
ALTER ROLE upred SET default_timezone TO 'UTC';
ALTER USER upred CREATEDB;
CREATE DATABASE upred_db OWNER upred;
\q

# Ejecutar script
psql -U upred -d upred_db < database_schema.sql
```

---

## 🚀 DESPLEGAR LA APLICACIÓN

### 1. Configurar Variables de Entorno

```bash
cd /web/upred-api
nano .env
```

**Contenido para producción:**

```env
# Database
DB_HOST=tu-endpoint.rds.amazonaws.com  # O localhost si es local
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=contraseña_fuerte_aqui
DB_NAME=upred_db

# JWT - Generar con: openssl rand -hex 32
SECRET_KEY=genera_una_clave_muy_larga_y_segura_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False  # IMPORTANTE: False en producción
```

Guardas: `Ctrl+O`, `Enter`, `Ctrl+X`

### 2. Instalar Gunicorn y dependencias

```bash
source venv/bin/activate
pip install gunicorn
```

### 3. Probar que funciona

```bash
# Desde el directorio de la app
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# Abre en navegador: http://tu-ip:8000/docs
# Si ves la documentación, ¡funciona!

# Detén con: Ctrl+C
```

---

## ⚙️ CONFIGURAR GUNICORN + NGINX

### 1. Crear Servicio Systemd para Gunicorn

```bash
sudo nano /etc/systemd/system/upred.service
```

**Contenido:**

```ini
[Unit]
Description=UPRed API Application
After=network.target

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=/web/upred-api
ExecStart=/web/upred-api/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 --timeout 60 --access-logfile - --error-logfile - main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio
sudo systemctl enable upred

# Iniciar
sudo systemctl start upred

# Verificar estado
sudo systemctl status upred

# Ver logs
sudo journalctl -u upred -f  # Ctrl+C para salir
```

### 2. Instalar y Configurar Nginx

```bash
sudo apt install -y nginx

# Crear configuración
sudo nano /etc/nginx/sites-available/upred
```

**Contenido:**

```nginx
upstream upred_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://upred_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    location /static/ {
        alias /web/upred-api/static/;
        expires 30d;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
}
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/upred /etc/nginx/sites-enabled/upred

# Eliminar default si existe
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Ver logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### 3. Permitir Nginx a través del Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow 22/tcp
sudo ufw enable
sudo ufw status
```

---

## 🔐 SSL CON CERTBOT

### 1. Instalar Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Obtener Certificado SSL

```bash
# Asegúrate que tu dominio apunte a la IP de EC2 en tu registrador
# Espera 5-10 minutos para propagación DNS

# Generar certificado
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Ingresar email para renovaciones
# Aceptar términos
# Permitir automático

# Verificar renovación automática
sudo systemctl status certbot.timer

# Probar renovación (no renueva pero verifica que funcionaría)
sudo certbot renew --dry-run
```

### 3. Auto-renovación (Automático con Certbot)

```bash
# El timer ya está configurado, verificar:
sudo systemctl list-timers | grep certbot

# Si no está, crear:
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 4. Verificar SSL

- Abre: https://tu-dominio.com/docs
- Verifica que no hay advertencia de SSL
- Usa: https://www.ssllabs.com/ssltest/ para revisar calificación

---

## 📊 MONITOREO Y LOGS

### 1. Ver Logs de la Aplicación

```bash
# Logs en tiempo real
sudo journalctl -u upred -f

# Últimas 100 líneas
sudo journalctl -u upred -n 100

# Log de hoy
sudo journalctl -u upred --since today
```

### 2. Ver Logs de Nginx

```bash
# Error log
sudo tail -f /var/log/nginx/error.log

# Access log
sudo tail -f /var/log/nginx/access.log

# 100 últimas líneas
sudo tail -100 /var/log/nginx/access.log
```

### 3. Monitoreo de Recursos

```bash
# Ver CPU y memoria
top

# Ver uso de disco
df -h

# Ver procesos de Python
ps aux | grep python

# Ver conexiones de red
netstat -an | grep LISTENING
```

### 4. Backup Automático de Base de Datos

```bash
# Crear script de backup
sudo nano /usr/local/bin/backup-upred-db.sh
```

**Contenido:**

```bash
#!/bin/bash

BACKUP_DIR="/backups/upred"
DATE=$(date +%Y%m%d_%H%M%S)
DB_HOST="tu-endpoint.rds.amazonaws.com"
DB_USER="postgres"
DB_NAME="upred_db"

mkdir -p $BACKUP_DIR

# Realizar backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/upred_$DATE.sql.gz

# Eliminar backups más antiguos de 7 días
find $BACKUP_DIR -name "upred_*.sql.gz" -mtime +7 -delete

echo "Backup completado: $BACKUP_DIR/upred_$DATE.sql.gz"
```

```bash
# Permisos
sudo chmod +x /usr/local/bin/backup-upred-db.sh

# Agregar a crontab (diario a las 2 AM)
sudo crontab -e

# Agregar línea:
# 0 2 * * * /usr/local/bin/backup-upred-db.sh >> /var/log/upred-backup.log 2>&1
```

### 5. Usar CloudWatch (AWS Native)

```bash
# Instalar CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# Configurar (follow interactive setup)
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Iniciar agente
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

---

## 🛠️ TROUBLESHOOTING

### Problema: La API no inicia

```bash
# Verificar logs
sudo journalctl -u upred -n 50

# Verificar que el puerto 8000 no esté en uso
sudo lsof -i :8000

# Matar proceso si es necesario
sudo kill -9 PID

# Reiniciar servicio
sudo systemctl restart upred
```

### Problema: Error 502 Bad Gateway

```bash
# Verificar que Gunicorn está corriendo
sudo systemctl status upred

# Verificar logs de Nginx
sudo tail -20 /var/log/nginx/error.log

# Reiniciar Nginx
sudo systemctl restart nginx

# Reiniciar ambos
sudo systemctl restart upred nginx
```

### Problema: PostgreSQL rechaza conexión

```bash
# Verificar que PostgreSQL está corriendo (si es local)
sudo systemctl status postgresql

# Verificar credenciales en .env
cat ~/upred-api/.env | grep DB_

# Probar conexión manual
psql -h tu-host -U tu-usuario -d tu-bd
```

### Problema: SSL no se renueva

```bash
# Forzar renovación
sudo certbot renew --force-renewal

# Ver estado de renovación
sudo systemctl status certbot.timer

# Logs de certbot
sudo tail -50 /var/log/letsencrypt/letsencrypt.log
```

### Problema: Memoria agotada

```bash
# Reducir workers de Gunicorn en /etc/systemd/system/upred.service
# Cambiar: -w 4  por  -w 2

# Reincargar
sudo systemctl daemon-reload
sudo systemctl restart upred

# Monitorear memoria
watch -n 1 free -h
```

---

## 📈 ESCALABILIDAD

### 1. Auto-scaling con EC2

- Crear AMI de tu instancia configurada
- Crear Launch Template
- Crear Auto Scaling Group
- Configurar load balancer (ALB)

### 2. Caché con ElastiCache (Redis)

```python
# En tu código
import redis

cache = redis.Redis(host='seu-elasticache.amazonaws.com', port=6379)
```

### 3. CDN con CloudFront

- Distribuir archivos estáticos
- Mejorar velocidad global

### 4. Monitoring con CloudWatch Alarms

- CPU > 70%
- Memoria > 80%
- Errores de aplicación
- Uptime checks

---

## ✅ CHECKLIST DE DEPLOYMENT

- [ ] Instancia EC2 creada y corriendo
- [ ] Security Groups configurados
- [ ] Dominio apunta a IP Elástica
- [ ] PostgreSQL creada (RDS o local)
- [ ] Script SQL ejecutado
- [ ] `.env` configurado en la instancia
- [ ] Dependencias instaladas
- [ ] Gunicorn funciona en puerto 8000
- [ ] Nginx configurado y corriendo
- [ ] API accesible en http://ip:80
- [ ] Certbot instaló certificado SSL
- [ ] API accesible en https://dominio.com
- [ ] Logs funcionando correctamente
- [ ] Backups configurados
- [ ] Servicio Gunicorn con systemd funciona
- [ ] Renovación automática SSL habilitada

---

## 🎯 COMANDOS ÚTILES FRECUENTES

```bash
# Verificar estado general
sudo systemctl status upred nginx

# Ver logs en tiempo real
sudo journalctl -u upred -f

# Reiniciar la app
sudo systemctl restart upred

# Actualizar código
cd /web/upred-api
git pull
source venv/bin/activate
pip install -r requirements.txt  # Si hay cambios
sudo systemctl restart upred

# Acceder a PostgreSQL (si es local)
sudo -u postgres psql -d upred_db

# Ver procesos Python
ps aux | grep gunicorn

# Ver puertos en uso
sudo netstat -tlnp | grep LISTEN

# Monitorear CPU y Memoria
top

# Ver logs de acceso a la API
sudo tail -f /var/log/nginx/access.log | grep api
```

---

## 📞 SOPORTE

- **AWS Docs**: https://docs.aws.amazon.com/
- **FastAPI Production**: https://fastapi.tiangolo.com/deployment/
- **Gunicorn**: https://gunicorn.org/
- **Nginx**: https://nginx.org/en/docs/

---

**Fecha**: 2026-02-25  
**Versión**: 1.0  
**Autor**: IDS-HUGO
