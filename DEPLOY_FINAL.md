# 🚀 DEPLOY A EC2 - INSTRUCCIONES FINALES

## ⚙️ REQUISITOS

1. **Archivo `.pem`** de tu instancia EC2
2. **OpenSSH instalado** (viene por defecto en Windows 10+)
3. **Acceso SSH** a tu servidor EC2

---

## 📋 PASOS

### 1️⃣ **Edita el script DEPLOY.ps1**

Abre `DEPLOY.ps1` y modifica estas líneas (cerca del inicio):

```powershell
$KeyFile = "C:\ruta\a\tu-clave.pem"      # Tu archivo .pem
$EC2User = "ubuntu"                       # Tu usuario (o ec2-user)
$EC2Host = "apiupred.ferluna.online"     # Tu dominio o IP
$RemotePath = "/home/ubuntu/API_UPRed"    # Ruta en el servidor
```

### 2️⃣ **Ejecuta el script**

En PowerShell:

```powershell
cd d:\UNIVERSIDAD\MOVILES\API_UPRed
.\DEPLOY.ps1
```

**Eso es todo.** El script automáticamente:
- ✅ Sube `routers/publicaciones.py`
- ✅ Sube `schemas.py`
- ✅ Sube `main.py`
- ✅ Reinicia el servicio uvicorn
- ✅ Verifica que funciona

### 3️⃣ **Verifica el deploy**

Ejecuta en tu servidor EC2 (o en terminal):

```bash
curl https://apiupred.ferluna.online/api/publicaciones/test
```

**Debe devolver:**
```json
{"status":"ok","message":"Publicaciones router está funcionando"}
```

---

## 🧪 TESTING

Si el test funciona, prueba en tu app Android:

1. Abre la app UPRed
2. Ve a **Publicaciones**
3. Toca el **+** para crear una publicación
4. Llena: Título, Contenido, Audiencia
5. Toca **Publicar**

**Debería funcionar sin error 404** ✅

---

## ❌ SI FALLA

### Error: Archivo .pem no encontrado

```powershell
# Edita DEPLOY.ps1 y pon la ruta COMPLETA, ejemplo:
$KeyFile = "C:\Users\Juan\Desktop\upred-key.pem"
```

### Error: Permission denied

```bash
# En tu servidor, ejecuta:
ssh -i tu-clave.pem ubuntu@tu-ip
sudo chown -R ubuntu:ubuntu /home/ubuntu/API_UPRed
```

### Error: 502 Bad Gateway

```bash
# El servidor está caído, reinicia:
sudo systemctl restart uvicorn
# O verifica los logs:
sudo journalctl -u uvicorn -n 20
```

---

## 📞 COMANDOS ÚTILES

```bash
# Ver status del API
curl https://apiupred.ferluna.online/health

# Ver documentación interactiva
https://apiupred.ferluna.online/docs

# Ver logs en tiempo real (en el servidor)
sudo journalctl -u uvicorn -f
```

---

## ✨ LISTO

Tu API está completamente funcional con CRUD de publicaciones.

**Endpoints disponibles:**
- `GET /api/publicaciones` - Listar publicaciones
- `POST /api/publicaciones` - Crear publicación
- `PUT /api/publicaciones/{id}` - Editar publicación
- `DELETE /api/publicaciones/{id}` - Eliminar publicación
- `GET /api/publicaciones/test` - Verificar que funciona
