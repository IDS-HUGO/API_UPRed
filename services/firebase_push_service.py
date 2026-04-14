from __future__ import annotations

import os
from typing import Optional
import logging

from config import settings

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception:  # pragma: no cover
    firebase_admin = None
    credentials = None
    messaging = None


class FirebasePushService:
    def __init__(self) -> None:
        self._enabled = False
        self._credential_path = ""
        self._logger = logging.getLogger("upred.firebase_push")
        self._initialize()

    def _initialize(self) -> None:
        if firebase_admin is None:
            self._logger.warning("firebase_admin no disponible. Push deshabilitado.")
            return

        credential_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
        
        # Si no hay path, buscar en la raíz del proyecto
        if not credential_path:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            possible_paths = [
                os.path.join(project_root, "firebase-service-account.json"),
                "/home/ec2-user/firebase-service-account.json",
                os.path.join(os.path.expanduser("~"), "firebase-service-account.json"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    credential_path = path
                    break
        
        self._credential_path = credential_path

        if not credential_path:
            self._logger.warning("FIREBASE_SERVICE_ACCOUNT_PATH vacio y no se encontro archivo en rutas comunes. Push deshabilitado.")
            return
        if not os.path.exists(credential_path):
            self._logger.error("No existe archivo de credenciales Firebase en ruta: %s", credential_path)
            return

        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(credential_path)
                firebase_admin.initialize_app(cred)
            self._enabled = True
            self._logger.info("Firebase Push habilitado correctamente con credenciales: %s", credential_path)
        except Exception as e:
            self._logger.error("Error inicializando Firebase: %s", str(e))
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def get_status(self) -> dict[str, bool]:
        return {
            "enabled": self._enabled,
            "service_account_path_present": bool(self._credential_path),
        }

    def send_to_token(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict[str, str]] = None,
    ) -> bool:
        if not self._enabled or messaging is None:
            self._logger.warning("Intento de envio push con Firebase deshabilitado. token_present=%s enabled=%s", bool(token), self._enabled)
            return False

        if not token or not token.strip():
            self._logger.warning("Token vacio o None en send_to_token")
            return False

        try:
            message = messaging.Message(
                token=token,
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                android=messaging.AndroidConfig(priority="high"),
            )
            response = messaging.send(message)
            self._logger.info("Push enviado correctamente. response=%s token_suffix=%s", response, token[-8:] if token else "none")
            return True
        except Exception as e:
            self._logger.exception("Error enviando push via Firebase. error_type=%s token_suffix=%s", type(e).__name__, token[-8:] if token else "none")
            return False


firebase_push_service = FirebasePushService()
