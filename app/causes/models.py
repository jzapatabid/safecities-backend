from datetime import datetime, timezone
from enum import Enum
from typing import List

from dateutil.relativedelta import relativedelta
from flask import url_for
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, ARRAY, DateTime, REAL, exists, select
from sqlalchemy.orm import relationship, Mapped

from app.auth.models.user_model import UserModel
from app.cause_problem_association.models import CauseAndProblemAssociation
from app.constants import format_data_characteristics
from db import db


class CauseType(Enum):
    personalized = "personalized"
    literature_based = "literature_based"


class CauseModel(db.Model):
    __tablename__ = "cause"
    __mapper_args__ = {
        "polymorphic_identity": "cause",
        "polymorphic_on": "type",
    }

    id = Column(Integer(), primary_key=True)
    name = Column(String(), nullable=False)
    justification = Column(String(), nullable=False)
    type = Column(String(), nullable=False)
    associated_problems: Mapped[List["CauseAndProblemAssociation"]] = relationship(
        back_populates="cause"
    )
    associated_initiatives: Mapped[List["InitiativeCauseAssociationModel"]] = relationship(
        back_populates="cause"
    )


class CustomCauseModel(CauseModel):
    __tablename__ = "custom_cause"
    __mapper_args__ = {
        "polymorphic_identity": "custom_cause",
    }

    id = Column(ForeignKey(CauseModel.__tablename__ + ".id"), primary_key=True)
    evidences = Column(String(), nullable=False)
    references = Column(ARRAY(String()), nullable=True)
    problems = relationship(
        "ProblemModel",
        secondary=CauseAndProblemAssociation.__table__,
        backref="custom_causes",
        overlaps="custom_causes,problems",
        foreign_keys="[CauseAndProblemAssociation.cause_id, CauseAndProblemAssociation.problem_id]"
    )
    annexes = relationship("AnnexModel", backref="custom_cause")
    created_by_id = Column(ForeignKey(UserModel.__tablename__ + ".id"), nullable=False)
    created_by: Mapped["UserModel"] = relationship()
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        problem_list = [problem.id for problem in self.problems]
        annexes_list = [{
            "id": annex.id,
            "fileName": annex.annexes_name,
            "url": url_for("serve_uploaded_file", filename=annex.annexes_name, _external=True)
        } for annex in self.annexes]

        return {
            "id": self.id,
            "name": self.name,
            "justification": self.justification,
            "type": self.type,
            "evidences": self.evidences,
            "references": self.references,
            "problems": problem_list,
            "annexes": annexes_list,
            "createdBy": dict(
                id=self.created_by.id,
                name=self.created_by.name,
                lastName=self.created_by.last_name,
            ),
            "createdAt": int(self.created_at.replace(tzinfo=timezone.utc).timestamp()),
            "updatedAt": int(self.updated_at.replace(tzinfo=timezone.utc).timestamp()),
            "prioritized": db.session.execute(
                select(exists().where(
                    CauseAndProblemAssociation.cause_id == self.id,
                    CauseAndProblemAssociation.prioritized == True
                ))
            ).scalar()
        }


class DefaultCauseModel(CauseModel):
    __tablename__ = "default_cause"
    __mapper_args__ = {
        "polymorphic_identity": "default_cause",
    }

    id = Column(ForeignKey(CauseModel.__tablename__ + ".id"), primary_key=True)
    code = Column(String(), nullable=False)

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            justification=self.justification,
            prioritized=db.session.execute(
                select(exists().where(
                    CauseAndProblemAssociation.cause_id == self.id,
                    CauseAndProblemAssociation.prioritized == True
                ))
            ).scalar()
        )


class CauseIndicatorModel(db.Model):
    __tablename__ = 'cause_indicator'

    id = Column(Integer(), primary_key=True)
    cause_id = Column(ForeignKey(CauseModel.__tablename__ + ".id"))
    code = Column(String(), unique=False)
    name = Column(String(), unique=False)
    measurement_unit = Column(String(), nullable=False)
    polarity = Column(String(), nullable=True)

    def to_dict(self):
        return dict(
            id=self.id,
            cause_id=self.cause_id,
            code=self.code,
            name=self.name,
            measurement_unit=self.measurement_unit,
            polarity=self.polarity
        )


class CauseIndicatorDataModel(db.Model):
    __tablename__ = 'cause_indicator_data'

    cause_indicator_id = Column(String(), primary_key=True)
    period = Column(Integer(), primary_key=True)

    city_rate = Column(REAL(precision=2), nullable=True)
    total_city_incidents = Column(Integer(), nullable=True)
    total_state_incidents = Column(Integer(), nullable=True)

    trend = Column(REAL(precision=2), nullable=True)
    trend_data = Column(JSON(), nullable=True)

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

    person_gender = Column(JSON(), nullable=True)
    person_ethnicity = Column(JSON(), nullable=True)
    person_age = Column(JSON(), nullable=True)

    event_public_area_type = Column(JSON(), nullable=True)
    event_educational_area = Column(JSON(), nullable=True)
    event_grade_level = Column(JSON(), nullable=True)
    event_concentration = Column(JSON(), nullable=True)

    prisoner_gender = Column(JSON(), nullable=True)
    prisoner_ethnicity = Column(JSON(), nullable=True)
    prisoner_age = Column(JSON(), nullable=True)
    prisoner_academic_level = Column(JSON(), nullable=True)
    felony_type = Column(JSON(), nullable=True)
    recidivism_quantity = Column(JSON(), nullable=True)
    place_concentration = Column(JSON(), nullable=True)
    
    @property
    def updated_at(self):
        updated_at = datetime.strptime(str(self.period), "%Y%m%d")
        return updated_at

    @property
    def trend_range(self):
        return (self.updated_at - relativedelta(years=5)), self.updated_at

    def to_dict(self):
        data_characteristics = format_data_characteristics(
            {str(column_name.name): getattr(self, str(column_name.name)) for column_name in self.__table__.columns}
        )
        period = str(self.period)
        return {
            "causeIndicatorId": self.cause_indicator_id,
            "period": self.period,
            "updatedAt": f"{period[:4]}-{period[4:6]}-{period[6:]}",
            "totalCityIncidents": self.total_city_incidents,
            "totalStateIncidents": self.total_state_incidents,
            "cityRate": self.city_rate,
            "kpi": {
                "trend": self.trend,
                "trendData": self.trend_data,
                "concentrationData": self.concentration,
            },
            "dataCharacteristics": data_characteristics
        }


class AnnexModel(db.Model):
    __tablename__ = "annex_model"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    annexes_name = Column(String(100), nullable=True)
    custom_cause_id = Column(ForeignKey(CustomCauseModel.__tablename__ + ".id"))
    path = Column(String(255), nullable=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_json(self):
        problem_list = [problem.id for problem in self.problems]
        annexes_list = [{"file_id": annex.id, "file_name": annex.annexes_name} for annex in self.annexes]

        return {
            "id": self.id,
            "name": self.name,
            "justification": self.justification,
            "type": self.type,
            "evidences": self.evidences,
            "references": self.references,
            "problems": problem_list,
            "annexes": annexes_list,
        }
