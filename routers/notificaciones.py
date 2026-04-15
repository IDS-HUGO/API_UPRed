from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from models import Notificacion, Usuario, RolUsuario, DispositivoUsuario, Auditoria
from schemas import (
    NotificacionCreate,
    NotificacionUpdate,
    NotificacionResponse,
    Message,
    DeviceRegistrationRequest,
    DeviceTokenUpdateRequest,
    NotificationConfigRequest,
    SyncEventsBatchRequest,
    NotificationSummaryResponse,
)
from auth import get_current_user, require_roles
from datetime import datetime
from services.firebase_push_service import firebase_push_service

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones"])

# =====================================================================
# ENDPOINTS DE NOTIFICACIONES
# =====================================================================

@router.get("", response_model=List[NotificacionResponse], include_in_schema=False)
@router.get("/", response_model=List[NotificacionResponse])
def listar_mis_notificaciones(
    leida: Optional[bool] = None,
    tipo: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las notificaciones del usuario actual"""
    query = db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id
    )
    
    if leida is not None:
        query = query.filter(Notificacion.leida == leida)
    
    if tipo:
        query = query.filter(Notificacion.tipo == tipo)
    
    notificaciones = query.order_by(
        Notificacion.creada_en.desc()
    ).offset(skip).limit(limit).all()
    
    return notificaciones

@router.get("/no-leidas", response_model=List[NotificacionResponse])
def listar_notificaciones_no_leidas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista solo las notificaciones no leídas"""
    notificaciones = db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id,
        Notificacion.leida == False
    ).order_by(
        Notificacion.creada_en.desc()
    ).offset(skip).limit(limit).all()
    
    return notificaciones

@router.get("/count")
def contar_notificaciones_no_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Cuenta las notificaciones no leídas del usuario"""
    count = db.query(func.count(Notificacion.id)).filter(
        Notificacion.usuario_id == current_user.id,
        Notificacion.leida == False
    ).scalar() or 0
    
    return {"total_no_leidas": count}


@router.get("/resumen", response_model=NotificationSummaryResponse)
def resumen_notificaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Resumen ligero para sincronizacion periodica móvil"""
    count = db.query(func.count(Notificacion.id)).filter(
        Notificacion.usuario_id == current_user.id,
        Notificacion.leida == False
    ).scalar() or 0

    last_notification_at = db.query(func.max(Notificacion.creada_en)).filter(
        Notificacion.usuario_id == current_user.id
    ).scalar()

    return {
        "total_no_leidas": count,
        "last_notification_at": last_notification_at
    }


@router.post("/dispositivos", response_model=Message)
def registrar_dispositivo(
    payload: DeviceRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Registra o reactiva un dispositivo del usuario autenticado"""
    dispositivo = db.query(DispositivoUsuario).filter(
        DispositivoUsuario.usuario_id == current_user.id,
        DispositivoUsuario.uuid_dispositivo == payload.uuid_dispositivo
    ).first()

    if dispositivo is None:
        dispositivo = DispositivoUsuario(
            usuario_id=current_user.id,
            uuid_dispositivo=payload.uuid_dispositivo,
            plataforma=payload.plataforma,
            token_push=payload.token_push,
            activo=True,
            ultima_actividad_en=datetime.utcnow()
        )
        db.add(dispositivo)
    else:
        dispositivo.plataforma = payload.plataforma
        if payload.token_push:
            dispositivo.token_push = payload.token_push
        dispositivo.activo = True
        dispositivo.ultima_actividad_en = datetime.utcnow()

    db.commit()
    return {"message": "Dispositivo registrado correctamente"}


@router.put("/dispositivos/token", response_model=Message)
def actualizar_token_dispositivo(
    payload: DeviceTokenUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza token push para un dispositivo existente"""
    dispositivo = db.query(DispositivoUsuario).filter(
        DispositivoUsuario.usuario_id == current_user.id,
        DispositivoUsuario.uuid_dispositivo == payload.uuid_dispositivo
    ).first()

    if dispositivo is None:
        dispositivo = DispositivoUsuario(
            usuario_id=current_user.id,
            uuid_dispositivo=payload.uuid_dispositivo,
            plataforma="android",
            token_push=payload.token_push,
            activo=True,
            ultima_actividad_en=datetime.utcnow()
        )
        db.add(dispositivo)
    else:
        dispositivo.token_push = payload.token_push
        dispositivo.activo = True
        dispositivo.ultima_actividad_en = datetime.utcnow()

    db.commit()
    return {"message": "Token actualizado"}


@router.get("/configuracion", response_model=NotificationConfigRequest)
def obtener_configuracion_notificaciones(
    current_user: Usuario = Depends(get_current_user)
):
    """Configuracion remota base para sincronizacion periódica"""
    return {
        "push_enabled": True,
        "chat_enabled": True,
        "groups_enabled": True,
        "social_enabled": True,
    }


@router.put("/configuracion", response_model=NotificationConfigRequest)
def actualizar_configuracion_notificaciones(
    payload: NotificationConfigRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Persistencia ligera en auditoria para trazabilidad de cambios de configuración"""
    auditoria = Auditoria(
        actor_usuario_id=current_user.id,
        accion="configuracion_notificaciones_actualizada",
        entidad="notificaciones",
        entidad_id=str(current_user.id),
        detalle=payload.model_dump()
    )
    db.add(auditoria)
    db.commit()
    return payload


@router.post("/eventos/sync", response_model=Message)
def sincronizar_eventos_diferidos(
    payload: SyncEventsBatchRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Recibe eventos no críticos en batch cuando el móvil recupera conectividad"""
    for event in payload.events:
        db.add(
            Auditoria(
                actor_usuario_id=current_user.id,
                accion=f"evento_diferido:{event.event_type}",
                entidad="mobile_sync",
                entidad_id=str(current_user.id),
                detalle={
                    "created_at": event.created_at,
                    "payload": event.payload,
                },
            )
        )

    db.commit()
    return {"message": f"{len(payload.events)} eventos sincronizados"}


@router.get("/push/status")
def estado_push():
    """Retorna si el backend de Firebase Push está habilitado"""
    status = firebase_push_service.get_status()
    return {
        "firebase_push_enabled": status["enabled"],
        "service_account_path_present": status["service_account_path_present"],
        "service_account_path": status.get("service_account_path"),
        "last_error": status.get("last_error"),
    }


@router.post("/push/test", response_model=Message)
def enviar_push_prueba(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Envía un push de prueba al primer dispositivo activo del usuario"""
    dispositivo = db.query(DispositivoUsuario).filter(
        DispositivoUsuario.usuario_id == current_user.id,
        DispositivoUsuario.activo == True,
        DispositivoUsuario.token_push.isnot(None)
    ).order_by(DispositivoUsuario.ultima_actividad_en.desc()).first()

    if not dispositivo or not dispositivo.token_push:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay token push activo para este usuario"
        )

    sent = firebase_push_service.send_to_token(
        token=dispositivo.token_push,
        title="UPRed",
        body="Push de prueba desde API",
        data={"target_type": "chat", "room_id": "0", "room_name": "Test", "room_type": "individual"},
    )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase no está configurado en el backend"
        )

    return {"message": "Push de prueba enviado"}

@router.get("/{notificacion_id}", response_model=NotificacionResponse)
def obtener_notificacion(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una notificación por ID"""
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id
    ).first()
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    # Verificar que la notificación pertenece al usuario actual
    if notificacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta notificación"
        )
    
    return notificacion

@router.post("/", response_model=NotificacionResponse, status_code=status.HTTP_201_CREATED)
def crear_notificacion(
    notificacion_data: NotificacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador, RolUsuario.moderador]))
):
    """Crea una nueva notificación (solo administradores y moderadores)"""
    # Verificar que el usuario destino existe
    usuario_destino = db.query(Usuario).filter(
        Usuario.id == notificacion_data.usuario_id
    ).first()
    
    if not usuario_destino:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario destino no encontrado"
        )
    
    nueva_notificacion = Notificacion(
        usuario_id=notificacion_data.usuario_id,
        tipo=notificacion_data.tipo,
        titulo=notificacion_data.titulo,
        cuerpo=notificacion_data.cuerpo,
        datos=notificacion_data.datos or {}
    )
    
    db.add(nueva_notificacion)
    db.commit()
    db.refresh(nueva_notificacion)
    
    return nueva_notificacion

@router.put("/{notificacion_id}", response_model=NotificacionResponse)
def marcar_como_leida(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Marca una notificación como leída"""
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id
    ).first()
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    # Verificar que la notificación pertenece al usuario actual
    if notificacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta notificación"
        )
    
    if not notificacion.leida:
        notificacion.leida = True
        notificacion.leida_en = datetime.utcnow()
        db.commit()
        db.refresh(notificacion)
    
    return notificacion

@router.put("/marcar-todas-leidas", response_model=Message)
def marcar_todas_como_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Marca todas las notificaciones del usuario como leídas"""
    notificaciones_no_leidas = db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id,
        Notificacion.leida == False
    ).all()
    
    ahora = datetime.utcnow()
    count = 0
    for notif in notificaciones_no_leidas:
        notif.leida = True
        notif.leida_en = ahora
        count += 1
    
    db.commit()
    
    return {"message": f"{count} notificaciones marcadas como leídas"}

@router.delete("/{notificacion_id}", response_model=Message)
def eliminar_notificacion(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina una notificación"""
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id
    ).first()
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    # Verificar que la notificación pertenece al usuario actual o es admin
    if notificacion.usuario_id != current_user.id and current_user.rol != RolUsuario.administrador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta notificación"
        )
    
    db.delete(notificacion)
    db.commit()
    
    return {"message": "Notificación eliminada correctamente"}

@router.delete("/eliminar-todas-leidas", response_model=Message)
def eliminar_todas_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina todas las notificaciones leídas del usuario"""
    notificaciones_leidas = db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id,
        Notificacion.leida == True
    ).all()
    
    count = len(notificaciones_leidas)
    for notif in notificaciones_leidas:
        db.delete(notif)
    
    db.commit()
    
    return {"message": f"{count} notificaciones eliminadas"}

# =====================================================================
# ENDPOINTS PARA CREAR NOTIFICACIONES DEL SISTEMA
# =====================================================================

def crear_notificacion_sistema(
    db: Session,
    usuario_id: int,
    tipo: str,
    titulo: str,
    cuerpo: str = None,
    datos: dict = None
):
    """Función auxiliar para crear notificaciones del sistema"""
    notificacion = Notificacion(
        usuario_id=usuario_id,
        tipo=tipo,
        titulo=titulo,
        cuerpo=cuerpo,
        datos=datos or {}
    )
    db.add(notificacion)
    db.commit()
    return notificacion
