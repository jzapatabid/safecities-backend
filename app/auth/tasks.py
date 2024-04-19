import datetime
from typing import List

import celery
from flask import render_template
from flask_mail import Message

from app import app
from app.auth.models.user_model import UserModel
from app.auth.utils import encode_jwt_token
from db import db
from mail_config import mail


@celery.shared_task
def task_send_activate_user_email(user_id_ls: List[int]):
    for user_id in user_id_ls:
        user_model: UserModel = db.session.query(UserModel) \
            .filter(UserModel.id == user_id).scalar()

        if user_model:
            jwt_token = encode_jwt_token({"id": user_id}, "super-secret", datetime.timedelta(hours=1))
            mail_msg = Message(
                subject="Convite: Acesse a Plataforma Cidades Seguras",
                sender=app.config["MAIL_DEFAULT_SENDER"],
                recipients=[user_model.email]
            )
            mail_ctx = dict(
                fullname=user_model.name.title() + " " + user_model.last_name.title(),
                url_host=app.config["SERVER_NAME_"],
                phone_number=app.config["BACKOFFICE_PHONE_NUMBER"],
                phone_annex=app.config["BACKOFFICE_PHONE_ANNEX"],
                token=jwt_token,
            )
            mail_msg.html = render_template("email/activation_account_email.html", **mail_ctx)
            mail_msg.body = render_template("email/activation_account_email.html", **mail_ctx)
            # todo: pending not html content for email
            mail.send(mail_msg)


@celery.shared_task
def task_send_email_to_restart_password(user_id: int):
    jwt_token = encode_jwt_token({"id": user_id}, "super-secret", datetime.timedelta(hours=1))

    user_model: UserModel = db.session.query(UserModel).filter(UserModel.id == user_id).scalar()
    mail_msg = Message(
        subject="Recuperação de senha: Plataforma Safe Cities",
        sender="admin@safecities.com",
        recipients=[user_model.email, ]
    )
    mail_ctx = dict(
        fullname=user_model.name.title() + " " + user_model.last_name.title(),
        url_host=app.config["SERVER_NAME_"],
        token=jwt_token,
        phone_number=app.config["BACKOFFICE_PHONE_NUMBER"],
        phone_annex=app.config["BACKOFFICE_PHONE_ANNEX"],
    )
    mail_msg.html = render_template("email/restart_password_email.html", **mail_ctx)
    # todo: pending not html content for email
    mail.send(mail_msg)
