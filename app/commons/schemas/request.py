from typing import List, Type

from marshmallow import fields, validate, Schema


class PaginationReqSchema(Schema):
    page = fields.Integer(
        load_default=1,
        validate=[validate.Range(min=1), ]
    )
    page_size = fields.Integer(load_default=10, data_key="page_size")


class SearchReqSchema(Schema):
    search = fields.String(allow_none=True)


def get_orderable_schema(orderable_fields: List):
    class PaginationOrderSchema(Schema):
        sort_type = fields.String(
            data_key="sort_type", load_default="asc",
            validate=[validate.OneOf(["asc", "desc"])]
        )
        order_field = fields.String(data_key="order_field", required=True, allow_none=False)

    PaginationOrderSchema._declared_fields["order_field"].validators.append(validate.OneOf(orderable_fields))
    return PaginationOrderSchema


def generate_field_delimiter_schema(fields: List):
    class FieldDelimiterSchema(Schema):
        fields = fields.List(fields.String(), data_key="fields[]", required=False)

    FieldDelimiterSchema._declared_fields["fields"].inner.validators.append(validate.OneOf(fields))
    return FieldDelimiterSchema


def factory_response_schema(target_schema: Type[Schema]):
    class TempSchema(Schema):
        data = fields.Nested(target_schema)

    return TempSchema
