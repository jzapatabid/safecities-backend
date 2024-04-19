import os
from http import HTTPStatus
from typing import Optional, Dict, List

from apiflask import abort
from sqlalchemy import select, func, and_, exists, delete
from sqlalchemy.orm import aliased
from werkzeug.utils import secure_filename

from app.cause_problem_association.models import CauseAndProblemAssociation
from app.causes.dto import CauseProblemPrioritizationDTO, CauseSummaryDTO, UpdateCausePrioritizationRequestDTO
from app.causes.models import DefaultCauseModel, CauseModel, CustomCauseModel, CauseIndicatorModel, \
    CauseIndicatorDataModel, AnnexModel
from app.causes.repositories import count_causes, count_prioritized_causes, count_associated_causes
from app.problems.models import ProblemModel
from db import db


def get_default_cause(cause_id: int) -> Optional[DefaultCauseModel]:
    select_stmt = select(DefaultCauseModel).where(DefaultCauseModel.id == cause_id).limit(1)
    cause_model = db.session.execute(select_stmt).scalar()
    return cause_model


def get_custom_cause(cause_id: int) -> Optional[CustomCauseModel]:
    select_stmt = select(CustomCauseModel).where(CustomCauseModel.id == cause_id).limit(1)
    cause_model = db.session.execute(select_stmt).scalar()
    return cause_model


def get_cause_summary() -> CauseSummaryDTO:
    return CauseSummaryDTO(
        total_causes=count_causes(),
        total_prioritized_causes=count_prioritized_causes(),
        total_relevant_causes=count_associated_causes(),
    )


def list_cause_indicators(
        cause_id
):
    select_stmt = select(CauseIndicatorModel).where(CauseIndicatorModel.cause_id == cause_id)
    rs = db.session.execute(select_stmt).scalars()
    return rs


def create_custom_cause(
        custom_cause: Dict,
        path,
        user_id: int
):
    try:
        custom_cause_obj = CustomCauseModel(
            name=custom_cause["name"],
            justification=custom_cause["justification"],
            evidences=custom_cause["evidences"],
            references=custom_cause.get("references", []),
            created_by_id=user_id
        )
        db.session.add(custom_cause_obj)
        db.session.flush()

        for problem_id in custom_cause.get("problems", []):
            db.session.add(CauseAndProblemAssociation(
                cause_id=custom_cause_obj.id,
                problem_id=problem_id,
            ))

        for annex_file in custom_cause.get("annexes", []):
            filename = secure_filename(annex_file.filename)
            annex_file.save(filepath := os.path.join(path, filename))
            db.session.add(AnnexModel(
                annexes_name=filename,
                custom_cause_id=custom_cause_obj.id,
                path=filepath
            ))

        db.session.commit()
        return custom_cause_obj
    except Exception:
        db.session.rollback()
        raise


def update_custom_cause(
        cause_id,
        custom_cause: Dict,
        path
):
    try:
        custom_cause_obj = db.session.execute(
            select(CustomCauseModel).where(CustomCauseModel.id == cause_id).limit(1)
        ).scalar()
        custom_cause_obj.name = custom_cause["name"]
        custom_cause_obj.justification = custom_cause["justification"]
        custom_cause_obj.evidences = custom_cause["evidences"]
        custom_cause_obj.references = custom_cause.get("references", [])
        db.session.add(custom_cause_obj)

        new_problems: List = custom_cause.get("problems", [])
        associated_problem_id_ls = db.session.execute(
            select(CauseAndProblemAssociation.problem_id).where(
                CauseAndProblemAssociation.cause_id == custom_cause_obj.id)
        ).scalars().all()

        for associated_problem_id in associated_problem_id_ls:
            if associated_problem_id in new_problems:
                new_problems.remove(associated_problem_id)
                associated_problem_id_ls.remove(associated_problem_id)

        db.session.execute(
            delete(CauseAndProblemAssociation)
            .where(
                CauseAndProblemAssociation.cause_id == cause_id,
                CauseAndProblemAssociation.problem_id.in_(associated_problem_id_ls)
            )
        )

        for problem_id in new_problems:
            db.session.add(CauseAndProblemAssociation(
                cause_id=custom_cause_obj.id,
                problem_id=problem_id,
            ))

        for annex_id in custom_cause.get("annexes_to_remove", []):
            db.session.execute(delete(AnnexModel).where(AnnexModel.id == annex_id))

        for annex_file in custom_cause.get("annexes_to_add", []):
            filename = secure_filename(annex_file.filename)
            annex_file.save(filepath := os.path.join(path, filename))
            db.session.add(AnnexModel(
                annexes_name=filename,
                custom_cause_id=custom_cause_obj.id,
                path=filepath
            ))

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def delete_custom_cause(
        cause_id
):
    try:
        db.session.execute(delete(AnnexModel).where(AnnexModel.custom_cause_id == cause_id))
        db.session.execute(delete(CustomCauseModel).where(CustomCauseModel.id == cause_id))
        db.session.execute(delete(CauseAndProblemAssociation).where(CauseAndProblemAssociation.cause_id == cause_id))
        db.session.execute(delete(CauseModel).where(CauseModel.id == cause_id))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def list_cause_indicators_with_last_data(
        cause_id
):
    select_cause_indicator_id_and_last_period = (
        select(
            CauseIndicatorDataModel.cause_indicator_id.label("cause_indicator_id"),
            func.max(CauseIndicatorDataModel.period).label("period")
        )
        .group_by(
            CauseIndicatorDataModel.cause_indicator_id
        )
    ).subquery()

    select_last_updated_cause_indicator_data = select(CauseIndicatorDataModel) \
        .join(
        select_cause_indicator_id_and_last_period,
        and_(
            CauseIndicatorDataModel.cause_indicator_id == select_cause_indicator_id_and_last_period.c.cause_indicator_id,
            CauseIndicatorDataModel.period == select_cause_indicator_id_and_last_period.c.period,
        )
    ).subquery()

    select_last_updated_cause_indicator_data = aliased(CauseIndicatorDataModel,
                                                       select_last_updated_cause_indicator_data)

    select_cause_indicator_and_last_updated_data = (
        select(CauseIndicatorModel, select_last_updated_cause_indicator_data)
        .outerjoin(
            select_last_updated_cause_indicator_data,
            CauseIndicatorModel.code == select_last_updated_cause_indicator_data.cause_indicator_id
        )
        .where(CauseIndicatorModel.cause_id == cause_id)
    )

    rs = db.session.execute(select_cause_indicator_and_last_updated_data).all()
    return rs


def check_cause_name_already_used(cause_name: str):
    value = db.session.execute(
        select(exists().where(CauseModel.name == cause_name))
    ).scalar()
    return value


def check_cause_is_prioritized(cause_id):
    select_stmt = select(exists().where(
        CauseAndProblemAssociation.cause_id == cause_id,
        CauseAndProblemAssociation.prioritized == True
    ))
    cause_prioritized = db.session.execute(select_stmt).scalar()
    return cause_prioritized


def list_cause_prioritization(cause_ids: List[int]):
    query = (
        select(
            CauseModel.id,
            CauseModel.name,
            ProblemModel.id,
            ProblemModel.name,
            CauseAndProblemAssociation.prioritized
        )
        .select_from(CauseAndProblemAssociation)
        .outerjoin(ProblemModel, ProblemModel.id == CauseAndProblemAssociation.problem_id)
        .outerjoin(CauseModel, CauseModel.id == CauseAndProblemAssociation.cause_id)
        .where(CauseAndProblemAssociation.cause_id.in_(cause_ids),
               ProblemModel.prioritized == True
               )
    )

    rs = db.session.execute(query).all()
    for cause_id, cause_name, problem_id, problem_name, prioritized in rs:
        yield CauseProblemPrioritizationDTO(
            cause_id=cause_id,
            cause_name=cause_name,
            problem_id=problem_id,
            problem_name=problem_name,
            prioritized=prioritized,
        )


def bulk_update_cause_prioritization(cause_prioritization_request_dto_ls: List[UpdateCausePrioritizationRequestDTO]):
    for cause_prioritization_request_dto in cause_prioritization_request_dto_ls:
        cause_id = cause_prioritization_request_dto.cause_id
        problem_ids_to_prioritize = cause_prioritization_request_dto.problem_ids_to_prioritize
        problem_ids_to_deprioritize = cause_prioritization_request_dto.problem_ids_to_deprioritize

        for problem_id in problem_ids_to_prioritize:
            exist = CauseAndProblemAssociation.check_exist(cause_id=cause_id, problem_id=problem_id)
            if not exist:
                abort(
                    HTTPStatus.BAD_REQUEST,
                    f"Cause and Problem aren't related so can't be prioritized, cause_id={cause_id} problem_id={problem_id}"
                )
            CauseAndProblemAssociation.set_prioritization(cause_id=cause_id, problem_id=problem_id, prioritized=True)

        for problem_id in problem_ids_to_deprioritize:
            exist = CauseAndProblemAssociation.check_exist(cause_id=cause_id, problem_id=problem_id)
            if not exist:
                abort(
                    HTTPStatus.BAD_REQUEST,
                    f"Cause and Problem aren't related so can't be prioritized, cause_id={cause_id} problem_id={problem_id}"
                )
            CauseAndProblemAssociation.set_prioritization(cause_id=cause_id, problem_id=problem_id, prioritized=False)

    db.session.commit()
