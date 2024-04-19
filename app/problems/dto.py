import dataclasses


@dataclasses.dataclass
class ProblemPaginationRequest:
    page: int
    page_size: int
    order_field: str
    sort_type: str


@dataclasses.dataclass
class Problem:
    id: id
    name: str
    description: str
    prioritized: str
    trend: int
    relative_incidence: int
    performance: int
    harm_potential: int
    criticality_level: int


class ProblemPaginationItemDTO:
    id: str
    name: str
    description: str
    prioritized: bool

    has_data: bool

    trend: int
    relative_incidence: int
    performance: int
    harm_potential: int
    criticality_level: int

    total_causes: int
    total_prioritized_causes: int

    def to_dict(self):
        return dict(
            id=None,
            name=None,
            description=None,
            prioritized=None,
            trend=None,
            relative_incidence=None,
            performance=None,
            harm_potential=None,
            criticality_level=None,
            total_causes=None,
            total_prioritized_causes=None,
        )
