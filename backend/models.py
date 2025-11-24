# backend/models.py
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    crawls = relationship("Crawl", back_populates="project")


class Crawl(Base):
    __tablename__ = "crawls"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="running")  # running | finished | failed
    dataforseo_task_id = Column(String(255), nullable=True)
    site_health = Column(Float, default=0.0)

    project = relationship("Project", back_populates="crawls")
    urls = relationship("Url", back_populates="crawl", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="crawl", cascade="all, delete-orphan")


class Url(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    crawl_id = Column(Integer, ForeignKey("crawls.id"), nullable=False)
    url = Column(Text, nullable=False)

    status_code = Column(Integer, nullable=True)
    title = Column(Text, nullable=True)
    title_length = Column(Integer, nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_description_length = Column(Integer, nullable=True)
    h1 = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=True)

    # PageSpeed / performance
    performance_score_mobile = Column(Float, nullable=True)
    performance_score_desktop = Column(Float, nullable=True)
    lcp = Column(Float, nullable=True)   # en ms
    cls = Column(Float, nullable=True)
    tbt = Column(Float, nullable=True)

    crawl = relationship("Crawl", back_populates="urls")
    issues = relationship("Issue", back_populates="url", cascade="all, delete-orphan")


class IssueType(Base):
    __tablename__ = "issue_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)  # critical | major | minor
    category = Column(String(100), nullable=False)  # technical | content | performance
    description = Column(Text, nullable=False)
    fix_template_for_impl = Column(Text, nullable=False)
    why_it_matters = Column(Text, nullable=False)
    technical_notes = Column(Text, nullable=True)

    issues = relationship("Issue", back_populates="issue_type")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    crawl_id = Column(Integer, ForeignKey("crawls.id"), nullable=False)
    url_id = Column(Integer, ForeignKey("urls.id"), nullable=False)
    issue_type_id = Column(Integer, ForeignKey("issue_types.id"), nullable=False)

    status = Column(String(50), default="pending")  # pending | in_progress | done
    implemented = Column(Boolean, default=False)
    details = Column(Text, nullable=True)  # JSON string si quieres más data
    comment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    crawl = relationship("Crawl", back_populates="issues")
    url = relationship("Url", back_populates="issues")
    issue_type = relationship("IssueType", back_populates="issues")
