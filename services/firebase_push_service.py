from __future__ import annotations

import os
from typing import Optional

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
        self._initialize()

    def _initialize(self) -> None:
        if firebase_admin is None:
            return

        credential_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
        if not credential_path:
            return
        if not os.path.exists(credential_path):
            return

        if not firebase_admin._apps:
            cred = credentials.Certificate(credential_path)
            firebase_admin.initialize_app(cred)

        self._enabled = True

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
            return False

        message = messaging.Message(
            token=token,
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            android=messaging.AndroidConfig(priority="high"),
        )
        messaging.send(message)
        return True


firebase_push_service = FirebasePushService()
