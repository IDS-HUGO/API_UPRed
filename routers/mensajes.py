from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from database import get_db
from models import (
    SalaChat, Mensaje, DestinatarioMensaje, Usuario, Grupo, MiembroGrupo,
    TipoSalaChat, TipoMensaje, EstadoMembresia, Auditoria
)
from schemas import (
    MensajeCreate, MensajeResponse, SalaChatResponse, Message
)
from auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/mensajes", tags=["Mensajería"])

# =====================================================================
# ENDPOINTS DE SALAS DE CHAT
# =====================================================================

@router.get("/salas", response_model=List[SalaChatResponse])
def listar_mis_salas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todas las salas de chat del usuario actual"""
    # Salas directas donde el usuario participa
    salas_directas = db.query(SalaChat).filter(
        SalaChat.tipo_sala == TipoSalaChat.directo,
        or_(
            SalaChat.usuario_a_id == current_user.id,
            SalaChat.usuario_b_id == current_user.id
        )
    ).all()
    
    # Salas grupales donde el usuario es miembro activo
    salas_grupales = db.query(SalaChat).join(
        Grupo, SalaChat.grupo_id == Grupo.id
    ).join(
        MiembroGrupo, and_(
            MiembroGrupo.grupo_id == Grupo.id,
            MiembroGrupo.usuario_id == current_user.id,
            MiembroGrupo.estado_membresia == EstadoMembresia.activo
        )
    ).filter(
        SalaChat.tipo_sala == TipoSalaChat.grupal
    ).all()
    
    todas_salas = salas_directas + salas_grupales
    
    # Agregar último mensaje a cada sala
    result = []
    for sala in todas_salas:
        sala_dict = SalaChatResponse.model_validate(sala)
        ultimo_mensaje = db.query(Mensaje).filter(
            Mensaje.sala_chat_id == sala.id,
            Mensaje.eliminado_en.is_(None)
        ).order_by(Mensaje.enviado_en.desc()).first()
        
        if ultimo_mensaje:
            sala_dict.ultimo_mensaje = MensajeResponse.model_validate(ultimo_mensaje)
        
        result.append(sala_dict)
    
    # Ordenar por fecha del último mensaje
    result.sort(key=lambda x: x.ultimo_mensaje.enviado_en if x.ultimo_mensaje else x.creado_en, reverse=True)
    
    return result

@router.get("/salas/{sala_id}", response_model=SalaChatResponse)
def obtener_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una sala de chat por ID"""
    sala = db.query(SalaChat).filter(SalaChat.id == sala_id).first()
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    # Verificar permisos
    tiene_acceso = False
    if sala.tipo_sala == TipoSalaChat.directo:
        tiene_acceso = current_user.id in [sala.usuario_a_id, sala.usuario_b_id]
    elif sala.tipo_sala == TipoSalaChat.grupal:
        miembro = db.query(MiembroGrupo).filter(
            MiembroGrupo.grupo_id == sala.grupo_id,
            MiembroGrupo.usuario_id == current_user.id,
            MiembroGrupo.estado_membresia == EstadoMembresia.activo
        ).first()
        tiene_acceso = miembro is not None
    
    if not tiene_acceso:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta sala"
        )
    
    return sala

@router.post("/salas/directa/{usuario_id}", response_model=SalaChatResponse)
def crear_o_obtener_sala_directa(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea o obtiene una sala de chat directa con otro usuario"""
    if usuario_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes crear un chat contigo mismo"
        )
    
    # Verificar que el usuario existe
    otro_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not otro_usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no found"
        )
    
    # Buscar sala existente (en cualquier orden de usuarios)
    sala_existente = db.query(SalaChat).filter(
        SalaChat.tipo_sala == TipoSalaChat.directo,
        or_(
            and_(
                SalaChat.usuario_a_id == min(current_user.id, usuario_id),
                SalaChat.usuario_b_id == max(current_user.id, usuario_id)
            ),
            and_(
                SalaChat.usuario_a_id == max(current_user.id, usuario_id),
                SalaChat.usuario_b_id == min(current_user.id, usuario_id)
            )
        )
    ).first()
    
    if sala_existente:
        return sala_existente
    
    # Crear nueva sala (siempre con usuario_a < usuario_b para consistencia)
    nueva_sala = SalaChat(
        tipo_sala=TipoSalaChat.directo,
        usuario_a_id=min(current_user.id, usuario_id),
        usuario_b_id=max(current_user.id, usuario_id)
    )
    
    db.add(nueva_sala)
    db.commit()
    db.refresh(nueva_sala)
    
    return nueva_sala

# =====================================================================
# ENDPOINTS DE MENSAJES
# =====================================================================

@router.get("/salas/{sala_id}/mensajes", response_model=List[MensajeResponse])
def listar_mensajes(
    sala_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista los mensajes de una sala de chat"""
    # Verificar acceso a la sala
    sala = db.query(SalaChat).filter(SalaChat.id == sala_id).first()
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    # Verificar permisos
    tiene_acceso = False
    if sala.tipo_sala == TipoSalaChat.directo:
        tiene_acceso = current_user.id in [sala.usuario_a_id, sala.usuario_b_id]
    elif sala.tipo_sala == TipoSalaChat.grupal:
        miembro = db.query(MiembroGrupo).filter(
            MiembroGrupo.grupo_id == sala.grupo_id,
            MiembroGrupo.usuario_id == current_user.id,
            MiembroGrupo.estado_membresia == EstadoMembresia.activo
        ).first()
        tiene_acceso = miembro is not None
    
    if not tiene_acceso:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta sala"
        )
    
    # Obtener mensajes
    mensajes = db.query(Mensaje).filter(
        Mensaje.sala_chat_id == sala_id,
        Mensaje.eliminado_en.is_(None)
    ).order_by(Mensaje.enviado_en.desc()).offset(skip).limit(limit).all()
    
    # Marcar mensajes como entregados
    for mensaje in mensajes:
        if mensaje.remitente_id != current_user.id:
            destinatario = db.query(DestinatarioMensaje).filter(
                DestinatarioMensaje.mensaje_id == mensaje.id,
                DestinatarioMensaje.destinatario_id == current_user.id
            ).first()
            
            if destinatario and not destinatario.entregado_en:
                destinatario.entregado_en = datetime.utcnow()
    
    db.commit()
    
    # Invertir el orden para mostrar los más antiguos primero
    mensajes.reverse()
    
    return mensajes

@router.post("/salas/{sala_id}/mensajes", response_model=MensajeResponse, status_code=status.HTTP_201_CREATED)
def enviar_mensaje_a_sala(
    sala_id: int,
    mensaje_data: MensajeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Envía un mensaje a una sala específica"""
    # Verificar acceso a la sala
    sala = db.query(SalaChat).filter(SalaChat.id == sala_id).first()
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    # Verificar permisos
    tiene_acceso = False
    if sala.tipo_sala == TipoSalaChat.directo:
        tiene_acceso = current_user.id in [sala.usuario_a_id, sala.usuario_b_id]
    elif sala.tipo_sala == TipoSalaChat.grupal:
        miembro = db.query(MiembroGrupo).filter(
            MiembroGrupo.grupo_id == sala.grupo_id,
            MiembroGrupo.usuario_id == current_user.id,
            MiembroGrupo.estado_membresia == EstadoMembresia.activo
        ).first()
        tiene_acceso = miembro is not None
    
    if not tiene_acceso:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta sala"
        )
    
    # Validar que haya contenido
    if not mensaje_data.contenido and not mensaje_data.url_archivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje debe tener contenido o un archivo"
        )
    
    # Crear mensaje
    nuevo_mensaje = Mensaje(
        sala_chat_id=sala_id,
        remitente_id=current_user.id,
        tipo_mensaje=mensaje_data.tipo_mensaje,
        contenido=mensaje_data.contenido,
        url_archivo=mensaje_data.url_archivo,
        metadatos=mensaje_data.metadatos or {}
    )
    
    db.add(nuevo_mensaje)
    db.flush()
    
    # Crear destinatarios
    if sala.tipo_sala == TipoSalaChat.directo:
        # Chat directo: el otro usuario es el destinatario
        destinatario_id = sala.usuario_b_id if current_user.id == sala.usuario_a_id else sala.usuario_a_id
        destinatario = DestinatarioMensaje(
            mensaje_id=nuevo_mensaje.id,
            destinatario_id=destinatario_id
        )
        db.add(destinatario)
    elif sala.tipo_sala == TipoSalaChat.grupal:
        # Chat grupal: todos los miembros activos excepto el remitente
        miembros = db.query(MiembroGrupo).filter(
            MiembroGrupo.grupo_id == sala.grupo_id,
            MiembroGrupo.estado_membresia == EstadoMembresia.activo,
            MiembroGrupo.usuario_id != current_user.id
        ).all()
        
        for miembro in miembros:
            destinatario = DestinatarioMensaje(
                mensaje_id=nuevo_mensaje.id,
                destinatario_id=miembro.usuario_id
            )
            db.add(destinatario)
    
    # Actualizar timestamp de la sala
    sala.actualizado_en = datetime.utcnow()
    
    # Registrar en auditoría
    tipo_accion = "enviar_mensaje_directo" if sala.tipo_sala == TipoSalaChat.directo else "enviar_mensaje_grupal"
    auditoria = Auditoria(
        actor_usuario_id=current_user.id,
        accion=tipo_accion,
        entidad="mensajes",
        entidad_id=str(nuevo_mensaje.id),
        detalle={"sala_chat_id": sala_id}
    )
    db.add(auditoria)
    
    db.commit()
    db.refresh(nuevo_mensaje)
    
    return nuevo_mensaje

@router.post("/directo/{usuario_id}", response_model=MensajeResponse, status_code=status.HTTP_201_CREATED)
def enviar_mensaje_directo(
    usuario_id: int,
    mensaje_data: MensajeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Envía un mensaje directo a un usuario (crea sala si no existe)"""
    if usuario_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes enviarte mensajes a ti mismo"
        )
    
    # Verificar que el usuario existe
    destinatario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not destinatario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Obtener o crear sala
    sala = db.query(SalaChat).filter(
        SalaChat.tipo_sala == TipoSalaChat.directo,
        or_(
            and_(
                SalaChat.usuario_a_id == min(current_user.id, usuario_id),
                SalaChat.usuario_b_id == max(current_user.id, usuario_id)
            )
        )
    ).first()
    
    if not sala:
        sala = SalaChat(
            tipo_sala=TipoSalaChat.directo,
            usuario_a_id=min(current_user.id, usuario_id),
            usuario_b_id=max(current_user.id, usuario_id)
        )
        db.add(sala)
        db.flush()
    
    # Validar contenido
    if not mensaje_data.contenido and not mensaje_data.url_archivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje debe tener contenido o un archivo"
        )
    
    # Crear mensaje
    nuevo_mensaje = Mensaje(
        sala_chat_id=sala.id,
        remitente_id=current_user.id,
        tipo_mensaje=mensaje_data.tipo_mensaje,
        contenido=mensaje_data.contenido,
        url_archivo=mensaje_data.url_archivo,
        metadatos=mensaje_data.metadatos or {}
    )
    
    db.add(nuevo_mensaje)
    db.flush()
    
    # Crear destinatario
    dest = DestinatarioMensaje(
        mensaje_id=nuevo_mensaje.id,
        destinatario_id=usuario_id
    )
    db.add(dest)
    
    # Actualizar sala
    sala.actualizado_en = datetime.utcnow()
    
    db.commit()
    db.refresh(nuevo_mensaje)
    
    return nuevo_mensaje

@router.put("/mensajes/{mensaje_id}/leer", response_model=Message)
def marcar_mensaje_como_leido(
    mensaje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Marca un mensaje como leído"""
    destinatario = db.query(DestinatarioMensaje).filter(
        DestinatarioMensaje.mensaje_id == mensaje_id,
        DestinatarioMensaje.destinatario_id == current_user.id
    ).first()
    
    if not destinatario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado o no eres el destinatario"
        )
    
    if not destinatario.leido_en:
        destinatario.leido_en = datetime.utcnow()
        if not destinatario.entregado_en:
            destinatario.entregado_en = datetime.utcnow()
        db.commit()
    
    return {"message": "Mensaje marcado como leído"}

@router.post("/salas/{sala_id}/marcar-leidos", response_model=Message)
def marcar_todos_como_leidos(
    sala_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Marca todos los mensajes de una sala como leídos"""
    # Verificar acceso a la sala
    sala = db.query(SalaChat).filter(SalaChat.id == sala_id).first()
    if not sala:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    # Obtener todos los mensajes no leídos donde el usuario es destinatario
    mensajes_no_leidos = db.query(DestinatarioMensaje).join(
        Mensaje, DestinatarioMensaje.mensaje_id == Mensaje.id
    ).filter(
        Mensaje.sala_chat_id == sala_id,
        DestinatarioMensaje.destinatario_id == current_user.id,
        DestinatarioMensaje.leido_en.is_(None)
    ).all()
    
    ahora = datetime.utcnow()
    for dest in mensajes_no_leidos:
        dest.leido_en = ahora
        if not dest.entregado_en:
            dest.entregado_en = ahora
    
    db.commit()
    
    return {"message": f"{len(mensajes_no_leidos)} mensajes marcados como leídos"}

@router.get("/no-leidos/count")
def contar_mensajes_no_leidos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Cuenta los mensajes no leídos del usuario"""
    count = db.query(func.count(DestinatarioMensaje.mensaje_id)).filter(
        DestinatarioMensaje.destinatario_id == current_user.id,
        DestinatarioMensaje.leido_en.is_(None)
    ).scalar() or 0
    
    return {"total_no_leidos": count}

@router.delete("/mensajes/{mensaje_id}", response_model=Message)
def eliminar_mensaje(
    mensaje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un mensaje (solo el remitente)"""
    mensaje = db.query(Mensaje).filter(Mensaje.id == mensaje_id).first()
    if not mensaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje no encontrado"
        )
    
    if mensaje.remitente_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes eliminar tus propios mensajes"
        )
    
    # Soft delete
    mensaje.eliminado_en = datetime.utcnow()
    db.commit()
    
    return {"message": "Mensaje eliminado"}
