from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from database import get_db
from models import Publicacion, Usuario, Like, Comentario, TipoUsuario
from schemas import (
    PublicacionCreate, PublicacionUpdate, PublicacionResponse,
    ComentarioCreate, ComentarioResponse, ComentarioUpdate,
    LikeCreate, LikeResponse, Message
)
from auth import get_current_user, can_modify_publicacion

router = APIRouter(prefix="/api/publicaciones", tags=["Publicaciones"])

def enriquecer_publicacion(db: Session, publicacion: Publicacion) -> dict:
    """Agrega información adicional a la publicación"""
    total_likes = db.query(func.count(Like.id)).filter(
        Like.publicacion_id == publicacion.id
    ).scalar()
    
    total_comentarios = db.query(func.count(Comentario.id)).filter(
        Comentario.publicacion_id == publicacion.id,
        Comentario.activo == True
    ).scalar()
    
    pub_dict = {
        "id": publicacion.id,
        "usuario_id": publicacion.usuario_id,
        "titulo": publicacion.titulo,
        "contenido": publicacion.contenido,
        "imagen_url": publicacion.imagen_url,
        "carrera_id": publicacion.carrera_id,
        "tipo_publicacion": publicacion.tipo_publicacion,
        "activo": publicacion.activo,
        "created_at": publicacion.created_at,
        "updated_at": publicacion.updated_at,
        "usuario": publicacion.usuario,
        "carrera": publicacion.carrera,
        "total_likes": total_likes or 0,
        "total_comentarios": total_comentarios or 0
    }
    
    return pub_dict

@router.post("", response_model=PublicacionResponse, status_code=status.HTTP_201_CREATED)
def crear_publicacion(
    publicacion_data: PublicacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva publicación"""
    
    # Crear la publicación
    nueva_publicacion = Publicacion(
        usuario_id=current_user.id,
        titulo=publicacion_data.titulo,
        contenido=publicacion_data.contenido,
        imagen_url=publicacion_data.imagen_url,
        carrera_id=publicacion_data.carrera_id,
        tipo_publicacion=publicacion_data.tipo_publicacion
    )
    
    db.add(nueva_publicacion)
    db.commit()
    db.refresh(nueva_publicacion)
    
    return enriquecer_publicacion(db, nueva_publicacion)

@router.get("", response_model=List[PublicacionResponse])
def listar_publicaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    carrera_id: Optional[int] = None,
    tipo_publicacion: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todas las publicaciones activas con paginación"""
    
    query = db.query(Publicacion).filter(Publicacion.activo == True)
    
    # Filtrar por carrera si se especifica
    if carrera_id:
        query = query.filter(Publicacion.carrera_id == carrera_id)
    
    # Filtrar por tipo si se especifica
    if tipo_publicacion:
        query = query.filter(Publicacion.tipo_publicacion == tipo_publicacion)
    
    # Ordenar por fecha de creación (más recientes primero)
    publicaciones = query.order_by(desc(Publicacion.created_at)).offset(skip).limit(limit).all()
    
    return [enriquecer_publicacion(db, pub) for pub in publicaciones]

@router.get("/mis-publicaciones", response_model=List[PublicacionResponse])
def listar_mis_publicaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las publicaciones del usuario autenticado"""
    
    publicaciones = db.query(Publicacion).filter(
        Publicacion.usuario_id == current_user.id
    ).order_by(desc(Publicacion.created_at)).offset(skip).limit(limit).all()
    
    return [enriquecer_publicacion(db, pub) for pub in publicaciones]

@router.get("/{publicacion_id}", response_model=PublicacionResponse)
def obtener_publicacion(
    publicacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una publicación por ID"""
    
    publicacion = db.query(Publicacion).filter(
        Publicacion.id == publicacion_id,
        Publicacion.activo == True
    ).first()
    
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    return enriquecer_publicacion(db, publicacion)

@router.put("/{publicacion_id}", response_model=PublicacionResponse)
def actualizar_publicacion(
    publicacion_id: int,
    publicacion_data: PublicacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una publicación existente"""
    
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    # Verificar permisos
    if not can_modify_publicacion(current_user, publicacion.usuario_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta publicación"
        )
    
    # Actualizar campos
    update_data = publicacion_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(publicacion, field, value)
    
    db.commit()
    db.refresh(publicacion)
    
    return enriquecer_publicacion(db, publicacion)

@router.delete("/{publicacion_id}", response_model=Message)
def eliminar_publicacion(
    publicacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina (desactiva) una publicación"""
    
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    # Verificar permisos
    if not can_modify_publicacion(current_user, publicacion.usuario_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta publicación"
        )
    
    # Soft delete
    publicacion.activo = False
    db.commit()
    
    return {"message": "Publicación eliminada exitosamente"}

# ===== LIKES =====

@router.post("/{publicacion_id}/like", response_model=LikeResponse, status_code=status.HTTP_201_CREATED)
def dar_like(
    publicacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Da like a una publicación"""
    
    # Verificar que la publicación exista
    publicacion = db.query(Publicacion).filter(
        Publicacion.id == publicacion_id,
        Publicacion.activo == True
    ).first()
    
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    # Verificar si ya dio like
    existing_like = db.query(Like).filter(
        Like.publicacion_id == publicacion_id,
        Like.usuario_id == current_user.id
    ).first()
    
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya diste like a esta publicación"
        )
    
    # Crear like
    nuevo_like = Like(
        publicacion_id=publicacion_id,
        usuario_id=current_user.id
    )
    
    db.add(nuevo_like)
    db.commit()
    db.refresh(nuevo_like)
    
    return nuevo_like

@router.delete("/{publicacion_id}/like", response_model=Message)
def quitar_like(
    publicacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Quita el like de una publicación"""
    
    like = db.query(Like).filter(
        Like.publicacion_id == publicacion_id,
        Like.usuario_id == current_user.id
    ).first()
    
    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No has dado like a esta publicación"
        )
    
    db.delete(like)
    db.commit()
    
    return {"message": "Like eliminado exitosamente"}

# ===== COMENTARIOS =====

@router.post("/{publicacion_id}/comentarios", response_model=ComentarioResponse, status_code=status.HTTP_201_CREATED)
def crear_comentario(
    publicacion_id: int,
    comentario_data: ComentarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un comentario en una publicación"""
    
    # Verificar que la publicación exista
    publicacion = db.query(Publicacion).filter(
        Publicacion.id == publicacion_id,
        Publicacion.activo == True
    ).first()
    
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    # Crear comentario
    nuevo_comentario = Comentario(
        publicacion_id=publicacion_id,
        usuario_id=current_user.id,
        contenido=comentario_data.contenido
    )
    
    db.add(nuevo_comentario)
    db.commit()
    db.refresh(nuevo_comentario)
    
    return nuevo_comentario

@router.get("/{publicacion_id}/comentarios", response_model=List[ComentarioResponse])
def listar_comentarios(
    publicacion_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista los comentarios de una publicación"""
    
    comentarios = db.query(Comentario).filter(
        Comentario.publicacion_id == publicacion_id,
        Comentario.activo == True
    ).order_by(Comentario.created_at).offset(skip).limit(limit).all()
    
    return comentarios

@router.delete("/comentarios/{comentario_id}", response_model=Message)
def eliminar_comentario(
    comentario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un comentario"""
    
    comentario = db.query(Comentario).filter(Comentario.id == comentario_id).first()
    
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado"
        )
    
    # Verificar permisos (dueño del comentario o admin)
    if comentario.usuario_id != current_user.id and current_user.tipo_usuario != TipoUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este comentario"
        )
    
    # Soft delete
    comentario.activo = False
    db.commit()
    
    return {"message": "Comentario eliminado exitosamente"}
