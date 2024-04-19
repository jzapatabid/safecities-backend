import dataclasses
from typing import List, Dict


@dataclasses.dataclass
class PaginationRequest:
    page: int
    page_size: int
    order_field: str
    sort_type: str = "asc"

    @classmethod
    def from_dict(self, d):
        return self(**d)

    @property
    def offset(self):
        return (self.page - 1) * self.page_size


@dataclasses.dataclass
class PaginationResponse:
    total_items: int
    total_pages: int
    results: List[Dict]

    @classmethod
    def from_dict(self, d):
        return self(**d)

    def to_dict(self):
        return {
            "totalItems": self.total_items,
            "totalPages": self.total_pages,
            "results": self.results,
        }
