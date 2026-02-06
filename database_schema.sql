-- Base de datos para Red Social Escolar
CREATE DATABASE IF NOT EXISTS red_social_escolar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE red_social_escolar;

-- Tabla de Carreras
CREATE TABLE carreras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de Dominios de Correo Electronico permitidos
CREATE TABLE dominios_correo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dominio VARCHAR(100) NOT NULL UNIQUE,
    tipo_usuario ENUM('ALUMNO', 'DOCENTE') NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Usuarios
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    tipo_usuario ENUM('ALUMNO', 'DOCENTE', 'ADMINISTRADOR') NOT NULL,
    carrera_id INT,
    matricula VARCHAR(50),
    numero_empleado VARCHAR(50),
    activo BOOLEAN DEFAULT TRUE,
    verificado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE SET NULL,
    INDEX idx_email (email),
    INDEX idx_tipo_usuario (tipo_usuario)
);

-- Tabla de Publicaciones
CREATE TABLE publicaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    contenido TEXT NOT NULL,
    imagen_url VARCHAR(500),
    carrera_id INT,
    tipo_publicacion ENUM('GENERAL', 'EVENTO', 'NOTICIA', 'PREGUNTA') DEFAULT 'GENERAL',
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE SET NULL,
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_carrera_id (carrera_id),
    INDEX idx_created_at (created_at)
);

-- Tabla de Comentarios
CREATE TABLE comentarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    publicacion_id INT NOT NULL,
    usuario_id INT NOT NULL,
    contenido TEXT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (publicacion_id) REFERENCES publicaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_publicacion_id (publicacion_id)
);

-- Tabla de Likes
CREATE TABLE likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    publicacion_id INT NOT NULL,
    usuario_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (publicacion_id) REFERENCES publicaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_like (publicacion_id, usuario_id),
    INDEX idx_publicacion_id (publicacion_id)
);

-- Datos iniciales de ejemplo

-- Insertar carreras de ejemplo
INSERT INTO carreras (nombre, descripcion) VALUES
('Ingeniería en Sistemas Computacionales', 'Carrera enfocada en desarrollo de software y sistemas'),
('Ingeniería Industrial', 'Carrera enfocada en optimización de procesos'),
('Ingeniería Electrónica', 'Carrera enfocada en sistemas electrónicos'),
('Licenciatura en Administración', 'Carrera enfocada en gestión empresarial'),
('Ingeniería Mecánica', 'Carrera enfocada en sistemas mecánicos');

-- Insertar dominios de correo permitidos
INSERT INTO dominios_correo (dominio, tipo_usuario) VALUES
('@alumno.escuela.edu.mx', 'ALUMNO'),
('@estudiante.escuela.edu.mx', 'ALUMNO'),
('@docente.escuela.edu.mx', 'DOCENTE'),
('@profesor.escuela.edu.mx', 'DOCENTE');

-- Insertar usuario administrador por defecto
-- Password: admin123 (deberás cambiarla al iniciar sesión)
INSERT INTO usuarios (nombre, apellido, email, password_hash, tipo_usuario, activo, verificado) VALUES
('Administrador', 'Sistema', 'admin@escuela.edu.mx', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqxFxGZe.u', 'ADMINISTRADOR', TRUE, TRUE);
