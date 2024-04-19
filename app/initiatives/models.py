from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Table, DateTime, ARRAY, select
from sqlalchemy.orm import relationship, Mapped

from app.causes.models import CauseModel
from db import db

municipal_department_per_initiative_association_table = Table(
    "municipal_department_per_initiative",
    db.metadata,
    Column("municipal_department_id", ForeignKey("municipal_department.id"), primary_key=True),
    Column("initiative_id", ForeignKey("initiative.id", ondelete="CASCADE"), primary_key=True),
)


class InitiativeModel(db.Model):
    __tablename__ = "initiative"

    id = Column(Integer(), primary_key=True)
    code = Column(String(), nullable=True)
    name = Column(String(), nullable=False, unique=True)
    justification = Column(String(), nullable=False)
    evidences = Column(String(), nullable=False)
    cost_level = Column(Integer(), nullable=True)
    efficiency_level = Column(Integer(), nullable=False)
    associated_causes: Mapped[List["InitiativeCauseAssociationModel"]] = relationship(
        back_populates="initiative"
    )
    municipal_departments: Mapped[List["MunicipalDepartmentModel"]] = relationship(
        secondary=municipal_department_per_initiative_association_table
    )
    reference_urls = Column(ARRAY(String()), default=list)
    annex_ids = Column(ARRAY(String()), default=list)

    is_default = Column(Boolean(), nullable=False, default=False)

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            justification=self.justification,
            evidences=self.evidences,
            costLevel=self.cost_level,
            efficiencyLevel=self.efficiency_level,
            municipalDepartments=[item.to_dict() for item in self.municipal_departments],
            referenceUrls=self.reference_urls,
            annexIds=self.annex_ids,
            # causes=[item.to_dict() for item in self.associated_causes],
        )

    @property
    def associated_macro_objectives(self):
        from app.cause_problem_association.models import CauseAndProblemAssociation
        from app.plan.models import MacroObjectiveProblemAssociationModel

        if self.is_default:
            query = (
                select(MacroObjectiveProblemAssociationModel.macro_objective)
                .select_from(InitiativeModel)
                .outerjoin(
                    InitiativeCauseProblemAssociationModel,
                    InitiativeCauseProblemAssociationModel.initiative_id == InitiativeModel.id
                )
                .outerjoin(
                    MacroObjectiveProblemAssociationModel,
                    MacroObjectiveProblemAssociationModel.problem_id == InitiativeCauseProblemAssociationModel.problem_id
                )
                .where(InitiativeModel.id == self.id)
                .distinct()
            )
        else:
            query = (
                select(MacroObjectiveProblemAssociationModel.macro_objective)
                .select_from(InitiativeModel)
                .outerjoin(
                    InitiativeCauseAssociationModel,
                    InitiativeCauseAssociationModel.initiative_id == InitiativeModel.id
                )
                .outerjoin(
                    CauseAndProblemAssociation,
                    CauseAndProblemAssociation.cause_id == InitiativeCauseAssociationModel.cause_id
                )
                .outerjoin(
                    MacroObjectiveProblemAssociationModel,
                    MacroObjectiveProblemAssociationModel.problem_id == CauseAndProblemAssociation.problem_id
                )
                .where(InitiativeModel.id == self.id)
                .distinct()
            )
        return db.session.execute(query).all()

    @property
    def associated_focuses(self):
        from app.causes.models import CauseIndicatorModel
        from app.plan.models import FocusAssociationModel

        if self.is_default:
            query = (
                select(FocusAssociationModel.focus)
                .select_from(InitiativeModel)
                .outerjoin(
                    InitiativeCauseProblemAssociationModel,
                    InitiativeCauseProblemAssociationModel.initiative_id == InitiativeModel.id
                )
                .outerjoin(
                    CauseIndicatorModel,
                    CauseIndicatorModel.cause_id == InitiativeCauseProblemAssociationModel.cause_id
                )
                .outerjoin(
                    FocusAssociationModel,
                    FocusAssociationModel.cause_indicator_id == CauseIndicatorModel.id
                )
                .where(InitiativeModel.id == self.id)
                .distinct()
            )
        else:
            query = (
                select(FocusAssociationModel.focus)
                .select_from(InitiativeModel)
                .outerjoin(
                    InitiativeCauseAssociationModel,
                    InitiativeCauseAssociationModel.initiative_id == InitiativeModel.id
                )
                .outerjoin(
                    CauseIndicatorModel,
                    CauseIndicatorModel.cause_id == InitiativeCauseAssociationModel.cause_id
                )
                .outerjoin(
                    FocusAssociationModel,
                    FocusAssociationModel.cause_indicator_id == CauseIndicatorModel.id
                )
                .where(InitiativeModel.id == self.id)
                .distinct()
            )
        return db.session.execute(query).all()


class InitiativeCauseAssociationModel(db.Model):
    __tablename__ = "initiative_cause_association"

    initiative_id = Column(ForeignKey("initiative" + ".id", ondelete="CASCADE"), primary_key=True)
    cause_id = Column(ForeignKey("cause" + ".id"), primary_key=True)

    initiative: Mapped["InitiativeModel"] = relationship(back_populates="associated_causes")
    cause: Mapped["CauseModel"] = relationship(back_populates="associated_initiatives")


class InitiativeCauseProblemAssociationModel(db.Model):
    __tablename__ = "initiative_cause_problem_association"

    initiative_id = Column(ForeignKey("initiative" + ".id", ondelete="CASCADE"), primary_key=True)
    cause_id = Column(ForeignKey("cause" + ".id"), primary_key=True)
    problem_id = Column(ForeignKey("problem" + ".id"), primary_key=True)


class InitiativePrioritizationModel(db.Model):
    __tablename__ = "initiative_prioritization"

    initiative_id = Column(ForeignKey("initiative" + ".id", ondelete="CASCADE"), primary_key=True)
    cause_id = Column(ForeignKey("cause" + ".id"), primary_key=True)
    problem_id = Column(ForeignKey("problem" + ".id"), primary_key=True)


class InitiativeAnnexFileModel(db.Model):
    uuid = Column(String(), default=str(uuid4()), primary_key=True)
    filename = Column(String(), nullable=False)
    path = Column(String(), nullable=False)
    created_at = Column(DateTime(), default=datetime.utcnow, nullable=False)


class InitiativeOutcomeModel(db.Model):
    __tablename__ = "initiative_outcome"

    id = Column(Integer(), primary_key=True)
    name = Column(String(), nullable=False)

    initiatives: Mapped[List[InitiativeModel]] = relationship(
        secondary="initiative_outcome_association"
    )


class InitiativeOutcomeAssociationModel(db.Model):
    __tablename__ = "initiative_outcome_association"

    initiative_id = Column(ForeignKey("initiative" + ".id", ondelete="CASCADE"), primary_key=True)
    initiative_outcome_id = Column(ForeignKey("initiative_outcome" + ".id"), primary_key=True)
