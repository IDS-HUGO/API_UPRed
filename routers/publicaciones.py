from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from typing import List, Optional
from database import get_db
from models import (
    Publicacion, TipoPublicacion, ComentarioPublicacion, ReaccionPublicacion,
    CatalogoReaccion, MultimediaPublicacion, Usuario, RolUsuario,
    AudienciaPublicacion, Auditoria
)
from schemas import (
    PublicacionCreate, PublicacionUpdate, PublicacionResponse,
    ComentarioPublicacionCreate, ComentarioPublicacionUpdate, ComentarioPublicacionResponse,
    ReaccionPublicacionCreate, ReaccionPublicacionResponse,
    TipoPublicacionResponse, CatalogoReaccionResponse,
    BusquedaPublicaciones, Message
)
from auth import get_current_user

router = APIRouter(prefix="/api/publicaciones", tags=["Publicaciones"])

# =====================================================================
# ENDPOINTS DE TIPOS DE PUBLICACIÓN
# =====================================================================

@router.get("/tipos", response_model=List[TipoPublicacionResponse])
def listar_tipos_publicacion(db: Session = Depends(get_db)):
    """Lista todos los tipos de publicación"""
    tipos = db.query(TipoPublicacion).all()
    return tipos

# =====================================================================
# ENDPOINTS DE PUBLICACIONES
# =====================================================================

@router.get("/", response_model=List[PublicacionResponse])
def listar_publicaciones(
    autor_id: Optional[int] = None,
    carrera_id: Optional[int] = None,
    tipo_publicacion_id: Optional[int] = None,
    audiencia: Optional[AudienciaPublicacion] = None,
    activa: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista publicaciones con filtros"""
    query = db.query(Publicacion)
    
    if autor_id:
        query = query.filter(Publicacion.autor_id == autor_id)
    if tipo_publicacion_id:
        query = query.filter(Publicacion.tipo_publicacion_id == tipo_publicacion_id)
    if audiencia:
        query = query.filter(Publicacion.audiencia == audiencia)
    if activa is not None:
        query = query.filter(Publicacion.activa == activa)
    
    # Filtrar según la carrera del usuario
    if carrera_id:
        query = query.filter(
            or_(
                Publicacion.audiencia == AudienciaPublicacion.general,
                and_(
                    Publicacion.audiencia == AudienciaPublicacion.carrera,
                    Publicacion.carrera_objetivo_id == carrera_id
                )
            )
        )
    else:
        # Si no se especifica carrera, mostrar publicaciones generales y de la carrera del usuario
        if current_user.carrera_id:
            query = query.filter(
                or_(
                    Publicacion.audiencia == AudienciaPublicacion.general,
                    and_(
                        Publicacion.audiencia == AudienciaPublicacion.carrera,
                        Publicacion.carrera_objetivo_id == current_user.carrera_id
                    )
                )
            )
        else:
            query = query.filter(Publicacion.audiencia == AudienciaPublicacion.general)
    
    publicaciones = query.order_by(Publicacion.publicada_en.desc()).offset(skip).limit(limit).all()
    
    # Agregar contadores
    result = []
    for pub in publicaciones:
        pub_dict = PublicacionResponse.model_validate(pub)
        pub_dict.total_comentarios = db.query(func.count(ComentarioPublicacion.id)).filter(
            ComentarioPublicacion.publicacion_id == pub.id,
            ComentarioPublicacion.activo == True
        ).scalar() or 0
        pub_dict.total_reacciones = db.query(func.count(ReaccionPublicacion.publicacion_id)).filter(
            ReaccionPublicacion.publicacion_id == pub.id
        ).scalar() or 0
        result.append(pub_dict)
    
    return result

@router.get("/feed", response_model=List[PublicacionResponse])
def obtener_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene el feed personalizado de publicaciones para el usuario actual"""
    query = db.query(Publicacion).filter(
        Publicacion.activa == True
    )
    
    # Filtrar por audiencia
    if current_user.carrera_id:
        query = query.filter(
            or_(
                Publicacion.audiencia == AudienciaPublicacion.general,
                and_(
                    Publicacion.audiencia == AudienciaPublicacion.carrera,
                    Publicacion.carrera_objetivo_id == current_user.carrera_id,
                    or_(
                        Publicacion.cuatrimestre_objetivo_id.is_(None),
                        Publicacion.cuatrimestre_objetivo_id == current_user.cuatrimestre_id
                    )
                )
            )
        )
    else:
        query = query.filter(Publicacion.audiencia == AudienciaPublicacion.general)
    
    publicaciones = query.order_by(Publicacion.publicada_en.desc()).offset(skip).limit(limit).all()
    
    # Agregar contadores
    result = []
    for pub in publicaciones:
        pub_dict = PublicacionResponse.model_validate(pub)
        pub_dict.total_comentarios = db.query(func.count(ComentarioPublicacion.id)).filter(
            ComentarioPublicacion.publicacion_id == pub.id,
            ComentarioPublicacion.activo == True
        ).scalar() or 0
        pub_dict.total_reacciones = db.query(func.count(ReaccionPublicacion.publicacion_id)).filter(
            ReaccionPublicacion.publicacion_id == pub.id
        ).scalar() or 0
        result.append(pub_dict)
    
    return result

@router.get("/buscar", response_model=List[PublicacionResponse])
def buscar_publicaciones(
    query: str = Query(..., min_length=1),
    carrera_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Busca publicaciones por título o contenido"""
    q = db.query(Publicacion).filter(
        Publicacion.activa == True,
        or_(
            Publicacion.titulo.ilike(f"%{query}%"),
            Publicacion.contenido.ilike(f"%{query}%")
        )
    )
    
    # Aplicar filtros de audiencia
    if current_user.carrera_id:
        q = q.filter(
            or_(
                Publicacion.audiencia == AudienciaPublicacion.general,
                and_(
                    Publicacion.audiencia == AudienciaPublicacion.carrera,
                    Publicacion.carrera_objetivo_id == current_user.carrera_id
                )
            )
        )
    else:
        q = q.filter(Publicacion.audiencia == AudienciaPublicacion.general)
    
    if carrera_id:
        q = q.filter(Publicacion.carrera_objetivo_id == carrera_id)
    
    publicaciones = q.order_by(Publicacion.publicada_en.desc()).limit(limit).all()
    
    # Agregar contadores
    result = []
    for pub in publicaciones:
        pub_dict = PublicacionResponse.model_validate(pub)
        pub_dict.total_comentarios = db.query(func.count(ComentarioPublicacion.id)).filter(
            ComentarioPublicacion.publicacion_id == pub.id,
            ComentarioPublicacion.activo == True
        ).scalar() or 0
        pub_dict.total_reacciones = db.query(func.count(ReaccionPublicacion.publicacion_id)).filter(
            ReaccionPublicacion.publicacion_id == pub.id
        ).scalar() or 0
        result.append(pub_dict)
    
    return result

@router.get("/{publicacion_id}", response_model=PublicacionResponse)
def obtener_publicacion(publicacion_id: int, db: Session = Depends(get_db)):
    """Obtiene una publicación por ID"""
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    pub_dict = PublicacionResponse.model_validate(publicacion)
    pub_dict.total_comentarios = db.query(func.count(ComentarioPublicacion.id)).filter(
        ComentarioPublicacion.publicacion_id == publicacion.id,
        ComentarioPublicacion.activo == True
    ).scalar() or 0
    pub_dict.total_reacciones = db.query(func.count(ReaccionPublicacion.publicacion_id)).filter(
        ReaccionPublicacion.publicacion_id == publicacion.id
    ).scalar() or 0
    
    return pub_dict

@router.post("/", response_model=PublicacionResponse, status_code=status.HTTP_201_CREATED)
def crear_publicacion(
    publicacion_data: PublicacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva publicación"""
    # Validar audiencia
    if publicacion_data.audiencia == AudienciaPublicacion.carrera and not publicacion_data.carrera_objetivo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Para publicaciones de carrera, debe especificar carrera_objetivo_id"
        )
    
    # Si es general, eliminar referencias de carrera
    if publicacion_data.audiencia == AudienciaPublicacion.general:
        publicacion_data.carrera_objetivo_id = None
        publicacion_data.cuatrimestre_objetivo_id = None
    
    nueva_publicacion = Publicacion(
        autor_id=current_user.id,
        **publicacion_data.model_dump()
    )
    
    db.add(nueva_publicacion)
    db.flush()
    
    # Registrar en auditoría
    auditoria = Auditoria(
        actor_usuario_id=current_user.id,
        accion="crear_publicacion",
        entidad="publicaciones",
        entidad_id=str(nueva_publicacion.id),
        detalle={
            "audiencia": publicacion_data.audiencia.value,
            "carrera_objetivo_id": publicacion_data.carrera_objetivo_id
        }
    )
    db.add(auditoria)
    
    db.commit()
    db.refresh(nueva_publicacion)
    
    return nueva_publicacion

@router.put("/{publicacion_id}", response_model=PublicacionResponse)
def actualizar_publicacion(
    publicacion_id: int,
    publicacion_data: PublicacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una publicación"""
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    # Verificar permisos
    if publicacion.autor_id != current_user.id and current_user.rol != RolUsuario.administrador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar esta publicación"
        )
    
    update_data = publicacion_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(publicacion, key, value)
    
    db.commit()
    db.refresh(publicacion)
    return publicacion

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
    if publicacion.autor_id != current_user.id and current_user.rol not in [RolUsuario.administrador, RolUsuario.moderador]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta publicación"
        )
    
    # Soft delete
    from datetime import datetime
    publicacion.activa = False
    publicacion.eliminada_en = datetime.utcnow()
    
    db.commit()
    return {"message": "Publicación eliminada correctamente"}

# =====================================================================
# ENDPOINTS DE COMENTARIOS
# =====================================================================

@router.get("/{publicacion_id}/comentarios", response_model=List[ComentarioPublicacionResponse])
def listar_comentarios(
    publicacion_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista comentarios de una publicación"""
    comentarios = db.query(ComentarioPublicacion).filter(
        ComentarioPublicacion.publicacion_id == publicacion_id,
        ComentarioPublicacion.activo == True
    ).order_by(ComentarioPublicacion.creado_en.asc()).offset(skip).limit(limit).all()
    
    return comentarios

@router.post("/{publicacion_id}/comentarios", response_model=ComentarioPublicacionResponse, status_code=status.HTTP_201_CREATED)
def crear_comentario(
    publicacion_id: int,
    comentario_data: ComentarioPublicacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un comentario en una publicación"""
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    if not publicacion.permite_comentarios:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta publicación no permite comentarios"
        )
    
    nuevo_comentario = ComentarioPublicacion(
        publicacion_id=publicacion_id,
        usuario_id=current_user.id,
        contenido=comentario_data.contenido,
        comentario_padre_id=comentario_data.comentario_padre_id
    )
    
    db.add(nuevo_comentario)
    db.commit()
    db.refresh(nuevo_comentario)
    
    return nuevo_comentario

@router.put("/comentarios/{comentario_id}", response_model=ComentarioPublicacionResponse)
def actualizar_comentario(
    comentario_id: int,
    comentario_data: ComentarioPublicacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un comentario"""
    comentario = db.query(ComentarioPublicacion).filter(ComentarioPublicacion.id == comentario_id).first()
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado"
        )
    
    # Verificar permisos
    if comentario.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este comentario"
        )
    
    update_data = comentario_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(comentario, key, value)
    
    db.commit()
    db.refresh(comentario)
    return comentario

@router.delete("/comentarios/{comentario_id}", response_model=Message)
def eliminar_comentario(
    comentario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina (desactiva) un comentario"""
    comentario = db.query(ComentarioPublicacion).filter(ComentarioPublicacion.id == comentario_id).first()
    if not comentario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado"
        )
    
    # Verificar permisos
    if comentario.usuario_id != current_user.id and current_user.rol not in [RolUsuario.administrador, RolUsuario.moderador]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este comentario"
        )
    
    comentario.activo = False
    db.commit()
    return {"message": "Comentario eliminado correctamente"}

# =====================================================================
# ENDPOINTS DE REACCIONES
# =====================================================================

@router.get("/reacciones/catalogo", response_model=List[CatalogoReaccionResponse])
def listar_catalogo_reacciones(db: Session = Depends(get_db)):
    """Lista todas las reacciones disponibles"""
    reacciones = db.query(CatalogoReaccion).all()
    return reacciones

@router.post("/{publicacion_id}/reacciones", response_model=Message, status_code=status.HTTP_201_CREATED)
def agregar_reaccion(
    publicacion_id: int,
    reaccion_data: ReaccionPublicacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Agrega o actualiza una reacción a una publicación"""
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    # Verificar si ya existe una reacción
    reaccion_existente = db.query(ReaccionPublicacion).filter(
        ReaccionPublicacion.publicacion_id == publicacion_id,
        ReaccionPublicacion.usuario_id == current_user.id
    ).first()
    
    if reaccion_existente:
        # Actualizar reacción
        reaccion_existente.reaccion_id = reaccion_data.reaccion_id
        db.commit()
        return {"message": "Reacción actualizada"}
    else:
        # Crear nueva reacción
        nueva_reaccion = ReaccionPublicacion(
            publicacion_id=publicacion_id,
            usuario_id=current_user.id,
            reaccion_id=reaccion_data.reaccion_id
        )
        db.add(nueva_reaccion)
        db.commit()
        return {"message": "Reacción agregada"}

@router.delete("/{publicacion_id}/reacciones", response_model=Message)
def eliminar_reaccion(
    publicacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina la reacción del usuario en una publicación"""
    reaccion = db.query(ReaccionPublicacion).filter(
        ReaccionPublicacion.publicacion_id == publicacion_id,
        ReaccionPublicacion.usuario_id == current_user.id
    ).first()
    
    if not reaccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes reacción en esta publicación"
        )
    
    db.delete(reaccion)
    db.commit()
    return {"message": "Reacción eliminada"}

@router.get("/{publicacion_id}/reacciones", response_model=List[ReaccionPublicacionResponse])
def listar_reacciones_publicacion(
    publicacion_id: int,
    db: Session = Depends(get_db)
):
    """Lista todas las reacciones de una publicación con conteos"""
    reacciones = db.query(ReaccionPublicacion).filter(
        ReaccionPublicacion.publicacion_id == publicacion_id
    ).all()
    
    return reacciones
