from marshmallow import fields, validate, Schema


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8),
            validate.Regexp(r'.*[A-Z].*', error="Should contains at least one uppercase letter."),
            validate.Regexp(r'.*[0-9].*', error="Should contains at least one number."),
        ]
    )
