from fastapi import APIRouter, Depends, HTTPException, Response, status, Query, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from typing import List, Optional
import logging
from pydantic import ValidationError
from database import get_db
from services.cloudinary_service import cloudinary_service
from services.firebase_push_service import firebase_push_service
from models import (
    Publicacion, TipoPublicacion, ComentarioPublicacion, ReaccionPublicacion,
    CatalogoReaccion, MultimediaPublicacion, Usuario, RolUsuario,
    AudienciaPublicacion, Auditoria, TipoMensaje, Notificacion, DispositivoUsuario
)
from schemas import (
    PublicacionCreate, PublicacionUpdate, PublicacionResponse,
    ComentarioPublicacionCreate, ComentarioPublicacionUpdate, ComentarioPublicacionResponse,
    ReaccionPublicacionCreate, ReaccionPublicacionResponse,
    TipoPublicacionResponse, CatalogoReaccionResponse,
    BusquedaPublicaciones, Message
)
from auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/publicaciones", tags=["Publicaciones"])
logger = logging.getLogger("upred.publicaciones")

# =====================================================================
# ENDPOINT SIMPLIFICADO PARA MÓVIL (SIN AUTENTICACIÓN PARA DEBUG)
# =====================================================================

@router.get("/test")
def test_endpoint():
    """Endpoint de prueba para verificar que el router funciona"""
    return {"status": "ok", "message": "Publicaciones router está funcionando"}

def _build_publicacion_response(pub: Publicacion, db: Session) -> dict:
    """Helper function para construir respuesta de publicación con formato correcto"""
    # Crear autor simplificado
    autor_data = None
    if pub.autor:
        autor_data = {
            "nombre": pub.autor.nombre,
            "apellido_paterno": pub.autor.apellido_paterno,
            "apellido_materno": pub.autor.apellido_materno,
            "foto_perfil_url": pub.autor.foto_perfil_url
        }
    
    # Construir respuesta
    return {
        "id": pub.id,
        "autor_id": pub.autor_id,
        "titulo": pub.titulo,
        "contenido": pub.contenido,
        "audiencia": pub.audiencia,
        "carrera_objetivo_id": pub.carrera_objetivo_id,
        "cuatrimestre_objetivo_id": pub.cuatrimestre_objetivo_id,
        "tipo_publicacion_id": pub.tipo_publicacion_id,
        "permite_comentarios": pub.permite_comentarios,
        "es_anonima": pub.es_anonima,
        "activa": pub.activa,
        "publicada_en": pub.publicada_en,
        "actualizada_en": pub.actualizada_en,
        "autor": autor_data,
        "imagen_url": _get_imagen_url(pub.id, db),
        "total_comentarios": db.query(func.count(ComentarioPublicacion.id)).filter(
            ComentarioPublicacion.publicacion_id == pub.id,
            ComentarioPublicacion.activo == True
        ).scalar() or 0,
        "total_reacciones": db.query(func.count(ReaccionPublicacion.publicacion_id)).filter(
            ReaccionPublicacion.publicacion_id == pub.id
        ).scalar() or 0
    }

def _get_imagen_url(publicacion_id: int, db: Session) -> Optional[str]:
    """Retorna la URL de Cloudinary si existe, o None."""
    media = db.query(MultimediaPublicacion).filter(
        MultimediaPublicacion.publicacion_id == publicacion_id,
        MultimediaPublicacion.tipo == TipoMensaje.imagen,
    ).order_by(MultimediaPublicacion.orden.asc()).first()
    if not media:
        return None
    # URL de Cloudinary tiene precedencia; fallback al endpoint binario legacy
    if media.url_archivo:
        return media.url_archivo
    return f"/api/publicaciones/{publicacion_id}/imagen"


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    value_str = str(value).strip()
    if value_str == "":
        return None
    try:
        return int(value_str)
    except ValueError:
        return None


def _parse_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    value_str = str(value).strip().lower()
    if value_str in ("true", "1", "yes", "si", "on"):
        return True
    if value_str in ("false", "0", "no", "off"):
        return False
    return default


async def _extract_publicacion_data(request: Request):
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        files = form.getlist("files")
        data = {
            "titulo": form.get("titulo"),
            "contenido": form.get("contenido"),
            "audiencia": form.get("audiencia") or AudienciaPublicacion.general,
            "carrera_objetivo_id": _parse_int(form.get("carrera_objetivo_id")),
            "cuatrimestre_objetivo_id": _parse_int(form.get("cuatrimestre_objetivo_id")),
            "tipo_publicacion_id": _parse_int(form.get("tipo_publicacion_id")),
            "permite_comentarios": _parse_bool(form.get("permite_comentarios"), True),
            "es_anonima": _parse_bool(form.get("es_anonima"), False),
        }
        files = [f for f in files if getattr(f, "filename", None)]
        return data, files

    payload = await request.json()
    return payload, []

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

@router.get("", response_model=List[PublicacionResponse])
def listar_publicaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista publicaciones activas ordenadas por fecha (endpoint principal para móvil)"""
    # Query simplificado: solo publicaciones activas
    query = db.query(Publicacion).filter(Publicacion.activa == True)
    
    # Filtrar según la carrera del usuario (mostrar generales y de su carrera)
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
        # Si no tiene carrera, solo mostrar generales
        query = query.filter(Publicacion.audiencia == AudienciaPublicacion.general)
    
    publicaciones = query.order_by(Publicacion.publicada_en.desc()).offset(skip).limit(limit).all()
    
    # Construir respuesta usando la función helper
    result = [_build_publicacion_response(pub, db) for pub in publicaciones]
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

@router.get("/recientes", response_model=List[PublicacionResponse])
def obtener_publicaciones_recientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene las publicaciones más recientes"""
    query = db.query(Publicacion).filter(Publicacion.activa == True)
    
    # Aplicar filtros de audiencia
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

@router.get("/por-carrera/{carrera_id}", response_model=List[PublicacionResponse])
def obtener_publicaciones_por_carrera(
    carrera_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene publicaciones filtradas por carrera específica"""
    query = db.query(Publicacion).filter(
        Publicacion.activa == True,
        or_(
            Publicacion.audiencia == AudienciaPublicacion.general,
            and_(
                Publicacion.audiencia == AudienciaPublicacion.carrera,
                Publicacion.carrera_objetivo_id == carrera_id
            )
        )
    )
    
    publicaciones = query.order_by(Publicacion.publicada_en.desc()).offset(skip).limit(limit).all()
    
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

@router.get("/populares", response_model=List[PublicacionResponse])
def obtener_publicaciones_populares(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene las publicaciones más populares (más reacciones y comentarios)"""
    query = db.query(Publicacion).filter(Publicacion.activa == True)
    
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
    
    # Subconsulta para contar reacciones
    subq_reacciones = db.query(
        ReaccionPublicacion.publicacion_id,
        func.count(ReaccionPublicacion.usuario_id).label('num_reacciones')
    ).group_by(ReaccionPublicacion.publicacion_id).subquery()
    
    # Subconsulta para contar comentarios
    subq_comentarios = db.query(
        ComentarioPublicacion.publicacion_id,
        func.count(ComentarioPublicacion.id).label('num_comentarios')
    ).filter(ComentarioPublicacion.activo == True).group_by(ComentarioPublicacion.publicacion_id).subquery()
    
    # Join con las subconsultas
    query = query.outerjoin(subq_reacciones, Publicacion.id == subq_reacciones.c.publicacion_id)
    query = query.outerjoin(subq_comentarios, Publicacion.id == subq_comentarios.c.publicacion_id)
    
    # Ordenar por popularidad (reacciones + comentarios)
    query = query.order_by(
        (func.coalesce(subq_reacciones.c.num_reacciones, 0) + func.coalesce(subq_comentarios.c.num_comentarios, 0)).desc(),
        Publicacion.publicada_en.desc()
    )
    
    publicaciones = query.offset(skip).limit(limit).all()
    
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

@router.get("/mis-publicaciones", response_model=List[PublicacionResponse])
def obtener_mis_publicaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene todas las publicaciones del usuario actual"""
    query = db.query(Publicacion).filter(
        Publicacion.autor_id == current_user.id,
        Publicacion.activa == True
    )
    
    publicaciones = query.order_by(Publicacion.publicada_en.desc()).offset(skip).limit(limit).all()
    
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

@router.get("/{publicacion_id}/imagen")
def obtener_imagen_publicacion(publicacion_id: int, db: Session = Depends(get_db)):
    """Redirige a la URL de Cloudinary o sirve datos binarios legacy"""
    media = db.query(MultimediaPublicacion).filter(
        MultimediaPublicacion.publicacion_id == publicacion_id,
        MultimediaPublicacion.tipo == TipoMensaje.imagen,
    ).order_by(MultimediaPublicacion.orden.asc()).first()

    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen no encontrada")

    if media.url_archivo:
        return RedirectResponse(url=media.url_archivo, status_code=302)

    # Fallback: datos binarios almacenados antes de Cloudinary
    if media.datos_archivo:
        return Response(content=media.datos_archivo, media_type="image/jpeg")

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen no encontrada")


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

@router.post("", response_model=PublicacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_publicacion(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una nueva publicación (compatible con formato simplificado de móvil)"""
    try:
        payload, files = await _extract_publicacion_data(request)
        
        # Asegurarse de que los campos opcionales tengan valores por defecto
        if "tipo_publicacion_id" not in payload or payload["tipo_publicacion_id"] is None:
            payload["tipo_publicacion_id"] = None
        if "permite_comentarios" not in payload:
            payload["permite_comentarios"] = True
        if "es_anonima" not in payload:
            payload["es_anonima"] = False
        if "carrera_objetivo_id" not in payload:
            payload["carrera_objetivo_id"] = None
        if "cuatrimestre_objetivo_id" not in payload:
            payload["cuatrimestre_objetivo_id"] = None
            
        publicacion_data = PublicacionCreate.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cuerpo de solicitud inválido: {str(e)}"
        )

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

    # Subir imágenes a Cloudinary
    if files:
        for index, file in enumerate(files, start=1):
            if not file.content_type or not file.content_type.startswith("image/"):
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Solo se permiten imagenes"
                )
            try:
                file_data = await file.read()

                if len(file_data) > 5 * 1024 * 1024:
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="La imagen no debe superar 5MB"
                    )

                public_id = f"publicaciones/{nueva_publicacion.id}_{index}"

                if cloudinary_service.is_configured():
                    cloudinary_url = cloudinary_service.upload_image(file_data, public_id)
                    multimedia = MultimediaPublicacion(
                        publicacion_id=nueva_publicacion.id,
                        tipo=TipoMensaje.imagen,
                        url_archivo=cloudinary_url,
                        datos_archivo=None,
                        orden=index
                    )
                else:
                    multimedia = MultimediaPublicacion(
                        publicacion_id=nueva_publicacion.id,
                        tipo=TipoMensaje.imagen,
                        url_archivo=None,
                        datos_archivo=file_data,
                        orden=index
                    )

                db.add(multimedia)
            except HTTPException:
                db.rollback()
                raise
            except Exception as e:
                try:
                    multimedia = MultimediaPublicacion(
                        publicacion_id=nueva_publicacion.id,
                        tipo=TipoMensaje.imagen,
                        url_archivo=None,
                        datos_archivo=file_data,
                        orden=index
                    )
                    db.add(multimedia)
                except Exception:
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error al procesar imagen: {str(e)}"
                    )

    # Registrar en auditoria
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

    # Devolver respuesta con formato correcto para móvil
    return _build_publicacion_response(nueva_publicacion, db)

@router.put("/{publicacion_id}", response_model=PublicacionResponse)
@router.put("/{publicacion_id}/", response_model=PublicacionResponse, include_in_schema=False)
@router.patch("/{publicacion_id}", response_model=PublicacionResponse, include_in_schema=False)
@router.patch("/{publicacion_id}/", response_model=PublicacionResponse, include_in_schema=False)
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
    
    # Devolver respuesta con formato correcto para móvil
    return _build_publicacion_response(publicacion, db)

@router.delete("/{publicacion_id}", response_model=Message)
@router.delete("/{publicacion_id}/", response_model=Message, include_in_schema=False)
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

    # Notificacion interna + push al autor de la publicacion (si comenta otra persona)
    if publicacion.autor_id != current_user.id:
        notificacion = Notificacion(
            usuario_id=publicacion.autor_id,
            tipo="nuevo_comentario",
            titulo="Nuevo comentario en tu publicacion",
            cuerpo=f"{current_user.nombre} {current_user.apellido_paterno} comento tu publicacion",
            datos={
                "target_type": "publicacion",
                "publication_id": str(publicacion_id),
                "user_id": str(publicacion.autor_id),
                "commenter_user_id": str(current_user.id),
            },
            leida=False,
        )
        db.add(notificacion)
        db.commit()

        try:
            dispositivo = db.query(DispositivoUsuario).filter(
                DispositivoUsuario.usuario_id == publicacion.autor_id,
                DispositivoUsuario.activo == True,
                DispositivoUsuario.token_push.isnot(None)
            ).order_by(DispositivoUsuario.ultima_actividad_en.desc()).first()

            if dispositivo and dispositivo.token_push:
                sent = firebase_push_service.send_to_token(
                    token=dispositivo.token_push,
                    title="Nuevo comentario",
                    body=f"{current_user.nombre} {current_user.apellido_paterno} comento tu publicacion",
                    data={
                        "target_type": "publicacion",
                        "title": "Nuevo comentario",
                        "body": f"{current_user.nombre} {current_user.apellido_paterno} comento tu publicacion",
                        "publication_id": str(publicacion_id),
                        "user_id": str(publicacion.autor_id),
                        "commenter_user_id": str(current_user.id),
                    },
                )
                logger.info(
                    "Push comentario desde publicaciones autor=%s comentario_id=%s enviado=%s",
                    publicacion.autor_id,
                    nuevo_comentario.id,
                    sent,
                )
            else:
                logger.warning(
                    "Sin dispositivo activo para push comentario autor=%s comentario_id=%s",
                    publicacion.autor_id,
                    nuevo_comentario.id,
                )
        except Exception:
            logger.exception(
                "Error push comentario desde publicaciones autor=%s comentario_id=%s",
                publicacion.autor_id,
                nuevo_comentario.id,
            )
    
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
