from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
import logging
from database import get_db
from models import (
    Usuario, Seguidor, RolUsuario, EstadoUsuario, Auditoria,
    Publicacion, ReaccionPublicacion, ComentarioPublicacion,
    Notificacion, DispositivoUsuario
)
from schemas import (
    UsuarioResponse, UsuarioUpdate, Message,
    SeguidorCreate, SeguidorResponse, BusquedaUsuarios,
    UsuarioUpdateWithFile
)
from auth import get_current_user, require_roles
from datetime import datetime
from services.firebase_push_service import firebase_push_service
from services.cloudinary_service import cloudinary_service


router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])
logger = logging.getLogger("upred.usuarios")

def _get_active_push_tokens(db: Session, user_id: int) -> list[str]:
    dispositivos = db.query(DispositivoUsuario).filter(
        DispositivoUsuario.usuario_id == user_id,
        DispositivoUsuario.activo == True,
        DispositivoUsuario.token_push.isnot(None)
    ).order_by(DispositivoUsuario.ultima_actividad_en.desc()).all()
    tokens: list[str] = []
    seen_tokens: set[str] = set()
    for dispositivo in dispositivos:
        token = (dispositivo.token_push or "").strip()
        if not token or token in seen_tokens:
            continue
        seen_tokens.add(token)
        tokens.append(token)
    return tokens

def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    value_str = str(value).strip().lower()
    return value_str in ('true', '1', 'yes', 'on')

def _parse_int(value):
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

async def _extract_update_data(request: Request):
    """Extrae datos de actualización de usuario, incluyendo archivo de foto de perfil"""
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("foto_perfil")
        data = {
            "nombre": form.get("nombre"),
            "apellido_paterno": form.get("apellido_paterno"),
            "apellido_materno": form.get("apellido_materno"),
            "fecha_nacimiento": form.get("fecha_nacimiento"),
            "telefono": form.get("telefono"),
            "biografia": form.get("biografia"),
            "carrera_id": _parse_int(form.get("carrera_id")),
            "cuatrimestre_id": _parse_int(form.get("cuatrimestre_id")),
        }
        # patch semantics: ignore omitted/blank fields to avoid nulling NOT NULL columns
        cleaned = {k: v for k, v in data.items() if v is not None and not (isinstance(v, str) and v.strip() == "")}
        return cleaned, file

    # Fallback para JSON (sin archivo)
    payload = await request.json()
    cleaned = {k: v for k, v in payload.items() if v is not None}
    return cleaned, None

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
async def actualizar_usuario(
    usuario_id: int,
    request: Request,
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
    
    try:
        payload, file = await _extract_update_data(request)
        usuario_data = UsuarioUpdateWithFile.model_validate(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datos inválidos: {str(e)}"
        )
    
    # Procesar foto de perfil si se proporcionó
    if file and file.filename:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten imágenes para la foto de perfil"
            )
        
        try:
            file_data = await file.read()
            if len(file_data) > 5 * 1024 * 1024:  # 5MB máximo
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La foto de perfil no debe superar 5MB"
                )
            
            public_id = f"perfiles/{usuario_id}"
            if cloudinary_service.is_configured():
                foto_perfil_url = cloudinary_service.upload_image(file_data, public_id)
                usuario.foto_perfil_url = foto_perfil_url
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Servicio de almacenamiento de imágenes no disponible"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar la foto de perfil: {str(e)}"
            )
    
    # Actualizar otros campos
    update_data = usuario_data.model_dump(exclude_unset=True, exclude_none=True)
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
    logger.info("Intentando seguir usuario_id=%s por current_user_id=%s", usuario_id, current_user.id)
    
    if usuario_id == current_user.id:
        logger.warning("Usuario intento seguirse a si mismo: %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes seguirte a ti mismo"
        )
    
    # Verificar que el usuario existe
    usuario_a_seguir = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario_a_seguir:
        logger.warning("Usuario a seguir no encontrado: %s", usuario_id)
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
        logger.warning("Usuario ya sigue a este usuario: follower=%s followed=%s", current_user.id, usuario_id)
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
    logger.info("Relacion de seguimiento creada: follower=%s followed=%s", current_user.id, usuario_id)

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
    )
    db.add(notificacion)
    logger.info("Notificacion creada para usuario_id=%s", usuario_id)

    db.commit()
    logger.info("Commit realizado para seguir usuario")

    # Intento de push FCM (no bloquea la accion principal si falla)
    try:
        tokens = _get_active_push_tokens(db, usuario_id)
        if not tokens:
            logger.warning(
                "Sin dispositivos activos para push nuevo_seguidor usuario_destino=%s follower=%s",
                usuario_id,
                current_user.id,
            )
        else:
            sent_count = 0
            for token in tokens:
                sent = firebase_push_service.send_to_token(
                    token=token,
                    title="Nuevo seguidor",
                    body=f"{current_user.nombre} {current_user.apellido_paterno} comenzo a seguirte",
                    data={
                        "target_type": "perfil",
                        "title": "Nuevo seguidor",
                        "body": f"{current_user.nombre} {current_user.apellido_paterno} comenzo a seguirte",
                        "follower_user_id": str(current_user.id),
                        "user_id": str(usuario_id),
                    },
                )
                if sent:
                    sent_count += 1
            logger.info(
                "Push nuevo_seguidor usuario_destino=%s follower=%s enviados=%s total_tokens=%s",
                usuario_id,
                current_user.id,
                sent_count,
                len(tokens),
            )
    except Exception:
        logger.exception(
            "Error enviando push nuevo_seguidor usuario_destino=%s follower=%s",
            usuario_id,
            current_user.id,
        )
    
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
async def actualizar_perfil(
    request: Request,
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
    
    try:
        payload, file = await _extract_update_data(request)
        usuario_update = UsuarioUpdateWithFile.model_validate(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datos inválidos: {str(e)}"
        )

    if file and file.filename:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten imágenes para la foto de perfil"
            )
        try:
            file_data = await file.read()
            if len(file_data) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La foto de perfil no debe superar 5MB"
                )
            if not cloudinary_service.is_configured():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Servicio de almacenamiento de imágenes no disponible"
                )
            public_id = f"perfiles/{current_user.id}"
            usuario.foto_perfil_url = cloudinary_service.upload_image(file_data, public_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar la foto de perfil: {str(e)}"
            )

    update_data = usuario_update.model_dump(exclude_unset=True, exclude_none=True)
    update_data.pop('correo_institucional', None)
    update_data.pop('id', None)

    for key, value in update_data.items():
        setattr(usuario, key, value)
    
    db.commit()
    db.refresh(usuario)
    
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
