from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import ALL_ROUTERS
from config import settings
import logging

# Comentar esta línea para que no cree tablas automáticamente (usaremos el script SQL)
# Base.metadata.create_all(bind=engine)

def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app = FastAPI(
        title="API UPRed - Red Social Universitaria",
        description="API REST completa para red social universitaria con estructura académica, publicaciones, grupos, mensajería y notificaciones",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        redirect_slashes=False,
    )
    _register_middlewares(app)
    _register_routes(app)
    _register_exception_handlers(app)
    return app


def _register_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_routes(app: FastAPI) -> None:
    for router in ALL_ROUTERS:
        app.include_router(router)

def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Error interno del servidor",
                "error": str(exc) if settings.DEBUG else "Internal Server Error",
            },
        )


app = create_app()


@app.get("/")
def root():
    return {
        "mensaje": "Bienvenido a UPRed - Red Social Universitaria",
        "version": "2.0.0",
        "documentacion": {
            "swagger": "/docs",
            "redoc": "/redoc",
        },
        "endpoints": {
            "autenticacion": "/api/auth",
            "estructura_academica": "/api/estructura",
            "usuarios": "/api/usuarios",
            "publicaciones": "/api/publicaciones",
            "comentarios": "/api/comentarios",
            "grupos": "/api/grupos",
            "mensajeria": "/api/mensajes",
            "notificaciones": "/api/notificaciones",
        },
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "database": "connected",
        "version": "2.0.0",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
