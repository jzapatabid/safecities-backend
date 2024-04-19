from app.commons.schemas.request import PaginationReqSchema, get_orderable_schema, SearchReqSchema


class UserListRequestSchema(
    PaginationReqSchema,
    SearchReqSchema,
    get_orderable_schema(["id", "name", "last_name", "email", "is_active"])
):
    pass
