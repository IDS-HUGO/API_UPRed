# API Red Social Escolar

## Instalar

```bash
pip install -r requirements.txt
```

## Configurar BD

```bash
mysql -u root -p < database_schema.sql
```

Edita `.env` (copia de `.env.example`):
```env
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=red_social_escolar
SECRET_KEY=cambia_esto_por_algo_seguro
```

## Correr

```bash
python main.py
```

**API:** http://localhost:8000  
**Docs:** http://localhost:8000/docs

**Admin:** `admin@escuela.edu.mx` / `admin123`

## CORS: ✅ Configurado para todas las conexiones
