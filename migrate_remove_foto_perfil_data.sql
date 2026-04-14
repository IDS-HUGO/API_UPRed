-- Migración para eliminar foto_perfil_data de usuarios
-- Ejecutar después de actualizar el código

-- Verificar si la columna existe antes de eliminarla
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'usuarios'
    AND COLUMN_NAME = 'foto_perfil_data'
);

-- Si la columna existe, eliminarla
SET @sql = IF(@column_exists > 0,
    'ALTER TABLE usuarios DROP COLUMN foto_perfil_data',
    'SELECT "Columna foto_perfil_data no existe, migración no necesaria" as mensaje'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;