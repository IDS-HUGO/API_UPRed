from . import auth, comentarios, estructura, grupos, mensajes, notificaciones, publicaciones, usuarios

ALL_ROUTERS = (
	auth.router,
	estructura.router,
	usuarios.router,
	publicaciones.router,
	comentarios.router,
	grupos.router,
	mensajes.router,
	notificaciones.router,
)

__all__ = ["ALL_ROUTERS"]
