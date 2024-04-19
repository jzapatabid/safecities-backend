import datetime
import math
from functools import wraps
from typing import Dict, List, Optional

import bcrypt
import jwt
from flask import request, jsonify
from sqlalchemy import select, Row, update, exists, desc, asc, func

from app.auth.errors import IncorrectPasswordError, RepeatedPasswordError, TokenUsedOrExpiredError
from app.auth.models.recovery_password_model import JWTBlackList
from app.auth.models.user_model import UserModel
from app.auth.utils import decode_jwt_token
from app.commons.dto.pagination import PaginationResponse
from db import db


def hash_password(password: str) -> str:
    bytes_hashed_pwd = bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt())
    return bytes_hashed_pwd.decode()


def check_password(password: str, hashed_password) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def signin_user(signin_schema: Dict):
    db.session.add(user_model := UserModel(**signin_schema))
    db.session.commit()

    from app.auth.tasks import task_send_activate_user_email
    task_send_activate_user_email.delay([user_model.id])


def activate_user(schema: Dict):
    token_decoded = decode_jwt_token(schema["token"], "super-secret")

    # validate token is not expired
    if token_expiration := token_decoded["exp"]:
        token_expiration = datetime.datetime.utcfromtimestamp(token_expiration)
        if token_expiration < datetime.datetime.utcnow():
            raise TokenUsedOrExpiredError

    # validate token is not in blacklist
    exists_jwt_in_blacklist_stmt = exists().where(JWTBlackList.uuid == token_decoded["uuid"])
    jwt_is_in_blacklist = db.session.query(exists_jwt_in_blacklist_stmt).scalar()
    if jwt_is_in_blacklist:
        raise TokenUsedOrExpiredError

    activate_user_stmt = (
        update(UserModel)
        .where(UserModel.id == token_decoded["id"])
        .values(is_active=1, password=hash_password(schema["password"]))
    )

    db.session.add(
        JWTBlackList(
            uuid=token_decoded["uuid"],
            token=schema["token"],
            used_at=datetime.datetime.utcnow()
        )
    )
    db.session.execute(activate_user_stmt)
    db.session.commit()


def resend_invitation(schema: Dict):
    user_id_ls = schema["user_id_ls"]
    from app.auth.tasks import task_send_activate_user_email
    task_send_activate_user_email.delay(user_id_ls)


def login_user(schema: Dict):
    user_model: UserModel = db.session.query(UserModel).filter(UserModel.email == schema["email"]).scalar()
    if user_model and check_password(schema["password"], user_model.password):
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        access_token = jwt.encode({"exp": expiration_time, "id": 1}, "super-secret", algorithm="HS256")
        return {
            "token": access_token,
            "isAdmin": user_model.is_admin,
            "fullName": user_model.name.split(" ")[0].capitalize() + " " + user_model.last_name.split(" ")[
                0].capitalize()
        }


def list_users(schema: Dict):
    select_stmt = select(
        UserModel.id,
        UserModel.email,
        UserModel.name,
        UserModel.last_name,
        UserModel.is_active
    )

    if schema.get("search"):
        select_stmt = select_stmt.where(
            (UserModel.email.like(f"%{schema['search']}%")) |
            (UserModel.name.like(f"%{schema['search']}%")) |
            (UserModel.last_name.like(f"%{schema['search']}%"))
        )

    total_items = db.session.execute(select(func.count("*")).select_from(select_stmt)).scalar()
    total_pages = math.ceil(total_items / schema["page_size"])

    sort_method = asc if schema["sort_type"] == "asc" else desc
    select_stmt = select_stmt.order_by(sort_method(schema["order_field"]))
    select_stmt = select_stmt.limit(schema["page_size"])
    select_stmt = select_stmt.offset((schema["page"] - 1) * schema["page_size"])

    user_model_row_ls: List[Row] = db.session.execute(select_stmt).all()
    cols = ["id", "email", "name", "lastName", "isActive"]
    results = [dict(zip(cols, item.tuple())) for item in user_model_row_ls]

    return PaginationResponse(
        total_items=total_items,
        total_pages=total_pages,
        results=results
    )


def list_all_users():
    select_user_stmt = select(
        UserModel.id,
        UserModel.email,
        UserModel.name,
        UserModel.last_name,
        UserModel.is_active
    )

    user_model_row_ls: List[Row] = db.session.execute(select_user_stmt).all()
    cols = ["id", "email", "name", "lastName", "isActive"]
    return [dict(zip(cols, item.tuple())) for item in user_model_row_ls]


def send_email_to_restart_password(email: str):
    from app.auth.tasks import task_send_email_to_restart_password
    user_model: Optional[UserModel] = db.session.execute(
        select(UserModel)
        .where(UserModel.email == email)
    ).scalar()
    if user_model and user_model.is_active:
        task_send_email_to_restart_password.delay(user_model.id)


def update_user_password_with_token(token: str, new_password: str):
    token_decoded: Dict = decode_jwt_token(token, "super-secret")
    current_password_hashed = db.session.execute(
        select(UserModel.password)
        .where(UserModel.id == token_decoded["id"])
    ).scalar()
    new_password_hashed = hash_password(new_password)

    # validate token is not expired
    if token_expiration := token_decoded["exp"]:
        token_expiration = datetime.datetime.utcfromtimestamp(token_expiration)
        if token_expiration < datetime.datetime.utcnow():
            raise TokenUsedOrExpiredError

    # validate new password is not the same that current password
    if check_password(new_password, current_password_hashed):
        raise RepeatedPasswordError

    db.session.execute(
        update(UserModel)
        .where(UserModel.id == token_decoded["id"])
        .values(password=new_password_hashed)
    )
    db.session.commit()


def update_user_password_with_previous_password(user_id: int, current_password: str, new_password: str):
    current_password_hashed = db.session.execute(
        select(UserModel.password)
        .where(UserModel.id == user_id)
        .limit(1)
    ).scalar()

    # validate current password is correct
    if not check_password(current_password, current_password_hashed):
        raise IncorrectPasswordError

    # validate new password is not the same that current password
    if check_password(new_password, current_password_hashed):
        raise RepeatedPasswordError

    new_password_hashed = hash_password(new_password)
    db.session.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(password=new_password_hashed)
    )
    db.session.commit()


def admin_only():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract the bearer token from the request header
            bearer_token = request.headers.get('Authorization')
            if bearer_token is None:
                return jsonify({'message': 'Missing bearer token', "code": 401}), 401

            bearer_token = bearer_token.split(" ")[1]
            jwt_token = decode_jwt_token(bearer_token, "super-secret")

            is_admin_user_stmt = (exists().where(
                UserModel.id == jwt_token["sub"],
                UserModel.is_active == True,
                UserModel.is_admin == True
            ))
            is_admin_user = db.session.query(is_admin_user_stmt).scalar()
            if not is_admin_user:
                return jsonify({'message': 'User should be an admin user', "code": 403}), 403

            # User has the required role, proceed with the decorated function
            return f(*args, **kwargs)

        return decorated_function

    return decorator
