from typing import Optional
from urllib.parse import urlparse
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecruiterDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(default=None, max_length=160)
    email: Optional[str] = Field(default=None, max_length=254)
    phone: Optional[str] = Field(default=None, max_length=40)


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message_text: str = Field(min_length=1, max_length=12000)
    company_name: str = Field(min_length=1, max_length=160)
    recruiter_details: Optional[RecruiterDetails] = None
    application_url: Optional[str] = Field(default=None, max_length=2048)
    job_listing_url: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("message_text", "company_name")
    @classmethod
    def reject_blank_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("application_url", "job_listing_url")
    @classmethod
    def validate_http_urls(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("URL must start with http:// or https:// and include a hostname.")
        if any(char.isspace() for char in value):
            raise ValueError("URL cannot contain whitespace.")
        return value


class InvestigationResponse(BaseModel):
    investigation_id: str
    overall_finding: dict
    claims: list
    search_queries: list
    sources: list
    evidence: list
    findings: list
    explanation: str
    investigation_trail: list
