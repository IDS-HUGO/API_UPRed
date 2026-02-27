# 🚀 GUÍA DE DEPLOY A EC2 - PUBLICACIONES API

## ⚠️ PROBLEMA ACTUAL

Tu servidor EC2 (`https://apiupred.ferluna.online/`) **NO tiene los cambios** de publicaciones que hicimos. Por eso recibes errores 404:

```
INFO: 187.244.123.238:0 - "GET /api/publicaciones HTTP/1.1" 404 Not Found
INFO: 187.244.123.238:0 - "POST /api/publicaciones HTTP/1.1" 404 Not Found
```

## ✅ SOLUCIÓN: Subir archivos actualizados a EC2

---

## 📦 ARCHIVOS QUE DEBES SUBIR

1. **`routers/publicaciones.py`** (actualizado con endpoints GET, POST, PUT, DELETE)
2. **`schemas.py`** (agregado AutorSimplificadoResponse)

---

## 🔧 OPCIÓN 1: Deploy con SSH/SCP (Recomendado)

### Pre-requisitos:
- Archivo `.pem` de tu instancia EC2
- OpenSSH instalado en Windows (viene por defecto en Windows 10+)

### Pasos:

**1. Edita el script `deploy_to_ec2.bat`**

Abre el archivo y modifica estas variables:

```batch
set KEY_FILE=C:\ruta\a\tu-clave.pem
set EC2_USER=ubuntu
set EC2_HOST=apiupred.ferluna.online
set REMOTE_PATH=/home/ubuntu/API_UPRed
```

**2. Ejecuta el script:**

```bash
cd d:\UNIVERSIDAD\MOVILES\API_UPRed
deploy_to_ec2.bat
```

**3. Verifica que funcione:**

```
https://apiupred.ferluna.online/api/publicaciones/test
```

Deberías ver:
```json
{"status":"ok","message":"Publicaciones router está funcionando"}
```

---

## 🔧 OPCIÓN 2: Deploy Manual con WinSCP/FileZilla

### 1. Descarga WinSCP:
https://winscp.net/eng/download.php

### 2. Configura la conexión:
- **File Protocol:** SFTP
- **Host:** apiupred.ferluna.online (o la IP de tu EC2)
- **Port:** 22
- **Username:** ubuntu (o ec2-user según tu EC2)
- **Password:** (dejar vacío)
- **Private key:** Selecciona tu archivo `.pem`

### 3. Conecta y sube archivos:

**Navega a:** `/home/ubuntu/API_UPRed/` (o donde esté tu API)

**Sube estos archivos:**
- Local: `d:\UNIVERSIDAD\MOVILES\API_UPRed\routers\publicaciones.py`
- Remoto: `/home/ubuntu/API_UPRed/routers/publicaciones.py`

- Local: `d:\UNIVERSIDAD\MOVILES\API_UPRed\schemas.py`
- Remoto: `/home/ubuntu/API_UPRed/schemas.py`

### 4. Reinicia el servicio:

En WinSCP, abre una terminal (Ctrl+T) y ejecuta:

```bash
cd /home/ubuntu/API_UPRed
sudo systemctl restart uvicorn
# o si no usas systemd:
sudo pkill -f uvicorn
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
```

---

## 🔧 OPCIÓN 3: Deploy con Git (Si tu servidor tiene Git)

### 1. En tu PC local:

```bash
cd d:\UNIVERSIDAD\MOVILES\API_UPRed

# Si aún no tienes git inicializado:
git init
git add routers/publicaciones.py schemas.py
git commit -m "🚀 Actualizar endpoints de publicaciones con formato móvil"

# Sube a tu repositorio (GitHub, GitLab, etc.)
git push origin main
```

### 2. En el servidor EC2 (por SSH):

```bash
ssh -i tu-clave.pem ubuntu@apiupred.ferluna.online

cd /home/ubuntu/API_UPRed
git pull origin main
sudo systemctl restart uvicorn
```

---

## 🔧 OPCIÓN 4: Deploy con VSCode Remote SSH (Más fácil)

### 1. Instala extensión:
- En VSCode: Instala **"Remote - SSH"**

### 2. Conecta a EC2:
- Presiona `F1` → "Remote-SSH: Connect to Host"
- Agrega: `ubuntu@apiupred.ferluna.online`
- Selecciona tu archivo `.pem`

### 3. Abre la carpeta remota:
- File → Open Folder → `/home/ubuntu/API_UPRed`

### 4. Reemplaza archivos:
- Copia el contenido de tu `routers/publicaciones.py` local
- Pégalo en el archivo remoto
- Haz lo mismo con `schemas.py`

### 5. Reinicia el servicio:
- Terminal en VSCode:
```bash
sudo systemctl restart uvicorn
```

---

## 🧪 VERIFICACIÓN DESPUÉS DEL DEPLOY

### 1. Test endpoint:
```bash
curl https://apiupred.ferluna.online/api/publicaciones/test
```

Debe devolver:
```json
{"status":"ok","message":"Publicaciones router está funcionando"}
```

### 2. Test GET publicaciones:
```bash
curl -H "Authorization: Bearer TU_TOKEN_JWT" https://apiupred.ferluna.online/api/publicaciones
```

Debe devolver un array de publicaciones (puede estar vacío si no hay publicaciones):
```json
[]
```

### 3. Test desde la app Android:
- Abre la app
- Ve a Publicaciones
- Intenta crear una publicación
- Ya NO debe dar error 404

---

## 🔍 SOLUCIÓN DE PROBLEMAS

### ❌ Error: Permission denied al subir archivos

**Solución:**
```bash
# En EC2, da permisos a tu usuario:
sudo chown -R ubuntu:ubuntu /home/ubuntu/API_UPRed
```

### ❌ Error: El servicio no se reinicia

**Opción 1 - Si usas systemd:**
```bash
sudo systemctl status uvicorn
sudo systemctl restart uvicorn
sudo systemctl status uvicorn  # Verificar que esté corriendo
```

**Opción 2 - Si NO usas systemd:**
```bash
# Matar proceso actual:
sudo pkill -f uvicorn

# Iniciar nuevamente:
cd /home/ubuntu/API_UPRed
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
```

**Opción 3 - Ver logs:**
```bash
# Si usas systemd:
sudo journalctl -u uvicorn -f

# Si usas nohup:
tail -f /home/ubuntu/API_UPRed/api.log
```

### ❌ Aún sale 404 después del deploy

**Verifica que los archivos se subieron correctamente:**
```bash
# Conecta por SSH
ssh -i tu-clave.pem ubuntu@apiupred.ferluna.online

# Verifica el contenido del archivo:
head -n 30 /home/ubuntu/API_UPRed/routers/publicaciones.py

# Busca la línea del router:
grep "router = APIRouter" /home/ubuntu/API_UPRed/routers/publicaciones.py
```

Debe mostrar:
```python
router = APIRouter(prefix="/api/publicaciones", tags=["Publicaciones"])
```

### ❌ Error: Connection timeout al conectar por SSH

**Verifica el Security Group de EC2:**
1. Ve a AWS Console → EC2 → Security Groups
2. Edita el Security Group de tu instancia
3. Asegúrate de tener estas reglas:
   - **Puerto 22** (SSH): Abierto para tu IP
   - **Puerto 8000**: Abierto para 0.0.0.0/0 (o solo HTTPS si usas proxy)
   - **Puerto 443** (HTTPS): Abierto para 0.0.0.0/0

---

## 📝 CHECKLIST FINAL

- [ ] Archivos subidos a EC2
  - [ ] routers/publicaciones.py
  - [ ] schemas.py
- [ ] Servicio API reiniciado
- [ ] Test endpoint responde OK
- [ ] App Android puede GET publicaciones
- [ ] App Android puede POST (crear) publicaciones
- [ ] Ya NO aparece error 404

---

## 🆘 SI NADA FUNCIONA

**Opción nuclear: Reiniciar todo el servidor**

```bash
ssh -i tu-clave.pem ubuntu@apiupred.ferluna.online
sudo reboot
```

Espera 2-3 minutos y verifica nuevamente.

---

## 📞 COMANDOS ÚTILES

```bash
# Ver procesos de Python/Uvicorn
ps aux | grep uvicorn

# Ver si el puerto 8000 está escuchando
sudo netstat -tlnp | grep 8000

# Ver logs en tiempo real
sudo journalctl -u uvicorn -f

# Probar desde el servidor mismo
curl http://localhost:8000/api/publicaciones/test
```

---

## ✨ DESPUÉS DEL DEPLOY EXITOSO

Tu app Android ahora podrá:
- ✅ Listar publicaciones (GET /api/publicaciones)
- ✅ Crear publicaciones (POST /api/publicaciones)
- ✅ Editar publicaciones (PUT /api/publicaciones/{id})
- ✅ Eliminar publicaciones (DELETE /api/publicaciones/{id})

¡Todo funcionando con el formato correcto para móvil!
