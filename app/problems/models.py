from datetime import datetime
from typing import List

from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import Column, String, Boolean, Integer, BigInteger, JSON, ForeignKey, REAL, ARRAY, DateTime
from sqlalchemy.orm import Mapped, relationship

from app.auth.models.user_model import UserModel
from db import db


class ProblemModel(db.Model):
    __tablename__ = "problem"

    id = Column(Integer(), primary_key=True)
    code = Column(String(), nullable=True)
    name = Column(String(), nullable=False, unique=True)
    description = Column(String(), nullable=False)
    indicator_name = Column(String(), nullable=True)
    measurement_unit = Column(String(), nullable=True)
    geonet_link = Column(String(), nullable=True)

    is_default = Column(Boolean(), nullable=False, default=False)
    prioritized = Column(Boolean(), nullable=False, default=False)

    # only for custom problems
    references = Column(ARRAY(String()), nullable=False, default=list)
    annexes = relationship("AnnexCustomProblemModel", backref="custom_problem")
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(ForeignKey(UserModel.__tablename__ + ".id"), nullable=True)
    created_by: Mapped["UserModel"] = relationship()

    polarity = Column(String(), nullable=True, default='neutral')
    indicator_code = Column(String(), nullable=True)

    # relations
    associated_causes: Mapped[List["CauseAndProblemAssociation"]] = relationship(
        back_populates="problem"
    )


class AnnexCustomProblemModel(db.Model):
    __tablename__ = "annex_custom_problem_model"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    annexes_name = Column(String(100), nullable=True)
    custom_problem_id = Column(ForeignKey(ProblemModel.__tablename__ + ".id"))
    path = Column(String(255), nullable=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProblemIndicatorDataModel(db.Model):
    __tablename__ = "problem_indicator_data"

    problem_id = Column(String(), primary_key=True)
    period = Column(Integer(), primary_key=True)  # format yyyymmdd

    city_rate = Column(REAL(precision=2), nullable=True)
    total_city_incidents = Column(BigInteger(), nullable=True)

    trend = Column(REAL(precision=2), nullable=True)
    trend_normalized = Column(Integer(), nullable=True)
    trend_data = Column(JSON(), nullable=True)
    performance = Column(REAL(precision=2), nullable=True)
    performance_normalized = Column(Integer(), nullable=True)
    performance_data = Column(JSON(), nullable=True)
    relative_frequency = Column(REAL(precision=2), nullable=True)
    relative_frequency_normalized = Column(Integer(), nullable=True)
    relative_frequency_data = Column(JSON(), nullable=True)
    harm_potential = Column(Integer(), nullable=True)
    harm_potential_normalized = Column(Integer(), nullable=True)
    criticality_level = Column(Integer(), nullable=True)

    perpetrator_identification = Column(JSON(), nullable=True)
    perpetrator_victim_relationship = Column(JSON(), nullable=True)
    perpetrator_gender = Column(JSON(), nullable=True)
    perpetrator_ethnicity = Column(JSON(), nullable=True)
    perpetrator_age_range = Column(JSON(), nullable=True)
    perpetrator_academic_level = Column(JSON(), nullable=True)
    perpetrator_job_status = Column(JSON(), nullable=True)

    victim_gender = Column(JSON(), nullable=True)
    victim_ethnicity = Column(JSON(), nullable=True)
    victim_age_range = Column(JSON(), nullable=True)
    victim_academic_level = Column(JSON(), nullable=True)
    victim_job_status = Column(JSON(), nullable=True)

    date_day_type = Column(JSON(), nullable=True)
    date_day_of_the_week = Column(JSON(), nullable=True)
    date_time_of_day = Column(JSON(), nullable=True)

    concentration = Column(JSON(), nullable=True)
    place_type = Column(JSON(), nullable=True)

    weapon = Column(JSON(), nullable=True)
    typology = Column(JSON(), nullable=True)

    @property
    def updated_at(self):
        updated_at = datetime.strptime(str(self.period), "%Y%m%d")
        return updated_at

    @property
    def trend_range(self):
        return (self.updated_at - relativedelta(years=5)), self.updated_at

    @property
    def performance_range(self):
        return (self.updated_at - relativedelta(years=1)), self.updated_at

    @property
    def relative_frequency_range(self):
        return (self.updated_at - relativedelta(years=1)), self.updated_at
