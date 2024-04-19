import datetime
import os
from typing import Optional, Dict, List

from dateutil.relativedelta import relativedelta
from flask import url_for
from sqlalchemy import select, func, exists, delete, and_
from sqlalchemy.sql.functions import max
from werkzeug.utils import secure_filename

from app.commons.dto.pagination import PaginationRequest
from app.constants import format_data_characteristics
from app.problems.models import ProblemIndicatorDataModel, ProblemModel, AnnexCustomProblemModel
from app.problems.repositories import ProblemRepository
from db import db

repo = ProblemRepository()


def get_problem(
        problem_id: str
):
    data = repo.get_problem(problem_id)
    return data


def format_relative_frequency(data: list):
    if data:
        problem_ids = [item["issue_id"].lower() for item in data if "issue_id" in item]
        problem_model_ls: List[ProblemModel] = db.session.execute(
            select(ProblemModel)
            .where(ProblemModel.code.in_(problem_ids))
        ).scalars()

        problem_subquery = (
            select(ProblemIndicatorDataModel.problem_id, max(ProblemIndicatorDataModel.period).label("period"))
            .group_by(ProblemIndicatorDataModel.problem_id)
            .subquery()
        )

        problem_ind_data_model_ls: List[ProblemIndicatorDataModel] = db.session.execute(
            select(ProblemIndicatorDataModel)
            .select_from(problem_subquery)
            .outerjoin(
                ProblemIndicatorDataModel,
                and_(
                    ProblemIndicatorDataModel.problem_id == problem_subquery.c.problem_id,
                    ProblemIndicatorDataModel.period == problem_subquery.c.period,
                )
            )
            .where(ProblemIndicatorDataModel.problem_id != None)
        ).scalars()

        problem_name_by_problem_code_dict = {
            item.code: item.name
            for item in problem_model_ls
        }
        total_city_incidents_by_problem_code_dict = {
            item.problem_id: item.total_city_incidents
            for item in problem_ind_data_model_ls
        }
        output = list()

        for item in data:
            if "issue_id" not in item:
                # this is a patch
                continue
            item["issue_id"] = item["issue_id"].lower()
            if (
                    problem_name_by_problem_code_dict.get(item["issue_id"])
                    and total_city_incidents_by_problem_code_dict.get(item["issue_id"])
            ):
                output.append(dict(
                    name=problem_name_by_problem_code_dict[item["issue_id"]],
                    value=total_city_incidents_by_problem_code_dict[item["issue_id"]],
                    percentage=round(item["rate_relative_frequency"] * 100, 2)
                ))

        output = sorted(output, key=lambda x: x["percentage"], reverse=True)

        return output


def get_problem_kpi(
        problem_id: str,
):
    problem_code = db.session.execute(
        select(ProblemModel.code).where(ProblemModel.id == problem_id)
    ).scalar()
    problem_code = problem_code or ''

    period_subquery = (
        select(func.max(ProblemIndicatorDataModel.period))
        .where(ProblemIndicatorDataModel.problem_id == problem_code)
        .subquery()
    )

    query = (
        select(
            ProblemIndicatorDataModel
        ).where(
            ProblemIndicatorDataModel.problem_id == problem_code,
            ProblemIndicatorDataModel.period == period_subquery
        ).limit(1)
    )

    ind_data_model = db.session.execute(query).scalar()
    if ind_data_model:
        return dict(
            trend=ind_data_model.trend,
            trendData=ind_data_model.trend_data,
            performance=ind_data_model.performance,
            performanceData=ind_data_model.performance_data,
            relativeFrequency=ind_data_model.relative_frequency,
            relativeFrequencyData=format_relative_frequency(ind_data_model.relative_frequency_data),
            concentrationData=ind_data_model.concentration,
        )
    return dict(
        trend=None,
        trendData=None,
        performance=None,
        performanceData=None,
        relativeFrequency=None,
        relativeFrequencyData=None,
        concentrationData=None
    )


def calculate_frequency():
    one_year_ago = datetime.date.today() - relativedelta(years=1)
    rs = db.session.execute(
        select(
            ProblemIndicatorDataModel.problem_id,
            period_column := func.max(ProblemIndicatorDataModel.period).label("period")
        )
        .group_by(
            ProblemIndicatorDataModel.problem_id
        ).filter(period_column >= int(f"{one_year_ago.year}{one_year_ago.month:02}"))
    ).all()
    print(rs)


def get_problem_data_characteristics(
        problem_id: str,
        period: Optional[int] = None
):
    problem_code = db.session.execute(
        select(ProblemModel.code).where(ProblemModel.id == problem_id)
    ).scalar()
    problem_code = problem_code or ''

    if not period:
        stmt = select(func.max(ProblemIndicatorDataModel.period)).where(
            ProblemIndicatorDataModel.problem_id == problem_code)
        period = db.session.execute(stmt).scalar()
        if not period:
            return dict()

    cols = [
        "period",
        "perpetrator_identification",
        "perpetrator_gender",
        "perpetrator_ethnicity",
        "perpetrator_age_range",
        "perpetrator_academic_level",
        "perpetrator_job_status",
        "perpetrator_victim_relationship",
        "victim_gender",
        "victim_ethnicity",
        "victim_age_range",
        "victim_job_status",
        "victim_academic_level",
        "date_day_type",
        "date_day_of_the_week",
        "date_time_of_day",
        "concentration",
        "place_type",
        "weapon",
        "typology",
    ]

    select_stmt = select(
        ProblemIndicatorDataModel.period,
        ProblemIndicatorDataModel.perpetrator_identification,
        ProblemIndicatorDataModel.perpetrator_gender,
        ProblemIndicatorDataModel.perpetrator_ethnicity,
        ProblemIndicatorDataModel.perpetrator_age_range,
        ProblemIndicatorDataModel.perpetrator_academic_level,
        ProblemIndicatorDataModel.perpetrator_job_status,
        ProblemIndicatorDataModel.perpetrator_victim_relationship,
        ProblemIndicatorDataModel.victim_gender,
        ProblemIndicatorDataModel.victim_ethnicity,
        ProblemIndicatorDataModel.victim_age_range,
        ProblemIndicatorDataModel.victim_job_status,
        ProblemIndicatorDataModel.victim_academic_level,
        ProblemIndicatorDataModel.date_day_type,
        ProblemIndicatorDataModel.date_day_of_the_week,
        ProblemIndicatorDataModel.date_time_of_day,
        ProblemIndicatorDataModel.concentration,
        ProblemIndicatorDataModel.place_type,
        ProblemIndicatorDataModel.weapon,
        ProblemIndicatorDataModel.typology,
    ).where(
        ProblemIndicatorDataModel.problem_id == problem_code,
        ProblemIndicatorDataModel.period == period
    ).limit(1)

    result = db.session.execute(select_stmt).first()
    result = dict(zip(cols, result))

    return format_data_characteristics(result)


def count_problems(problem_id):
    return repo.count_problems(problem_id)


def get_problem_rate(problem_id) -> float:
    return repo.get_problem_rate(problem_id)


def count_population():
    return 508826


def list_problems(
        pagination_req: PaginationRequest,
        prioritized_filter: Optional[bool]
):
    pages = repo.list_problems(pagination_req, prioritized_filter)
    return pages


def list_associated_causes(
        problem_id,
        pagination_req: PaginationRequest,
):
    pages = repo.list_associated_causes(problem_id, pagination_req)
    return pages


def count_potentials_problems(
):
    return repo.count_all_problems()


def count_prioritized_problems(
):
    return repo.count_prioritized_problems()


def count_critical_problems(
):
    return repo.count_critical_problems()


def prioritize_problem(
        problem_id: str
):
    if not repo.check_problem_exist(problem_id):
        raise Exception
    repo.patch_problem_prioritization(problem_id, prioritized=True)


def deprioritize_problem(
        problem_id: str
):
    if not repo.check_problem_exist(problem_id):
        raise Exception
    repo.patch_problem_prioritization(problem_id, prioritized=False)


def check_problems_id_not_in_db(problems_id):
    ids_not_in_db = []

    for problem_id in problems_id:
        if not repo.check_problem_exist(problem_id):
            ids_not_in_db.append(problem_id)

    return ids_not_in_db


def get_trend_data(problem_id):
    # ProblemSummaryModel.
    pass


def list_problem_options():
    column_names = ["id", "name", ]
    select_result = db.session.execute(
        select(ProblemModel.id, ProblemModel.name)
    ).all()
    result = [dict(zip(column_names, item.tuple())) for item in select_result]
    return result


# CUSTOM-PROBLEMS
from datetime import datetime


def create_custom_problem(
        custom_cause: Dict,
        path,
        user_id: int
):
    try:
        custom_problem_obj = ProblemModel(
            name=custom_cause.get("name"),
            description=custom_cause.get("description"),
            references=custom_cause.get("references"),
            created_by_id=user_id,
        )
        db.session.add(custom_problem_obj)
        db.session.flush()

        for annex_file in custom_cause.get("annexes", []):
            filename = secure_filename(annex_file.filename)
            annex_file.save(filepath := os.path.join(path, filename))
            db.session.add(AnnexCustomProblemModel(
                annexes_name=filename,
                custom_problem_id=custom_problem_obj.id,
                path=filepath
            ))

        db.session.commit()
        return custom_problem_obj
    except Exception:
        db.session.rollback()
        raise


def update_custom_problem_service(
        problem_model: ProblemModel,
        problem_dict: Dict,
        path
):
    try:
        problem_model.name = problem_dict.get("name", problem_model.name)
        problem_model.description = problem_dict.get("description", problem_model.description)
        problem_model.references = problem_dict.get("references", problem_model.references)

        db.session.merge(problem_model)

        for annex_id in problem_dict.get("annexes_to_remove", []):
            db.session.execute(
                delete(AnnexCustomProblemModel)
                .where(
                    AnnexCustomProblemModel.id == annex_id,
                    AnnexCustomProblemModel.custom_problem_id == problem_model.id
                )
            )

        for annex_file in problem_dict.get("annexes_to_add", []):
            filename = secure_filename(annex_file.filename)
            annex_file.save(filepath := os.path.join(path, filename))
            db.session.add(AnnexCustomProblemModel(
                annexes_name=filename,
                custom_problem_id=problem_model.id,
                path=filepath
            ))

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def check_problem_name_already_used(problem_name: str, ignore_id=None):
    filter_params = []
    if ignore_id:
        filter_params.append(
            ProblemModel.id != ignore_id
        )
    query = (
        select(exists().where(ProblemModel.name == problem_name, *filter_params))
    )
    value = db.session.execute(query).scalar()
    return value


def get_custom_problem(custom_problem_id: int) -> Optional[Dict]:
    select_stmt = (
        select(ProblemModel)
        .where(
            ProblemModel.id == custom_problem_id,
            ProblemModel.is_default == False
        )
        .limit(1)
    )
    problem_model: ProblemModel = db.session.execute(select_stmt).scalar()
    if problem_model:
        return dict(
            id=problem_model.id,
            name=problem_model.name,
            description=problem_model.description,
            prioritized=problem_model.prioritized,
            references=problem_model.references,
            isDefault=problem_model.is_default,
            annexes=[
                dict(
                    id=item.id,
                    name=item.annexes_name,
                    url=url_for("serve_uploaded_file", filename=item.annexes_name, _external=True)
                ) for item in problem_model.annexes
            ],
            createdAt=problem_model.created_at and problem_model.created_at.isoformat(),
            createdBy=dict(
                id=problem_model.created_by.id,
                name=problem_model.created_by.name,
                lastName=problem_model.created_by.last_name,
            )
        )


def get_problem_model(problem_id):
    query = (
        select(
            ProblemModel
        ).where(ProblemModel.id == problem_id)
    )

    return db.session.execute(query).scalar()


def delete_custom_problem(
        problem_id
):
    try:
        db.session.execute(
            delete(AnnexCustomProblemModel).where(AnnexCustomProblemModel.custom_problem_id == problem_id))
        db.session.execute(delete(ProblemModel).where(ProblemModel.id == problem_id))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
