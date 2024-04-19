import csv
import io
from http import HTTPStatus
from typing import Dict

import jsonschema
from apiflask import abort
from apiflask.views import MethodView
from flask import current_app, Response
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.auth.auth_config import auth_token
from app.commons.dto.pagination import PaginationRequest
from app.problems import bp
from app.problems.models import ProblemIndicatorDataModel, ProblemModel
from app.problems.schemas import ProblemListRequestSchema, BulkProblemPrioritizationRequest, \
    ListAssociatedCausesReqSchema, CreateCustomProblemsSchema, UpdateCustomProblemsSchema, \
    relative_frequency_data_schema
from app.problems.services import list_problems, count_potentials_problems, count_prioritized_problems, \
    count_critical_problems, prioritize_problem, deprioritize_problem, get_problem, count_problems, \
    list_associated_causes, get_problem_data_characteristics, get_problem_kpi, list_problem_options, \
    create_custom_problem, get_problem_rate, get_custom_problem, delete_custom_problem, get_problem_model, \
    check_problem_name_already_used, update_custom_problem_service
from db import db


@bp.get("")
@bp.input(ProblemListRequestSchema, location="query")
@bp.auth_required(auth_token)
def list_problems_controller(query):
    prioritized_filter = query.pop("prioritized") if "prioritized" in query else None
    pagination_req = PaginationRequest.from_dict(query)
    pagination_res = list_problems(pagination_req, prioritized_filter)
    return {
        "code": HTTPStatus.OK,
        "data": pagination_res.to_dict()
    }


@bp.get("/<problem_id>")
@bp.auth_required(auth_token)
def get_problem_controller(problem_id: str):
    from app.causes.services import count_causes
    problem = get_problem(problem_id)
    if not problem:
        abort(HTTPStatus.NOT_FOUND)

    if problem.get("updatedAt"):
        updated_at = str(problem["updatedAt"])
        problem["updatedAt"] = f"{updated_at[:4]}-{updated_at[4:6]}-{updated_at[6:8]}"

    kpi = get_problem_kpi(problem_id)
    data_characteristics = get_problem_data_characteristics(problem_id)
    incidences = count_problems(problem_id)
    problem_rate = get_problem_rate(problem_id)
    total_related_causes = count_causes(problem_id=problem_id)
    return {
        "code": HTTPStatus.OK,
        "data": {
            "problem": problem,
            "kpi": kpi,
            "dataCharacteristics": data_characteristics,
            "totalIncidences": incidences,
            "ratePerPopulation": round(problem_rate, 2),
            "totalCauses": total_related_causes
        }
    }


@bp.get("/<problem_id>/causes")
@bp.input(ListAssociatedCausesReqSchema, location="query")
@bp.auth_required(auth_token)
def list_associated_causes_controller(problem_id, query: Dict):
    pagination_req = PaginationRequest.from_dict(query)
    pagination_res = list_associated_causes(problem_id, pagination_req)
    return {
        "code": HTTPStatus.OK,
        "data": pagination_res.to_dict()
    }


@bp.get("/summary")
@bp.auth_required(auth_token)
def get_status_controller():
    potentials_problems_total = count_potentials_problems()
    prioritized_problems_total = count_prioritized_problems()
    critical_problems_total = count_critical_problems()
    return {
        "code": HTTPStatus.OK,
        "data": {
            "potentialProblemsTotal": potentials_problems_total,
            "prioritizedProblemsTotal": prioritized_problems_total,
            "criticalProblemsTotal": critical_problems_total,
        }
    }


class ProblemPrioritizationView(MethodView):
    decorators = [
        bp.auth_required(auth_token),
    ]

    def put(self, problem_id: str):
        prioritize_problem(problem_id)
        return {
            "code": HTTPStatus.OK,
            "message": 'Problem prioritized correctly'
        }

    def delete(self, problem_id: int):
        deprioritize_problem(problem_id)
        return {
            "code": HTTPStatus.OK,
            "message": 'Problem deprioritized correctly'
        }


class BulkProblemPrioritizationView(MethodView):
    decorators = [
        bp.input(BulkProblemPrioritizationRequest, location="json"),
        bp.auth_required(auth_token),
    ]

    def put(self, data):
        for problem_id in data["problems_id"]:
            prioritize_problem(problem_id)
        return {
            "code": HTTPStatus.OK,
            "message": 'Problems prioritized correctly'
        }

    def delete(self, data):
        for problem_id in data["problems_id"]:
            deprioritize_problem(problem_id)
        return {
            "code": HTTPStatus.OK,
            "message": 'Problems deprioritized correctly'
        }


bp.add_url_rule('/prioritize', view_func=BulkProblemPrioritizationView.as_view("problem-prioritization"))
bp.add_url_rule('/<problem_id>/prioritize',
                view_func=ProblemPrioritizationView.as_view('bulk-problem-prioritization'))


@bp.get("/options/all")
@bp.auth_required(auth_token)
def list_problem_options_controller():
    data = list_problem_options()
    return {
        "code": HTTPStatus.OK,
        "data": data
    }


# CUSTOM-PROBLEMS


@bp.post("/custom-problem")
@bp.input(CreateCustomProblemsSchema, location="files")
@bp.auth_required(auth_token)
def post_custom_problem(body: Dict):
    path = current_app.config["UPLOAD_FOLDER"]
    custom_problem_obj = create_custom_problem(body, path, auth_token.current_user["id"])
    return {
        "code": HTTPStatus.OK,
        "message": "Custom problem registered.",
        "problem_id": custom_problem_obj.id,
    }


@bp.put("/custom-problem/<int:custom_problem_id>")
@bp.input(UpdateCustomProblemsSchema, location="files")
@bp.auth_required(auth_token)
def update_custom_problem(problem_id, body):
    path = current_app.config["UPLOAD_FOLDER"]
    name_already_used = ("name" in body) and check_problem_name_already_used(body["name"], ignore_id=problem_id)
    if name_already_used:
        raise ValidationError({"name": ["Name already used"]})

    problem_model = get_problem_model(problem_id)
    if not problem_model:
        abort(HTTPStatus.NOT_FOUND)

    if problem_model.is_default:
        abort(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Default Problem can't be edited"
        )

    update_custom_problem_service(problem_model, body, path)
    return {
        "code": HTTPStatus.OK,
        "message": "Custom problem updated"
    }


@bp.get("/custom-problem/<int:problem_id>")
@bp.auth_required(auth_token)
def get_custom_problem_controller(problem_id):
    custom_problem = get_custom_problem(problem_id)
    if custom_problem:
        return {
            "code": HTTPStatus.OK,
            "data": custom_problem
        }
    raise abort(HTTPStatus.NOT_FOUND, "Custom Problem not found")


@bp.delete("/custom-problem/<int:problem_id>")
@bp.output({}, status_code=204)
@bp.auth_required(auth_token)
def delete_custom_problem_ontroller(problem_id):
    problem_model = get_problem_model(problem_id)
    if problem_model:
        if problem_model.is_default:
            abort(
                HTTPStatus.BAD_REQUEST,
                "Default Problem can't be deleted"
            )
        if problem_model.associated_causes:
            abort(
                HTTPStatus.BAD_REQUEST,
                "Problem has associated causes",
                dict(causes=[item.name for item in problem_model.associated_causes])
            )
        delete_custom_problem(problem_id)
    return {
        "code": HTTPStatus.OK
    }


@bp.get("<int:problem_id>/trend/csv")
@bp.output(None, content_type="text/csv")
def trend_csv_controller(problem_id: int):
    graph_data = db.session.execute(
        select(ProblemIndicatorDataModel.trend_data).where(
            ProblemIndicatorDataModel.problem_id == select(ProblemModel.code).where(
                ProblemModel.id == problem_id).subquery()
        )
    ).scalar()

    buffer = io.StringIO()
    csv_writer = csv.DictWriter(buffer, fieldnames=["year", "quarter", "totalCityIncidents", "rateCityIncidents", ])
    csv_writer.writeheader()

    if graph_data and isinstance(graph_data, list):
        graph_data = sorted(
            graph_data,
            key=lambda x: (x["year"], x["quarter"]),
            reverse=True
        )
        csv_writer.writerows(graph_data)

    buffer.seek(0)
    return Response(
        buffer,
        content_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )


@bp.get("<int:problem_id>/performance/csv")
@bp.output(None, content_type="text/csv")
def performance_csv_controller(problem_id: int):
    graph_data_ls = db.session.execute(
        select(ProblemIndicatorDataModel.performance_data).where(
            ProblemIndicatorDataModel.problem_id == select(ProblemModel.code).where(
                ProblemModel.id == problem_id).subquery()
        )
    ).scalar()

    buffer = io.StringIO()
    csv_writer = csv.DictWriter(
        buffer,
        fieldnames=["year", "month", "cityRate", "stateRate"]
    )
    csv_writer.writeheader()

    if graph_data_ls and isinstance(graph_data_ls, list):
        # for graph_data in graph_data_ls:
            # graph_data.pop("rate")
            # graph_data["averageCityRate"] = graph_data.pop("stateRate")

        graph_data_ls = sorted(
            graph_data_ls,
            key=lambda x: (x["year"], x["month"]),
            reverse=False
        )
        csv_writer.writerows(graph_data_ls)

    buffer.seek(0)
    return Response(
        buffer,
        content_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )


@bp.get("<int:problem_id>/relative-frequency/csv")
@bp.output(None, content_type="text/csv")
def frequency_csv_controller(problem_id: int):
    buffer = io.StringIO()
    csv_writer = csv.DictWriter(
        buffer,
        fieldnames=["problem", "period", "totalCityIncidents", "percentage", ]
    )
    csv_writer.writeheader()

    graph_data = db.session.execute(
        select(ProblemIndicatorDataModel.relative_frequency_data)
        .where(
            ProblemIndicatorDataModel.problem_id == (
                select(ProblemModel.code)
                .where(ProblemModel.id == problem_id)
                .subquery()
            )
        )
    ).scalar()

    if graph_data:
        try:
            jsonschema.validate(graph_data, relative_frequency_data_schema)
            problem_codes = [item["issue_id"].lower() for item in graph_data]

            problem_ind_data_subquery = (
                select(ProblemIndicatorDataModel)
                .select_from(ProblemIndicatorDataModel)
                .where(ProblemIndicatorDataModel.problem_id.in_(problem_codes))
                .subquery()
            )
            problem_ind_data_subquery = aliased(ProblemIndicatorDataModel, problem_ind_data_subquery)

            problem_ls = db.session.execute(
                select(ProblemModel.code, ProblemModel.name, problem_ind_data_subquery.total_city_incidents)
                .outerjoin(problem_ind_data_subquery, problem_ind_data_subquery.problem_id == ProblemModel.code)
                .where(ProblemModel.code.in_([item["issue_id"].lower() for item in graph_data]))
            ).all()
            problem_dict = {
                item[0]: dict(
                    name=item[1],
                    total_city_incidents=item[2],
                )
                for item in problem_ls
            }

            for row in graph_data:
                if row["issue_id"].lower() in problem_dict:
                    csv_writer.writerow({
                        "problem": problem_dict[row["issue_id"].lower()]["name"],
                        "period": row["period_date"],
                        "percentage": row.get("rate_relative_frequency", 0) * 100,
                        "totalCityIncidents": problem_dict[row["issue_id"].lower()]["total_city_incidents"],
                    })
        except jsonschema.exceptions.ValidationError:
            pass

    buffer.seek(0)
    return Response(
        buffer,
        content_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )
