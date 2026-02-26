from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from database import get_db
from models import (
    Grupo, MiembroGrupo, PublicacionGrupo, Usuario, 
    RolMiembroGrupo, EstadoMembresia, PrivacidadGrupo, Auditoria
)
from schemas import (
    GrupoCreate, GrupoUpdate, GrupoResponse, GrupoDetailResponse,
    MiembroGrupoCreate, MiembroGrupoUpdate, MiembroGrupoResponse, MiembroGrupoDetailResponse,
    PublicacionGrupoCreate, PublicacionGrupoUpdate, PublicacionGrupoResponse,
    BusquedaGrupos, Message
)
from auth import get_current_user

router = APIRouter(prefix="/api/grupos", tags=["Grupos"])

# =====================================================================
# ENDPOINTS DE GRUPOS
# =====================================================================

@router.get("/", response_model=List[GrupoResponse])
def listar_grupos(
    carrera_id: Optional[int] = None,
    privacidad: Optional[PrivacidadGrupo] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista grupos con filtros opcionales"""
    query = db.query(Grupo)
    
    if carrera_id:
        query = query.filter(Grupo.carrera_id == carrera_id)
    if privacidad:
        query = query.filter(Grupo.privacidad == privacidad)
    
    grupos = query.offset(skip).limit(limit).all()
    
    # Agregar contador de miembros
    result = []
    for grupo in grupos:
        grupo_dict = GrupoResponse.model_validate(grupo)
        grupo_dict.total_miembros = db.query(func.count(MiembroGrupo.usuario_id)).filter(
            MiembroGrupo.grupo_id == grupo.id,
            MiembroGrupo.estado_membresia == EstadoMembresia.activo
        ).scalar() or 0
        result.append(grupo_dict)
    
    return result

@router.get("/buscar", response_model=List[GrupoResponse])
def buscar_grupos(
    query: str = Query(..., min_length=1),
    carrera_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Busca grupos por nombre o descripción"""
    q = db.query(Grupo).filter(
        or_(
            Grupo.nombre.ilike(f"%{query}%"),
            Grupo.descripcion.ilike(f"%{query}%")
        )
    )
    
    if carrera_id:
        q = q.filter(Grupo.carrera_id == carrera_id)
    
    grupos = q.limit(limit).all()
    
    # Agregar contador de miembros
    result = []
    for grupo in grupos:
        grupo_dict = GrupoResponse.model_validate(grupo)
        grupo_dict.total_miembros = db.query(func.count(MiembroGrupo.usuario_id)).filter(
            MiembroGrupo.grupo_id == grupo.id,
            MiembroGrupo.estado_membresia == EstadoMembresia.activo
        ).scalar() or 0
        result.append(grupo_dict)
    
    return result

@router.get("/mis-grupos", response_model=List[GrupoResponse])
def listar_mis_grupos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista los grupos del usuario actual"""
    grupos = db.query(Grupo).join(
        MiembroGrupo, MiembroGrupo.grupo_id == Grupo.id
    ).filter(
        MiembroGrupo.usuario_id == current_user.id,
        MiembroGrupo.estado_membresia == EstadoMembresia.activo
    ).all()
    
    # Agregar contador de miembros
    result = []
    for grupo in grupos:
        grupo_dict = GrupoResponse.model_validate(grupo)
        grupo_dict.total_miembros = db.query(func.count(MiembroGrupo.usuario_id)).filter(
            MiembroGrupo.grupo_id == grupo.id,
            MiembroGrupo.estado_membresia == EstadoMembresia.activo
        ).scalar() or 0
        result.append(grupo_dict)
    
    return result

@router.get("/{grupo_id}", response_model=GrupoDetailResponse)
def obtener_grupo(grupo_id: int, db: Session = Depends(get_db)):
    """Obtiene un grupo por ID con todos sus detalles y miembros"""
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado"
        )

    miembros = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.estado_membresia == EstadoMembresia.activo
    ).all()

    miembros_detail = []
    for miembro in miembros:
        usuario = miembro.usuario
        miembros_detail.append(
            MiembroGrupoDetailResponse(
                usuario_id=usuario.id,
                nombre=usuario.nombre,
                apellido_paterno=usuario.apellido_paterno,
                apellido_materno=usuario.apellido_materno,
                foto_perfil_url=usuario.foto_perfil_url,
                rol_miembro=miembro.rol_miembro,
                estado_membresia=miembro.estado_membresia
            )
        )

    return GrupoDetailResponse(
        id=grupo.id,
        nombre=grupo.nombre,
        descripcion=grupo.descripcion,
        carrera_id=grupo.carrera_id,
        privacidad=grupo.privacidad,
        foto_grupo_url=grupo.foto_grupo_url,
        usuario_dueno_id=grupo.usuario_dueno_id,
        creado_en=grupo.creado_en,
        actualizado_en=grupo.actualizado_en,
        dueno=grupo.dueno,
        carrera=grupo.carrera,
        total_miembros=len(miembros_detail),
        miembros=miembros_detail
    )

@router.get("/{grupo_id}/detalle", response_model=GrupoDetailResponse)
def obtener_grupo_detalle(grupo_id: int, db: Session = Depends(get_db)):
    """Alias para obtener detalles completos del grupo"""
    return obtener_grupo(grupo_id, db)

@router.post("/", response_model=GrupoResponse, status_code=status.HTTP_201_CREATED)
def crear_grupo(
    grupo_data: GrupoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo grupo"""
    # Verificar si ya existe un grupo con el mismo nombre y carrera
    grupo_existente = db.query(Grupo).filter(
        Grupo.nombre == grupo_data.nombre,
        Grupo.carrera_id == grupo_data.carrera_id
    ).first()
    
    if grupo_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un grupo con ese nombre en la misma carrera"
        )
    
    nuevo_grupo = Grupo(
        usuario_dueno_id=current_user.id,
        **grupo_data.model_dump()
    )
    
    db.add(nuevo_grupo)
    db.flush()
    
    # Agregar al creador como dueño del grupo
    miembro_dueno = MiembroGrupo(
        grupo_id=nuevo_grupo.id,
        usuario_id=current_user.id,
        rol_miembro=RolMiembroGrupo.dueno,
        estado_membresia=EstadoMembresia.activo
    )
    db.add(miembro_dueno)
    
    # Registrar en auditoría
    auditoria = Auditoria(
        actor_usuario_id=current_user.id,
        accion="crear_grupo",
        entidad="grupos",
        entidad_id=str(nuevo_grupo.id),
        detalle={"privacidad": grupo_data.privacidad.value}
    )
    db.add(auditoria)
    
    db.commit()
    db.refresh(nuevo_grupo)
    
    # Construir respuesta con todas las relaciones cargadas
    grupo_dict = GrupoResponse.model_validate(nuevo_grupo)
    grupo_dict.total_miembros = 1  # Incluye al creador
    
    return grupo_dict

@router.put("/{grupo_id}", response_model=GrupoResponse)
def actualizar_grupo(
    grupo_id: int,
    grupo_data: GrupoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un grupo (solo dueño o admin)"""
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado"
        )
    
    # Verificar permisos
    miembro = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == current_user.id,
        MiembroGrupo.estado_membresia == EstadoMembresia.activo
    ).first()
    
    if not miembro or miembro.rol_miembro not in [RolMiembroGrupo.dueno, RolMiembroGrupo.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este grupo"
        )
    
    update_data = grupo_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(grupo, key, value)
    
    db.commit()
    db.refresh(grupo)
    return grupo

@router.delete("/{grupo_id}", response_model=Message)
def eliminar_grupo(
    grupo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un grupo (solo dueño)"""
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado"
        )
    
    if grupo.usuario_dueno_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el dueño puede eliminar el grupo"
        )
    
    db.delete(grupo)
    db.commit()
    return {"message": "Grupo eliminado correctamente"}

# =====================================================================
# ENDPOINTS DE MIEMBROS
# =====================================================================

@router.get("/{grupo_id}/miembros", response_model=List[MiembroGrupoResponse])
def listar_miembros(
    grupo_id: int,
    estado: Optional[EstadoMembresia] = EstadoMembresia.activo,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista los miembros de un grupo"""
    query = db.query(MiembroGrupo).filter(MiembroGrupo.grupo_id == grupo_id)
    
    if estado:
        query = query.filter(MiembroGrupo.estado_membresia == estado)
    
    miembros = query.offset(skip).limit(limit).all()
    return miembros

@router.post("/{grupo_id}/unirse", response_model=Message, status_code=status.HTTP_201_CREATED)
def unirse_a_grupo(
    grupo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Solicita unirse o se une directamente a un grupo"""
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado"
        )
    
    # Verificar si ya es miembro
    miembro_existente = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == current_user.id
    ).first()
    
    if miembro_existente:
        if miembro_existente.estado_membresia == EstadoMembresia.activo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya eres miembro de este grupo"
            )
        elif miembro_existente.estado_membresia == EstadoMembresia.pendiente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya tienes una solicitud pendiente"
            )
    
    # Determinar el estado según la privacidad del grupo
    estado_inicial = EstadoMembresia.pendiente if grupo.privacidad == PrivacidadGrupo.privado else EstadoMembresia.activo
    
    nuevo_miembro = MiembroGrupo(
        grupo_id=grupo_id,
        usuario_id=current_user.id,
        rol_miembro=RolMiembroGrupo.miembro,
        estado_membresia=estado_inicial
    )
    
    db.add(nuevo_miembro)
    db.commit()
    
    mensaje = "Solicitud enviada, espera aprobación" if estado_inicial == EstadoMembresia.pendiente else "Te has unido al grupo"
    return {"message": mensaje}

@router.post("/{grupo_id}/miembros/{usuario_id}/invitar", response_model=Message, status_code=status.HTTP_201_CREATED)
def invitar_miembro(
    grupo_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Invita a un usuario al grupo directamente (solo admin o dueño)"""
    # Verificar permisos del usuario actual
    miembro_actual = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == current_user.id,
        MiembroGrupo.estado_membresia == EstadoMembresia.activo
    ).first()
    
    if not miembro_actual or miembro_actual.rol_miembro not in [RolMiembroGrupo.dueno, RolMiembroGrupo.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para invitar miembros"
        )
    
    # Verificar que el usuario a invitar existe
    usuario_invitado = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario_invitado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar si ya es miembro
    miembro_existente = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == usuario_id
    ).first()
    
    if miembro_existente and miembro_existente.estado_membresia == EstadoMembresia.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya es miembro del grupo"
        )
    
    # Agregar miembro directamente como activo
    if miembro_existente:
        miembro_existente.estado_membresia = EstadoMembresia.activo
        miembro_existente.rol_miembro = RolMiembroGrupo.miembro
    else:
        nuevo_miembro = MiembroGrupo(
            grupo_id=grupo_id,
            usuario_id=usuario_id,
            rol_miembro=RolMiembroGrupo.miembro,
            estado_membresia=EstadoMembresia.activo
        )
        db.add(nuevo_miembro)
    
    db.commit()
    return {"message": f"Usuario {usuario_invitado.nombre} agregado al grupo correctamente"}

@router.post("/{grupo_id}/miembros/invitar-por-correo", response_model=Message, status_code=status.HTTP_201_CREATED)
def invitar_miembro_por_correo(
    grupo_id: int,
    correo: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Invita a un usuario al grupo por correo (solo admin o dueño)"""
    # Verificar permisos del usuario actual
    miembro_actual = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == current_user.id,
        MiembroGrupo.estado_membresia == EstadoMembresia.activo
    ).first()
    
    if not miembro_actual or miembro_actual.rol_miembro not in [RolMiembroGrupo.dueno, RolMiembroGrupo.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para invitar miembros"
        )
    
    # Buscar usuario por correo
    usuario_invitado = db.query(Usuario).filter(Usuario.correo_institucional.ilike(correo)).first()
    if not usuario_invitado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con correo {correo} no encontrado"
        )
    
    # Verificar si ya es miembro
    miembro_existente = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == usuario_invitado.id
    ).first()
    
    if miembro_existente and miembro_existente.estado_membresia == EstadoMembresia.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya es miembro del grupo"
        )
    
    # Agregar miembro directamente como activo
    if miembro_existente:
        miembro_existente.estado_membresia = EstadoMembresia.activo
        miembro_existente.rol_miembro = RolMiembroGrupo.miembro
    else:
        nuevo_miembro = MiembroGrupo(
            grupo_id=grupo_id,
            usuario_id=usuario_invitado.id,
            rol_miembro=RolMiembroGrupo.miembro,
            estado_membresia=EstadoMembresia.activo
        )
        db.add(nuevo_miembro)
    
    db.commit()
    return {"message": f"Usuario {usuario_invitado.nombre} agregado al grupo correctamente"}

@router.post("/{grupo_id}/miembros/{usuario_id}/aprobar", response_model=Message)
def aprobar_miembro(
    grupo_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Aprueba la solicitud de un miembro (solo admin o dueño)"""
    # Verificar permisos del usuario actual
    miembro_actual = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == current_user.id,
        MiembroGrupo.estado_membresia == EstadoMembresia.activo
    ).first()
    
    if not miembro_actual or miembro_actual.rol_miembro not in [RolMiembroGrupo.dueno, RolMiembroGrupo.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para aprobar miembros"
        )
    
    # Aprobar miembro
    miembro_pendiente = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == usuario_id,
        MiembroGrupo.estado_membresia == EstadoMembresia.pendiente
    ).first()
    
    if not miembro_pendiente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay solicitud pendiente para este usuario"
        )
    
    miembro_pendiente.estado_membresia = EstadoMembresia.activo
    db.commit()
    
    return {"message": "Miembro aprobado correctamente"}

@router.delete("/{grupo_id}/salir", response_model=Message)
def salir_del_grupo(
    grupo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Sale de un grupo"""
    grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo no encontrado"
        )
    
    # No permitir al dueño salir
    if grupo.usuario_dueno_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El dueño no puede salir del grupo. Transfiere la propiedad primero o elimina el grupo."
        )
    
    miembro = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == current_user.id,
        MiembroGrupo.estado_membresia == EstadoMembresia.activo
    ).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No eres miembro de este grupo"
        )
    
    from datetime import datetime
    miembro.estado_membresia = EstadoMembresia.salio
    miembro.salio_en = datetime.utcnow()
    db.commit()
    
    return {"message": "Has salido del grupo"}

# =====================================================================
# ENDPOINTS DE PUBLICACIONES EN GRUPOS
# =====================================================================

@router.get("/{grupo_id}/publicaciones", response_model=List[PublicacionGrupoResponse])
def listar_publicaciones_grupo(
    grupo_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las publicaciones de un grupo"""
    # Verificar que el usuario es miembro del grupo
    miembro = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == current_user.id,
        MiembroGrupo.estado_membresia == EstadoMembresia.activo
    ).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes ser miembro del grupo para ver las publicaciones"
        )
    
    publicaciones = db.query(PublicacionGrupo).filter(
        PublicacionGrupo.grupo_id == grupo_id
    ).order_by(PublicacionGrupo.creado_en.desc()).offset(skip).limit(limit).all()
    
    return publicaciones

@router.post("/{grupo_id}/publicaciones", response_model=PublicacionGrupoResponse, status_code=status.HTTP_201_CREATED)
def crear_publicacion_grupo(
    grupo_id: int,
    publicacion_data: PublicacionGrupoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea una publicación en un grupo"""
    # Verificar que el usuario es miembro activo del grupo
    miembro = db.query(MiembroGrupo).filter(
        MiembroGrupo.grupo_id == grupo_id,
        MiembroGrupo.usuario_id == current_user.id,
        MiembroGrupo.estado_membresia == EstadoMembresia.activo
    ).first()
    
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes ser miembro del grupo para publicar"
        )
    
    nueva_publicacion = PublicacionGrupo(
        grupo_id=grupo_id,
        autor_id=current_user.id,
        titulo=publicacion_data.titulo,
        contenido=publicacion_data.contenido
    )
    
    db.add(nueva_publicacion)
    db.commit()
    db.refresh(nueva_publicacion)
    
    return nueva_publicacion

@router.put("/publicaciones/{publicacion_id}", response_model=PublicacionGrupoResponse)
def actualizar_publicacion_grupo(
    publicacion_id: int,
    publicacion_data: PublicacionGrupoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una publicación de grupo"""
    publicacion = db.query(PublicacionGrupo).filter(PublicacionGrupo.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    # Verificar permisos
    if publicacion.autor_id != current_user.id:
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

@router.delete("/publicaciones/{publicacion_id}", response_model=Message)
def eliminar_publicacion_grupo(
    publicacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina una publicación de grupo"""
    publicacion = db.query(PublicacionGrupo).filter(PublicacionGrupo.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )
    
    # Verificar permisos (autor o admin del grupo)
    if publicacion.autor_id != current_user.id:
        miembro = db.query(MiembroGrupo).filter(
            MiembroGrupo.grupo_id == publicacion.grupo_id,
            MiembroGrupo.usuario_id == current_user.id,
            MiembroGrupo.estado_membresia == EstadoMembresia.activo
        ).first()
        
        if not miembro or miembro.rol_miembro not in [RolMiembroGrupo.dueno, RolMiembroGrupo.admin]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para eliminar esta publicación"
            )
    
    db.delete(publicacion)
    db.commit()
    return {"message": "Publicación eliminada correctamente"}
