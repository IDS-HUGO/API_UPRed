from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class TipoUsuario(str, enum.Enum):
    ALUMNO = "ALUMNO"
    DOCENTE = "DOCENTE"
    ADMINISTRADOR = "ADMINISTRADOR"

class TipoPublicacion(str, enum.Enum):
    GENERAL = "GENERAL"
    EVENTO = "EVENTO"
    NOTICIA = "NOTICIA"
    PREGUNTA = "PREGUNTA"

class Carrera(Base):
    __tablename__ = "carreras"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuarios = relationship("Usuario", back_populates="carrera")
    publicaciones = relationship("Publicacion", back_populates="carrera")

class DominioCorreo(Base):
    __tablename__ = "dominios_correo"
    
    id = Column(Integer, primary_key=True, index=True)
    dominio = Column(String(100), nullable=False, unique=True)
    tipo_usuario = Column(Enum(TipoUsuario), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    tipo_usuario = Column(Enum(TipoUsuario), nullable=False, index=True)
    carrera_id = Column(Integer, ForeignKey("carreras.id", ondelete="SET NULL"))
    matricula = Column(String(50))
    numero_empleado = Column(String(50))
    activo = Column(Boolean, default=True)
    verificado = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    carrera = relationship("Carrera", back_populates="usuarios")
    publicaciones = relationship("Publicacion", back_populates="usuario", cascade="all, delete-orphan")
    comentarios = relationship("Comentario", back_populates="usuario", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="usuario", cascade="all, delete-orphan")

class Publicacion(Base):
    __tablename__ = "publicaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    titulo = Column(String(200), nullable=False)
    contenido = Column(Text, nullable=False)
    imagen_url = Column(String(500))
    carrera_id = Column(Integer, ForeignKey("carreras.id", ondelete="SET NULL"), index=True)
    tipo_publicacion = Column(Enum(TipoPublicacion), default=TipoPublicacion.GENERAL)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="publicaciones")
    carrera = relationship("Carrera", back_populates="publicaciones")
    comentarios = relationship("Comentario", back_populates="publicacion", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="publicacion", cascade="all, delete-orphan")

class Comentario(Base):
    __tablename__ = "comentarios"
    
    id = Column(Integer, primary_key=True, index=True)
    publicacion_id = Column(Integer, ForeignKey("publicaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    contenido = Column(Text, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    publicacion = relationship("Publicacion", back_populates="comentarios")
    usuario = relationship("Usuario", back_populates="comentarios")

class Like(Base):
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, index=True)
    publicacion_id = Column(Integer, ForeignKey("publicaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    publicacion = relationship("Publicacion", back_populates="likes")
    usuario = relationship("Usuario", back_populates="likes")
