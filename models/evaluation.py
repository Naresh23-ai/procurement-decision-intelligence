from typing import List
from pydantic import BaseModel, Field


class CriterionEvaluation(BaseModel):
    criterion_id: int
    criterion_name: str = ''
    score: float = 0
    max_score: float = 10
    justification: str = ''
    evidence: str = ''


class SupplierEvaluation(BaseModel):
    supplier_name: str
    criteria: List[CriterionEvaluation] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    overall_summary: str = ''
    warnings: List[str] = Field(default_factory=list)
