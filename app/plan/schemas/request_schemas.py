from apiflask import Schema, fields
from marshmallow import post_load, validates_schema, ValidationError, validate, validates

from app.commons.repositories import neighborhood_repo
from app.initiatives import repositories as initiative_repo
from app.plan.dto import CreateOrUpdateMacroObjectiveGoalRequestDTO, CreateOrUpdatePlanRequestDTO, \
    UpdateFocusGoalRequestDTO, SetDiagnosisToProblemIndRequestDTO, SetDiagnosisToCauseIndRequestDTO, \
    SetTacticalDimensionDTO


class CreateOrUpdatePlanRequestSchema(Schema):
    __model__ = CreateOrUpdatePlanRequestDTO

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)

    title = fields.String(required=False)
    start_at = fields.Date(required=False)
    end_at = fields.Date(required=False)


class UpdateMacroObjectiveGoalRequestSchema(Schema):
    __model__ = CreateOrUpdateMacroObjectiveGoalRequestDTO

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)

    class CustomIndicatorSchema(Schema):
        __model__ = CreateOrUpdateMacroObjectiveGoalRequestDTO.CustomIndicatorDTO

        @post_load
        def make_object(self, data, **kwargs):
            return self.__model__(**data)

        id = fields.UUID(required=True)
        name = fields.String(required=True, data_key="name")
        formula_description = fields.String(required=True, data_key="formulaDescription")
        unit_metric = fields.String(required=True, data_key="unitMetric")
        source = fields.String(required=True, data_key="source")
        frequency = fields.String(required=True, data_key="frequency")
        baseline_value = fields.Float(required=True, data_key="baselineValue")
        baseline_year = fields.Integer(required=True, data_key="baselineYear")
        observation = fields.String(required=False, data_key="observation")

    id = fields.Integer(required=False, allow_none=True)
    problem_id = fields.String(required=False, allow_none=True, data_key="problemId")
    custom_indicator_id = fields.String(required=False, allow_none=True, data_key="customIndicatorId")
    custom_indicators = fields.Nested(
        CustomIndicatorSchema, many=True, data_key="customIndicators",
        required=False, allow_none=True
    )
    initial_rate = fields.Float(required=True, data_key="initialRate")
    goal_value = fields.Float(required=True, data_key="goalValue")
    goal_justification = fields.String(required=True, data_key="goalJustification")
    end_at = fields.Date(required=True, data_key="endAt")

    @validates_schema
    def validate_upper_bound(self, data, **kwargs):
        errors = {}
        if bool(data.get("problem_id")) == bool(data.get("custom_indicator_id")):
            errors["problemId"] = ["Only one field should be filled, customIndicatorId or problemId"]
            errors["customIndicatorId"] = ["Only one field should be filled, customIndicatorId or problemId"]

        if errors:
            raise ValidationError(errors)


class UpdateFocusGoalRequestSchema(Schema):
    __model__ = UpdateFocusGoalRequestDTO

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)

    class CustomIndicatorSchema(Schema):
        __model__ = UpdateFocusGoalRequestDTO.CustomIndicatorDTO

        @post_load
        def make_object(self, data, **kwargs):
            return self.__model__(**data)

        id = fields.UUID(required=True)
        name = fields.String(required=True, data_key="name")
        formula_description = fields.String(required=True, data_key="formulaDescription")
        unit_metric = fields.String(required=True, data_key="unitMetric")
        source = fields.String(required=True, data_key="source")
        frequency = fields.String(required=True, data_key="frequency")
        baseline_value = fields.Float(required=True, data_key="baselineValue")
        baseline_year = fields.Integer(required=True, data_key="baselineYear")
        observation = fields.String(required=False, data_key="observation")

    id = fields.Integer(required=False, allow_none=True)
    cause_indicator_id = fields.String(required=False, allow_none=True, data_key="causeIndicatorId")
    custom_indicator_id = fields.String(required=False, allow_none=True, data_key="customIndicatorId")

    custom_indicators = fields.Nested(
        CustomIndicatorSchema, many=True, data_key="customIndicators",
        required=False, allow_none=True
    )
    initial_rate = fields.Float(required=True, data_key="initialRate")
    goal_value = fields.Float(required=True, data_key="goalValue")
    goal_justification = fields.String(required=True, data_key="goalJustification")
    end_at = fields.Date(required=True, data_key="endAt")

    @validates_schema
    def validate_upper_bound(self, data, **kwargs):
        errors = {}
        if bool(data.get("cause_indicator_id")) == bool(data.get("custom_indicator_id")):
            errors["causeIndicatorId"] = ["Only one field should be filled, customIndicatorId or causeIndicatorId"]
            errors["customIndicatorId"] = ["Only one field should be filled, customIndicatorId or causeIndicatorId"]

        if errors:
            raise ValidationError(errors)


class SetDiagnosisToProblemIndRequestSchema(Schema):
    __model__ = SetDiagnosisToProblemIndRequestDTO

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)

    problem_id = fields.Integer(required=True)
    diagnosis = fields.String(required=True, validate=validate.Length(min=1, error="Diagnosis can't be empty"))
    diagnosis_graphs = fields.List(
        fields.String(),
        required=False, allow_none=False,
        validate=validate.ContainsOnly(["trend", "performance", "relative_frequency"])
    )


class SetDiagnosisToCauseIndRequestSchema(Schema):
    __model__ = SetDiagnosisToCauseIndRequestDTO

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)

    cause_indicator_id = fields.Integer(required=True)
    diagnosis = fields.String(required=True, validate=validate.Length(min=1, error="Diagnosis can't be empty"))
    kpi_graphs = fields.List(
        fields.String(),
        required=False, allow_none=False,
        validate=validate.ContainsOnly(["trend", ])
    )


class SetTacticalDimensionRequestSchema(Schema):
    __model__ = SetTacticalDimensionDTO

    @post_load
    def make_object(self, data, **kwargs):
        return self.__model__(**data)

    class GoalSchema(Schema):
        __model__ = SetTacticalDimensionDTO.GoalDTO

        @post_load
        def make_object(self, data, **kwargs):
            return self.__model__(**data)

        initiative_outcome_id = fields.Integer(required=True)
        goal = fields.Decimal(required=True, places=2)
        date = fields.Date(required=True, format="%Y-%m")

        @validates("initiative_outcome_id")
        def validate_initiative_outcome_id(self, initiative_outcome_id: int):
            if not initiative_repo.check_initiative_outcome_exist_by_id(initiative_outcome_id):
                raise ValidationError("initiative_outcome_id doesn't exist")

    class DepartmentRoleSchema(Schema):
        __model__ = SetTacticalDimensionDTO.DepartmentRoleDTO

        @post_load
        def make_object(self, data, **kwargs):
            return self.__model__(**data)

        department_id = fields.Decimal(required=True, places=2)
        role = fields.String(required=True, validate=validate.Length(min=1, error='Empty value not allowed'))

        @validates("department_id")
        def validate_department_id(self, department_id: int):
            if not initiative_repo.check_municipal_department_exist_by_id(department_id):
                raise ValidationError("department_id doesn't exist")

    initiative_id = fields.Integer(required=True)
    diagnosis = fields.String(
        required=True,
        validate=validate.Length(min=1, error='Empty value not allowed')
    )
    neighborhood_id = fields.Integer(required=True)
    sociodemographic_targeting = fields.String(
        required=True,
        validate=validate.Length(min=1, error='Empty value not allowed')
    )
    start_at = fields.Date(required=True, format="%Y-%m-%d")
    end_at = fields.Date(required=True, format="%Y-%m-%d")
    total_cost = fields.Decimal(required=True, places=2)
    goals = fields.Nested(GoalSchema, many=True, validate=validate.Length(min=1))
    department_roles = fields.Nested(DepartmentRoleSchema, many=True, validate=validate.Length(min=1))

    @validates("initiative_id")
    def validate_initiative_id(self, initiative_id: int):
        if not initiative_repo.check_initiative_exist_by_id(initiative_id):
            raise ValidationError("initiative_id doesn't exist")

    @validates("neighborhood_id")
    def validate_neighborhood_id(self, neighborhood_id):
        if not neighborhood_repo.check_neighborhood_exist_by_id(neighborhood_id):
            raise ValidationError("neighborhood_id doesn't exist")
