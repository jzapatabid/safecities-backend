from typing import List

from apiflask import Schema, fields
from flask_marshmallow.sqla import SQLAlchemySchema
from marshmallow import validates, ValidationError, validate, post_load, pre_load
from marshmallow_sqlalchemy import auto_field
from sqlalchemy import select, distinct

from app.cause_problem_association.models import CauseAndProblemAssociation
from app.initiatives.constants import EFFICIENCY_LEVEL_DICT, COST_LEVEL_DICT
from app.initiatives.dto import InitiativePrioritizationRequestDTO
from app.initiatives.models import InitiativeOutcomeModel
from app.initiatives.services import check_municipal_department_id_exist, check_initiative_name_already_exist
from db import db


class CreateCustomInitiativeRequestSchema(Schema):
    name = fields.String(required=True)
    justification = fields.String(required=True)
    evidences = fields.String(required=True)
    cost_level = fields.Integer(
        required=True, data_key="costLevel", validate=validate.OneOf(COST_LEVEL_DICT.values())
    )
    efficiency_level = fields.Integer(
        required=True, data_key="efficiencyLevel", validate=validate.OneOf(EFFICIENCY_LEVEL_DICT.values())
    )
    cause_ids = fields.List(
        fields.Integer(), required=True,
        validate=validate.Length(min=1), data_key="causeIds"
    )
    municipal_department_ids = fields.List(
        fields.Integer(), required=True, validate=validate.Length(min=1),
        data_key="municipalDepartmentIds"
    )
    reference_urls = fields.List(
        fields.URL(), required=False, validate=validate.Length(max=5),
        data_key="referenceUrls"
    )
    annex_files = fields.List(
        fields.File(), required=False, validate=validate.Length(max=5),
        data_key="annexFiles"
    )

    @pre_load
    def add_scheme_to_urls(self, data, **kwargs):
        url_fields = ["referenceUrls", ]
        if data.getlist('referenceUrls'):
            for url_field in url_fields:
                data.setlist(url_field, [f"https://{url}" if url.startswith("www.") else url for url in data[url_field]])
        return data

    @validates("name")
    def validate_name(self, name: str):
        if check_initiative_name_already_exist(name):
            raise ValidationError(f"Initiative name already registered")

    @validates("municipal_department_ids")
    def validate_municipal_department(self, municipal_department_ids: List):
        for municipal_department_id in municipal_department_ids:
            if not check_municipal_department_id_exist(municipal_department_id):
                raise ValidationError(f"MunicipalDepartment ID doesn't exist {municipal_department_id}")

    @validates("cause_ids")
    def validate_causes(self, cause_ids: List):
        cause_ids = list(set(cause_ids))
        select_stmt = select(distinct(CauseAndProblemAssociation.cause_id)).where(
            CauseAndProblemAssociation.cause_id.in_(cause_ids),
            CauseAndProblemAssociation.prioritized == True
        )
        valid_causes_id = db.session.execute(select_stmt).scalars().all()
        if len(valid_causes_id) != len(cause_ids):
            not_valid_id_ls = [cause_id for cause_id in cause_ids if cause_id not in valid_causes_id]
            raise ValidationError(f"Cause ID doesn't exist or It is not prioritized, {not_valid_id_ls}")


class UpdateCustomInitiativeSchema(Schema):
    name = fields.String(required=True)
    justification = fields.String(required=True)
    evidences = fields.String(required=True)
    cost_level = fields.Integer(
        required=True, data_key="costLevel", validate=validate.OneOf(COST_LEVEL_DICT.values())
    )
    efficiency_level = fields.Integer(
        required=True, data_key="efficiencyLevel", validate=validate.OneOf(EFFICIENCY_LEVEL_DICT.values())
    )
    cause_ids = fields.List(
        fields.Integer(), required=False, validate=validate.Length(min=1),
        data_key="causeIds"
    )
    municipal_department_ids = fields.List(
        fields.Integer(), required=False, validate=validate.Length(min=1),
        data_key="municipalDepartmentIds"
    )
    reference_urls = fields.List(
        fields.URL(), required=False, validate=validate.Length(max=5),
        data_key="referenceUrls"
    )
    annex_files = fields.List(
        fields.File(), required=False,
        data_key="annexFiles"
    )
    annex_files_to_delete_ids = fields.List(
        fields.String(), required=False,
        data_key="annexFilesToDeleteIds"
    )

    @pre_load
    def add_scheme_to_urls(self, data, **kwargs):
        url_fields = ["referenceUrls", ]
        if data.getlist('referenceUrls'):
            for url_field in url_fields:
                data.setlist(url_field, [f"https://{url}" if url.startswith("www.") else url for url in data[url_field]])
        return data

    @validates("municipal_department_ids")
    def validate_municipal_department(self, municipal_department_ids):
        municipal_department_ids = list(set(municipal_department_ids))
        for municipal_department_id in municipal_department_ids:
            if not check_municipal_department_id_exist(municipal_department_id):
                raise ValidationError(f"MunicipalDepartment ID doesn't exist {municipal_department_id}")

    @validates("cause_ids")
    def validate_causes(self, cause_ids: List):
        cause_ids = list(set(cause_ids))
        select_stmt = select(distinct(CauseAndProblemAssociation.cause_id)).where(
            CauseAndProblemAssociation.cause_id.in_(cause_ids),
            CauseAndProblemAssociation.prioritized == True
        )
        valid_causes_id = db.session.execute(select_stmt).scalars().all()
        if len(valid_causes_id) != len(cause_ids):
            not_valid_id_ls = [cause_id for cause_id in cause_ids if cause_id not in valid_causes_id]
            raise ValidationError(f"Cause ID doesn't exist or It is not prioritized, {not_valid_id_ls}")


from app.commons.schemas.request import PaginationReqSchema, get_orderable_schema


class InitiativePaginationRequestSchema(PaginationReqSchema, get_orderable_schema([
    "initiative_id",
    "initiative_name",
    "prioritized",
    "justification",
    "evidences",
    "cost_level",
    "efficiency_level"
])):
    pass


class ListInitiativeAssociationRequestSchema(Schema):
    initiative_ids = fields.List(
        fields.Integer(),
        required=True,
        validate=validate.Length(min=1)
    )


class BulkUpdateInitiativePrioritizationRequestSchema(Schema):
    class InitiativePrioritizationSchema(Schema):
        __model__ = InitiativePrioritizationRequestDTO

        @post_load
        def make_object(self, data, **kwargs):
            return self.__model__(**data)

        initiative_id = fields.Integer(
            required=True,
            data_key="initiativeId"
        )
        cause_id = fields.Integer(
            required=True,
            data_key="causeId"
        )
        problem_id = fields.String(
            required=True,
            data_key="problemId"
        )

    prioritize = fields.Nested(InitiativePrioritizationSchema, many=True, data_key="prioritize")
    deprioritize = fields.Nested(InitiativePrioritizationSchema, many=True, data_key="deprioritize")


class InitiativeOutcomeSchema(SQLAlchemySchema):
    class Meta:
        model = InitiativeOutcomeModel
        load_instance = True

    id = auto_field()
    name = auto_field()
