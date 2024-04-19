from marshmallow import Schema, fields


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)
