from typing import List

from sqlalchemy import select, func, distinct, exists

from app.cause_problem_association.models import CauseAndProblemAssociation
from app.causes.models import CauseModel
from db import db


def count_causes(problem_id=None) -> int:
    query = select(func.count(CauseModel.id))
    if problem_id:
        query = query.where(
            CauseModel.associated_problems.any(CauseAndProblemAssociation.problem_id == problem_id)
        )
    return db.session.execute(query).scalar()


def count_prioritized_causes() -> int:
    query = (
        select(func.count(distinct(CauseAndProblemAssociation.cause_id)))
        .where(CauseAndProblemAssociation.prioritized == True)
    )
    return db.session.execute(query).scalar()


def count_associated_causes() -> int:
    query = (
        select(func.count(distinct(CauseAndProblemAssociation.cause_id)))
    )
    return db.session.execute(query).scalar()


def list_prioritized_causes() -> List[CauseModel]:
    query = (
        select(CauseModel)
        .where(
            exists().where(
                CauseAndProblemAssociation.cause_id == CauseModel.id,
                CauseAndProblemAssociation.prioritized == True,
            ).correlate(CauseModel)
        )
    )
    return db.session.execute(query).all()
