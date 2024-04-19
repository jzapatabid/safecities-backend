from sqlalchemy import select

from app.auth.models.user_model import UserModel
from db import db


def check_user_exist(email: str):
    stmt = select(UserModel.id).where(UserModel.email == email)
    user_exist = bool(db.session.execute(stmt).scalar())
    return user_exist
