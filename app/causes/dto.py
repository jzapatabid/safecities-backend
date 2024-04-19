import dataclasses
from typing import List

from app.cause_problem_association.models import CauseAndProblemAssociation


@dataclasses.dataclass
class CauseSummaryDTO:
    total_causes: int
    total_prioritized_causes: int
    total_relevant_causes: int

    def to_dict(self):
        return dict(
            totalCauses=self.total_causes,
            totalPrioritizedCauses=self.total_prioritized_causes,
            totalRelevantCauses=self.total_relevant_causes,
        )


@dataclasses.dataclass
class CauseProblemPrioritizationDTO:
    cause_id: int
    cause_name: str
    problem_id: str
    problem_name: str
    prioritized: bool

    def to_dict(self):
        return dict(
            causeId=self.cause_id,
            causeName=self.cause_name,
            problemId=self.problem_id,
            problemName=self.problem_name,
            prioritized=self.prioritized,
        )


@dataclasses.dataclass
class CauseAndProblemRelationDTO:
    cause_id: int
    problem_id: str
    prioritized: bool

    @staticmethod
    def create_from_model(model: CauseAndProblemAssociation):
        return CauseAndProblemRelationDTO(
            cause_id=model.cause_id,
            problem_id=model.problem_id,
            prioritized=model.prioritized
        )

    def to_dict(self):
        return dict(
            causeId=self.cause_id,
            problemId=self.problem_id,
            prioritized=self.prioritized,
        )


@dataclasses.dataclass
class UpdateCausePrioritizationRequestDTO:
    cause_id: int
    problem_ids_to_prioritize: List[str]
    problem_ids_to_deprioritize: List[str]
