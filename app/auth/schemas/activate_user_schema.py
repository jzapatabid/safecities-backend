from marshmallow import fields, validate, Schema

from app.commons.constants import field_hints

UPDATE_PASSWORD_WITH_TOKEN_EXAMPLE = dict(
    token=field_hints.TOKEN,
    password=field_hints.PASSWORD
)


class ActivateUserRequestSchema(Schema):
    token = fields.String(required=True)
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8),
            validate.Regexp(r".*[A-Z].*", error="Should contains at least one uppercase letter."),
            validate.Regexp(r".*[0-9].*", error="Should contains at least one number."),
        ]
    )
