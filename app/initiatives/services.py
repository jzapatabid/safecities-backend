import logging
import math
from http import HTTPStatus
from typing import Dict, Optional, List, Generator

from apiflask import abort
from sqlalchemy import select, exists, delete, distinct, func
from sqlalchemy.orm import joinedload

from app.cause_problem_association.models import CauseAndProblemAssociation
from app.causes.models import CauseModel
from app.commons.dto.pagination import PaginationResponse
from app.commons.models.file_model import FileModel
from app.commons.models.municipal_department_model import MunicipalDepartmentModel
from app.initiatives import repositories
from app.initiatives.dto import InitiativeDetailDTO, InitiativeAssociationDto, \
    InitiativePrioritizationRequestDTO
from app.initiatives.models import InitiativeModel, InitiativePrioritizationModel, \
    municipal_department_per_initiative_association_table, InitiativeCauseAssociationModel, InitiativeOutcomeModel
from app.initiatives.repositories import InitiativeRepository
from app.problems.models import ProblemModel
from db import db


def check_municipal_department_id_exist(municipal_department_id):
    exist = db.session.execute(
        select(exists().where(MunicipalDepartmentModel.id == municipal_department_id))
    ).scalar()
    return exist


def check_initiative_name_already_exist(name):
    exist = db.session.execute(
        select(exists().where(InitiativeModel.name == name))
    ).scalar()
    return exist


def check_initiative_is_prioritized(initiative_id):
    select_stmt = select(exists().where(
        InitiativePrioritizationModel.initiative_id == initiative_id,
    ))
    prioritized = db.session.execute(select_stmt).scalar()
    return prioritized


def create_initiative(initiative_dict: Dict):
    file_model_ids = list()

    try:
        for file in initiative_dict.get("annex_files", list()):
            file_model = FileModel.store_file(file)
            file_model_ids.append(file_model.id)

        initiative_obj = InitiativeModel(
            name=initiative_dict["name"],
            justification=initiative_dict["justification"],
            evidences=initiative_dict["evidences"],
            cost_level=initiative_dict["cost_level"],
            efficiency_level=initiative_dict["efficiency_level"],
            reference_urls=initiative_dict.get("reference_urls", list()),
            annex_ids=file_model_ids
        )
        db.session.add(initiative_obj)
        db.session.flush()

        # Match initiative with municipal departments
        db.session.execute(municipal_department_per_initiative_association_table.insert().values(
            [
                dict(
                    initiative_id=initiative_obj.id,
                    municipal_department_id=municipal_department_id
                )
                for municipal_department_id in initiative_dict["municipal_department_ids"]
            ]
        ))

        # Match initiative with causes
        db.session.add_all(
            [
                InitiativeCauseAssociationModel(
                    initiative_id=initiative_obj.id,
                    cause_id=cause_id,
                )
                for cause_id in initiative_dict["cause_ids"]
            ]
        )

        db.session.commit()
        return initiative_obj
    except Exception:
        db.session.rollback()
        raise


def update_initiative(initiative_model: InitiativeModel, initiative_dict: Dict):
    try:
        initiative_model.name = initiative_dict.get("name", initiative_model.name)
        initiative_model.justification = initiative_dict.get("justification", initiative_model.justification)
        initiative_model.evidences = initiative_dict.get("evidences", initiative_model.evidences)
        initiative_model.cost_level = initiative_dict.get("cost_level", initiative_model.efficiency_level)
        initiative_model.efficiency_level = initiative_dict.get("efficiency_level", initiative_model.efficiency_level)
        initiative_model.reference_urls = initiative_dict.get("reference_urls", initiative_model.reference_urls)

        annexes_to_edit_ids = list(initiative_model.annex_ids)
        for file in initiative_dict.get("annex_files", list()):
            file_model = FileModel.store_file(file, commit=True)
            annexes_to_edit_ids.append(file_model.id)

        for file_to_delete_id in initiative_dict.get("annex_files_to_delete_ids", list()):
            if file_to_delete_id in annexes_to_edit_ids:
                annexes_to_edit_ids.remove(file_to_delete_id)
                FileModel.remove_file(file_to_delete_id, commit=True)

        initiative_model.annex_ids = annexes_to_edit_ids
        db.session.add(initiative_model)

        if "municipal_department_ids" in initiative_dict:
            prev_id_related_ls = list([item.id for item in initiative_model.municipal_departments])
            municipal_department_ids_to_delete_ls = list(prev_id_related_ls)
            municipal_department_ids_to_add_ls = list()
            for municipal_department_id in initiative_dict["municipal_department_ids"]:
                if municipal_department_id in prev_id_related_ls:
                    municipal_department_ids_to_delete_ls.remove(municipal_department_id)
                else:
                    municipal_department_ids_to_add_ls.append(municipal_department_id)

            if municipal_department_ids_to_add_ls:
                db.session.execute(municipal_department_per_initiative_association_table.insert().values(
                    [
                        dict(initiative_id=initiative_model.id, municipal_department_id=municipal_department_id)
                        for municipal_department_id in municipal_department_ids_to_add_ls
                    ]
                ))

            if municipal_department_ids_to_delete_ls:
                db.session.execute(
                    delete(municipal_department_per_initiative_association_table)
                    .where(
                        municipal_department_per_initiative_association_table.c.initiative_id == initiative_model.id,
                        municipal_department_per_initiative_association_table.c.municipal_department_id.in_(
                            municipal_department_ids_to_delete_ls
                        )
                    )
                )

        if "cause_ids" in initiative_dict:
            cause_id_prev_related_ls = db.session.execute(
                select(InitiativeCauseAssociationModel.cause_id)
                .where(InitiativeCauseAssociationModel.initiative_id == initiative_model.id)
            ).scalars().all()
            cause_id_to_delete_ls = list(cause_id_prev_related_ls)
            for cause_id in initiative_dict["cause_ids"]:
                if cause_id in cause_id_prev_related_ls:
                    cause_id_to_delete_ls.remove(cause_id)
                    continue
                else:
                    db.session.add(
                        InitiativeCauseAssociationModel(
                            cause_id=cause_id,
                            initiative_id=initiative_model.id
                        )
                    )
            db.session.execute(
                delete(InitiativeCauseAssociationModel)
                .where(
                    InitiativeCauseAssociationModel.initiative_id == initiative_model.id,
                    InitiativeCauseAssociationModel.cause_id.in_(cause_id_to_delete_ls)
                )
            )

        db.session.commit()
        return initiative_model
    except Exception:
        db.session.rollback()
        raise


def get_initiative(initiative_id) -> InitiativeDetailDTO:
    initiative_model, prioritized = db.session.execute(
        select(
            InitiativeModel,
            exists(InitiativePrioritizationModel.initiative_id)
            .where(InitiativePrioritizationModel.initiative_id == InitiativeModel.id)
        )
        .options(joinedload(InitiativeModel.associated_causes).subqueryload(InitiativeCauseAssociationModel.cause))
        .options(joinedload(InitiativeModel.municipal_departments))
        .where(InitiativeModel.id == initiative_id)
        .limit(1)
    ).first()
    if not initiative_model:
        abort(HTTPStatus.NOT_FOUND)
    return InitiativeDetailDTO.create_from_model(initiative_model, prioritized)


def get_initiative_model(initiative_id) -> Optional[InitiativeModel]:
    initiative_obj: InitiativeModel = db.session.execute(
        select(InitiativeModel).where(InitiativeModel.id == initiative_id).limit(1)
    ).scalar()
    return initiative_obj


def delete_initiative(initiative_id):
    db.session.execute(
        delete(InitiativeModel)
        .where(InitiativeModel.id == initiative_id)
    )
    db.session.commit()


def list_initiative_association(initiative_ids: List[int]) -> Generator[InitiativeAssociationDto, None, None]:
    default_initiative_ids, custom_initiative_ids = repositories.get_initiative_types(initiative_ids)
    default_initiative_ids = list(default_initiative_ids)
    custom_initiative_ids = list(custom_initiative_ids)

    initiative_association_ls = repositories.list_default_initiative_association(default_initiative_ids)
    initiative_association_ls += repositories.list_custom_initiative_association(custom_initiative_ids)
    for initiative_id, initiative_name, cause_id, cause_name, problem_id, problem_name, prioritized, problem_prioritized in initiative_association_ls:
        yield InitiativeAssociationDto(
            initiative_id=initiative_id,
            initiative_name=initiative_name,
            cause_id=cause_id,
            cause_name=cause_name,
            problem_id=problem_id,
            problem_name=problem_name,
            prioritized=prioritized,
            problem_prioritized=problem_prioritized
        )


def bulk_update_initiative_prioritization(
        to_prioritize: List[InitiativePrioritizationRequestDTO],
        to_deprioritize: List[InitiativePrioritizationRequestDTO]
):
    for item in to_prioritize:
        prioritization_is_valid = repositories.check_initiative_prioritization_is_valid(
            item.initiative_id, item.cause_id, item.problem_id
        )
        if not prioritization_is_valid:
            abort(
                HTTPStatus.BAD_REQUEST,
                f"Initiatives, cause and problem aren't related so can't be prioritized, initiative_id={item.initiative_id} cause_id={item.cause_id} problem_id={item.problem_id}"
            )
        repositories.prioritize_initiative(item.initiative_id, item.cause_id, item.problem_id)

    for item in to_deprioritize:
        repositories.deprioritize_initiative(item.initiative_id, item.cause_id, item.problem_id)

    db.session.commit()


class InitiativeService:
    def __init__(self):
        self.user_repo = InitiativeRepository()
        self.logger = logging.getLogger(__name__)

    def get_initiative_list_service(self, pagination_req, prioritized_filter):
        initiative_list = self.user_repo.get_initiative_list_repo(pagination_req, prioritized_filter)
        result = []
        for row in initiative_list:
            initiative_id, initiative_name, prioritized, justification, evidences, cost_level, efficiency_level, total_cause_count, total_problem_count = row
            result.append({
                "initiativeId": initiative_id,
                "initiativeName": initiative_name,
                "justification": justification,
                "evidences": evidences,
                "prioritized": prioritized,
                "costLevel": cost_level,
                "efficiencyLevel": efficiency_level,
                "totalCauseCount": total_cause_count,
                "totalProblemCount": total_problem_count,
            })

        row = self.user_repo.total_items()
        total_items = row[0]
        total_pages = math.ceil(total_items / pagination_req.page_size)

        return PaginationResponse(
            total_items=total_items,
            total_pages=total_pages,
            results=result
        )


def list_causes_options():
    from app.causes.models import CauseModel
    from app.cause_problem_association.models import CauseAndProblemAssociation

    column_names = ["id", "name"]
    results = db.session.execute(
        select(distinct(CauseModel.id), CauseModel.name)
        .where(
            CauseAndProblemAssociation.prioritized == True,
            CauseAndProblemAssociation.cause_id == CauseModel.id
        )
    ).all()

    results = [dict(zip(column_names, item.tuple())) for item in results]
    return results


def list_municipal_departments_options():
    column_names = ["id", "name"]
    results = db.session.execute(select(MunicipalDepartmentModel.id, MunicipalDepartmentModel.name)).all()
    results = [dict(zip(column_names, item.tuple())) for item in results]
    return results


def get_summary():
    total_problems_query = select(func.count(ProblemModel.id))
    total_prioritized_problems_query = select(func.count(ProblemModel.id)).where(ProblemModel.prioritized == True)
    total_causes_query = select(func.count(CauseModel.id))
    total_prioritized_causes_query = select(func.count(distinct(CauseModel.id))) \
        .where(CauseAndProblemAssociation.cause_id == CauseModel.id, CauseAndProblemAssociation.prioritized == True)

    rs = db.session.execute(
        select(
            total_problems_query.subquery(),
            total_prioritized_problems_query.subquery(),
            total_causes_query.subquery(),
            total_prioritized_causes_query.subquery()
        )
    ).first()

    return dict(
        totalProblems=rs[0],
        totalPrioritizedProblems=rs[1],
        totalCauses=rs[2],
        totalPrioritizedCauses=rs[3],
    )


def list_initiative_outcomes(initiative_id: int) -> List[InitiativeOutcomeModel]:
    return repositories.list_initiative_outcomes(initiative_id)
