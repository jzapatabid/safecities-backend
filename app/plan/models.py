from datetime import datetime
from typing import List

from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, REAL, ARRAY, TEXT, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship

from app.causes.models import CauseIndicatorModel, CauseModel
from app.commons.models.municipal_department_model import MunicipalDepartmentModel
from app.commons.models.neighborhood_model import NeighborhoodModel
from app.problems.models import ProblemModel
from db import db


class PlanModel(db.Model):
    __tablename__ = "plan"

    id = Column(Integer(), primary_key=True)
    title = Column(String(), nullable=True)
    start_at = Column(Date(), nullable=True)
    end_at = Column(Date(), nullable=True)

    created_at = Column(DateTime(), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    diagnosis_updated_at = Column(DateTime(), nullable=True)
    tactical_dimension_updated_at = Column(DateTime(), nullable=True)
    strategic_dimension_updated_at = Column(DateTime(), nullable=True)


class MacroObjectiveModel(db.Model):
    __tablename__ = "macro_objective"

    id = Column(Integer(), primary_key=True)
    name = Column(String(), nullable=False, unique=True)
    icon_name = Column(String(), nullable=True)

    custom_indicators: Mapped[List["MacroObjectiveCustomIndicatorModel"]] = relationship()
    problems: Mapped[List["ProblemModel"]] = relationship(
        secondary="macro_objective_problem_association",
    )
    prioritized_problems: Mapped[List["ProblemModel"]] = relationship(
        secondary="macro_objective_problem_association",
        primaryjoin="MacroObjectiveProblemAssociationModel.macro_objective_id == MacroObjectiveModel.id",
        secondaryjoin="""and_(
            MacroObjectiveProblemAssociationModel.problem_id == ProblemModel.id,
            ProblemModel.prioritized == True
        )""",
        viewonly=True
    )


class MacroObjectiveProblemAssociationModel(db.Model):
    __tablename__ = "macro_objective_problem_association"

    macro_objective_id = Column(ForeignKey(MacroObjectiveModel.__tablename__ + ".id"), primary_key=True)
    problem_id = Column(ForeignKey("problem.id"), primary_key=True, unique=True)

    macro_objective: Mapped["MacroObjectiveModel"] = relationship()


class MacroObjectiveGoalModel(db.Model):
    __tablename__ = "macro_objective_goal"
    # __table_args__ = (
    #     ForeignKeyConstraint(
    #         [
    #             "macro_objective_id",
    #             "problem_id"
    #         ],
    #         [
    #             MacroObjectiveProblemAssociationModel.__tablename__ + ".macro_objective_id",
    #             MacroObjectiveProblemAssociationModel.__tablename__ + ".problem_id"
    #         ],
    #     ),
    # )

    id = Column(Integer(), primary_key=True, autoincrement=True)

    plan_id = Column(ForeignKey(PlanModel.__tablename__ + ".id"), nullable=False)
    macro_objective_id = Column(ForeignKey(MacroObjectiveModel.__tablename__ + ".id"), nullable=False)

    problem_id = Column(Integer(), nullable=True)
    custom_indicator_id = Column(ForeignKey("macro_objetive_custom_indicator" + ".id"), nullable=True)

    initial_rate = Column(REAL(precision=2), nullable=False)
    goal_value = Column(REAL(precision=2), nullable=False)
    goal_justification = Column(String(), nullable=False)
    end_at = Column(Date(), nullable=False)

    macro_objective: Mapped["MacroObjectiveModel"] = relationship()


class FocusModel(db.Model):
    __tablename__ = "focus"

    id = Column(Integer(), primary_key=True)
    name = Column(String(), nullable=False, unique=True)
    icon_name = Column(String(), nullable=True)

    custom_indicators: Mapped[List["FocusCustomIndicatorModel"]] = relationship()


class FocusAssociationModel(db.Model):
    __tablename__ = "focus_association"

    focus_id = Column(ForeignKey(FocusModel.__tablename__ + ".id"), primary_key=True)
    macro_objective_id = Column(ForeignKey(MacroObjectiveModel.__tablename__ + ".id"), primary_key=True)
    cause_indicator_id = Column(ForeignKey("cause_indicator.id"), primary_key=True)

    macro_objective: Mapped["MacroObjectiveModel"] = relationship()
    focus: Mapped["FocusModel"] = relationship()


class FocusGoalModel(db.Model):
    __tablename__ = "focus_goal"
    # __table_args__ = (
    #     ForeignKeyConstraint(
    #         [
    #             "macro_objective_id",
    #             "focus_id",
    #             "cause_indicator_id"
    #         ],
    #         [
    #             FocusAssociationModel.__tablename__ + ".macro_objective_id",
    #             FocusAssociationModel.__tablename__ + ".focus_id",
    #             FocusAssociationModel.__tablename__ + ".cause_indicator_id",
    #         ],
    #     ),
    # )

    id = Column(Integer(), primary_key=True, autoincrement=True)

    plan_id = Column(ForeignKey(PlanModel.__tablename__ + ".id"), nullable=False)
    macro_objective_id = Column(Integer(), nullable=False)
    focus_id = Column(Integer(), nullable=False)

    cause_indicator_id = Column(ForeignKey("cause_indicator.id"), nullable=True)
    custom_indicator_id = Column(ForeignKey("focus_custom_indicator" + ".id"), nullable=True)

    initial_rate = Column(REAL(precision=2), nullable=False)
    goal_value = Column(REAL(precision=2), nullable=False)
    goal_justification = Column(String(), nullable=False)
    end_at = Column(Date(), nullable=False)

    # focus: Mapped["FocusModel"] = relationship()


class MacroObjectiveCustomIndicatorModel(db.Model):
    __tablename__ = "macro_objetive_custom_indicator"

    macro_objective_id = Column(ForeignKey(MacroObjectiveModel.__tablename__ + ".id"), nullable=False)

    id = Column(String(), primary_key=True)
    name = Column(String(), nullable=False)
    formula_description = Column(String(), nullable=False)
    unit_metric = Column(String(), nullable=False)
    source = Column(String(), nullable=False)
    frequency = Column(String(), nullable=False)
    baseline_value = Column(REAL(precision=2), nullable=False)
    baseline_year = Column(Integer(), nullable=False)
    observation = Column(String(), nullable=True)


class FocusCustomIndicatorModel(db.Model):
    __tablename__ = "focus_custom_indicator"

    focus_id = Column(ForeignKey(FocusModel.__tablename__ + ".id"), nullable=False)

    id = Column(String(), primary_key=True)
    name = Column(String(), nullable=False)
    formula_description = Column(String(), nullable=False)
    unit_metric = Column(String(), nullable=False)
    source = Column(String(), nullable=False)
    frequency = Column(String(), nullable=False)
    baseline_value = Column(REAL(precision=2), nullable=False)
    baseline_year = Column(Integer(), nullable=False)
    observation = Column(String(), nullable=True)


class ProblemDiagnosisModel(db.Model):
    __tablename__ = "problem_diagnosis"
    __table_args__ = (
        UniqueConstraint("plan_id", "problem_id", ),
    )

    id = Column(Integer(), primary_key=True)
    plan_id = Column(ForeignKey(PlanModel.__tablename__ + ".id"), nullable=False)
    problem_id = Column(ForeignKey(ProblemModel.__tablename__ + ".id"), nullable=False)

    kpi_graphs = Column(ARRAY(String()), default=list, nullable=False)
    diagnosis = Column(TEXT(), nullable=False)

    problem: Mapped["ProblemModel"] = relationship()


class CauseIndicatorDiagnosisModel(db.Model):
    __tablename__ = "cause_indicator_diagnosis"
    __table_args__ = (
        UniqueConstraint("plan_id", "cause_id", "cause_indicator_id", ),
    )

    id = Column(Integer(), primary_key=True)
    plan_id = Column(ForeignKey(PlanModel.__tablename__ + ".id"), nullable=False)
    cause_id = Column(ForeignKey(CauseModel.__tablename__ + ".id"), nullable=False)
    cause_indicator_id = Column(ForeignKey(CauseIndicatorModel.__tablename__ + ".id"), nullable=False)

    kpi_graphs = Column(ARRAY(String()), default=list, nullable=False)
    diagnosis = Column(TEXT(), nullable=False)


class TacticalDimensionGoalModel(db.Model):
    __tablename__ = "tactical_dimension_goal"

    id = Column(Integer(), primary_key=True)
    tactical_dimension_id = Column(ForeignKey("tactical_dimension.id"), nullable=False)
    initiative_outcome_id = Column(ForeignKey("initiative_outcome.id"), nullable=False)
    goal = Column(REAL(precision=2), nullable=False)
    date = Column(Date(), nullable=False)

    initiative_outcome: Mapped["InitiativeOutcomeModel"] = relationship()


class TacticalDimensionDepartmentRoleModel(db.Model):
    __tablename__ = "tactical_dimension_department_role"

    id = Column(Integer(), primary_key=True)
    tactical_dimension_id = Column(ForeignKey("tactical_dimension.id"), nullable=False)
    department_id = Column(ForeignKey("municipal_department.id"), nullable=False)
    role = Column(String(), nullable=False)

    department: Mapped["MunicipalDepartmentModel"] = relationship()


class TacticalDimensionModel(db.Model):
    __tablename__ = "tactical_dimension"

    id = Column(Integer(), primary_key=True)
    plan_id = Column(ForeignKey(PlanModel.__tablename__ + ".id"), nullable=False)
    initiative_id = Column(ForeignKey("initiative.id", ondelete="CASCADE"), nullable=False)

    diagnosis = Column(TEXT(), nullable=False)
    neighborhood_id = Column(ForeignKey(NeighborhoodModel.__tablename__ + ".id"), nullable=False)
    sociodemographic_targeting = Column(TEXT(), nullable=False)
    start_at = Column(Date(), nullable=False)
    end_at = Column(Date(), nullable=False)
    total_cost = Column(REAL(precision=2), nullable=False)

    goals: Mapped[List["TacticalDimensionGoalModel"]] = relationship()
    department_roles: Mapped[List[TacticalDimensionDepartmentRoleModel]] = relationship()

    initiative: Mapped["InitiativeModel"] = relationship()
    neighborhood: Mapped["NeighborhoodModel"] = relationship()
