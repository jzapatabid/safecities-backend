from typing import Optional

from sqlalchemy import Column, Integer, ForeignKey, Boolean, select, exists, update
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import expression

from db import db


class CauseAndProblemAssociation(db.Model):
    __tablename__ = "cause_problem_association"

    id = Column(Integer(), primary_key=True)
    cause_id = Column(ForeignKey("cause" + ".id"))
    problem_id = Column(ForeignKey("problem" + ".id"))
    cause: Mapped["CauseModel"] = relationship(back_populates="associated_problems")
    problem: Mapped["ProblemModel"] = relationship(back_populates="associated_causes")
    prioritized = Column(Boolean(), nullable=False, default=expression.false())

    @staticmethod
    def check_exist(cause_id, problem_id) -> bool:
        query = select(
            exists()
            .where(
                CauseAndProblemAssociation.cause_id == cause_id,
                CauseAndProblemAssociation.problem_id == problem_id
            )
        )
        exist = db.session.execute(query).scalar()
        return exist

    @staticmethod
    def set_prioritization(cause_id, problem_id, prioritized: bool, commit=False):
        query = (
            update(CauseAndProblemAssociation)
            .where(CauseAndProblemAssociation.cause_id == cause_id, CauseAndProblemAssociation.problem_id == problem_id)
            .values(prioritized=prioritized)
        )
        db.session.execute(query)
        if commit:
            db.session.commit()

    @staticmethod
    def get_by_pk(cause_id, problem_id) -> Optional["CauseAndProblemAssociation"]:
        query = (
            select(CauseAndProblemAssociation)
            .where(CauseAndProblemAssociation.cause_id == cause_id, CauseAndProblemAssociation.problem_id == problem_id)
            .limit(1)
        )
        return db.session.execute(query).scalar()
