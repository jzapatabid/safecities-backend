import os
from typing import List

from apiflask import fields, Schema
from marshmallow import ValidationError, validates, validate, post_load, pre_load

from app.causes.dto import UpdateCausePrioritizationRequestDTO


class CreateCustomCauseRequestSchema(Schema):
    name = fields.String(required=True)
    justification = fields.String(required=True)
    evidences = fields.String(required=True, validate=validate.Length(min=1, error='Empty value not allowed'))
    problems = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    annexes = fields.List(fields.File(), required=False, allow_none=True, validate=validate.Length(max=5))
    references = fields.List(fields.URL(), required=False, allow_none=True, validate=validate.Length(max=5))

    @pre_load
    def add_scheme_to_urls(self, data, **kwargs):
        url_fields = ["references", ]
        if data.getlist('references'):
            for url_field in url_fields:
                data.setlist(url_field, [f"https://{url}" if url.startswith("www.") else url for url in data[url_field]])
        return data

    @validates("annexes")
    def files_validator(self, annex_ls):
        allowed_extensions = {'.doc', '.docx', '.ppt', '.pptx', '.pdf', '.epub', '.html', '.xls', '.xlsx', '.csv'}
        max_docs = 5

        if len(annex_ls) > max_docs:
            raise ValidationError(f'you have exceeded the number of added documents. {max_docs}')

        for value in annex_ls:
            file_extension = os.path.splitext(value.filename)[1].lower()

            if file_extension not in allowed_extensions:
                raise ValidationError("Invalid file type.")

    @validates('problems')
    def validate_problems(self, problem_id_ls: List):
        from app.problems.services import check_problems_id_not_in_db
        ids_not_in_db = check_problems_id_not_in_db(problem_id_ls)
        if ids_not_in_db:
            raise ValidationError(f"Problems ID doesn't exist {ids_not_in_db}")

    @validates('name')
    def validate_cause_name(self, cause_name: str):
        from app.causes.services import check_cause_name_already_used
        name_already_used = check_cause_name_already_used(cause_name)
        if name_already_used:
            raise ValidationError(f"Cause name already used")


class UpdateCustomCauseSchema(Schema):
    name = fields.String(required=True)
    justification = fields.String(required=True)
    evidences = fields.String(required=True)
    problems = fields.List(fields.String(), required=False, allow_none=True)
    references = fields.List(fields.URL(), required=False, allow_none=True)
    annexes_to_add = fields.List(fields.File(), required=False, allow_none=True, data_key="annexesToAdd")
    annexes_to_remove = fields.List(fields.Integer(), required=False, allow_none=True, data_key="annexesToRemove")

    @pre_load
    def add_scheme_to_urls(self, data, **kwargs):
        url_fields = ["references", ]
        if data.getlist('references'):
            for url_field in url_fields:
                data.setlist(url_field, [f"https://{url}" if url.startswith("www.") else url for url in data[url_field]])
        return data

    @validates("annexes_to_add")
    def files_validator(self, annex_ls):
        allowed_extensions = {'.doc', '.docx', '.ppt', '.pptx', '.pdf', '.epub', '.html', '.xls', '.xlsx', '.csv'}
        max_docs = 5

        if len(annex_ls) > max_docs:
            raise ValidationError(f'you have exceeded the number of added documents. {max_docs}')

        for value in annex_ls:
            file_extension = os.path.splitext(value.filename)[1].lower()

            if file_extension not in allowed_extensions:
                raise ValidationError("Invalid file type.")

    @validates('problems')
    def validate_problems(self, problem_id_ls: List):
        from app.problems.services import check_problems_id_not_in_db
        ids_not_in_db = check_problems_id_not_in_db(problem_id_ls)
        if ids_not_in_db:
            raise ValidationError(f"Problems ID doesn't exist {ids_not_in_db}")


class UpdateCausePrioritizationRequestSchema(Schema):
    __model__ = UpdateCausePrioritizationRequestDTO

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)

    cause_id = fields.Integer(
        data_key="causeId",
        required=True,
    )
    problem_ids_to_prioritize = fields.List(
        fields.Integer(),
        data_key="problemIdsToPrioritize",
        required=True,

    )
    problem_ids_to_deprioritize = fields.List(
        fields.Integer(),
        data_key="problemIdsToDeprioritize",
        required=True,
    )


class BulkUpdateCausePrioritizationRequestSchema(Schema):
    items = fields.Nested(
        UpdateCausePrioritizationRequestSchema,
        many=True,
        validate=validate.Length(min=1)
    )


class ListCauseAssociationRequestSchema(Schema):
    cause_ids = fields.List(
        fields.Integer(),
        required=True,
        validate=validate.Length(min=1)
    )
