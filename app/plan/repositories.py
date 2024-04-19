from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func, exists, tuple_, delete, not_, desc, and_, update
from sqlalchemy.orm import aliased

from app.cause_problem_association.models import CauseAndProblemAssociation
from app.causes.models import CauseIndicatorModel, CauseModel
from app.initiatives.models import InitiativeModel, InitiativePrioritizationModel
from app.plan.dto import MacroObjectiveDTO, CreateOrUpdateMacroObjectiveGoalRequestDTO, \
    CreateOrUpdatePlanRequestDTO, FocusListItemDTO, UpdateFocusGoalRequestDTO, \
    ProblemDiagnosisListItemDTO, SetDiagnosisToProblemIndRequestDTO, \
    FocusIndicatorIncludedInPLanListItemDTO, SetDiagnosisToCauseIndRequestDTO, TacticalDimensionListItemDTO, \
    SetTacticalDimensionDTO
from app.plan.models import PlanModel, MacroObjectiveModel, \
    MacroObjectiveProblemAssociationModel, FocusModel, FocusAssociationModel, FocusGoalModel, \
    MacroObjectiveCustomIndicatorModel, MacroObjectiveGoalModel, FocusCustomIndicatorModel, \
    ProblemDiagnosisModel, CauseIndicatorDiagnosisModel, TacticalDimensionModel, TacticalDimensionDepartmentRoleModel, \
    TacticalDimensionGoalModel
from app.problems.models import ProblemModel
from db import db


def get_last_plan_id() -> Optional[int]:
    query = (
        select(func.max(PlanModel.id))
        .select_from(PlanModel)
    )
    return db.session.execute(query).scalar()


def get_last_plan() -> Optional[PlanModel]:
    query = (
        select(PlanModel)
        .order_by(desc(PlanModel.id))
        .limit(1)
    )
    return db.session.execute(query).scalar()


def get_plan(plan_id: int):
    query = (
        select(PlanModel)
        .where(PlanModel.id == plan_id)
        .limit(1)
    )
    return db.session.execute(query).scalar()


def create_plan(dto: CreateOrUpdatePlanRequestDTO):
    plan_model = PlanModel(
        title=dto.title,
        start_at=dto.start_at,
        end_at=dto.end_at,
    )
    db.session.add(plan_model)


def update_plan(plan_id: int, dto: CreateOrUpdatePlanRequestDTO):
    select_query = select(PlanModel).where(PlanModel.id == plan_id)
    plan_model = db.session.execute(select_query).scalar()
    if plan_model:
        plan_model.title = dto.title
        plan_model.start_at = dto.start_at
        plan_model.end_at = dto.end_at
        db.session.merge(plan_model)


def list_macro_objectives():
    query = select(
        MacroObjectiveModel.id,
        MacroObjectiveModel.name,
        MacroObjectiveModel.icon_name,
    )
    rs = db.session.execute(query).all()
    return [
        MacroObjectiveDTO(
            id=macro_objective_id,
            name=macro_objective_name,
            icon_name=macro_objective_icon_name,
        )
        for macro_objective_id, macro_objective_name, macro_objective_icon_name in rs
    ]


def list_macro_objectives_with_goals(plan_id: int) -> List[MacroObjectiveDTO]:
    macro_query = (
        select(
            MacroObjectiveModel
        ).select_from(MacroObjectiveModel)
    )
    macro_rs = db.session.execute(macro_query).scalars()

    problem_query = (
        select(
            MacroObjectiveProblemAssociationModel.macro_objective_id,
            ProblemModel
        )
        .select_from(MacroObjectiveProblemAssociationModel)
        .outerjoin(ProblemModel, ProblemModel.id == MacroObjectiveProblemAssociationModel.problem_id)
        .where(ProblemModel.prioritized == True)
    )
    problem_rs = db.session.execute(problem_query).all()

    macro_goal_query = (
        select(
            MacroObjectiveGoalModel.macro_objective_id,
            MacroObjectiveGoalModel,
        ).select_from(MacroObjectiveGoalModel)
        .outerjoin(ProblemModel, ProblemModel.id == MacroObjectiveGoalModel.problem_id)
        .where(
            MacroObjectiveGoalModel.plan_id == plan_id,
            ProblemModel.prioritized == True
        )
    )
    macro_goal_query2 = (
        select(
            MacroObjectiveGoalModel.macro_objective_id,
            MacroObjectiveGoalModel,
        ).select_from(MacroObjectiveGoalModel)
        .where(
            MacroObjectiveGoalModel.plan_id == plan_id,
            MacroObjectiveGoalModel.problem_id == None
        )
    )
    macro_goal_rs = db.session.execute(macro_goal_query).all()
    macro_goal_rs += db.session.execute(macro_goal_query2).all()

    output = dict()

    for macro_objective_model in macro_rs:
        macro_objective_dto = MacroObjectiveDTO(
            id=macro_objective_model.id,
            name=macro_objective_model.name,
            icon_name=macro_objective_model.icon_name,
        )
        for custom_indicator_model in macro_objective_model.custom_indicators:
            macro_objective_dto.custom_indicators.append(
                MacroObjectiveDTO.CustomIndicatorDTO(
                    id=custom_indicator_model.id,
                    name=custom_indicator_model.name,
                    formula_description=custom_indicator_model.formula_description,
                    unit_metric=custom_indicator_model.unit_metric,
                    source=custom_indicator_model.source,
                    frequency=custom_indicator_model.frequency,
                    baseline_value=custom_indicator_model.baseline_value,
                    baseline_year=custom_indicator_model.baseline_year,
                    observation=custom_indicator_model.observation,
                )
            )

        output[macro_objective_model.id] = macro_objective_dto

    for macro_objective_id, problem_model in problem_rs:
        macro_dto: MacroObjectiveDTO = output[macro_objective_id]
        problem_dto = MacroObjectiveDTO.ProblemDTO(
            id=problem_model.id,
            name=problem_model.indicator_name
        )
        macro_dto.problems.append(problem_dto)

    for macro_objective_id, macro_goal_model in macro_goal_rs:
        macro_dto: MacroObjectiveDTO = output[macro_objective_id]
        macro_goal_model: MacroObjectiveGoalModel
        macro_goal_dto = MacroObjectiveDTO.GoalDTO(
            id=macro_goal_model.id,
            problem_id=macro_goal_model.problem_id,
            custom_indicator_id=macro_goal_model.custom_indicator_id,
            initial_rate=macro_goal_model.initial_rate,
            goal_value=macro_goal_model.goal_value,
            goal_justification=macro_goal_model.goal_justification,
            end_at=macro_goal_model.end_at,
        )
        macro_dto.goals.append(macro_goal_dto)

    return list(output.values())


def delete_unused_macro_objective_goals(
        plan_id: int,
        macro_objective_id: int,
        goal_ids_in_use: List[int]
):
    query = delete(MacroObjectiveGoalModel).where(
        MacroObjectiveGoalModel.plan_id == plan_id,
        MacroObjectiveGoalModel.macro_objective_id == macro_objective_id,
    )
    if goal_ids_in_use:
        query = query.where(
            not_(MacroObjectiveGoalModel.id.in_(goal_ids_in_use)),
        )
    db.session.execute(query)


def create_or_update_macro_objective_goal(
        plan_id: int,
        macro_objective_id: int,
        create_macro_objective_goal_dto: CreateOrUpdateMacroObjectiveGoalRequestDTO
) -> MacroObjectiveGoalModel:
    model = MacroObjectiveGoalModel(
        plan_id=plan_id,
        macro_objective_id=macro_objective_id,
        problem_id=create_macro_objective_goal_dto.problem_id,
        custom_indicator_id=create_macro_objective_goal_dto.custom_indicator_id,

        initial_rate=create_macro_objective_goal_dto.initial_rate,
        goal_value=create_macro_objective_goal_dto.goal_value,
        goal_justification=create_macro_objective_goal_dto.goal_justification,
        end_at=create_macro_objective_goal_dto.end_at,
    )
    if create_macro_objective_goal_dto.id:
        model.id = create_macro_objective_goal_dto.id
        db.session.merge(model)
    else:
        db.session.add(model)
        db.session.flush()
    return model


def create_or_update_macro_objective_custom_indicator(
        macro_objective_id: int,
        dto: CreateOrUpdateMacroObjectiveGoalRequestDTO.CustomIndicatorDTO
) -> MacroObjectiveCustomIndicatorModel:
    model = MacroObjectiveCustomIndicatorModel(
        macro_objective_id=macro_objective_id,
        id=str(dto.id),

        name=dto.name,
        formula_description=dto.formula_description,
        unit_metric=dto.unit_metric,
        source=dto.source,
        frequency=dto.frequency,
        baseline_value=dto.baseline_value,
        baseline_year=dto.baseline_year,
        observation=dto.observation,
    )
    db.session.merge(model)
    return model


def check_macro_objective_and_problem_are_related(macro_objective_id: int, problem_id: int):
    query = select(exists().where(
        MacroObjectiveProblemAssociationModel.macro_objective_id == macro_objective_id,
        MacroObjectiveProblemAssociationModel.problem_id == problem_id,
    ))
    return db.session.execute(query).scalar()


def find_macro_objective_problem_association(items):
    where_conditions = [
        tuple_(MacroObjectiveProblemAssociationModel.macro_objective_id,
               MacroObjectiveProblemAssociationModel.problem_id) == (macro_objective_id, problem_id)
        for macro_objective_id, problem_id in items
    ]
    query = select(
        MacroObjectiveProblemAssociationModel.macro_objective_id,
        MacroObjectiveProblemAssociationModel.problem_id
    )
    query = query.filter(tuple_(*where_conditions))
    return db.session.execute(query).all()


def list_focuses(plan_id: int) -> List[FocusListItemDTO]:
    macro_query = (
        select(
            MacroObjectiveModel
        ).select_from(MacroObjectiveModel)
    )
    macro_rs = db.session.execute(macro_query).scalars()

    macro_goal_query = (
        select(
            MacroObjectiveGoalModel.macro_objective_id,
            MacroObjectiveGoalModel,
            ProblemModel
        ).select_from(MacroObjectiveGoalModel)
        .outerjoin(ProblemModel, ProblemModel.id == MacroObjectiveGoalModel.problem_id)
        .where(
            MacroObjectiveGoalModel.plan_id == plan_id,
            ProblemModel.prioritized == True
        )
    )
    macro_goal_rs = db.session.execute(macro_goal_query).all()

    focus_query = (
        select(
            FocusAssociationModel.macro_objective_id,
            FocusModel
        ).select_from(FocusAssociationModel)
        .join(FocusModel, FocusModel.id == FocusAssociationModel.focus_id)
        .group_by(
            FocusAssociationModel.macro_objective_id,
            FocusModel
        )
    )
    focus_rs = db.session.execute(focus_query).all()

    focus_goal_query = (
        select(
            FocusGoalModel
        )
        .where(FocusGoalModel.plan_id == plan_id)
        .where(
            exists().where(
                CauseIndicatorModel.id == FocusGoalModel.cause_indicator_id,
                CauseAndProblemAssociation.cause_id == CauseIndicatorModel.cause_id,
                CauseAndProblemAssociation.prioritized == True
            ) == True
        )
    )
    focus_goal_query2 = (
        select(
            FocusGoalModel,
        ).select_from(FocusGoalModel)
        .where(
            FocusGoalModel.plan_id == plan_id,
            FocusGoalModel.cause_indicator_id == None,
        )
    )
    focus_goal_rs = list(db.session.execute(focus_goal_query).scalars())
    focus_goal_rs += list(db.session.execute(focus_goal_query2).scalars())

    cause_indicator_query = (
        select(
            FocusAssociationModel.macro_objective_id,
            FocusAssociationModel.focus_id,
            CauseIndicatorModel,

        )
        .select_from(FocusAssociationModel)
        .join(CauseIndicatorModel, CauseIndicatorModel.id == FocusAssociationModel.cause_indicator_id)
        .where(
            exists().where(
                CauseAndProblemAssociation.cause_id == CauseIndicatorModel.cause_id,
                CauseAndProblemAssociation.prioritized == True
            ) == True
        )
    )
    cause_indicator_rs = db.session.execute(cause_indicator_query).all()

    problem_query = (
        select(
            MacroObjectiveProblemAssociationModel.macro_objective_id,
            ProblemModel
        )
        .select_from(MacroObjectiveProblemAssociationModel)
        .outerjoin(ProblemModel, ProblemModel.id == MacroObjectiveProblemAssociationModel.problem_id)
        .where(ProblemModel.prioritized == True)
    )
    problem_rs = db.session.execute(problem_query).all()

    output = dict()
    focus_goal_dict = dict()
    cause_ind_dict = dict()

    for macro_objective_model in macro_rs:
        focus_list_dto = FocusListItemDTO(
            id=macro_objective_model.id,
            name=macro_objective_model.name,
            icon_name=macro_objective_model.icon_name,
        )
        output[macro_objective_model.id] = focus_list_dto

    for macro_objective_id, macro_goal_model, problem_model in macro_goal_rs:
        focus_list_dto = output[macro_objective_id]
        macro_goal_dto = FocusListItemDTO.MacroObjectiveGoalDTO(
            problem_id=macro_goal_model.problem_id,
            problem_name=problem_model.name,
            initial_rate=macro_goal_model.initial_rate,
            goal_value=macro_goal_model.goal_value,
            goal_justification=macro_goal_model.goal_justification,
            end_at=macro_goal_model.end_at,
        )
        focus_list_dto.goals.append(macro_goal_dto)

    for macro_objective_id, problem_model in problem_rs:
        focus_list_dto = output[macro_objective_id]
        problem_dto = FocusListItemDTO.ProblemDTO(
            id=problem_model.id,
            name=problem_model.indicator_name
        )
        focus_list_dto.problems.append(problem_dto)

    for focus_goal_model in focus_goal_rs:
        focus_goal_model: FocusGoalModel
        key = f"{focus_goal_model.macro_objective_id}-{focus_goal_model.focus_id}"
        temp_ls = focus_goal_dict.get(key, list())
        focus_goal_dto = FocusListItemDTO.FocusDTO.FocusGoalDTO(
            focus_id=focus_goal_model.focus_id,
            cause_indicator_id=focus_goal_model.cause_indicator_id,
            custom_indicator_id=focus_goal_model.custom_indicator_id,
            initial_rate=focus_goal_model.initial_rate,
            goal_value=focus_goal_model.goal_value,
            goal_justification=focus_goal_model.goal_justification,
            end_at=focus_goal_model.end_at,
        )
        temp_ls.append(focus_goal_dto)
        focus_goal_dict[key] = temp_ls

    for macro_objective_id, focus_id, cause_indicator_model in cause_indicator_rs:
        cause_indicator_model: CauseIndicatorModel
        key = f"{macro_objective_id}-{focus_id}"
        temp_ls = cause_ind_dict.get(key, list())
        cause_ind_dto = FocusListItemDTO.FocusDTO.CauseIndicatorDTO(
            id=cause_indicator_model.id,
            name=cause_indicator_model.name,
        )
        temp_ls.append(cause_ind_dto)
        cause_ind_dict[key] = temp_ls

    for macro_objective_id, focus_model in focus_rs:
        focus_list_dto = output[macro_objective_id]
        focus_goal_dto_ls = focus_goal_dict.get(f"{macro_objective_id}-{focus_model.id}", list())
        cause_ind_dto_ls = cause_ind_dict.get(f"{macro_objective_id}-{focus_model.id}", list())
        focus_dto = FocusListItemDTO.FocusDTO(
            id=focus_model.id,
            name=focus_model.name,
            icon_name=focus_model.icon_name,
            goals=focus_goal_dto_ls,
            cause_indicators=cause_ind_dto_ls,
        )

        for custom_indicator_model in focus_model.custom_indicators:
            focus_dto.custom_indicators.append(
                FocusListItemDTO.FocusDTO.CustomIndicatorDTO(
                    id=custom_indicator_model.id,
                    name=custom_indicator_model.name,
                    formula_description=custom_indicator_model.formula_description,
                    unit_metric=custom_indicator_model.unit_metric,
                    source=custom_indicator_model.source,
                    frequency=custom_indicator_model.frequency,
                    baseline_value=custom_indicator_model.baseline_value,
                    baseline_year=custom_indicator_model.baseline_year,
                    observation=custom_indicator_model.observation,
                )
            )

        focus_list_dto.focuses.append(focus_dto)

    return list(output.values())


def create_or_update_focus_goal(plan_id: int, macro_objective_id: int, focus_id: int, dto: UpdateFocusGoalRequestDTO):
    model = FocusGoalModel(
        plan_id=plan_id,
        macro_objective_id=macro_objective_id,
        focus_id=focus_id,

        cause_indicator_id=dto.cause_indicator_id,
        custom_indicator_id=dto.custom_indicator_id,

        initial_rate=dto.initial_rate,
        goal_value=dto.goal_value,
        goal_justification=dto.goal_justification,
        end_at=dto.end_at,
    )
    if dto.id:
        model.id = dto.id
        db.session.merge(model)
    else:
        db.session.add(model)
        db.session.flush()
    return model


def create_or_update_focus_custom_indicator(
        focus_id: int,
        dto: UpdateFocusGoalRequestDTO.CustomIndicatorDTO
) -> MacroObjectiveCustomIndicatorModel:
    model = FocusCustomIndicatorModel(
        focus_id=focus_id,
        id=str(dto.id),

        name=dto.name,
        formula_description=dto.formula_description,
        unit_metric=dto.unit_metric,
        source=dto.source,
        frequency=dto.frequency,
        baseline_value=dto.baseline_value,
        baseline_year=dto.baseline_year,
        observation=dto.observation,
    )
    db.session.merge(model)
    return model


def list_selected_macro_objective_indicator(last_plan_id: int):
    query = (
        select(
            ProblemModel,
            ProblemDiagnosisModel,
        )
        .outerjoin(
            ProblemDiagnosisModel,
            and_(
                ProblemDiagnosisModel.plan_id == last_plan_id,
                ProblemDiagnosisModel.problem_id == ProblemModel.id
            )
        )
        .where(
            ProblemModel.prioritized == True
        )
    )

    query_result = db.session.execute(query).all()

    output = list()
    for problem_model, diagnosis_model in query_result:
        output.append(
            ProblemDiagnosisListItemDTO(
                problem_id=problem_model.id,
                problem_name=problem_model.name,
                problem_is_default=problem_model.is_default,
                diagnosis=diagnosis_model and diagnosis_model.diagnosis,
                kpi_graphs=diagnosis_model.kpi_graphs if diagnosis_model else list(),
            )
        )

    return output


def set_diagnosis_to_problem_indicator(
        plan_id: Optional[int],
        dto: SetDiagnosisToProblemIndRequestDTO
):
    diagnosis_model = db.session.execute(
        select(ProblemDiagnosisModel)
        .where(
            ProblemDiagnosisModel.plan_id == plan_id,
            ProblemDiagnosisModel.problem_id == dto.problem_id,
        )
        .limit(1)
    ).scalar()
    if diagnosis_model:
        diagnosis_model.kpi_graphs = dto.diagnosis_graphs
        diagnosis_model.diagnosis = dto.diagnosis
    else:
        diagnosis_model = ProblemDiagnosisModel(
            plan_id=plan_id,
            problem_id=dto.problem_id,
            kpi_graphs=dto.diagnosis_graphs,
            diagnosis=dto.diagnosis,
        )
        db.session.add(diagnosis_model)


def delete_problem_indicator_diagnoses(plan_id: int):
    query = (
        delete(ProblemDiagnosisModel)
        .where(
            ProblemDiagnosisModel.plan_id == plan_id
        )
    )
    db.session.execute(query)


def list_cause_diagnoses(last_plan_id: int):
    prioritized_causes_subquery = (
        select(CauseModel)
        .where(
            exists().where(
                CauseAndProblemAssociation.cause_id == CauseModel.id,
                CauseAndProblemAssociation.prioritized == True,
            ).correlate(CauseModel)
        )
        .subquery()
    )

    prioritized_causes_subquery = aliased(CauseModel, prioritized_causes_subquery)

    query = (
        select(prioritized_causes_subquery, CauseIndicatorModel, CauseIndicatorDiagnosisModel)
        .select_from(prioritized_causes_subquery)
        .outerjoin(
            CauseIndicatorModel,
            CauseIndicatorModel.cause_id == prioritized_causes_subquery.id
        )
        .outerjoin(
            CauseIndicatorDiagnosisModel,
            and_(
                CauseIndicatorDiagnosisModel.plan_id == last_plan_id,
                CauseIndicatorDiagnosisModel.cause_id == prioritized_causes_subquery.id,
                CauseIndicatorDiagnosisModel.cause_indicator_id == CauseIndicatorModel.id
            )
        )
        .where(
            CauseIndicatorModel.id != None
        )
    )

    query_result = db.session.execute(query).all()

    output = dict()
    for cause_model, cause_ind_model, diagnosis_model in query_result:
        dto = output.get(
            cause_model.id,
            FocusIndicatorIncludedInPLanListItemDTO(
                cause_id=cause_model.id,
                cause_name=cause_model.name,
            )
        )
        output[cause_model.id] = dto

        dto.cause_indicators.append(
            FocusIndicatorIncludedInPLanListItemDTO.CauseIndicatorDTO(
                cause_indicator_id=cause_ind_model.id,
                cause_indicator_name=cause_ind_model.name,
            )
        )

        if diagnosis_model:
            dto.diagnoses.append(
                FocusIndicatorIncludedInPLanListItemDTO.DiagnosisDTO(
                    cause_indicator_id=cause_ind_model.id,
                    diagnosis=diagnosis_model.diagnosis,
                    kpi_graphs=diagnosis_model.kpi_graphs,
                )
            )

    return list(output.values())


def set_diagnosis_to_cause_indicator(plan_id, cause_id, dto: SetDiagnosisToCauseIndRequestDTO):
    diagnosis_model = CauseIndicatorDiagnosisModel(
        plan_id=plan_id,
        cause_id=cause_id,
        cause_indicator_id=dto.cause_indicator_id,
        kpi_graphs=dto.kpi_graphs,
        diagnosis=dto.diagnosis,
    )
    db.session.merge(diagnosis_model)


def delete_cause_indicator_diagnoses(plan_id: int, cause_id: int):
    query = (
        delete(CauseIndicatorDiagnosisModel)
        .where(
            CauseIndicatorDiagnosisModel.plan_id == plan_id,
            CauseIndicatorDiagnosisModel.cause_id == cause_id,
        )
    )
    db.session.execute(query)


def list_tactical_dimensions(last_plan_id: int):
    tactical_dim_subquery = aliased(
        TacticalDimensionModel,
        (
            select(TacticalDimensionModel)
            .where(TacticalDimensionModel.plan_id == last_plan_id)
            .subquery()
        )
    )

    prioritized_initiatives_subquery = (
        select(InitiativeModel)
        .where(exists().where(InitiativePrioritizationModel.initiative_id == InitiativeModel.id) == True)
        .subquery()
    )
    prioritized_initiatives_subquery = aliased(InitiativeModel, prioritized_initiatives_subquery)

    query = (
        select(prioritized_initiatives_subquery, tactical_dim_subquery)
        .select_from(prioritized_initiatives_subquery)
        .outerjoin(tactical_dim_subquery, tactical_dim_subquery.initiative_id == prioritized_initiatives_subquery.id)
    )

    query_rs = db.session.execute(query).all()

    for initiative_model, tactical_dim_model in query_rs:
        dto = TacticalDimensionListItemDTO(
            initiative_id=initiative_model.id,
            initiative_name=initiative_model.name,
            total_macro_objectives=len(initiative_model.associated_macro_objectives),
            total_focuses=len(initiative_model.associated_focuses),
        )
        dto.tactical_dimension = TacticalDimensionListItemDTO.TacticalDimensionDTO()
        if tactical_dim_model:
            tactical_dim_model: TacticalDimensionModel
            dto.tactical_dimension = TacticalDimensionListItemDTO.TacticalDimensionDTO(
                id=tactical_dim_model.id,
                start_at=tactical_dim_model.start_at,
                end_at=tactical_dim_model.end_at,
                diagnosis=tactical_dim_model.diagnosis,
                sociodemographic_targeting=tactical_dim_model.sociodemographic_targeting,
                total_cost=tactical_dim_model.total_cost,
                neighborhood_id=tactical_dim_model.neighborhood_id,
                goals=[
                    TacticalDimensionListItemDTO.TacticalDimensionDTO.GoalDTO(
                        id=goal_model.id,
                        initiative_outcome_id=goal_model.initiative_outcome_id,
                        goal=goal_model.goal,
                        date=goal_model.date,
                    )
                    for goal_model in tactical_dim_model.goals
                ],
                department_roles=[
                    TacticalDimensionListItemDTO.TacticalDimensionDTO.DepartmentRoleDTO(
                        id=deparment_role_model.id,
                        department_id=deparment_role_model.department_id,
                        role=deparment_role_model.role,
                    )
                    for deparment_role_model in tactical_dim_model.department_roles
                ]
            )

        yield dto


def create_or_update_tactical_dimension(plan_id: int, dto: SetTacticalDimensionDTO):
    preexisting_id = db.session.execute(
        select(TacticalDimensionModel.id)
        .where(
            TacticalDimensionModel.plan_id == plan_id,
            TacticalDimensionModel.initiative_id == dto.initiative_id,
        )
        .limit(1)
    ).scalar()

    tactical_dim_model = TacticalDimensionModel(
        id=preexisting_id,
        plan_id=plan_id,
        initiative_id=dto.initiative_id,
        diagnosis=dto.diagnosis,
        neighborhood_id=dto.neighborhood_id,
        sociodemographic_targeting=dto.sociodemographic_targeting,
        start_at=dto.start_at,
        end_at=dto.end_at,
        total_cost=dto.total_cost,
    )
    if tactical_dim_model.id:
        db.session.merge(tactical_dim_model)
        db.session.execute(
            delete(TacticalDimensionDepartmentRoleModel).where(
                TacticalDimensionDepartmentRoleModel.tactical_dimension_id == tactical_dim_model.id
            )
        )
        db.session.execute(
            delete(TacticalDimensionGoalModel).where(
                TacticalDimensionGoalModel.tactical_dimension_id == tactical_dim_model.id
            )
        )
    else:
        db.session.add(tactical_dim_model)
        db.session.flush()

    for department_role_dto in dto.department_roles:
        department_role_model = TacticalDimensionDepartmentRoleModel(
            tactical_dimension_id=tactical_dim_model.id,
            department_id=department_role_dto.department_id,
            role=department_role_dto.role,
        )
        db.session.add(department_role_model)

    for goal_dto in dto.goals:
        goal_model = TacticalDimensionGoalModel(
            tactical_dimension_id=tactical_dim_model.id,
            initiative_outcome_id=goal_dto.initiative_outcome_id,
            goal=goal_dto.goal,
            date=goal_dto.date,
        )
        db.session.add(goal_model)

    return tactical_dim_model


def update_diagnosis_updated_at(plan_id: int):
    db.session.execute(
        update(PlanModel)
        .where(PlanModel.id == plan_id)
        .values(diagnosis_updated_at=datetime.utcnow())
    )


def update_tactical_dimension_updated_at(plan_id: int):
    db.session.execute(
        update(PlanModel)
        .where(PlanModel.id == plan_id)
        .values(tactical_dimension_updated_at=datetime.utcnow())
    )


def update_strategic_dimension_updated_at(plan_id: int):
    db.session.execute(
        update(PlanModel)
        .where(PlanModel.id == plan_id)
        .values(strategic_dimension_updated_at=datetime.utcnow())
    )
