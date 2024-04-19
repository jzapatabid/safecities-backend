from sqlalchemy import Column, Integer, String

from db import db


class MunicipalDepartmentModel(db.Model):
    __tablename__ = "municipal_department"

    id = Column(Integer(), primary_key=True)
    name = Column(String(), nullable=False, unique=True)

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
        )
