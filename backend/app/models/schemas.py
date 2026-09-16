from pydantic import BaseModel
from typing import Optional


class RecruiterDetails(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class InvestigationRequest(BaseModel):
    message_text: str
    company_name: str
    recruiter_details: Optional[RecruiterDetails] = None
    application_url: Optional[str] = None
    job_listing_url: Optional[str] = None


class InvestigationResponse(BaseModel):
    investigation_id: str
    overall_finding: dict
    claims: list
    search_queries: list
    sources: list
    findings: list
    explanation: str
    investigation_trail: list