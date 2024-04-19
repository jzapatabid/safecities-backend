from typing import Dict

from marshmallow import fields, validate, Schema, ValidationError, validates_schema

from app.auth.errors import RepeatedPasswordError


class ChangePasswordRequestSchema(Schema):
    last_password = fields.String(required=True, data_key="lastPassword")
    new_password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8),
            validate.Regexp(r'.*[A-Z].*', error="Should contains at least one uppercase letter."),
            validate.Regexp(r'.*[0-9].*', error="Should contains at least one number."),
        ],
        data_key="newPassword"
    )

    @validates_schema
    def validate_password(self, data: Dict, **kwargs):
        last_password = data["last_password"]
        new_password = data["new_password"]

        if new_password == last_password:
            raise RepeatedPasswordError
