from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from models import TipoUsuario, TipoPublicacion

# ===== SCHEMAS DE USUARIO =====

class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    tipo_usuario: TipoUsuario
    carrera_id: Optional[int] = None
    matricula: Optional[str] = Field(None, max_length=50)
    numero_empleado: Optional[str] = Field(None, max_length=50)

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, max_length=100)

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(None, min_length=1, max_length=100)
    carrera_id: Optional[int] = None
    matricula: Optional[str] = Field(None, max_length=50)
    numero_empleado: Optional[str] = Field(None, max_length=50)

class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool
    verificado: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

# ===== SCHEMAS DE TOKEN =====

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    tipo_usuario: Optional[TipoUsuario] = None

# ===== SCHEMAS DE CARRERA =====

class CarreraBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None

class CarreraCreate(CarreraBase):
    pass

class CarreraResponse(CarreraBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ===== SCHEMAS DE PUBLICACION =====

class PublicacionBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    contenido: str = Field(..., min_length=1)
    imagen_url: Optional[str] = Field(None, max_length=500)
    carrera_id: Optional[int] = None
    tipo_publicacion: TipoPublicacion = TipoPublicacion.GENERAL

class PublicacionCreate(PublicacionBase):
    pass

class PublicacionUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    contenido: Optional[str] = Field(None, min_length=1)
    imagen_url: Optional[str] = Field(None, max_length=500)
    carrera_id: Optional[int] = None
    tipo_publicacion: Optional[TipoPublicacion] = None
    activo: Optional[bool] = None

class PublicacionResponse(PublicacionBase):
    id: int
    usuario_id: int
    activo: bool
    created_at: datetime
    updated_at: datetime
    
    # Datos relacionados
    usuario: Optional[UsuarioResponse] = None
    carrera: Optional[CarreraResponse] = None
    total_likes: int = 0
    total_comentarios: int = 0
    
    model_config = ConfigDict(from_attributes=True)

# ===== SCHEMAS DE COMENTARIO =====

class ComentarioBase(BaseModel):
    contenido: str = Field(..., min_length=1)

class ComentarioCreate(ComentarioBase):
    publicacion_id: int

class ComentarioUpdate(BaseModel):
    contenido: Optional[str] = Field(None, min_length=1)
    activo: Optional[bool] = None

class ComentarioResponse(ComentarioBase):
    id: int
    publicacion_id: int
    usuario_id: int
    activo: bool
    created_at: datetime
    
    usuario: Optional[UsuarioResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

# ===== SCHEMAS DE LIKE =====

class LikeCreate(BaseModel):
    publicacion_id: int

class LikeResponse(BaseModel):
    id: int
    publicacion_id: int
    usuario_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ===== SCHEMAS DE DOMINIO DE CORREO =====

class DominioCorreoBase(BaseModel):
    dominio: str = Field(..., min_length=1, max_length=100)
    tipo_usuario: TipoUsuario
    activo: bool = True

class DominioCorreoCreate(DominioCorreoBase):
    pass

class DominioCorreoResponse(DominioCorreoBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ===== SCHEMAS GENERALES =====

class Message(BaseModel):
    message: str

class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    data: List[dict]
