from datetime import datetime

from cryptography.fernet import Fernet
from sqlalchemy import Column, String, Boolean, DateTime

import constants
from db import db


class JWTBlackList(db.Model):
    uuid = Column(String(), primary_key=True)
    _token = Column("token", String(), nullable=False)
    used = Column(Boolean(), nullable=False, default=False)
    used_at = Column(DateTime(), nullable=True)
    created_at = Column(DateTime(), default=datetime.utcnow)

    @property
    def token(self):
        fernet = Fernet(b"o8mtlNVO2PgOib9xXHG4Z29D0z1h_pqrBhxf2v_KZDE=")
        return fernet.decrypt(self._token).decode(constants.DEFAULT_ENCODING)

    @token.setter
    def token(self, value: str):
        value = value.encode()
        fernet = Fernet(b"o8mtlNVO2PgOib9xXHG4Z29D0z1h_pqrBhxf2v_KZDE=")
        self._token = fernet.encrypt(value).decode(constants.DEFAULT_ENCODING)
