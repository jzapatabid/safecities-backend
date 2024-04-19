from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested

from app.commons.models.municipal_department_model import MunicipalDepartmentModel
from app.commons.models.neighborhood_model import NeighborhoodModel
from app.initiatives.models import InitiativeModel, InitiativeOutcomeModel
from app.plan.models import TacticalDimensionGoalModel, TacticalDimensionDepartmentRoleModel


class InitiativeModelSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = InitiativeModel
        include_relationships = True
        load_instance = True


class NeighborhoodModelSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = NeighborhoodModel
        include_relationships = True
        load_instance = True


class InitiativeOutcomeModelSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = InitiativeOutcomeModel
        include_relationships = True
        load_instance = True


class TacticalDimensionGoalModelSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TacticalDimensionGoalModel
        include_relationships = True
        load_instance = True

    initiative_outcome = Nested(InitiativeOutcomeModelSchema)


class MunicipalDepartmentModelSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MunicipalDepartmentModel
        include_relationships = True
        load_instance = True


class TacticalDimensionDepartmentRoleModelSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TacticalDimensionDepartmentRoleModel
        include_relationships = True
        load_instance = True

    department = Nested(MunicipalDepartmentModelSchema)
