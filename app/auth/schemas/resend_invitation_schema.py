from marshmallow import Schema, fields, validate


class ResendInvitationSchema(Schema):
    user_id_ls = fields.List(fields.Integer(), required=True, data_key="usersId", validate=[
        validate.Length(min=1, max=100)
    ])
