from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from database import get_db
from models import Sede, Facultad, Carrera, Cuatrimestre, Usuario, RolUsuario
from schemas import (
    SedeCreate, SedeUpdate, SedeResponse,
    FacultadCreate, FacultadUpdate, FacultadResponse,
    CarreraCreate, CarreraUpdate, CarreraResponse,
    CuatrimestreCreate, CuatrimestreUpdate, CuatrimestreResponse,
    Message
)
from auth import get_current_user, require_roles

router = APIRouter(prefix="/api/estructura", tags=["Estructura Académica"])

# =====================================================================
# ENDPOINTS DE SEDES
# =====================================================================

@router.get("/sedes", response_model=List[SedeResponse])
def listar_sedes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista todas las sedes"""
    sedes = db.query(Sede).offset(skip).limit(limit).all()
    return sedes

@router.get("/sedes/buscar", response_model=List[SedeResponse])
def buscar_sedes(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Busca sedes por nombre o código"""
    sedes = db.query(Sede).filter(
        or_(
            Sede.nombre.ilike(f"%{query}%"),
            Sede.codigo.ilike(f"%{query}%")
        )
    ).all()
    return sedes

@router.get("/sedes/{sede_id}", response_model=SedeResponse)
def obtener_sede(sede_id: int, db: Session = Depends(get_db)):
    """Obtiene una sede por ID"""
    sede = db.query(Sede).filter(Sede.id == sede_id).first()
    if not sede:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sede no encontrada"
        )
    return sede

@router.post("/sedes", response_model=SedeResponse, status_code=status.HTTP_201_CREATED)
def crear_sede(
    sede_data: SedeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Crea una nueva sede (solo administradores)"""
    # Verificar que el código no exista
    if db.query(Sede).filter(Sede.codigo == sede_data.codigo).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de sede ya existe"
        )
    
    nueva_sede = Sede(**sede_data.model_dump())
    db.add(nueva_sede)
    db.commit()
    db.refresh(nueva_sede)
    return nueva_sede

@router.put("/sedes/{sede_id}", response_model=SedeResponse)
def actualizar_sede(
    sede_id: int,
    sede_data: SedeUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Actualiza una sede (solo administradores)"""
    sede = db.query(Sede).filter(Sede.id == sede_id).first()
    if not sede:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sede no encontrada"
        )
    
    update_data = sede_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sede, key, value)
    
    db.commit()
    db.refresh(sede)
    return sede

@router.delete("/sedes/{sede_id}", response_model=Message)
def eliminar_sede(
    sede_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Elimina una sede (solo administradores)"""
    sede = db.query(Sede).filter(Sede.id == sede_id).first()
    if not sede:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sede no encontrada"
        )
    
    db.delete(sede)
    db.commit()
    return {"message": "Sede eliminada correctamente"}

# =====================================================================
# ENDPOINTS DE FACULTADES
# =====================================================================

@router.get("/facultades", response_model=List[FacultadResponse])
def listar_facultades(
    sede_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista todas las facultades, opcionalmente filtradas por sede"""
    query = db.query(Facultad)
    if sede_id:
        query = query.filter(Facultad.sede_id == sede_id)
    facultades = query.offset(skip).limit(limit).all()
    return facultades

@router.get("/facultades/buscar", response_model=List[FacultadResponse])
def buscar_facultades(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Busca facultades por nombre o código"""
    facultades = db.query(Facultad).filter(
        or_(
            Facultad.nombre.ilike(f"%{query}%"),
            Facultad.codigo.ilike(f"%{query}%")
        )
    ).all()
    return facultades

@router.get("/facultades/{facultad_id}", response_model=FacultadResponse)
def obtener_facultad(facultad_id: int, db: Session = Depends(get_db)):
    """Obtiene una facultad por ID"""
    facultad = db.query(Facultad).filter(Facultad.id == facultad_id).first()
    if not facultad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facultad no encontrada"
        )
    return facultad

@router.post("/facultades", response_model=FacultadResponse, status_code=status.HTTP_201_CREATED)
def crear_facultad(
    facultad_data: FacultadCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Crea una nueva facultad (solo administradores)"""
    if db.query(Facultad).filter(Facultad.codigo == facultad_data.codigo).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de facultad ya existe"
        )
    
    nueva_facultad = Facultad(**facultad_data.model_dump())
    db.add(nueva_facultad)
    db.commit()
    db.refresh(nueva_facultad)
    return nueva_facultad

@router.put("/facultades/{facultad_id}", response_model=FacultadResponse)
def actualizar_facultad(
    facultad_id: int,
    facultad_data: FacultadUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Actualiza una facultad (solo administradores)"""
    facultad = db.query(Facultad).filter(Facultad.id == facultad_id).first()
    if not facultad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facultad no encontrada"
        )
    
    update_data = facultad_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(facultad, key, value)
    
    db.commit()
    db.refresh(facultad)
    return facultad

@router.delete("/facultades/{facultad_id}", response_model=Message)
def eliminar_facultad(
    facultad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Elimina una facultad (solo administradores)"""
    facultad = db.query(Facultad).filter(Facultad.id == facultad_id).first()
    if not facultad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facultad no encontrada"
        )
    
    db.delete(facultad)
    db.commit()
    return {"message": "Facultad eliminada correctamente"}

# =====================================================================
# ENDPOINTS DE CARRERAS
# =====================================================================

@router.get("/carreras", response_model=List[CarreraResponse])
def listar_carreras(
    facultad_id: Optional[int] = None,
    activa: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lista todas las carreras con filtros opcionales"""
    query = db.query(Carrera)
    if facultad_id:
        query = query.filter(Carrera.facultad_id == facultad_id)
    if activa is not None:
        query = query.filter(Carrera.activa == activa)
    carreras = query.offset(skip).limit(limit).all()
    return carreras

@router.get("/carreras/buscar", response_model=List[CarreraResponse])
def buscar_carreras(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Busca carreras por nombre o código"""
    carreras = db.query(Carrera).filter(
        or_(
            Carrera.nombre.ilike(f"%{query}%"),
            Carrera.codigo.ilike(f"%{query}%")
        )
    ).all()
    return carreras

@router.get("/carreras/{carrera_id}", response_model=CarreraResponse)
def obtener_carrera(carrera_id: int, db: Session = Depends(get_db)):
    """Obtiene una carrera por ID"""
    carrera = db.query(Carrera).filter(Carrera.id == carrera_id).first()
    if not carrera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrera no encontrada"
        )
    return carrera

@router.post("/carreras", response_model=CarreraResponse, status_code=status.HTTP_201_CREATED)
def crear_carrera(
    carrera_data: CarreraCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Crea una nueva carrera (solo administradores)"""
    if db.query(Carrera).filter(Carrera.codigo == carrera_data.codigo).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de carrera ya existe"
        )
    
    nueva_carrera = Carrera(**carrera_data.model_dump())
    db.add(nueva_carrera)
    db.commit()
    db.refresh(nueva_carrera)
    return nueva_carrera

@router.put("/carreras/{carrera_id}", response_model=CarreraResponse)
def actualizar_carrera(
    carrera_id: int,
    carrera_data: CarreraUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Actualiza una carrera (solo administradores)"""
    carrera = db.query(Carrera).filter(Carrera.id == carrera_id).first()
    if not carrera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrera no encontrada"
        )
    
    update_data = carrera_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(carrera, key, value)
    
    db.commit()
    db.refresh(carrera)
    return carrera

@router.delete("/carreras/{carrera_id}", response_model=Message)
def eliminar_carrera(
    carrera_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
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
    return {"message": "Carrera eliminada correctamente"}

# =====================================================================
# ENDPOINTS DE CUATRIMESTRES
# =====================================================================

@router.get("/cuatrimestres", response_model=List[CuatrimestreResponse])
def listar_cuatrimestres(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Lista todos los cuatrimestres"""
    query = db.query(Cuatrimestre)
    if activo is not None:
        query = query.filter(Cuatrimestre.activo == activo)
    cuatrimestres = query.order_by(Cuatrimestre.numero).all()
    return cuatrimestres

@router.get("/cuatrimestres/{cuatrimestre_id}", response_model=CuatrimestreResponse)
def obtener_cuatrimestre(cuatrimestre_id: int, db: Session = Depends(get_db)):
    """Obtiene un cuatrimestre por ID"""
    cuatrimestre = db.query(Cuatrimestre).filter(Cuatrimestre.id == cuatrimestre_id).first()
    if not cuatrimestre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuatrimestre no encontrado"
        )
    return cuatrimestre

@router.post("/cuatrimestres", response_model=CuatrimestreResponse, status_code=status.HTTP_201_CREATED)
def crear_cuatrimestre(
    cuatrimestre_data: CuatrimestreCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Crea un nuevo cuatrimestre (solo administradores)"""
    if db.query(Cuatrimestre).filter(Cuatrimestre.numero == cuatrimestre_data.numero).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de cuatrimestre ya existe"
        )
    
    nuevo_cuatrimestre = Cuatrimestre(**cuatrimestre_data.model_dump())
    db.add(nuevo_cuatrimestre)
    db.commit()
    db.refresh(nuevo_cuatrimestre)
    return nuevo_cuatrimestre

@router.put("/cuatrimestres/{cuatrimestre_id}", response_model=CuatrimestreResponse)
def actualizar_cuatrimestre(
    cuatrimestre_id: int,
    cuatrimestre_data: CuatrimestreUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Actualiza un cuatrimestre (solo administradores)"""
    cuatrimestre = db.query(Cuatrimestre).filter(Cuatrimestre.id == cuatrimestre_id).first()
    if not cuatrimestre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuatrimestre no encontrado"
        )
    
    update_data = cuatrimestre_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cuatrimestre, key, value)
    
    db.commit()
    db.refresh(cuatrimestre)
    return cuatrimestre

@router.delete("/cuatrimestres/{cuatrimestre_id}", response_model=Message)
def eliminar_cuatrimestre(
    cuatrimestre_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles([RolUsuario.administrador]))
):
    """Elimina un cuatrimestre (solo administradores)"""
    cuatrimestre = db.query(Cuatrimestre).filter(Cuatrimestre.id == cuatrimestre_id).first()
    if not cuatrimestre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuatrimestre no encontrado"
        )
    
    db.delete(cuatrimestre)
    db.commit()
    return {"message": "Cuatrimestre eliminado correctamente"}
