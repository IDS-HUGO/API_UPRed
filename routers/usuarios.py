from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from database import get_db
from models import Usuario, Seguidor, RolUsuario, EstadoUsuario, Auditoria
from schemas import (
    UsuarioResponse, UsuarioUpdate, Message,
    SeguidorCreate, SeguidorResponse, BusquedaUsuarios
)
from auth import get_current_user, require_roles

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
    db.commit()
    
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
