from http import HTTPStatus
from typing import Dict

from apiflask import HTTPError, abort
from flask import current_app

from app.auth.auth_config import auth_token
from app.causes import bp
from app.causes import services
from app.causes.schemas import CreateCustomCauseRequestSchema, UpdateCustomCauseSchema, \
    BulkUpdateCausePrioritizationRequestSchema, ListCauseAssociationRequestSchema
from app.causes.services import get_cause_summary


@bp.get("/summary")
@bp.auth_required(auth_token)
def summary_controller():
    cause_summary_dto = get_cause_summary()
    return dict(
        code=HTTPStatus.OK,
        data=cause_summary_dto.to_dict()
    )


@bp.get("/default-causes/<int:cause_id>")
@bp.auth_required(auth_token)
def get_default_cause_controller(cause_id: int):
    cause_obj = services.get_default_cause(cause_id)
    if cause_obj:
        return {
            "code": HTTPStatus.OK,
            "data": cause_obj.to_dict()
        }
    raise HTTPError(HTTPStatus.NOT_FOUND, "Cause not found")


@bp.get("/<cause_id>/indicators/all")
@bp.auth_required(auth_token)
def list_cause_indicators_controller(cause_id):
    cause_indicator_ls = services.list_cause_indicators_with_last_data(cause_id)
    cause_indicator_ls = [
        {
            "causeIndicator": cause_indicator.to_dict(),
            "causeIndicatorData": cause_indicator_data.to_dict() if cause_indicator_data else None
        }
        for cause_indicator, cause_indicator_data in cause_indicator_ls
    ]
    return {
        "code": HTTPStatus.OK,
        "data": cause_indicator_ls
    }


@bp.post("/custom-causes")
@bp.input(CreateCustomCauseRequestSchema, location="files")
@bp.auth_required(auth_token)
def post_custom_causes(body: Dict):
    path = current_app.config["UPLOAD_FOLDER"]
    custom_cause_obj = services.create_custom_cause(body, path, auth_token.current_user["id"])
    return {
        "code": HTTPStatus.OK,
        "message": "Cause registered.",
        "custom_cause_id": custom_cause_obj.id,
    }


@bp.put("/custom-causes/<int:cause_id>")
@bp.input(UpdateCustomCauseSchema, location="files")
@bp.auth_required(auth_token)
def update_custom_cause_controller(cause_id, body):
    path = current_app.config["UPLOAD_FOLDER"]
    services.update_custom_cause(cause_id, body, path)
    return {
        "code": HTTPStatus.OK,
        "message": "Cause updated"
    }


@bp.get("/custom-causes/<int:cause_id>")
@bp.auth_required(auth_token)
def get_custom_cause_controller(cause_id):
    cause_model = services.get_custom_cause(cause_id)
    if cause_model:
        return {
            "code": HTTPStatus.OK,
            "data": cause_model.to_dict()
        }
    raise HTTPError(HTTPStatus.NOT_FOUND, "Cause not found")


@bp.delete("/custom-causes/<int:cause_id>")
@bp.output({}, status_code=204)
@bp.auth_required(auth_token)
def delete_custom_cause_controller(cause_id):
    cause_is_prioritized = services.check_cause_is_prioritized(cause_id)
    if cause_is_prioritized:
        abort(HTTPStatus.BAD_REQUEST, "Prioritized cause can't be deleted")
    services.delete_custom_cause(cause_id)
    return {
        "code": HTTPStatus.OK
    }


@bp.get("/prioritization/all")
@bp.input(ListCauseAssociationRequestSchema, location="query")
@bp.auth_required(auth_token)
def list_cause_prioritization_controller(query: Dict):
    data = services.list_cause_prioritization(query["cause_ids"])
    return dict(data=[item.to_dict() for item in data])


@bp.put("/prioritization")
@bp.input(BulkUpdateCausePrioritizationRequestSchema)
@bp.auth_required(auth_token)
def bulk_update_cause_prioritization_controller(body: Dict):
    services.bulk_update_cause_prioritization(body["items"])
    return dict()
