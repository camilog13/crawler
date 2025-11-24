# backend/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    domain: str


class ProjectOut(BaseModel):
    id: int
    name: str
    domain: str
    created_at: datetime

    class Config:
        orm_mode = True


class CrawlOut(BaseModel):
    id: int
    project_id: int
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    site_health: float

    class Config:
        orm_mode = True


class IssueTypeOut(BaseModel):
    id: int
    code: str
    name: str
    severity: str
    category: str
    description: str
    fix_template_for_impl: str
    why_it_matters: str
    technical_notes: Optional[str]

    class Config:
        orm_mode = True


class IssueOut(BaseModel):
    id: int
    url_id: int
    issue_type: IssueTypeOut
    status: str
    implemented: bool
    details: Optional[str]
    comment: Optional[str]

    class Config:
        orm_mode = True


class IssueUpdate(BaseModel):
    implemented: Optional[bool] = None
    status: Optional[str] = None
    comment: Optional[str] = None


class UrlOut(BaseModel):
    id: int
    url: str
    status_code: Optional[int]
    title: Optional[str]
    performance_score_mobile: Optional[float]
    performance_score_desktop: Optional[float]

    class Config:
        orm_mode = True


class CrawlSummary(BaseModel):
    crawl: CrawlOut
    total_urls: int
    total_issues: int
    issues_by_severity: dict
    issues_by_category: dict
    site_health: float
