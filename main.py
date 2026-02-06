from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import engine, Base
from routers import auth, publicaciones, carreras, usuarios
from config import settings

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Inicializar FastAPI
app = FastAPI(
    title="API Red Social Escolar",
    description="API REST para una red social escolar organizada por carreras con login, registro y CRUD de publicaciones",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir acceso desde apps móviles
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(publicaciones.router)
app.include_router(carreras.router)
app.include_router(usuarios.router)

# Ruta raíz
@app.get("/")
def root():
    return {
        "mensaje": "Bienvenido a la API de Red Social Escolar",
        "version": "1.0.0",
        "documentacion": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "autenticacion": "/api/auth",
            "publicaciones": "/api/publicaciones",
            "carreras": "/api/carreras",
            "usuarios": "/api/usuarios"
        }
    }

# Ruta de health check
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": "connected"
    }

# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "error": str(exc) if settings.DEBUG else "Internal Server Error"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
