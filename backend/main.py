# backend/main.py
from datetime import datetime
from typing import List, Dict

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .db import Base, engine, SessionLocal
from . import models, schemas, crud
from .dataforseo_client import DataForSEOClient
from .pagespeed_client import fetch_pagespeed, extract_performance_metrics
from .issues_logic import ensure_issue_types, generate_issues_for_crawl, compute_site_health

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SEO Auditor - DataForSEO + PageSpeed",
    version="0.1.0",
    description="MVP de auditoría SEO técnica con motor de crawling DataForSEO y performance con PageSpeed Insights."
)


# -------------------------------------------------------------------
# DEPENDENCIA DB
# -------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------------
# STARTUP: asegurar catálogo de issues
# -------------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        ensure_issue_types(db)
    finally:
        db.close()


# -------------------------------------------------------------------
# PROYECTOS
# -------------------------------------------------------------------
@app.post("/projects", response_model=schemas.ProjectOut)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """
    Crear un proyecto (dominio).
    """
    existing = db.query(models.Project).filter_by(domain=project.domain).first()
    if existing:
        raise HTTPException(status_code=400, detail="Domain already exists")

    return crud.create_project(db, project)


@app.get("/projects", response_model=List[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    """
    Listar proyectos.
    """
    return crud.get_projects(db)


@app.get("/projects/{project_id}", response_model=schemas.ProjectOut)
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    """
    Detalle de un proyecto.
    """
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# -------------------------------------------------------------------
# CRAWL – EJECUCIÓN COMPLETA (DataForSEO + PageSpeed + Issues + Site Health)
# -------------------------------------------------------------------
@app.post("/projects/{project_id}/crawl", response_model=schemas.CrawlOut)
def run_crawl(project_id: int, db: Session = Depends(get_db)):
    """
    Ejecuta un crawl completo:
    1) Crea tarea en DataForSEO On-Page.
    2) Espera resultados y guarda URLs.
    3) Llama a PageSpeed por URL (estrategia mobile).
    4) Genera issues (issues_logic.generate_issues_for_crawl).
    5) Calcula Site Health.
    """
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Crear registro de Crawl
    crawl = models.Crawl(project_id=project.id, status="running")
    db.add(crawl)
    db.commit()
    db.refresh(crawl)

    # 2. DataForSEO – crear y ejecutar tarea
    df_client = DataForSEOClient()
    task_id = df_client.create_onpage_task(project.domain)
    crawl.dataforseo_task_id = task_id
    db.commit()

    # Esperar resultados
    results = df_client.wait_for_task_and_get_results(task_id)

    # 3. Mapear resultados -> tabla Url
    # NOTA: adapta los campos a la respuesta real de DataForSEO On-Page
    for r in results:
        page_url = r.get("url")
        status_code = r.get("status_code")
        meta = r.get("meta", {}) or {}
        content = r.get("content", {}) or {}

        title = meta.get("title")
        meta_description = meta.get("description")
        word_count = content.get("word_count")

        url_obj = models.Url(
            crawl_id=crawl.id,
            url=page_url,
            status_code=status_code,
            title=title,
            title_length=len(title) if title else None,
            meta_description=meta_description,
            meta_description_length=len(meta_description) if meta_description else None,
            word_count=word_count,
        )
        db.add(url_obj)

    db.commit()

    # 4. PageSpeed – performance por URL (mobile en MVP)
    urls = db.query(models.Url).filter_by(crawl_id=crawl.id).all()
    for u in urls:
        # Puedes limitar el número de URLs por crawl para controlar cuotas/costos.
        try:
            psi = fetch_pagespeed(u.url, strategy="mobile")
            perf = extract_performance_metrics(psi)

            u.performance_score_mobile = perf.get("performance_score")
            u.lcp = perf.get("lcp")
            u.cls = perf.get("cls")
            u.tbt = perf.get("tbt")

            db.add(u)
            db.commit()
        except Exception:
            # Si PSI falla, seguimos. Puedes loguear el error en la práctica.
            continue

    # 5. Generar issues a partir de datos de Url + PSI
    generate_issues_for_crawl(db, crawl)

    # 6. Calcular Site Health
    site_health = compute_site_health(db, crawl)
    crawl.site_health = site_health
    crawl.status = "finished"
    crawl.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(crawl)

    return crawl


# -------------------------------------------------------------------
# CRAWLS – LISTAR Y RESUMEN
# -------------------------------------------------------------------
@app.get("/projects/{project_id}/crawls", response_model=List[schemas.CrawlOut])
def list_crawls(project_id: int, db: Session = Depends(get_db)):
    """
    Lista los crawls de un proyecto.
    """
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    crawls = (
        db.query(models.Crawl)
        .filter_by(project_id=project.id)
        .order_by(models.Crawl.started_at.desc())
        .all()
    )
    return crawls


@app.get("/projects/{project_id}/crawls/latest/summary", response_model=schemas.CrawlSummary)
def get_latest_crawl_summary(project_id: int, db: Session = Depends(get_db)):
    """
    Devuelve un resumen del último crawl:
    - Site Health
    - Conteo de URLs
    - Conteo de issues total
    - Issues por severidad
    - Issues por categoría
    """
    crawl = crud.get_last_crawl_for_project(db, project_id)
    if not crawl:
        raise HTTPException(status_code=404, detail="No crawl found")

    total_urls = db.query(models.Url).filter_by(crawl_id=crawl.id).count()
    total_issues = db.query(models.Issue).filter_by(crawl_id=crawl.id).count()

    issues = db.query(models.Issue).filter_by(crawl_id=crawl.id).all()

    issues_by_severity: Dict[str, int] = {}
    issues_by_category: Dict[str, int] = {}

    for i in issues:
        sev = i.issue_type.severity
        cat = i.issue_type.category
        issues_by_severity[sev] = issues_by_severity.get(sev, 0) + 1
        issues_by_category[cat] = issues_by_category.get(cat, 0) + 1

    return schemas.CrawlSummary(
        crawl=crawl,
        total_urls=total_urls,
        total_issues=total_issues,
        issues_by_severity=issues_by_severity,
        issues_by_category=issues_by_category,
        site_health=crawl.site_health,
    )


# -------------------------------------------------------------------
# ISSUES – AGRUPADOS POR TIPO Y LISTADO
# -------------------------------------------------------------------
@app.get("/crawls/{crawl_id}/issues/by-type")
def issues_by_type(crawl_id: int, db: Session = Depends(get_db)):
    """
    Devuelve issues agrupados por tipo para un crawl:
    - code
    - name
    - severity
    - category
    - count
    """
    rows = (
        db.query(
            models.IssueType.code,
            models.IssueType.name,
            models.IssueType.severity,
            models.IssueType.category,
            func.count(models.Issue.id).label("count"),
        )
        .join(models.Issue, models.Issue.issue_type_id == models.IssueType.id)
        .filter(models.Issue.crawl_id == crawl_id)
        .group_by(
            models.IssueType.code,
            models.IssueType.name,
            models.IssueType.severity,
            models.IssueType.category,
        )
        .all()
    )

    return [
        {
            "code": r[0],
            "name": r[1],
            "severity": r[2],
            "category": r[3],
            "count": r[4],
        }
        for r in rows
    ]


@app.get("/crawls/{crawl_id}/issues/{issue_code}", response_model=List[schemas.IssueOut])
def list_issues_for_type(crawl_id: int, issue_code: str, db: Session = Depends(get_db)):
    """
    Lista todos los issues de un tipo (issue_code) para un crawl,
    pensado para que el frontend muestre la tabla de URLs con checkboxes.
    """
    issue_type = db.query(models.IssueType).filter_by(code=issue_code).first()
    if not issue_type:
        raise HTTPException(status_code=404, detail="Issue type not found")

    issues = (
        db.query(models.Issue)
        .filter_by(crawl_id=crawl_id, issue_type_id=issue_type.id)
        .all()
    )
    return issues


# -------------------------------------------------------------------
# URL – DETALLE
# -------------------------------------------------------------------
@app.get("/urls/{url_id}", response_model=schemas.UrlOut)
def get_url_detail(url_id: int, db: Session = Depends(get_db)):
    """
    Devuelve datos básicos de una URL:
    - url
    - status_code
    - título
    - métricas de performance
    (el frontend puede luego pedir /crawls/{crawl_id}/issues por tipo y filtrar por url_id)
    """
    u = db.query(models.Url).filter_by(id=url_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="URL not found")
    return u


# -------------------------------------------------------------------
# ISSUES – UPDATE (casilla implementado, status, comentarios)
# -------------------------------------------------------------------
@app.patch("/issues/{issue_id}", response_model=schemas.IssueOut)
def update_issue(issue_id: int, payload: schemas.IssueUpdate, db: Session = Depends(get_db)):
    """
    Actualiza un issue:
    - implemented: casilla de 'implementado'
    - status: pending | in_progress | done
    - comment: comentario del implementador / SEO
    """
    issue = db.query(models.Issue).filter_by(id=issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if payload.implemented is not None:
        issue.implemented = payload.implemented
        if payload.implemented:
            issue.status = "done"

    if payload.status is not None:
        issue.status = payload.status

    if payload.comment is not None:
        issue.comment = payload.comment

    issue.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(issue)
    return issue
