import datetime
from typing import Dict

from marshmallow import fields, validate, Schema, validates, ValidationError, validates_schema
from sqlalchemy import select

from app.auth.errors import RepeatedPasswordError
from app.auth.models.user_model import UserModel
from app.auth.services import check_password
from app.auth.utils import decode_jwt_token
from app.commons.constants import field_hints
from db import db

UPDATE_PASSWORD_WITH_TOKEN_EXAMPLE = dict(
    token=field_hints.TOKEN,
    password=field_hints.PASSWORD
)


class ResetPasswordRequestSchema(Schema):
    token = fields.String(required=True)
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8),
            validate.Regexp(r".*[A-Z].*", error="Should contains at least one uppercase letter."),
            validate.Regexp(r".*[0-9].*", error="Should contains at least one number."),
        ]
    )

    @validates("token")
    def validate_token(self, value: str):
        token_decoded = decode_jwt_token(value, "super-secret")
        if token_expiration := token_decoded.get("exp"):
            token_expiration = datetime.datetime.utcfromtimestamp(token_expiration)
            if token_expiration < datetime.datetime.utcnow():
                raise ValidationError("Token already used or expired")
