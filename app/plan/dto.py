from dataclasses import field, dataclass
from datetime import date
from typing import List, Optional
from uuid import UUID


@dataclass
class CreateOrUpdatePlanRequestDTO:
    title: Optional[str]
    start_at: Optional[date]
    end_at: Optional[date]


@dataclass
class MacroObjectiveDTO:
    @dataclass
    class ProblemDTO:
        id: str
        name: str

        def to_dict(self):
            return dict(
                id=self.id,
                name=self.name,
            )

    @dataclass
    class GoalDTO:
        id: int
        initial_rate: float
        goal_value: float
        goal_justification: str
        end_at: date

        problem_id: Optional[str] = None
        custom_indicator_id: Optional[UUID] = None

        def to_dict(self):
            return dict(
                problemId=self.problem_id,
                initialRate=self.initial_rate,
                goalValue=self.goal_value,
                goalJustification=self.goal_justification,
                endAt=self.end_at
            )

    @dataclass
    class CustomIndicatorDTO:
        id: UUID
        name: str
        formula_description: str
        unit_metric: str
        source: str
        frequency: str
        baseline_value: float
        baseline_year: int
        observation: str

    id: int
    name: str
    icon_name: str
    goals: List[GoalDTO] = field(default_factory=list)
    problems: List[ProblemDTO] = field(default_factory=list)
    custom_indicators: List[CustomIndicatorDTO] = field(default_factory=list)

    @property
    def enabled(self):
        return bool(self.problems)


@dataclass
class FocusListItemDTO:
    @dataclass
    class FocusDTO:
        @dataclass
        class FocusGoalDTO:
            focus_id: int
            cause_indicator_id: int
            custom_indicator_id: int
            initial_rate: float
            goal_value: float
            goal_justification: str
            end_at: date

        @dataclass
        class CauseIndicatorDTO:
            id: int
            name: str

        @dataclass
        class CustomIndicatorDTO:
            id: UUID
            name: str
            formula_description: str
            unit_metric: str
            source: str
            frequency: str
            baseline_value: float
            baseline_year: int
            observation: str

        id: int
        name: str
        icon_name: str
        goals: List[FocusGoalDTO] = field(default_factory=list)
        cause_indicators: List[CauseIndicatorDTO] = field(default_factory=list)
        custom_indicators: List[CustomIndicatorDTO] = field(default_factory=list)

        @property
        def enabled(self):
            return bool(self.cause_indicators)

    @dataclass
    class MacroObjectiveGoalDTO:
        problem_id: str
        problem_name: str
        initial_rate: float
        goal_value: float
        goal_justification: str
        end_at: date

    @dataclass
    class ProblemDTO:
        id: str
        name: str

        def to_dict(self):
            return dict(
                id=self.id,
                name=self.name,
            )

    id: int
    name: str
    icon_name: str
    focuses: List[FocusDTO] = field(default_factory=list)
    goals: List[MacroObjectiveGoalDTO] = field(default_factory=list)
    problems: List[ProblemDTO] = field(default_factory=list)

    @property
    def enabled(self):
        return bool(self.problems)


@dataclass
class CreateOrUpdateMacroObjectiveGoalRequestDTO:
    @dataclass
    class CustomIndicatorDTO:
        id: UUID
        name: str
        formula_description: str
        unit_metric: str
        source: str
        frequency: str
        baseline_value: float
        baseline_year: int
        observation: Optional[str]

    initial_rate: float
    goal_value: float
    goal_justification: str
    end_at: date

    custom_indicators: List[CustomIndicatorDTO] = field(default_factory=list)

    id: Optional[int] = None
    problem_id: Optional[int] = None
    custom_indicator_id: Optional[str] = None


@dataclass
class UpdateFocusGoalRequestDTO:
    @dataclass
    class CustomIndicatorDTO:
        id: UUID
        name: str
        formula_description: str
        unit_metric: str
        source: str
        frequency: str
        baseline_value: float
        baseline_year: int
        observation: Optional[str]

    initial_rate: float
    goal_value: float
    goal_justification: str
    end_at: date

    custom_indicators: List[CustomIndicatorDTO] = field(default_factory=list)

    id: Optional[int] = None
    cause_indicator_id: Optional[int] = None
    custom_indicator_id: Optional[str] = None


@dataclass
class ProblemDiagnosisListItemDTO:
    problem_id: int
    problem_name: str
    problem_is_default: bool
    diagnosis: Optional[str]
    kpi_graphs: Optional[List] = field(default_factory=list)


@dataclass
class SetDiagnosisToProblemIndRequestDTO:
    problem_id: int
    diagnosis: str
    diagnosis_graphs: List = field(default_factory=list)


@dataclass
class FocusIndicatorIncludedInPLanListItemDTO:
    @dataclass
    class CauseIndicatorDTO:
        cause_indicator_id: int
        cause_indicator_name: str

    @dataclass
    class DiagnosisDTO:
        cause_indicator_id: int
        diagnosis: Optional[str]
        kpi_graphs: Optional[List] = field(default_factory=list)

    cause_id: int
    cause_name: str
    diagnoses: List[DiagnosisDTO] = field(default_factory=list)
    cause_indicators: List[CauseIndicatorDTO] = field(default_factory=list)


@dataclass
class SetDiagnosisToCauseIndRequestDTO:
    cause_indicator_id: int
    diagnosis: str
    kpi_graphs: List = field(default_factory=list)


@dataclass
class TacticalDimensionListItemDTO:
    @dataclass
    class TacticalDimensionDTO:
        @dataclass
        class GoalDTO:
            id: int
            initiative_outcome_id: int
            goal: float
            date: date

        @dataclass
        class DepartmentRoleDTO:
            id: int
            department_id: int
            role: str

        id: int = None
        start_at: date = None
        end_at: date = None
        diagnosis: str = None
        sociodemographic_targeting: str = None
        total_cost: float = None
        neighborhood_id: int = None
        goals: List[GoalDTO] = field(default_factory=list)
        department_roles: List[DepartmentRoleDTO] = field(default_factory=list)

    initiative_id: int
    initiative_name: str
    total_macro_objectives: int
    total_focuses: int
    tactical_dimension: Optional[TacticalDimensionDTO] = None


@dataclass
class SetTacticalDimensionDTO:
    initiative_id: int
    diagnosis: str
    neighborhood_id: int
    sociodemographic_targeting: str
    start_at: date
    end_at: date
    total_cost: float

    @dataclass
    class GoalDTO:
        initiative_outcome_id: int
        goal: float
        date: date

    goals: List[GoalDTO]

    @dataclass
    class DepartmentRoleDTO:
        department_id: int
        role: str

    department_roles: List[DepartmentRoleDTO]
