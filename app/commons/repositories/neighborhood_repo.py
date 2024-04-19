from sqlalchemy import exists, select

from app.commons.models.neighborhood_model import NeighborhoodModel
from db import db


def check_neighborhood_exist_by_id(id: int) -> bool:
    return db.session.execute(
        select(
            exists().where(NeighborhoodModel.id == id)
        )
    ).scalar()
