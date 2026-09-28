from dataclasses import dataclass


@dataclass
class SupplierMetadata:
    supplier_name: str
    submission_date: str
    experience_rating: float
    industry: str = 'General'
    area: str = 'India'
    pdf_name: str = ''
