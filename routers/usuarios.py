from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Usuario, TipoUsuario
from schemas import UsuarioResponse, UsuarioUpdate, Message
from auth import get_current_user, require_roles, get_password_hash

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])

@router.get("/me", response_model=UsuarioResponse)
def obtener_perfil(
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene el perfil del usuario autenticado"""
    return current_user

@router.put("/me", response_model=UsuarioResponse)
def actualizar_perfil(
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza el perfil del usuario autenticado"""
    
    # Actualizar campos permitidos
    update_data = usuario_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("", response_model=List[UsuarioResponse])
def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tipo_usuario: str = None,
    carrera_id: int = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista usuarios con filtros opcionales"""
    
    query = db.query(Usuario).filter(Usuario.activo == True)
    
    if tipo_usuario:
        query = query.filter(Usuario.tipo_usuario == tipo_usuario)
    
    if carrera_id:
        query = query.filter(Usuario.carrera_id == carrera_id)
    
    usuarios = query.offset(skip).limit(limit).all()
    return usuarios

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un usuario por ID"""
    
    usuario = db.query(Usuario).filter(
        Usuario.id == usuario_id,
        Usuario.activo == True
    ).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return usuario

@router.delete("/{usuario_id}", response_model=Message)
def desactivar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([TipoUsuario.ADMINISTRADOR]))
):
    """Desactiva un usuario (solo administradores)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if usuario.tipo_usuario == TipoUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede desactivar a un administrador"
        )
    
    usuario.activo = False
    db.commit()
    
    return {"message": "Usuario desactivado exitosamente"}

@router.post("/{usuario_id}/activar", response_model=Message)
def activar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([TipoUsuario.ADMINISTRADOR]))
):
    """Activa un usuario desactivado (solo administradores)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    usuario.activo = True
    db.commit()
    
    return {"message": "Usuario activado exitosamente"}
