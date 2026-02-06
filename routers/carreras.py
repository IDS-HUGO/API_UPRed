from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Carrera, Usuario, TipoUsuario
from schemas import CarreraCreate, CarreraResponse, Message
from auth import get_current_user, require_roles

router = APIRouter(prefix="/api/carreras", tags=["Carreras"])

@router.get("", response_model=List[CarreraResponse])
def listar_carreras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista todas las carreras disponibles"""
    carreras = db.query(Carrera).offset(skip).limit(limit).all()
    return carreras

@router.get("/{carrera_id}", response_model=CarreraResponse)
def obtener_carrera(
    carrera_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene una carrera por ID"""
    carrera = db.query(Carrera).filter(Carrera.id == carrera_id).first()
    
    if not carrera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrera no encontrada"
        )
    
    return carrera

@router.post("", response_model=CarreraResponse, status_code=status.HTTP_201_CREATED)
def crear_carrera(
    carrera_data: CarreraCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([TipoUsuario.ADMINISTRADOR]))
):
    """Crea una nueva carrera (solo administradores)"""
    
    nueva_carrera = Carrera(
        nombre=carrera_data.nombre,
        descripcion=carrera_data.descripcion
    )
    
    db.add(nueva_carrera)
    db.commit()
    db.refresh(nueva_carrera)
    
    return nueva_carrera

@router.put("/{carrera_id}", response_model=CarreraResponse)
def actualizar_carrera(
    carrera_id: int,
    carrera_data: CarreraCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([TipoUsuario.ADMINISTRADOR]))
):
    """Actualiza una carrera existente (solo administradores)"""
    
    carrera = db.query(Carrera).filter(Carrera.id == carrera_id).first()
    
    if not carrera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrera no encontrada"
        )
    
    carrera.nombre = carrera_data.nombre
    if carrera_data.descripcion:
        carrera.descripcion = carrera_data.descripcion
    
    db.commit()
    db.refresh(carrera)
    
    return carrera

@router.delete("/{carrera_id}", response_model=Message)
def eliminar_carrera(
    carrera_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([TipoUsuario.ADMINISTRADOR]))
):
    """Elimina una carrera (solo administradores)"""
    
    carrera = db.query(Carrera).filter(Carrera.id == carrera_id).first()
    
    if not carrera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrera no encontrada"
        )
    
    db.delete(carrera)
    db.commit()
    
    return {"message": "Carrera eliminada exitosamente"}
