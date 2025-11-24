# backend/crud.py
from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas


def create_project(db: Session, data: schemas.ProjectCreate) -> models.Project:
    proj = models.Project(name=data.name, domain=data.domain)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


def get_projects(db: Session) -> List[models.Project]:
    return db.query(models.Project).all()


def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    return db.query(models.Project).filter_by(id=project_id).first()


def get_last_crawl_for_project(db: Session, project_id: int) -> Optional[models.Crawl]:
    return (
        db.query(models.Crawl)
        .filter_by(project_id=project_id)
        .order_by(models.Crawl.started_at.desc())
        .first()
    )
