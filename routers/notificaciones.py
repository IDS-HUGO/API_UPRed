from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from database import get_db
from models import Notificacion, Usuario, RolUsuario
from schemas import (
    NotificacionCreate, NotificacionUpdate, NotificacionResponse, Message
)
from auth import get_current_user, require_roles
from datetime import datetime

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones"])

# =====================================================================
# ENDPOINTS DE NOTIFICACIONES
# =====================================================================

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
