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
        self._logger = logging.getLogger("upred.firebase_push")
        self._initialize()

    def _initialize(self) -> None:
        if firebase_admin is None:
            self._logger.warning("firebase_admin no disponible. Push deshabilitado.")
            return

        credential_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
        if not credential_path:
            self._logger.warning("FIREBASE_SERVICE_ACCOUNT_PATH vacio. Push deshabilitado.")
            return
        if not os.path.exists(credential_path):
            self._logger.error("No existe archivo de credenciales Firebase en ruta: %s", credential_path)
            return

        if not firebase_admin._apps:
            cred = credentials.Certificate(credential_path)
            firebase_admin.initialize_app(cred)

        self._enabled = True
        self._logger.info("Firebase Push habilitado correctamente con credenciales: %s", credential_path)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def send_to_token(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict[str, str]] = None,
    ) -> bool:
        if not self._enabled or messaging is None:
            self._logger.warning("Intento de envio push con Firebase deshabilitado. token_present=%s", bool(token))
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
        except Exception:
            self._logger.exception("Error enviando push via Firebase. token_suffix=%s", token[-8:] if token else "none")
            return False


firebase_push_service = FirebasePushService()
