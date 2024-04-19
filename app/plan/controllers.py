from http import HTTPStatus
from typing import List

from apiflask import abort
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.sql.functions import max

from app.auth.auth_config import auth_token
from app.causes.models import CauseIndicatorDataModel, CauseIndicatorModel
from app.commons.schemas.request import factory_response_schema
from app.commons.sqlalchemy_utils import desc_
from app.plan import bp, services
from app.plan.dto import CreateOrUpdateMacroObjectiveGoalRequestDTO, CreateOrUpdatePlanRequestDTO, \
    UpdateFocusGoalRequestDTO, SetDiagnosisToProblemIndRequestDTO, SetDiagnosisToCauseIndRequestDTO, \
    SetTacticalDimensionDTO
from app.plan.models import ProblemDiagnosisModel, CauseIndicatorDiagnosisModel, TacticalDimensionModel, PlanModel
from app.plan.schemas.request_schemas import CreateOrUpdatePlanRequestSchema, \
    UpdateMacroObjectiveGoalRequestSchema, UpdateFocusGoalRequestSchema, SetDiagnosisToProblemIndRequestSchema, \
    SetDiagnosisToCauseIndRequestSchema, SetTacticalDimensionRequestSchema
from app.plan.schemas.response_schemas import ListMacroObjectivesResponseSchema, ListFocusesResponseSchema, \
    DetailPlanResponseSchema, TacticalDimensionResSchema
from app.problems.models import ProblemModel, ProblemIndicatorDataModel
from app.problems.services import format_relative_frequency
from db import db


@bp.get("/status")
# @bp.auth_required(auth_token)
def get_status_controller():
    return services.get_status()


@bp.post("")
@bp.input(CreateOrUpdatePlanRequestSchema, location="json")
@bp.auth_required(auth_token)
def create_or_update_plan_controller(create_or_update_plan_request_dto: CreateOrUpdatePlanRequestDTO):
    services.create_or_update_plan(create_or_update_plan_request_dto)
    return dict()


@bp.get("")
@bp.output(factory_response_schema(DetailPlanResponseSchema))
@bp.auth_required(auth_token)
def get_plan_controller():
    plan_model = services.get_current_plan()
    if plan_model:
        return dict(data=plan_model)
    abort(HTTPStatus.NOT_FOUND)


@bp.get("/macro-objectives/all")
@bp.output(ListMacroObjectivesResponseSchema(many=True))
@bp.auth_required(auth_token)
def list_macro_objectives_controller():
    macro_objectives = services.list_macro_objectives()
    return macro_objectives


@bp.put("/macro-objectives/<int:macro_obj_id>/goals")
@bp.input(UpdateMacroObjectiveGoalRequestSchema(many=True), "json")
@bp.auth_required(auth_token)
def update_macro_objectives_goals_controller(
        macro_obj_id: int,
        dto_ls: List[CreateOrUpdateMacroObjectiveGoalRequestDTO]
):
    services.bulk_create_or_update_macro_objective_goals(macro_obj_id, dto_ls)
    return dict()


@bp.get("/macro-objectives/focus/all")
@bp.output(ListFocusesResponseSchema(many=True))
@bp.auth_required(auth_token)
def list_focus_controller():
    focus_dto_ls = services.list_focuses()
    return focus_dto_ls


@bp.put("/macro-objectives/<int:macro_obj_id>/focus/<int:focus_id>/goals")
@bp.input(UpdateFocusGoalRequestSchema(many=True), "json")
@bp.auth_required(auth_token)
def update_focus_goals_controller(
        macro_obj_id: int,
        focus_id: int,
        dto_ls: List[UpdateFocusGoalRequestDTO]
):
    services.update_focus_goals(macro_obj_id, focus_id, dto_ls)
    return dict()


@bp.get("/problem-diagnoses")
# @bp.auth_required(auth_token)
def list_problem_diagnosis_controller():
    dto_ls = services.list_problem_diagnosis()
    return dto_ls


@bp.put("/problem-diagnoses")
@bp.input(SetDiagnosisToProblemIndRequestSchema(many=True), "json")
# @bp.auth_required(auth_token)
def set_problem_diagnosis_controller(
        set_diagnosis_dto_ls: List[SetDiagnosisToProblemIndRequestDTO]
):
    services.set_problem_diagnosis(set_diagnosis_dto_ls)
    return dict()


@bp.get("/cause-diagnoses")
# @bp.auth_required(auth_token)
def list_cause_diagnosis_controller():
    return services.list_cause_diagnosis()


@bp.put("/causes/<int:cause_id>/cause-diagnoses")
@bp.input(SetDiagnosisToCauseIndRequestSchema(many=True), "json")
# @bp.auth_required(auth_token)
def set_cause_diagnosis_controller(
        cause_id: int,
        set_diagnosis_dto_ls: List[SetDiagnosisToCauseIndRequestDTO]
):
    services.set_cause_diagnosis(cause_id, set_diagnosis_dto_ls)
    return dict()


@bp.get("/tactical-dimension")
def list_tactical_dimensions_controller():
    return services.list_tactical_dimensions()


@bp.put("/tactical-dimension")
@bp.input(SetTacticalDimensionRequestSchema, "json")
def set_tactical_dimension_controller(dto: SetTacticalDimensionDTO):
    services.set_tactical_dimension(dto)
    return dict()


# @bp.get("<initiative_id>/ignore")
# def get_ini(initiative_id: int):
#     initiative_model = db.session.execute(
#         select(InitiativeModel).where(InitiativeModel.id == initiative_id).limit(1)
#     ).scalar()
#
#     if not initiative_model:
#         abort(HTTPStatus.NOT_FOUND)
#
#     query = (
#         select(
#             MacroObjectiveGoalModel,
#             FocusGoalModel
#         )
#         .select_from(MacroObjectiveGoalModel)
#         .outerjoin(
#             FocusGoalModel,
#             FocusGoalModel.macro_objective_id == MacroObjectiveGoalModel.macro_objective_id
#         )
#         .where(
#             MacroObjectiveGoalModel.plan_id == 1,
#             FocusGoalModel.plan_id == 1,
#             MacroObjectiveGoalModel.problem_id != None,
#             FocusGoalModel.id != None,
#         )
#         .options(joinedload(MacroObjectiveGoalModel.macro_objective))
#         # .options(joinedload(FocusGoalModel.focus))
#     )
#
#     data = db.session.execute(query).all()
#     macro_output = dict()
#     focus_output = dict()
#
#     for macro_obj_goal_model, focus_goal_model in data:
#         if macro_obj_goal_model.macro_objective in initiative_model.associated_macro_objectives:
#             macro_temp = macro_output.get(macro_obj_goal_model.macro_objective_id, dict(
#                 macro_objective_id=macro_obj_goal_model.macro_objective.id,
#                 macro_objective_name=macro_obj_goal_model.macro_objective.name,
#                 goals=[]
#             ))
#             macro_output[macro_obj_goal_model.macro_objective_id] = macro_temp
#             macro_temp["goals"].append(
#                 dict(
#
#                 )
#             )
#
#     return macro_output

def _get_causes():
    last_period_by_cause_ind_id_subquery = (
        select(
            CauseIndicatorDataModel.cause_indicator_id,
            max(CauseIndicatorDataModel.period).label("period"),
        )
        .select_from(CauseIndicatorDataModel)
        .group_by(CauseIndicatorDataModel.cause_indicator_id)
        .subquery()
    )

    cause_ind_data_subquery = (
        select(CauseIndicatorDataModel)
        .select_from(last_period_by_cause_ind_id_subquery)
        .outerjoin(
            CauseIndicatorDataModel,
            and_(
                CauseIndicatorDataModel.cause_indicator_id == last_period_by_cause_ind_id_subquery.c.cause_indicator_id,
                CauseIndicatorDataModel.period == last_period_by_cause_ind_id_subquery.c.period,
            )
        )
        .subquery()
    )

    cause_ind_data_subquery = aliased(CauseIndicatorDataModel, cause_ind_data_subquery)

    query = (
        select(
            CauseIndicatorDiagnosisModel,
            CauseIndicatorModel,
            cause_ind_data_subquery
        )
        .select_from(CauseIndicatorDiagnosisModel)
        .outerjoin(
            CauseIndicatorModel,
            CauseIndicatorModel.id == CauseIndicatorDiagnosisModel.cause_indicator_id
        )
        .outerjoin(
            cause_ind_data_subquery,
            cause_ind_data_subquery.cause_indicator_id == CauseIndicatorModel.code
        )
    )

    return list(db.session.execute(query).all())


def _get_ini():
    query = (
        select(TacticalDimensionModel)
    )
    return list(
        db.session.execute(query).scalars()
    )


@bp.get("/pdf")
def get_pdf():
    last_period_by_problem_id_subquery = (
        select(ProblemIndicatorDataModel.problem_id, max(ProblemIndicatorDataModel.period).label("period"))
        .group_by(ProblemIndicatorDataModel.problem_id)
        .subquery()
    )

    problem_ind_data_subquery = (
        select(ProblemIndicatorDataModel)
        .select_from(last_period_by_problem_id_subquery)
        .outerjoin(
            ProblemIndicatorDataModel,
            and_(
                ProblemIndicatorDataModel.problem_id == last_period_by_problem_id_subquery.c.problem_id,
                ProblemIndicatorDataModel.period == last_period_by_problem_id_subquery.c.period,
            )
        )
        .subquery()
    )

    problem_ind_data_subquery = aliased(ProblemIndicatorDataModel, problem_ind_data_subquery)

    rs = db.session.execute(
        select(ProblemDiagnosisModel, ProblemModel, problem_ind_data_subquery)
        .select_from(ProblemDiagnosisModel)
        .options(joinedload(ProblemDiagnosisModel.problem))
        .outerjoin(
            ProblemModel,
            ProblemModel.id == ProblemDiagnosisModel.problem_id
        ).outerjoin(
            problem_ind_data_subquery,
            problem_ind_data_subquery.problem_id == ProblemModel.code
        )
    ).all()

    output = dict(
        plan=None,
        problem_diagnoses=list(),
        cause_indicator_diagnoses=list(),
        initiative_plans=list(),
    )

    plan_model = db.session.execute(
        select(PlanModel)
        .order_by(desc_(PlanModel.id))
        .limit(1)
    ).scalar()

    output["plan"] = dict(
        title=plan_model.title,
        start_at=plan_model.start_at.isoformat() if plan_model.start_at else None,
        end_at=plan_model.end_at.isoformat() if plan_model.end_at else None,
        updated_at=plan_model.updated_at.isoformat() if plan_model.updated_at else None,
    )

    for problem_diagnosis_model, problem_model, problem_ind_model in rs:
        problem_ind_model: "ProblemIndicatorDataModel"

        diagnosis_dict = dict(
            problem_name=problem_model.name,
            measurement_unit=problem_model.measurement_unit,
            polarity=problem_model.polarity,
            diagnosis=problem_diagnosis_model.diagnosis,
        )

        if problem_ind_model:
            for kpi_graph in problem_diagnosis_model.kpi_graphs:
                diagnosis_dict[kpi_graph] = getattr(problem_ind_model, f"{kpi_graph}")
                diagnosis_dict[f"{kpi_graph}_data"] = getattr(problem_ind_model, f"{kpi_graph}_data")
                start_at, end_at = getattr(problem_ind_model, f"{kpi_graph}_range")
                diagnosis_dict[f"{kpi_graph}_start_at"] = start_at.strftime("%Y-%m-%d")
                diagnosis_dict[f"{kpi_graph}_end_at"] = end_at.strftime("%Y-%m-%d")

                if kpi_graph == "relative_frequency":
                    diagnosis_dict[f"{kpi_graph}_data"] = format_relative_frequency(diagnosis_dict[f"{kpi_graph}_data"])

        output["problem_diagnoses"].append(diagnosis_dict)

    for cause_diagnosis_model, cause_indicator_model, cause_ind_data_model in _get_causes():
        diagnosis_dict = dict(
            cause_indicator_name=cause_indicator_model.name,
            diagnosis=cause_diagnosis_model.diagnosis,
        )
        if cause_ind_data_model:
            diagnosis_dict["trend"] = cause_ind_data_model.trend
            diagnosis_dict["trend_data"] = cause_ind_data_model.trend_data
            start_at, end_at = cause_ind_data_model.trend_range
            diagnosis_dict["trend_start_at"] = start_at.strftime("%Y-%m-%d")
            diagnosis_dict["trend_end_at"] = end_at.strftime("%Y-%m-%d")

        output["cause_indicator_diagnoses"].append(diagnosis_dict)

    output["initiative_plans"] = TacticalDimensionResSchema().dump(_get_ini(), many=True)

    return output
