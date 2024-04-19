from sqlalchemy import Column, Integer, String

from db import db


class NeighborhoodModel(db.Model):
    __tablename__ = "neighborhood"

    id = Column(Integer(), primary_key=True)
    name = Column(String(), nullable=False)
