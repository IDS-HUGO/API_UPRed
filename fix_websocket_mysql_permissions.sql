CREATE USER IF NOT EXISTS 'websocket_user'@'100.49.233.10' IDENTIFIED BY 'tu_password_seguro_aqui';

GRANT SELECT, INSERT, UPDATE ON upred_db.* TO 'websocket_user'@'100.49.233.10';

FLUSH PRIVILEGES;

SELECT user, host FROM mysql.user WHERE user IN ('websocket_user', 'root');
