import logging
from typing import List

from sqlalchemy import text, select, exists, delete, distinct
from sqlalchemy.sql.functions import count

from app.cause_problem_association.models import CauseAndProblemAssociation
from app.causes.models import CauseModel
from app.commons.models.municipal_department_model import MunicipalDepartmentModel
from app.initiatives.models import InitiativeModel, InitiativeCauseAssociationModel, \
    InitiativePrioritizationModel, InitiativeCauseProblemAssociationModel, InitiativeOutcomeModel, \
    InitiativeOutcomeAssociationModel
from app.initiatives.queries import Queries
from app.problems.models import ProblemModel
from db import db


def get_initiative_types(initiative_ids: List[int]):
    default_initiative_ids = db.session.execute(
        select(InitiativeModel.id)
        .where(InitiativeModel.id.in_(initiative_ids), InitiativeModel.is_default == True)
    ).scalars()

    custom_initiative_ids = db.session.execute(
        select(InitiativeModel.id)
        .where(InitiativeModel.id.in_(initiative_ids), InitiativeModel.is_default == False)
    ).scalars()

    return default_initiative_ids, custom_initiative_ids


def list_default_initiative_association(initiative_ids: List[int]):
    query = select(
        InitiativeModel.id,
        InitiativeModel.name,
        CauseModel.id,
        CauseModel.name,
        ProblemModel.id,
        ProblemModel.name,
        exists().where(
            InitiativePrioritizationModel.initiative_id == InitiativeModel.id,
            InitiativePrioritizationModel.cause_id == CauseModel.id,
            InitiativePrioritizationModel.problem_id == ProblemModel.id
        ).label("prioritized"),
        CauseAndProblemAssociation.prioritized
    ).select_from(InitiativeModel)

    query = query.join(
        InitiativeCauseProblemAssociationModel,
        InitiativeCauseProblemAssociationModel.initiative_id == InitiativeModel.id
    )
    query = query.join(
        CauseAndProblemAssociation,
        CauseAndProblemAssociation.cause_id == InitiativeCauseProblemAssociationModel.cause_id
    )
    query = query.join(CauseModel, CauseModel.id == InitiativeCauseProblemAssociationModel.cause_id)
    query = query.join(ProblemModel, ProblemModel.id == InitiativeCauseProblemAssociationModel.problem_id)
    query = query.where(InitiativeModel.id.in_(initiative_ids))
    query = query.where(ProblemModel.prioritized==True)
    query = query.where(CauseAndProblemAssociation.prioritized==True)
    query = query.where(CauseAndProblemAssociation.problem_id == InitiativeCauseProblemAssociationModel.problem_id)
    query = query.order_by(InitiativeModel.id, CauseModel.id, ProblemModel.id)

    # todo: validar esta logica con sergio, por que tengo que validar de que si o si el problema esta priorizado?
    # query = query.where(InitiativeModel.id == initiative_id, ProblemModel.prioritized == True)

    rs = db.session.execute(query).all()
    return rs


def list_custom_initiative_association(initiative_ids: List[int]):
    query = select(
        InitiativeModel.id,
        InitiativeModel.name,
        CauseModel.id,
        CauseModel.name,
        ProblemModel.id,
        ProblemModel.name,
        exists().where(
            InitiativePrioritizationModel.initiative_id == InitiativeModel.id,
            InitiativePrioritizationModel.cause_id == CauseModel.id,
            InitiativePrioritizationModel.problem_id == ProblemModel.id
        ).label("prioritized"),
        CauseAndProblemAssociation.prioritized
    ).select_from(InitiativeModel)
    query = query.join(
        InitiativeCauseAssociationModel,
        InitiativeCauseAssociationModel.initiative_id == InitiativeModel.id
    )
    query = query.join(
        CauseAndProblemAssociation,
        CauseAndProblemAssociation.cause_id == InitiativeCauseAssociationModel.cause_id
    )
    query = query.join(CauseModel, CauseModel.id == CauseAndProblemAssociation.cause_id)
    query = query.join(ProblemModel, ProblemModel.id == CauseAndProblemAssociation.problem_id)
    query = query.where(InitiativeModel.id.in_(initiative_ids))
    query = query.where(CauseAndProblemAssociation.prioritized==True)
    query = query.where(ProblemModel.prioritized==True)
    query = query.order_by(InitiativeModel.id, CauseModel.id, ProblemModel.id)

    rs = db.session.execute(query).all()
    return rs


def check_initiative_prioritization_is_valid(initiative_id: int, cause_id: int, problem_id: str):
    is_default = db.session.execute(
        select(InitiativeModel.is_default).where(InitiativeModel.id == initiative_id)
    ).scalar()

    if is_default:
        query = (
            select(
                exists()
                .where(
                    InitiativeCauseProblemAssociationModel.initiative_id == initiative_id,
                    InitiativeCauseProblemAssociationModel.cause_id == cause_id,
                    InitiativeCauseProblemAssociationModel.problem_id == problem_id,
                )
            )
        )
    else:
        query = (
            select(
                exists()
                .where(
                    InitiativeCauseAssociationModel.cause_id == CauseAndProblemAssociation.cause_id,  # inner join
                    InitiativeCauseAssociationModel.initiative_id == initiative_id,
                    InitiativeCauseAssociationModel.cause_id == cause_id,
                    CauseAndProblemAssociation.problem_id == problem_id,
                )
            )
        )

    return db.session.execute(query).scalar()


def prioritize_initiative(initiative_id: int, cause_id: int, problem_id: str):
    model = InitiativePrioritizationModel(
        initiative_id=initiative_id,
        cause_id=cause_id,
        problem_id=problem_id,
    )
    db.session.merge(model)


def deprioritize_initiative(initiative_id: int, cause_id: int, problem_id: str):
    query = (
        delete(InitiativePrioritizationModel)
        .where(
            InitiativePrioritizationModel.initiative_id == initiative_id,
            InitiativePrioritizationModel.cause_id == cause_id,
            InitiativePrioritizationModel.problem_id == problem_id,
        )
    )
    db.session.execute(query)


def count_prioritized_initiatives():
    query = (
        select(count(distinct(InitiativePrioritizationModel.initiative_id)))
        .select_from(
            InitiativePrioritizationModel
        )
    )
    return db.session.execute(query).scalar()


class InitiativeRepository:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.queries = Queries()

    def get_initiative_list_repo(self, pagination_req, prioritized_filter):
        limit = pagination_req.page_size
        offset = (pagination_req.page - 1) * limit
        order_field = pagination_req.order_field
        sort_type = pagination_req.sort_type

        query = text(self.queries.CUSTOM_INITIATIVE_LIST.replace(':sorttype', sort_type)
                     .replace(':orderfield', order_field))

        initiative_list = db.session.execute(query,
                                             {'limitt': limit,
                                              'offsett': offset,
                                              'orderfield': order_field}).fetchall()

        return initiative_list

    def total_items(self):
        query = text(self.queries.TOTAL_INITIATIVE_ELEMENTS)
        total_items = db.session.execute(query).fetchone()
        return total_items


def check_initiative_exist_by_id(id: int):
    return db.session.execute(
        select(
            exists().where(InitiativeModel.id == id)
        )
    ).scalar()


def check_initiative_outcome_exist_by_id(id: int):
    return db.session.execute(
        select(
            exists().where(InitiativeOutcomeModel.id == id)
        )
    ).scalar()


def check_municipal_department_exist_by_id(id: int):
    return db.session.execute(
        select(
            exists().where(MunicipalDepartmentModel.id == id)
        )
    ).scalar()


def list_initiative_outcomes(initiative_id: int) -> List[InitiativeOutcomeModel]:
    outcome_model_ls = db.session.execute(
        select(InitiativeOutcomeModel)
        .where(InitiativeOutcomeModel.initiatives.any(InitiativeOutcomeAssociationModel.initiative_id == initiative_id))
    ).scalars()
    return outcome_model_ls
