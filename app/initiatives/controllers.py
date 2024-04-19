from http import HTTPStatus
from typing import Dict

from apiflask import abort
from sqlalchemy import select

from app.auth.auth_config import auth_token
from app.commons.dto.pagination import PaginationRequest
from app.initiatives import bp, services
from app.initiatives.models import InitiativeModel
from app.initiatives.schemas import InitiativePaginationRequestSchema, CreateCustomInitiativeRequestSchema, \
    UpdateCustomInitiativeSchema, \
    BulkUpdateInitiativePrioritizationRequestSchema, ListInitiativeAssociationRequestSchema, InitiativeOutcomeSchema
from app.initiatives.services import InitiativeService, get_summary
from db import db

initiative_service = InitiativeService()


@bp.get("")
@bp.input(InitiativePaginationRequestSchema, location="query")
@bp.auth_required(auth_token)
def get_initiative_list(query):
    """
    Present list initiatives
    """
    prioritized_filter = query.pop("prioritized") if "prioritized" in query else None
    pagination_req = PaginationRequest.from_dict(query)
    pagination_res = initiative_service.get_initiative_list_service(pagination_req, prioritized_filter)

    return {
        "code": HTTPStatus.OK,
        "data": pagination_res.to_dict(),
    }


@bp.get("/summary")
@bp.auth_required(auth_token)
def get_summary_controller():
    """
    Return total problems and causes
    :return:
    """
    data = get_summary()
    return dict(data=data)


@bp.post("")
@bp.input(CreateCustomInitiativeRequestSchema, location="files")
@bp.auth_required(auth_token)
def create_initiative_controller(body: Dict):
    initiative_obj = services.create_initiative(body)
    return {
        "data": initiative_obj.to_dict()
    }


@bp.get("/<initiative_id>")
@bp.auth_required(auth_token)
def get_initiative_controller(initiative_id: str):
    initiative_detail_dto = services.get_initiative(initiative_id)
    return dict(data=initiative_detail_dto.to_dict())


@bp.put("/<initiative_id>")
@bp.input(UpdateCustomInitiativeSchema, location="files")
@bp.auth_required(auth_token)
def update_initiative_controller(initiative_id: str, body: Dict):
    initiative_model = services.get_initiative_model(initiative_id)
    if not initiative_model:
        abort(HTTPStatus.NOT_FOUND)
    if initiative_model.is_default:
        abort(HTTPStatus.UNPROCESSABLE_ENTITY, "Default Initiative can't be edited")
    initiative_obj = services.update_initiative(initiative_model, body)
    return {
        "data": initiative_obj.to_dict()
    }


@bp.delete("/<initiative_id>")
@bp.auth_required(auth_token)
def delete_initiative_controller(initiative_id: str):
    initiative_is_prioritized = services.check_initiative_is_prioritized(initiative_id)
    if initiative_is_prioritized:
        abort(HTTPStatus.BAD_REQUEST, "The initiative is prioritized so can't be deleted")
    services.delete_initiative(initiative_id)
    return {}


@bp.get("/prioritization/all")
@bp.input(ListInitiativeAssociationRequestSchema, location="query")
@bp.auth_required(auth_token)
def list_initiative_association_controller(query: Dict):
    initiative_ids = query["initiative_ids"]

    output = dict()
    for item in services.list_initiative_association(initiative_ids):
        initiative_dict = output.get(
            item.initiative_id,
            dict(initiativeId=item.initiative_id, initiativeName=item.initiative_name, causes=dict())
        )
        output[item.initiative_id] = initiative_dict

    for item in services.list_initiative_association(initiative_ids):
        cause_dict = output[item.initiative_id]["causes"]
        t = cause_dict.get(
            item.cause_id,
            dict(causeId=item.cause_id, causeName=item.cause_name, problems=dict())
        )
        cause_dict[item.cause_id] = t

    for item in services.list_initiative_association(initiative_ids):
        problem_dict = output[item.initiative_id]["causes"][item.cause_id]["problems"]
        problem_dict[item.problem_id] = problem_dict.get(
            item.problem_id,
            dict(problemId=item.problem_id, problemName=item.problem_name, prioritized=item.prioritized)
        )

    output = list(output.values())
    for item in output:
        item["causes"] = list(item["causes"].values())
        for cause in item["causes"]:
            cause["problems"] = list(cause["problems"].values())

    return dict(data=output)


@bp.put("/prioritization")
@bp.input(BulkUpdateInitiativePrioritizationRequestSchema)
@bp.auth_required(auth_token)
def bulk_update_initiative_prioritization_controller(body: dict):
    to_prioritize = body["prioritize"]
    to_deprioritize = body["deprioritize"]
    services.bulk_update_initiative_prioritization(to_prioritize, to_deprioritize)
    return dict()


@bp.get("/options/causes")
@bp.auth_required(auth_token)
def list_causes_controller():
    data = services.list_causes_options()
    return dict(data=data)


@bp.get("/options/municipal-departments")
@bp.auth_required(auth_token)
def list_municipal_department_controller():
    data = services.list_municipal_departments_options()
    return dict(data=data)


@bp.get("<initiative_id>/initiative-outcomes")
@bp.output(InitiativeOutcomeSchema(many=True))
def list_initiative_outcomes_controller(initiative_id: int):
    return services.list_initiative_outcomes(initiative_id)


