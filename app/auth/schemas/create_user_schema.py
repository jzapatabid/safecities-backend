# from apiflask import Schema, fields
import re

from marshmallow import validates, ValidationError, Schema, fields

from app.auth.repositories import check_user_exist


class SignUpSchema(Schema):
    email = fields.Email(required=True, hint="email@mail.com")
    name = fields.String(required=True, hint="John")
    last_name = fields.String(required=True, data_key="lastName", hint="Doe")

    @validates('email')
    def validate_email(self, value):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValidationError(f"The username or email has an invalid format")
        if check_user_exist(value):
            raise ValidationError(f'Email already registered')


def get_schema_example(c):
    x = c()
    example = {}
    for field_name, field_obj in x.fields.items():
        if data_key := field_obj.data_key:
            example[data_key] = field_obj.metadata.get("hint")
        else:
            example[field_name] = field_obj.metadata.get("hint")

    return example
