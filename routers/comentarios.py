from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import (
    ComentarioPublicacion, Usuario, Publicacion, Auditoria
)
from schemas import (
    ComentarioPublicacionCreate, ComentarioPublicacionUpdate, 
    ComentarioPublicacionResponse, Message
)
from auth import get_current_user

router = APIRouter(prefix="/api/comentarios", tags=["Comentarios"])

# =====================================================================
# ENDPOINTS DE COMENTARIOS EN PUBLICACIONES
# =====================================================================

@router.post("/publicaciones/{publicacion_id}", response_model=ComentarioPublicacionResponse)
def crear_comentario(
    publicacion_id: int,
    comentario_data: ComentarioPublicacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo comentario en una publicación"""
    # Verificar que la publicación existe
    publicacion = db.query(Publicacion).filter(
        Publicacion.id == publicacion_id
    ).first()
    
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    # Verificar que el comentario padre existe (si aplica)
    if comentario_data.comentario_padre_id:
        comentario_padre = db.query(ComentarioPublicacion).filter(
            ComentarioPublicacion.id == comentario_data.comentario_padre_id,
            ComentarioPublicacion.publicacion_id == publicacion_id
        ).first()
        
        if not comentario_padre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comentario padre no encontrado"
            )
    
    # Crear nuevo comentario
    nuevo_comentario = ComentarioPublicacion(
        publicacion_id=publicacion_id,
        usuario_id=current_user.id,
        comentario_padre_id=comentario_data.comentario_padre_id,
        contenido=comentario_data.contenido,
        activo=True
    )
    
    db.add(nuevo_comentario)
    db.commit()
    db.refresh(nuevo_comentario)
    
    # Registrar auditoría
    auditoria = Auditoria(
        tipo_accion="crear_comentario",
        usuario_id=current_user.id,
        detalles={"comentario_id": nuevo_comentario.id, "publicacion_id": publicacion_id}
    )
    db.add(auditoria)
    db.commit()
    
    return nuevo_comentario


@router.get("/publicaciones/{publicacion_id}", response_model=List[ComentarioPublicacionResponse])
def obtener_comentarios_publicacion(
    publicacion_id: int,
    comentario_padre_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtener todos los comentarios de una publicación (con paginación)"""
    # Verificar que la publicación existe
    publicacion = db.query(Publicacion).filter(
        Publicacion.id == publicacion_id
    ).first()
    
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    query = db.query(ComentarioPublicacion).filter(
        ComentarioPublicacion.publicacion_id == publicacion_id,
        ComentarioPublicacion.activo == True
    )
    
    # Si se pide comentarios anidados (respuestas a un comentario)
    if comentario_padre_id is not None:
        query = query.filter(
            ComentarioPublicacion.comentario_padre_id == comentario_padre_id
        )
    else:
        # Solo comentarios principales (sin padre)
        query = query.filter(
            ComentarioPublicacion.comentario_padre_id == None
        )
    
    comentarios = query.order_by(
        ComentarioPublicacion.creado_en.desc()
    ).offset(skip).limit(limit).all()
    
    return comentarios


@router.get("/{comentario_id}", response_model=ComentarioPublicacionResponse)
def obtener_comentario(
    comentario_id: int,
    db: Session = Depends(get_db)
):
    """Obtener un comentario específico por ID"""
    comentario = db.query(ComentarioPublicacion).filter(
        ComentarioPublicacion.id == comentario_id,
        ComentarioPublicacion.activo == True
    ).first()
    
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado"
        )
    
    return comentario


@router.get("/{comentario_id}/respuestas", response_model=List[ComentarioPublicacionResponse])
def obtener_respuestas_comentario(
    comentario_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Obtener todas las respuestas a un comentario"""
    # Verificar que el comentario padre existe
    comentario_padre = db.query(ComentarioPublicacion).filter(
        ComentarioPublicacion.id == comentario_id,
        ComentarioPublicacion.activo == True
    ).first()
    
    if not comentario_padre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado"
        )
    
    respuestas = db.query(ComentarioPublicacion).filter(
        ComentarioPublicacion.comentario_padre_id == comentario_id,
        ComentarioPublicacion.activo == True
    ).order_by(
        ComentarioPublicacion.creado_en.desc()
    ).offset(skip).limit(limit).all()
    
    return respuestas


@router.put("/{comentario_id}", response_model=ComentarioPublicacionResponse)
def actualizar_comentario(
    comentario_id: int,
    comentario_data: ComentarioPublicacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un comentario (solo el propietario puede hacerlo)"""
    comentario = db.query(ComentarioPublicacion).filter(
        ComentarioPublicacion.id == comentario_id
    ).first()
    
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado"
        )
    
    # Verificar permisos
    if comentario.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para editar este comentario"
        )
    
    # Actualizar contenido
    if comentario_data.contenido:
        comentario.contenido = comentario_data.contenido
    
    db.commit()
    db.refresh(comentario)
    
    # Registrar auditoría
    auditoria = Auditoria(
        tipo_accion="actualizar_comentario",
        usuario_id=current_user.id,
        detalles={"comentario_id": comentario_id}
    )
    db.add(auditoria)
    db.commit()
    
    return comentario


@router.delete("/{comentario_id}", response_model=Message)
def eliminar_comentario(
    comentario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar un comentario (soft delete - solo marca como inactivo)"""
    comentario = db.query(ComentarioPublicacion).filter(
        ComentarioPublicacion.id == comentario_id
    ).first()
    
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado"
        )
    
    # Verificar permisos (propietario o admin)
    if comentario.usuario_id != current_user.id and current_user.rol.value != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este comentario"
        )
    
    # Soft delete
    comentario.activo = False
    db.commit()
    
    # Registrar auditoría
    auditoria = Auditoria(
        tipo_accion="eliminar_comentario",
        usuario_id=current_user.id,
        detalles={"comentario_id": comentario_id}
    )
    db.add(auditoria)
    db.commit()
    
    return {"message": "Comentario eliminado correctamente"}


@router.get("/contar/{publicacion_id}", response_model=dict)
def contar_comentarios(
    publicacion_id: int,
    db: Session = Depends(get_db)
):
    """Contar comentarios principales de una publicación"""
    # Verificar que la publicación existe
    publicacion = db.query(Publicacion).filter(
        Publicacion.id == publicacion_id
    ).first()
    
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    total = db.query(ComentarioPublicacion).filter(
        ComentarioPublicacion.publicacion_id == publicacion_id,
        ComentarioPublicacion.comentario_padre_id == None,
        ComentarioPublicacion.activo == True
    ).count()
    
    return {"publicacion_id": publicacion_id, "total_comentarios": total}
