from http import HTTPStatus
from typing import List, Optional

from apiflask import abort
from sqlalchemy import distinct, select
from sqlalchemy.sql.functions import count

from app.cause_problem_association.models import CauseAndProblemAssociation
from app.causes import repositories as cause_repo
from app.causes.models import CauseIndicatorModel
from app.initiatives import repositories as initiative_repo
from app.plan import repositories
from app.plan.dto import MacroObjectiveDTO, CreateOrUpdateMacroObjectiveGoalRequestDTO, \
    CreateOrUpdatePlanRequestDTO, FocusListItemDTO, UpdateFocusGoalRequestDTO, SetDiagnosisToProblemIndRequestDTO, \
    SetDiagnosisToCauseIndRequestDTO, SetTacticalDimensionDTO
from app.plan.models import PlanModel, CauseIndicatorDiagnosisModel, ProblemDiagnosisModel, TacticalDimensionModel, \
    MacroObjectiveProblemAssociationModel, FocusAssociationModel, MacroObjectiveGoalModel, FocusGoalModel
from app.problems import repositories as problem_repo
from app.problems.models import ProblemModel
from db import db


def create_empty_plan():
    pass


def create_or_update_plan(create_or_update_plan_request_dto: CreateOrUpdatePlanRequestDTO):
    plan_id = repositories.get_last_plan_id()
    if plan_id:
        repositories.update_plan(plan_id, create_or_update_plan_request_dto)
    else:
        repositories.create_plan(create_or_update_plan_request_dto)
    db.session.commit()


def get_current_plan() -> PlanModel:
    plan_id = repositories.get_last_plan_id()
    if plan_id:
        return repositories.get_plan(plan_id)


def get_status():
    plan_model = repositories.get_last_plan()

    def _calculate_bi_progress(plan_model: Optional[PlanModel]):
        if not plan_model:
            return 0

        total_fields = 3
        total_filled_fields = int(bool(plan_model.title)) + int(bool(plan_model.start_at)) + int(
            bool(plan_model.end_at))
        return round((total_filled_fields / total_fields) * 100)

    def _calculate_diagnostic_progress(plan_model: Optional[PlanModel]):
        if not plan_model:
            return 0

        total_causes = cause_repo.count_prioritized_causes()
        total_problems = problem_repo.count_prioritized_problems()
        total_fields = total_problems + total_causes

        if total_fields == 0:
            return 0

        total_filled_causes = db.session.execute(
            select(count(distinct(CauseIndicatorDiagnosisModel.cause_id)))
            .where(CauseIndicatorDiagnosisModel.plan_id == plan_model.id)
        ).scalar()
        total_filled_problems = db.session.execute(
            select(count(distinct(ProblemDiagnosisModel.problem_id)))
            .where(ProblemDiagnosisModel.plan_id == plan_model.id)
        ).scalar()

        total_filled_fields = total_filled_problems + total_filled_causes
        return round((total_filled_fields / total_fields) * 100)

    def _calculate_tactical_dimension(plan_model: Optional[PlanModel]):
        if not plan_model:
            return 0

        total_fields = initiative_repo.count_prioritized_initiatives()
        if total_fields == 0:
            return 0
        total_filled_fields = db.session.execute(
            select(count(TacticalDimensionModel.id))
            .where(TacticalDimensionModel.plan_id == plan_model.id)
        ).scalar()

        return round((total_filled_fields / total_fields) * 100)

    def _calculate_strategic_dimension(plan_model: Optional[PlanModel]):
        total_macros = db.session.execute(
            select(count(distinct(MacroObjectiveProblemAssociationModel.macro_objective_id)))
            .select_from(MacroObjectiveProblemAssociationModel)
            .outerjoin(
                ProblemModel,
                ProblemModel.id == MacroObjectiveProblemAssociationModel.problem_id
            )
            .where(
                ProblemModel.prioritized == True
            )
        ).scalar()
        total_focuses = db.session.execute(
            select(count(distinct(FocusAssociationModel.focus_id)))
            .select_from(FocusAssociationModel)
            .outerjoin(CauseIndicatorModel, FocusAssociationModel.cause_indicator_id == CauseIndicatorModel.id)
            .outerjoin(CauseAndProblemAssociation, CauseAndProblemAssociation.cause_id == CauseIndicatorModel.cause_id)
            .where(
                CauseAndProblemAssociation.prioritized == True
            )
        ).scalar()
        total_fields = total_macros + total_focuses

        if total_fields == 0:
            return 0

        total_filled_macros = db.session.execute(
            select(count(distinct(MacroObjectiveGoalModel.macro_objective_id)))
            .select_from(MacroObjectiveGoalModel)
            .where(MacroObjectiveGoalModel.plan_id == plan_model.id)
        ).scalar()
        total_filled_focuses = db.session.execute(
            select(count(distinct(FocusGoalModel.focus_id)))
            .select_from(FocusGoalModel)
            .where(FocusGoalModel.plan_id == plan_model.id)
        ).scalar()

        total_filled_fields = total_filled_macros + total_filled_focuses
        return round((total_filled_fields / total_fields) * 100)

    output = dict(
        prioritizedProblems=problem_repo.count_prioritized_problems(),
        prioritizedCauses=cause_repo.count_prioritized_causes(),
        prioritizedInitiatives=initiative_repo.count_prioritized_initiatives(),
        basicInformation=None,
        diagnostic=None,
        tactical_dimension=None,
        strategic_dimension=None,
    )

    if plan_model:
        progress = dict(
            basicInformation=dict(
                progressPercentage=_calculate_bi_progress(plan_model),
                lastUpdate=plan_model.updated_at.isoformat()
            ),
            diagnostic=dict(
                progressPercentage=_calculate_diagnostic_progress(plan_model),
                lastUpdate=plan_model.diagnosis_updated_at and plan_model.diagnosis_updated_at.isoformat()
            ),
            tactical_dimension=dict(
                progressPercentage=_calculate_tactical_dimension(plan_model),
                lastUpdate=plan_model.tactical_dimension_updated_at and plan_model.tactical_dimension_updated_at.isoformat()
            ),
            strategic_dimension=dict(
                progressPercentage=_calculate_strategic_dimension(plan_model),
                lastUpdate=plan_model.strategic_dimension_updated_at and plan_model.strategic_dimension_updated_at.isoformat()
            )
        )
        output.update(progress)

    return output


def list_macro_objectives() -> List[MacroObjectiveDTO]:
    plan_id = repositories.get_last_plan_id()
    if plan_id:
        return repositories.list_macro_objectives_with_goals(plan_id)
    else:
        return repositories.list_macro_objectives()


def bulk_create_or_update_macro_objective_goals(
        macro_objective_id: int,
        create_or_update_macro_objective_goal_dto_ls: List[CreateOrUpdateMacroObjectiveGoalRequestDTO]
):
    plan_id = repositories.get_last_plan_id()
    if not plan_id:
        abort(
            HTTPStatus.BAD_REQUEST,
            f"Before creating a MacroObjectiveGoal you must create a Plan"
        )
    try:
        repositories.delete_unused_macro_objective_goals(
            plan_id,
            macro_objective_id,
            [item.id for item in create_or_update_macro_objective_goal_dto_ls if item.id]
        )

        for goal_dto in create_or_update_macro_objective_goal_dto_ls:
            if goal_dto.problem_id:
                is_valid = repositories.check_macro_objective_and_problem_are_related(
                    macro_objective_id,
                    goal_dto.problem_id
                )
                if not is_valid:
                    abort(
                        HTTPStatus.BAD_REQUEST,
                        f"Macro Objective and Problem are not related, macro_objective_id={macro_objective_id} problem_id={goal_dto.problem_id}"
                    )

            for custom_indicator_dto in goal_dto.custom_indicators:
                repositories.create_or_update_macro_objective_custom_indicator(macro_objective_id, custom_indicator_dto)

            repositories.create_or_update_macro_objective_goal(plan_id, macro_objective_id, goal_dto)

        repositories.update_strategic_dimension_updated_at(plan_id)
        db.session.commit()
    except:
        db.session.rollback()
        raise


def list_focuses() -> List[FocusListItemDTO]:
    plan_id = repositories.get_last_plan_id()
    return repositories.list_focuses(plan_id)


def update_focus_goals(
        macro_objective_id: int,
        focus_id: int,
        focus_goal_dto_ls: List[UpdateFocusGoalRequestDTO],
):
    plan_id = repositories.get_last_plan_id()
    try:
        for dto in focus_goal_dto_ls:
            for custom_indicator_dto in dto.custom_indicators:
                repositories.create_or_update_focus_custom_indicator(focus_id, custom_indicator_dto)
            repositories.create_or_update_focus_goal(plan_id, macro_objective_id, focus_id, dto)

        repositories.update_strategic_dimension_updated_at(plan_id)
        db.session.commit()
    except:
        db.session.rollback()
        raise


def list_problem_diagnosis():
    last_plan_id = repositories.get_last_plan_id()
    if not last_plan_id:
        return []
    return repositories.list_selected_macro_objective_indicator(last_plan_id)


def set_problem_diagnosis(
        set_diagnosis_dto_ls: List[SetDiagnosisToProblemIndRequestDTO]
):
    plan_id = repositories.get_last_plan_id()
    try:
        for dto in set_diagnosis_dto_ls:
            repositories.set_diagnosis_to_problem_indicator(plan_id, dto)
        repositories.update_diagnosis_updated_at(plan_id)
        db.session.commit()
    except:
        db.session.rollback()
        raise


def list_cause_diagnosis():
    last_plan_id = repositories.get_last_plan_id()
    if not last_plan_id:
        return []
    return repositories.list_cause_diagnoses(last_plan_id)


def set_cause_diagnosis(cause_id: int, set_diagnosis_dto_ls: List[SetDiagnosisToCauseIndRequestDTO]):
    plan_id = repositories.get_last_plan_id()
    if not plan_id:
        abort(
            HTTPStatus.BAD_REQUEST,
            f"Before creating a CauseDiagnosis you must create a Plan"
        )
    try:
        repositories.delete_cause_indicator_diagnoses(plan_id, cause_id)
        for dto in set_diagnosis_dto_ls:
            repositories.set_diagnosis_to_cause_indicator(plan_id, cause_id, dto)
        repositories.update_diagnosis_updated_at(plan_id)
        db.session.commit()
    except:
        db.session.rollback()
        raise


def list_tactical_dimensions():
    last_plan_id = repositories.get_last_plan_id()
    if not last_plan_id:
        return []
    return list(repositories.list_tactical_dimensions(last_plan_id))


def set_tactical_dimension(dto: SetTacticalDimensionDTO):
    plan_id = repositories.get_last_plan_id()
    if not plan_id:
        abort(
            HTTPStatus.BAD_REQUEST,
            f"Before creating a TacticalDimension you must create a Plan"
        )
    try:
        repositories.create_or_update_tactical_dimension(plan_id, dto)
        repositories.update_tactical_dimension_updated_at(plan_id)
        db.session.commit()
    except:
        db.session.rollback()
