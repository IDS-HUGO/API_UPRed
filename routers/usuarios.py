from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from database import get_db
from models import (
    Usuario, Seguidor, RolUsuario, EstadoUsuario, Auditoria,
    Publicacion, ReaccionPublicacion, ComentarioPublicacion,
    Notificacion, DispositivoUsuario
)
from schemas import (
    UsuarioResponse, UsuarioUpdate, Message,
    SeguidorCreate, SeguidorResponse, BusquedaUsuarios
)
from auth import get_current_user, require_roles
from datetime import datetime
from services.firebase_push_service import firebase_push_service


router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])

# =====================================================================
# ENDPOINTS DE USUARIOS
# =====================================================================

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    carrera_id: Optional[int] = None,
    cuatrimestre_id: Optional[int] = None,
    rol: Optional[RolUsuario] = None,
    estado: Optional[EstadoUsuario] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista usuarios con filtros opcionales"""
    query = db.query(Usuario)
    
    if carrera_id:
        query = query.filter(Usuario.carrera_id == carrera_id)
    if cuatrimestre_id:
        query = query.filter(Usuario.cuatrimestre_id == cuatrimestre_id)
    if rol:
        query = query.filter(Usuario.rol == rol)
    if estado:
        query = query.filter(Usuario.estado == estado)
    
    usuarios = query.offset(skip).limit(limit).all()
    return usuarios

@router.get("/buscar", response_model=List[UsuarioResponse])
def buscar_usuarios(
    query: str = Query(..., min_length=1),
    carrera_id: Optional[int] = None,
    cuatrimestre_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Busca usuarios por nombre, apellido o correo"""
    q = db.query(Usuario).filter(
        or_(
            Usuario.nombre.ilike(f"%{query}%"),
            Usuario.apellido_paterno.ilike(f"%{query}%"),
            Usuario.apellido_materno.ilike(f"%{query}%"),
            Usuario.correo_institucional.ilike(f"%{query}%")
        )
    )
    
    if carrera_id:
        q = q.filter(Usuario.carrera_id == carrera_id)
    if cuatrimestre_id:
        q = q.filter(Usuario.cuatrimestre_id == cuatrimestre_id)
    
    usuarios = q.limit(limit).all()
    return usuarios

@router.get("/por-correo/{correo}", response_model=UsuarioResponse)
def obtener_usuario_por_correo(
    correo: str,
    db: Session = Depends(get_db)
):
    """Obtiene un usuario por correo institucional (para iniciar chats)"""
    usuario = db.query(Usuario).filter(Usuario.correo_institucional.ilike(correo)).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con correo {correo} no encontrado"
        )
    return usuario

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtiene un usuario por ID"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un usuario (solo el mismo usuario o admin)"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar permisos
    if current_user.id != usuario_id and current_user.rol != RolUsuario.administrador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este usuario"
        )
    
    update_data = usuario_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(usuario, key, value)
    
    db.commit()
    db.refresh(usuario)
    return usuario

@router.delete("/{usuario_id}", response_model=Message)
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Elimina (marca como eliminado) un usuario (solo administradores)"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Soft delete
    usuario.estado = EstadoUsuario.eliminado
    from datetime import datetime
    usuario.eliminado_en = datetime.utcnow()
    
    db.commit()
    return {"message": "Usuario eliminado correctamente"}

# =====================================================================
# ENDPOINTS DE SEGUIDORES
# =====================================================================

@router.post("/{usuario_id}/seguir", response_model=Message)
def seguir_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Sigue a un usuario"""
    if usuario_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes seguirte a ti mismo"
        )
    
    # Verificar que el usuario existe
    usuario_a_seguir = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario_a_seguir:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar si ya lo sigue
    seguidor_existente = db.query(Seguidor).filter(
        Seguidor.seguidor_id == current_user.id,
        Seguidor.seguido_id == usuario_id
    ).first()
    
    if seguidor_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya sigues a este usuario"
        )
    
    # Crear relación de seguimiento
    nuevo_seguidor = Seguidor(
        seguidor_id=current_user.id,
        seguido_id=usuario_id
    )
    db.add(nuevo_seguidor)

    # Notificacion interna para centro de notificaciones
    notificacion = Notificacion(
        usuario_id=usuario_id,
        tipo="nuevo_seguidor",
        titulo="Tienes un nuevo seguidor",
        cuerpo=f"{current_user.nombre} {current_user.apellido_paterno} comenzo a seguirte",
        datos={
            "follower_user_id": str(current_user.id),
            "follower_name": f"{current_user.nombre} {current_user.apellido_paterno}".strip(),
        },
        leida=False,
        creada_en=datetime.utcnow(),
    )
    db.add(notificacion)

    db.commit()

    # Intento de push FCM (no bloquea la accion principal si falla)
    try:
        dispositivo = db.query(DispositivoUsuario).filter(
            DispositivoUsuario.usuario_id == usuario_id,
            DispositivoUsuario.activo == True,
            DispositivoUsuario.token_push.isnot(None)
        ).order_by(DispositivoUsuario.ultima_actividad_en.desc()).first()

        if dispositivo and dispositivo.token_push:
            firebase_push_service.send_to_token(
                token=dispositivo.token_push,
                title="Nuevo seguidor",
                body=f"{current_user.nombre} {current_user.apellido_paterno} comenzo a seguirte",
                data={
                    "title": "Nuevo seguidor",
                    "body": f"{current_user.nombre} {current_user.apellido_paterno} comenzo a seguirte",
                    "follower_user_id": str(current_user.id),
                },
            )
    except Exception:
        pass
    
    return {"message": "Ahora sigues a este usuario"}

@router.delete("/{usuario_id}/seguir", response_model=Message)
def dejar_de_seguir(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Deja de seguir a un usuario"""
    seguidor = db.query(Seguidor).filter(
        Seguidor.seguidor_id == current_user.id,
        Seguidor.seguido_id == usuario_id
    ).first()
    
    if not seguidor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sigues a este usuario"
        )
    
    db.delete(seguidor)
    db.commit()
    
    return {"message": "Has dejado de seguir a este usuario"}

@router.get("/{usuario_id}/seguidores", response_model=List[UsuarioResponse])
def obtener_seguidores(
    usuario_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtiene los seguidores de un usuario"""
    seguidores = db.query(Usuario).join(
        Seguidor, Seguidor.seguidor_id == Usuario.id
    ).filter(
        Seguidor.seguido_id == usuario_id
    ).offset(skip).limit(limit).all()
    
    return seguidores

@router.get("/{usuario_id}/siguiendo", response_model=List[UsuarioResponse])
def obtener_siguiendo(
    usuario_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtiene los usuarios que sigue un usuario"""
    siguiendo = db.query(Usuario).join(
        Seguidor, Seguidor.seguido_id == Usuario.id
    ).filter(
        Seguidor.seguidor_id == usuario_id
    ).offset(skip).limit(limit).all()
    
    return siguiendo

@router.get("/{usuario_id}/stats")
def obtener_estadisticas_usuario(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas de un usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Contar seguidores
    total_seguidores = db.query(func.count(Seguidor.seguidor_id)).filter(
        Seguidor.seguido_id == usuario_id
    ).scalar() or 0
    
    # Contar siguiendo
    total_siguiendo = db.query(func.count(Seguidor.seguido_id)).filter(
        Seguidor.seguidor_id == usuario_id
    ).scalar() or 0
    
    # Contar publicaciones
    total_publicaciones = db.query(func.count(Publicacion.id)).filter(
        Publicacion.autor_id == usuario_id
    ).scalar() or 0
    
    # Contar comentarios
    total_comentarios = db.query(func.count(ComentarioPublicacion.id)).filter(
        ComentarioPublicacion.usuario_id == usuario_id,
        ComentarioPublicacion.activo == True
    ).scalar() or 0
    
    # Contar reacciones
    total_reacciones = db.query(func.count(ReaccionPublicacion.usuario_id)).filter(
        ReaccionPublicacion.usuario_id == usuario_id
    ).scalar() or 0
    
    return {
        "usuario_id": usuario_id,
        "nombre_completo": f"{usuario.nombre} {usuario.apellido_paterno}",
        "total_seguidores": total_seguidores,
        "total_siguiendo": total_siguiendo,
        "total_publicaciones": total_publicaciones,
        "total_comentarios": total_comentarios,
        "total_reacciones": total_reacciones
    }


# =====================================================================
# ENDPOINTS DE PERFIL
# =====================================================================

@router.get("/perfil/actual", response_model=UsuarioResponse)
def obtener_perfil_actual(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene el perfil del usuario autenticado"""
    usuario = db.query(Usuario).filter(Usuario.id == current_user.id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario


@router.put("/perfil/actualizar", response_model=UsuarioResponse)
def actualizar_perfil(
    usuario_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza el perfil del usuario autenticado"""
    usuario = db.query(Usuario).filter(Usuario.id == current_user.id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar campos permitidos
    update_data = usuario_update.model_dump(exclude_unset=True)
    
    # Excluir cambios de email o ID
    update_data.pop('correo_institucional', None)
    update_data.pop('id', None)
    
    for key, value in update_data.items():
        setattr(usuario, key, value)
    
    db.commit()
    db.refresh(usuario)
    
    # Registrar auditoría
    auditoria = Auditoria(
        accion="actualizar_perfil",
        entidad="usuarios",
        entidad_id=str(current_user.id),
        actor_usuario_id=current_user.id,
        detalle={"usuario_id": current_user.id}
    )
    db.add(auditoria)
    db.commit()
    
    return usuario


@router.get("/perfil/completo/{usuario_id}")
def obtener_perfil_completo(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene el perfil completo de un usuario con estadísticas"""
    usuario = db.query(Usuario).filter(
        Usuario.id == usuario_id,
        Usuario.estado == EstadoUsuario.activo
    ).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado o no disponible"
        )
    
    # Obtener estadísticas
    total_seguidores = db.query(func.count(Seguidor.seguidor_id)).filter(
        Seguidor.seguido_id == usuario_id
    ).scalar() or 0
    
    total_siguiendo = db.query(func.count(Seguidor.seguido_id)).filter(
        Seguidor.seguidor_id == usuario_id
    ).scalar() or 0
    
    total_publicaciones = db.query(func.count(Publicacion.id)).filter(
        Publicacion.autor_id == usuario_id
    ).scalar() or 0
    
    # Verificar si el usuario actual sigue al usuario consultado
    ya_sigue = db.query(Seguidor).filter(
        Seguidor.seguidor_id == current_user.id,
        Seguidor.seguido_id == usuario_id
    ).first() is not None
    
    return {
        "usuario": UsuarioResponse.model_validate(usuario),
        "estadisticas": {
            "total_seguidores": total_seguidores,
            "total_siguiendo": total_siguiendo,
            "total_publicaciones": total_publicaciones
        },
        "relacion_actual": {
            "ya_sigue": ya_sigue,
            "es_mismo_usuario": current_user.id == usuario_id
        }
    }

    
    # Contar publicaciones
    from models import Publicacion
    total_publicaciones = db.query(func.count(Publicacion.id)).filter(
        Publicacion.autor_id == usuario_id,
        Publicacion.activa == True
    ).scalar() or 0
    
    return {
        "usuario_id": usuario_id,
        "total_seguidores": total_seguidores,
        "total_siguiendo": total_siguiendo,
        "total_publicaciones": total_publicaciones
    }
