from sqlalchemy import select

from app.commons import bp
from app.commons.models.municipal_department_model import MunicipalDepartmentModel
from app.commons.models.neighborhood_model import NeighborhoodModel
from db import db


@bp.get("/neighborhoods")
def list_neighborhoods_controller():
    data = db.session.execute(
        select(NeighborhoodModel)
    ).scalars()
    result = list()
    for item in data:
        result.append(dict(
            id=item.id,
            name=item.name,
        ))
    return result


@bp.get("/municipal-departments")
def list_municipal_departments_controller():
    data = db.session.execute(
        select(MunicipalDepartmentModel)
    ).scalars()
    result = list()
    for item in data:
        result.append(dict(
            id=item.id,
            name=item.name,
        ))
    return result
