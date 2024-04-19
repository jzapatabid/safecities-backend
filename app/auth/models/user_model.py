from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean

from db import db


class UserModel(db.Model):
    __tablename__ = "users"

    id = Column(Integer(), primary_key=True)
    email = Column(String(), nullable=False, unique=True)
    password = Column(String(), nullable=True)
    name = Column(String(), nullable=False)
    last_name = Column(String(), nullable=False)
    is_active = Column(Boolean(), default=False)
    is_admin = Column(Boolean(), default=False)

    created_at = Column(DateTime(), default=datetime.utcnow)
