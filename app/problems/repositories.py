import datetime
import math
from typing import Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func, update, exists, and_, case
from sqlalchemy.sql.elements import and_

from app.cause_problem_association.models import CauseAndProblemAssociation
from app.causes.models import CauseModel, CauseIndicatorDataModel, CauseIndicatorModel, DefaultCauseModel
from app.commons.dto.pagination import PaginationRequest, PaginationResponse
from app.commons.sqlalchemy_utils import asc_, desc_
from app.problems.models import ProblemModel, ProblemIndicatorDataModel
from db import db


class ProblemRepository:

    def get_problem(self, problem_id: str):
        column_names = [
            "id", "name", "description", "prioritized", "geonetLink", "polarity", "measurement_unit", "updatedAt", "isDefault", "hasData" 
        ]

        select_stmt = (
            select(
                ProblemModel.id,
                ProblemModel.name,
                ProblemModel.description,
                ProblemModel.prioritized,
                ProblemModel.geonet_link,
                ProblemModel.polarity,
                ProblemModel.measurement_unit,
                select(func.max(ProblemIndicatorDataModel.period))
                .where(
                    ProblemIndicatorDataModel.problem_id == (
                        select(ProblemModel.code)
                        .where(ProblemModel.id == problem_id)
                        .subquery()
                    )
                ).subquery(),
                ProblemModel.is_default,
                exists().where(
                    ProblemIndicatorDataModel.problem_id == (
                        select(ProblemModel.code)
                        .where(ProblemModel.id == problem_id)
                        .subquery()
                    )
                ),
            )
            .where(ProblemModel.id == problem_id)
            .select_from(ProblemModel)
            .limit(1)
        )

        result = db.session.execute(select_stmt).first()
        if result:
            result = dict(zip(column_names, result))
            return result

    def count_problems(self, problem_id) -> int:
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
            select(ProblemIndicatorDataModel.total_city_incidents)
            .where(
                ProblemIndicatorDataModel.problem_id == problem_code,
                ProblemIndicatorDataModel.period == period_subquery,
            )
            .limit(1)
        )

        return db.session.execute(query).scalar()

    def get_problem_rate(self, problem_id) -> float:
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
            select(ProblemIndicatorDataModel.city_rate)
            .where(
                ProblemIndicatorDataModel.problem_id == problem_code,
                ProblemIndicatorDataModel.period == period_subquery,
            )
            .limit(1)
        )

        result = db.session.execute(query).scalar()
        if result:
            return result
        return 0

    def list_problems(self, pagination_req: PaginationRequest, prioritized_filter: Optional[bool]):
        column_names = [
            "id", "name", "description", "prioritized", "isDefault", "trend", "relativeFrequency", "performance",
            "harmPotential", "criticalityLevel", "hasData", "totalCauses", "totalPrioritizedCauses",
        ]
        column_names = [
            "id", "name", "description", "prioritized", "is_default", "trend", "relative_incidence", "performance",
            "harm_potential", "criticality_level", "has_data", "total_causes", "total_prioritized_causes",
        ]

        previous_year = datetime.date.today() - relativedelta(years=1)
        start_period = int(f"{previous_year.year}{previous_year.month:02d}")

        last_updated_period_subquery = select(
            ProblemIndicatorDataModel.problem_id,
            func.max(ProblemIndicatorDataModel.period).label("period"),
        ).where(ProblemIndicatorDataModel.period >= start_period).group_by(
            ProblemIndicatorDataModel.problem_id).subquery()

        problem_indicator_data_subquery = (
            select(
                ProblemIndicatorDataModel.problem_id,
                ProblemIndicatorDataModel.period,
                ProblemIndicatorDataModel.trend_normalized,
                ProblemIndicatorDataModel.performance_normalized,
                ProblemIndicatorDataModel.relative_frequency_normalized,
                ProblemIndicatorDataModel.harm_potential_normalized,
                ProblemIndicatorDataModel.criticality_level,
            )
            .join(
                last_updated_period_subquery,
                and_(
                    last_updated_period_subquery.c.problem_id == ProblemIndicatorDataModel.problem_id,
                    last_updated_period_subquery.c.period == ProblemIndicatorDataModel.period)
            )
            .subquery()
        )

        select_stmt = (
            select(
                ProblemModel.id,
                ProblemModel.name,
                ProblemModel.description,
                ProblemModel.prioritized,
                ProblemModel.is_default,
                problem_indicator_data_subquery.c.trend_normalized.label('trend'),
                problem_indicator_data_subquery.c.relative_frequency_normalized.label('relative_incidence'),
                problem_indicator_data_subquery.c.performance_normalized.label('performance'),
                problem_indicator_data_subquery.c.harm_potential_normalized.label('harm_potential'),
                problem_indicator_data_subquery.c.criticality_level.label('criticality_level'),
                has_data_column := case(
                    (problem_indicator_data_subquery.c.problem_id.isnot(None), True),
                    else_=False
                ).label("has_data"),
                select(func.count(CauseAndProblemAssociation.id)).where(
                    CauseAndProblemAssociation.problem_id == ProblemModel.id,
                ).label("total_causes"),
                select(func.count(CauseAndProblemAssociation.id)).where(
                    CauseAndProblemAssociation.prioritized == True,
                    CauseAndProblemAssociation.problem_id == ProblemModel.id,
                ).label("total_prioritized_causes")
            )
            .select_from(ProblemModel)
            .outerjoin(
                problem_indicator_data_subquery,
                ProblemModel.code == problem_indicator_data_subquery.c.problem_id
            )
        )

        if prioritized_filter:
            select_stmt = select_stmt.where(ProblemModel.prioritized == prioritized_filter)

        total_items = db.session.execute(select(func.count("*")).select_from(select_stmt)).scalar()
        total_pages = math.ceil(total_items / pagination_req.page_size)

        sort_method = asc_ if pagination_req.sort_type == "asc" else desc_
        select_stmt = select_stmt.order_by(sort_method(pagination_req.order_field))
        select_stmt = select_stmt.offset((pagination_req.page - 1) * pagination_req.page_size)
        select_stmt = select_stmt.limit(pagination_req.page_size)

        problems_ls = db.session.execute(select_stmt).all()
        results = [dict(zip(column_names, item.tuple())) for item in problems_ls]

        return PaginationResponse(
            total_items=total_items,
            total_pages=total_pages,
            results=results
        )

    def list_associated_causes(self, problem_id, pagination_req: PaginationRequest):
        """
        List causes that are associated with a specific problem.
        return cause_id, cause_name, cause_type, prioritized flag, worst_trend
        :param problem_id:
        :param pagination_req:
        :return:
        """
        cols = ["id", "name", "type", "prioritized", "trend"]

        select_cause_id_and_last_period = (
            select(
                CauseAndProblemAssociation.cause_id,
                func.max(CauseIndicatorDataModel.period).label("period")
            )
            .select_from(CauseAndProblemAssociation)
            .outerjoin(CauseIndicatorModel, CauseIndicatorModel.cause_id == CauseAndProblemAssociation.cause_id)
            .outerjoin(CauseIndicatorDataModel, CauseIndicatorDataModel.cause_indicator_id == CauseIndicatorModel.code)
            .where(CauseAndProblemAssociation.problem_id == problem_id)
            .group_by(CauseAndProblemAssociation.cause_id)
            .subquery()
        )

        select_cause_id_and_worst_trend = (
            select(
                select_cause_id_and_last_period.c.cause_id,
                func.max(CauseIndicatorDataModel.trend).label("trend")
            )
            .select_from(select_cause_id_and_last_period)
            .outerjoin(CauseIndicatorModel, CauseIndicatorModel.cause_id == select_cause_id_and_last_period.c.cause_id)
            .outerjoin(CauseIndicatorDataModel, and_(
                CauseIndicatorDataModel.cause_indicator_id == CauseIndicatorModel.code,
                CauseIndicatorDataModel.period == select_cause_id_and_last_period.c.period
            ))
            .group_by(select_cause_id_and_last_period.c.cause_id)
            .subquery()
        )

        select_stmt = (
            select(
                CauseModel.id,
                CauseModel.name,
                CauseModel.type,
                CauseAndProblemAssociation.prioritized,
                select_cause_id_and_worst_trend.c.trend.label('trend'),
            )
            .select_from(CauseAndProblemAssociation)
            .join(CauseModel, CauseModel.id == CauseAndProblemAssociation.cause_id)
            .outerjoin(
                select_cause_id_and_worst_trend,
                select_cause_id_and_worst_trend.c.cause_id == CauseAndProblemAssociation.cause_id
            )
            .where(
                CauseAndProblemAssociation.problem_id == problem_id
            )
        )

        total_items = db.session.execute(select(func.count("*")).select_from(select_stmt)).scalar()
        total_pages = math.ceil(total_items / pagination_req.page_size)

        sort_method = asc_ if pagination_req.sort_type == "asc" else desc_
        select_stmt = select_stmt.order_by(sort_method(pagination_req.order_field))
        select_stmt = select_stmt.offset((pagination_req.page - 1) * pagination_req.page_size)
        select_stmt = select_stmt.limit(pagination_req.page_size)

        results = db.session.execute(select_stmt).all()
        results = [dict(zip(cols, item.tuple())) for item in results]

        return PaginationResponse(
            total_items=total_items,
            total_pages=total_pages,
            results=results
        )

    def count_all_problems(self) -> int:
        count_stmt = select(func.count(ProblemModel.id))
        return db.session.execute(count_stmt).scalar()

    def count_prioritized_problems(self) -> int:
        count_stmt = select(func.count(ProblemModel.id)).where(ProblemModel.prioritized == True)
        return db.session.execute(count_stmt).scalar()

    def count_critical_problems(self) -> int:

        count_stmt = select(
            func.count(ProblemIndicatorDataModel.problem_id)
                            ).select_from(ProblemIndicatorDataModel
                                          ).join(
            ProblemModel, 
            ProblemModel.code == ProblemIndicatorDataModel.problem_id
            ).where(ProblemIndicatorDataModel.criticality_level >= 7)

        return db.session.execute(count_stmt).scalar()

    def check_problem_exist(self, problem_id) -> bool:
        exists_stmt = (exists().where(
            ProblemModel.id == problem_id
        ))
        problem_exists = db.session.query(exists_stmt).scalar()
        return problem_exists

    def patch_problem_prioritization(self, problem_id: str, prioritized: bool) -> None:
        stmt = update(ProblemModel).where(ProblemModel.id == problem_id).values(prioritized=prioritized)
        db.session.execute(stmt)
        db.session.commit()


def count_prioritized_problems() -> int:
    count_stmt = select(func.count(ProblemModel.id)).where(ProblemModel.prioritized == True)
    return db.session.execute(count_stmt).scalar()
