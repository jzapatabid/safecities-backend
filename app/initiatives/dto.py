import os
from dataclasses import dataclass
from typing import List

from flask import url_for
from sqlalchemy import select, distinct
from sqlalchemy.sql.functions import count

from app.cause_problem_association.models import CauseAndProblemAssociation
from app.commons.models.file_model import FileModel
from app.initiatives.models import InitiativeModel, InitiativeCauseProblemAssociationModel, \
    InitiativeCauseAssociationModel
from app.problems.models import ProblemModel
from db import db

path = os.getenv(
    "UPLOAD_FILE_PATH",
    os.path.join(os.getcwd(), "uploads")
)


@dataclass
class InitiativeDetailDTO:
    id: int
    name: str
    justification: str
    evidences: str
    cost_level: int
    efficiency_level: int
    causes: List
    municipal_departments: List

    references: List[str]
    annexes: List

    total_causes: int
    total_problems: int
    is_default: bool
    prioritized: bool

    @staticmethod
    def create_from_model(initiative_model: InitiativeModel, prioritized: bool):
        if initiative_model.is_default:
            total_causes, total_problems = db.session.execute(
                select(
                    count(distinct(InitiativeCauseProblemAssociationModel.cause_id)),
                    count(distinct(InitiativeCauseProblemAssociationModel.problem_id))
                )
                .select_from(InitiativeCauseProblemAssociationModel)
                .join(
                    CauseAndProblemAssociation,
                    CauseAndProblemAssociation.cause_id == InitiativeCauseProblemAssociationModel.cause_id
                )                
                .join(
                    ProblemModel,
                    ProblemModel.id == InitiativeCauseProblemAssociationModel.problem_id
                )
                .where(InitiativeCauseProblemAssociationModel.initiative_id == initiative_model.id, 
                       ProblemModel.prioritized == True, CauseAndProblemAssociation.prioritized == True,
                       CauseAndProblemAssociation.problem_id == InitiativeCauseProblemAssociationModel.problem_id
                       )
            ).first()
        else:
            total_causes, total_problems = db.session.execute(
                select(
                    count(distinct(CauseAndProblemAssociation.cause_id)),
                    count(distinct(CauseAndProblemAssociation.problem_id))
                )
                .select_from(InitiativeCauseAssociationModel)
                .outerjoin(
                    CauseAndProblemAssociation,
                    CauseAndProblemAssociation.cause_id == InitiativeCauseAssociationModel.cause_id
                )
                .outerjoin(
                    ProblemModel,
                    ProblemModel.id == CauseAndProblemAssociation.problem_id
                )
                .where(InitiativeCauseAssociationModel.initiative_id == initiative_model.id, 
                       ProblemModel.prioritized == True, CauseAndProblemAssociation.prioritized == True
                       )
            ).first()

        file_model_ls = list()
        if initiative_model.annex_ids:
            file_model_ls = db.session.execute(
                select(FileModel).where(FileModel.id.in_(
                    initiative_model.annex_ids
                ))
            ).scalars()

        return InitiativeDetailDTO(
            id=initiative_model.id,
            name=initiative_model.name,
            justification=initiative_model.justification,
            evidences=initiative_model.evidences,
            cost_level=initiative_model.cost_level,
            efficiency_level=initiative_model.efficiency_level,
            causes=[{"id": item.cause.id, "name": item.cause.name} for item in initiative_model.associated_causes],
            municipal_departments=[{"id": item.id, "name": item.name} for item in
                                   initiative_model.municipal_departments],
            total_causes=total_causes,
            total_problems=total_problems,
            is_default=initiative_model.is_default,
            references=initiative_model.reference_urls,
            prioritized=prioritized,
            annexes=[
                dict(
                    id=item.id,
                    fileName=item.filename,
                    url=url_for("serve_uploaded_file", filename=item.id, _external=True)
                )
                for item in file_model_ls
            ]
        )

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            justification=self.justification,
            evidences=self.evidences,
            costLevel=self.cost_level,
            efficiencyLevel=self.efficiency_level,
            municipalDepartments=self.municipal_departments,
            causes=self.causes,
            totalCauses=self.total_causes,
            totalProblems=self.total_problems,
            isDefault=self.is_default,
            prioritized=self.prioritized,
            references=self.references,
            annexes=self.annexes,
        )


@dataclass
class InitiativeAssociationDto:
    initiative_id: int
    initiative_name: str
    cause_id: int
    cause_name: str
    problem_id: str
    problem_name: str
    prioritized: bool
    problem_prioritized: bool

    def to_dict(self):
        return dict(
            initiativeId=self.initiative_id,
            initiativeName=self.initiative_name,
            causeId=self.cause_id,
            causeName=self.cause_name,
            problemId=self.problem_id,
            problemName=self.problem_name,
            prioritized=self.prioritized,
            problem_prioritized=self.problem_prioritized,
        )


@dataclass
class InitiativePrioritizationRequestDTO:
    initiative_id: int
    cause_id: int
    problem_id: str
