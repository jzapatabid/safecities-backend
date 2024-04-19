from apiflask import Schema, fields
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested

from app.plan.models import TacticalDimensionModel
from app.plan.schemas.model_schemas import InitiativeModelSchema, NeighborhoodModelSchema, \
    TacticalDimensionGoalModelSchema, TacticalDimensionDepartmentRoleModelSchema


class ListMacroObjectivesResponseSchema(Schema):
    class GoalSchema(Schema):
        id = fields.Integer()
        problem_id = fields.String(data_key="problemId")
        custom_indicator_id = fields.UUID(data_key="customIndicatorId")
        initial_rate = fields.Float(data_key="initialRate")
        goal_value = fields.Float(data_key="goalValue")
        goal_justification = fields.String(data_key="goalJustification")
        end_at = fields.Date(data_key="endAt", format="%Y-%m")

    class CustomIndicatorSchema(Schema):
        id = fields.UUID()
        name = fields.String()
        formula_description = fields.String(data_key="formulaDescription")
        unit_metric = fields.String(data_key="unitMetric")
        source = fields.String()
        frequency = fields.String()
        baseline_value = fields.Float(data_key="baselineValue")
        baseline_year = fields.Integer(data_key="baselineYear")
        observation = fields.String()

    class ProblemSchema(Schema):
        id = fields.String()
        name = fields.String()

    id = fields.Integer()
    name = fields.String()
    icon_name = fields.String(data_key="iconName")
    goals = fields.Nested(GoalSchema, many=True)
    problems = fields.Nested(ProblemSchema, many=True)
    custom_indicators = fields.Nested(CustomIndicatorSchema, many=True, data_key="customIndicators")
    enabled = fields.Boolean()


class ListFocusesResponseSchema(Schema):
    class MacroObjectiveGoalSchema(Schema):
        problem_id = fields.String(data_key="problemId")
        problem_name = fields.String(data_key="problemName")
        initial_rate = fields.Float(data_key="initialRate")
        goal_value = fields.Float(data_key="goalValue")
        goal_justification = fields.String(data_key="goalJustification")
        end_at = fields.Date(data_key="endAt", format="%Y-%m")

    class FocusSchema(Schema):
        class FocusGoalSchema(Schema):
            focus_id = fields.Integer(data_key="focusId")
            custom_indicator_id = fields.UUID(data_key="customIndicatorId")
            cause_indicator_id = fields.Integer(data_key="causeIndicatorId")
            initial_rate = fields.Float(data_key="initialRate")
            goal_value = fields.Float(data_key="goalValue")
            goal_justification = fields.String(data_key="goalJustification")
            end_at = fields.Date(data_key="endAt", format="%Y-%m")

        class CauseIndicatorSchema(Schema):
            id = fields.Integer()
            name = fields.String()

        class CustomIndicatorSchema(Schema):
            id = fields.UUID()
            name = fields.String()
            formula_description = fields.String(data_key="formulaDescription")
            unit_metric = fields.String(data_key="unitMetric")
            source = fields.String()
            frequency = fields.String()
            baseline_value = fields.Float(data_key="baselineValue")
            baseline_year = fields.Integer(data_key="baselineYear")
            observation = fields.String()

        id = fields.Integer()
        name = fields.String()
        icon_name = fields.String(data_key="iconName")
        goals = fields.Nested(FocusGoalSchema, many=True)
        cause_indicators = fields.Nested(CauseIndicatorSchema, many=True, data_key="causeIndicators")
        custom_indicators = fields.Nested(CustomIndicatorSchema, many=True, data_key="customIndicators")
        enabled = fields.Boolean()

    id = fields.Integer()
    name = fields.String()
    icon_name = fields.String(data_key="iconName")
    goals = fields.Nested(MacroObjectiveGoalSchema, many=True)
    focuses = fields.Nested(FocusSchema, many=True)
    enabled = fields.Boolean()


class DetailPlanResponseSchema(Schema):
    title = fields.String()
    start_at = fields.Date(data_key="startAt")
    end_at = fields.Date(data_key="endAt")


class TacticalDimensionResSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TacticalDimensionModel
        # include_relationships = True
        load_instance = True

    initiative = Nested(InitiativeModelSchema, only=["id", "name"])
    neighborhood = Nested(NeighborhoodModelSchema, only=["id", "name"])
    goals = Nested(
        TacticalDimensionGoalModelSchema,
        many=True,
        exclude=[
            "initiative_outcome.initiatives",
        ]
    )
    department_roles= Nested(
        TacticalDimensionDepartmentRoleModelSchema,
        many=True,
    )
