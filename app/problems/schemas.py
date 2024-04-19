import dataclasses
import os
from typing import List

from apiflask import fields, Schema
from marshmallow import validate, validates, ValidationError, pre_load

from app.commons.schemas.request import PaginationReqSchema, get_orderable_schema
from app.problems.services import check_problems_id_not_in_db, check_problem_name_already_used


class ProblemListRequestSchema(
    PaginationReqSchema,
    get_orderable_schema([
        "id",
        "name",
        "prioritized",
        "trend",
        "relative_incidence",
        "performance",
        "harm_potential",
        "criticality_level",
        "total_causes",
        "total_prioritized_causes"
    ])
):
    prioritized = fields.Boolean(required=False, default=None)


class ListAssociatedCausesReqSchema(
    PaginationReqSchema,
    get_orderable_schema([
        "id",
        "name",
        "prioritized",
        "trend",
        "type",
    ])
):
    pass


class BulkProblemPrioritizationRequest(Schema):
    problems_id = fields.List(
        fields.Integer(),
        allow_none=False,
        data_key="problemsId"
    )

    @validates('problems_id')
    def validate_token(self, value: List):
        ids_not_in_db = check_problems_id_not_in_db(value)
        if ids_not_in_db:
            raise ValidationError(f"Problems ID doesn't exist {ids_not_in_db}")


class GetTrendRequest(Schema):
    problem_id = fields.Integer()
    start_year = fields.Integer()
    start_month = fields.Integer()
    end_year = fields.Integer()
    end_month = fields.Integer()

    # @validates_schema
    # def validate_numbers(self, data, **kwargs):
    #     if data["start_date"] > data["end_date"]:
    #         raise ValidationError("start_date must be greater than end_date")


@dataclasses.dataclass
class TrendItem:
    period: int
    total_incidents: int


class FakeResponse(Schema):
    result = fields.Boolean()


# CUSTOM-PROBLEMS


class CreateCustomProblemsSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(required=True)
    references = fields.List(fields.URL(), required=False, validate=validate.Length(max=5))
    annexes = fields.List(fields.File(), required=False, validate=validate.Length(max=5))

    @pre_load
    def add_scheme_to_urls(self, data, **kwargs):
        url_fields = ["references", ]
        if data.getlist('references'):
            for url_field in url_fields:
                data.setlist(url_field, [f"https://{url}" if url.startswith("www.") else url for url in data[url_field]])
        return data

    @validates('name')
    def validate_custom_cause_name(self, custom_name: str):
        name_already_used = check_problem_name_already_used(custom_name)
        if name_already_used:
            raise ValidationError(f'Problem name already used')

    @validates('annexes')
    def files_validator(self, annex_ls):
        allowed_extensions = {'.doc', '.docx', '.ppt', '.pptx', '.pdf', '.epub', '.html', '.xls', '.xlsx', '.csv'}

        for value in annex_ls:
            file_extension = os.path.splitext(value.filename)[1].lower()

            if file_extension not in allowed_extensions:
                raise ValidationError('Invalid file type')


class UpdateCustomProblemsSchema(Schema):
    name = fields.String(required=False)
    description = fields.String(required=False)
    references = fields.List(fields.URL(), required=False)
    annexes_to_add = fields.List(fields.File(), required=False, data_key="annexesToAdd")
    annexes_to_remove = fields.List(fields.Integer(), required=False, data_key="annexesToRemove")

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


relative_frequency_data_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "issue_id": {"type": "string"},
            "period_date": {"type": "string"},  # yyyy-mm-dd
            "rate_relative_frequency": {"type": "number"},
        },
        "required": ["issue_id", "period_date", "rate_relative_frequency", ]
    }
}
