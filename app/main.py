from fastapi import FastAPI, Request, Depends, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import os, hashlib

import app.models  # noqa
from app.database import init_db, SessionLocal, get_db
from app.services.seed_service import seed_all
from app.routes import upload, projects, mapping, audit, generate, export, supplementary, data_entry
from app.models import (Client, Project, TrialBalance, AuditEntry, CoAMaster,
                         SigningBlock, CompanyProfile)
from app.models.client import Director, KMP
from app.services import (project_service, mapping_service, financial_engine, notes_engine,
                           closing_stock_service, ppe_service, note_enrichment_service, disclosure_engine)

ACCESS_CODE = os.environ.get("TCE_ACCESS_CODE", "ssaa2025")

def _check_auth(request: Request) -> bool:
    token = request.cookies.get("tce_auth")
    return token == hashlib.sha256(ACCESS_CODE.encode()).hexdigest()[:16] if token else False

LOGIN_HTML = '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SSAA Financials Tool</title><style>*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#f8f9fb;display:flex;align-items:center;justify-content:center;min-height:100vh}
.box{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:40px;width:380px;box-shadow:0 4px 20px rgba(0,0,0,0.08);text-align:center}
.box h1{color:#1a2744;font-size:22px;margin-bottom:4px}.box small{color:#c8973e;font-size:11px;letter-spacing:2px;text-transform:uppercase}
.box p{color:#64748b;font-size:13px;margin:20px 0 16px}.box input{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:6px;font-size:16px;text-align:center;letter-spacing:3px;margin-bottom:12px}
.box input:focus{outline:none;border-color:#1a2744}.box button{width:100%;padding:12px;background:#1a2744;color:#fff;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer}
.err{color:#c0392b;font-size:12px;margin-top:8px}</style></head><body>
<div class="box"><h1>SSAA Financials Tool</h1><small>Financial Statement Platform</small>
<p>Enter access code to continue</p><form method="POST" action="/login">
<input type="password" name="code" placeholder="Access Code" required autofocus>
<button type="submit">Enter</button>{error}</form></div></body></html>'''


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        print(f"DB Init: {seed_all(db)}")
    finally:
        db.close()
    yield

app = FastAPI(title="SSAA Financials Tool", version="5.0", lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

# API routers
for r, p, t in [
    (projects.router, "/api", "Clients & Projects"), (upload.router, "/api", "TB Upload"),
    (mapping.router, "/api", "Mapping"), (audit.router, "/api", "Audit"),
    (generate.router, "/api", "Generation"), (export.router, "/api", "Export"),
    (supplementary.router, "/api", "Supplementary"), (data_entry.router, "/api", "Data Entry"),
]:
    app.include_router(r, prefix=p, tags=[t])

# Auth
@app.get("/login")
def login_page():
    return HTMLResponse(LOGIN_HTML.replace("{error}", ""))

@app.post("/login")
async def login_submit(code: str = Form(...)):
    if code == ACCESS_CODE:
        resp = RedirectResponse(url="/", status_code=302)
        resp.set_cookie("tce_auth", hashlib.sha256(ACCESS_CODE.encode()).hexdigest()[:16], max_age=604800, httponly=True)
        return resp
    return HTMLResponse(LOGIN_HTML.replace("{error}", '<p class="err">Invalid code</p>'))

@app.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("tce_auth")
    return resp

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if any(path.startswith(s) for s in ["/login", "/static", "/docs", "/openapi.json", "/favicon"]):
            return await call_next(request)
        if not _check_auth(request):
            return JSONResponse({"detail": "Unauthorized"}, 401) if path.startswith("/api") else RedirectResponse("/login")
        return await call_next(request)

app.add_middleware(AuthMiddleware)


# ============= HELPERS =============
def _project_context(db, project_id):
    project = project_service.get_project(db, project_id)
    proj_obj = db.query(Project).filter(Project.id == project_id).first()
    ms = mapping_service.get_mapping_summary(db, project_id)
    coa = db.query(CoAMaster).order_by(CoAMaster.code).all()
    major = {c.code: c.particulars for c in coa if c.level in (2, 3)}
    s2m = {}
    sm = sorted(major.keys(), key=len, reverse=True)
    for c in coa:
        if c.level > 3:
            for m in sm:
                if c.code.startswith(m):
                    s2m[c.code] = m; break
    sb = db.query(SigningBlock).filter(SigningBlock.project_id == project_id).first()
    signing = {}
    if sb:
        for k in ['auditor_firm','auditor_frn','partner_name','partner_membership_no','partner_udin',
                   'director1_name','director1_din','director1_designation','director2_name','director2_din',
                   'director2_designation','place']:
            signing[k] = getattr(sb, k, '') or ''
        signing['signing_date'] = str(sb.signing_date) if sb.signing_date else ''
    return {"project": project, "proj_obj": proj_obj, "mapping": ms, "coa_codes": coa,
            "major_codes": major, "sub_to_major": s2m, "signing": signing}


# ============= LEVEL 1: FIRM DASHBOARD =============
@app.get("/")
def firm_dashboard(request: Request, db: Session = Depends(get_db)):
    clients_raw = db.query(Client).all()
    clients = []
    total_projects = ready = exported = 0
    for c in clients_raw:
        pcount = len(c.projects)
        total_projects += pcount
        for p in c.projects:
            if p.status in ('generated', 'exported'): ready += 1
            if p.status == 'exported': exported += 1
        clients.append({"id": c.id, "name": c.name, "cin": c.cin, "pan": c.pan,
                         "principal_activity": c.principal_activity, "project_count": pcount})
    return templates.TemplateResponse(request, "firm_dashboard.html", {
        "clients": clients, "total_projects": total_projects,
        "ready_count": ready, "exported_count": exported})


# ============= LEVEL 2: CLIENT DASHBOARD =============
@app.get("/client/{client_id}")
def client_dashboard(request: Request, client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return RedirectResponse("/")
    dirs = db.query(Director).filter(Director.client_id == client_id, Director.is_active == True).all()
    kmps = db.query(KMP).filter(KMP.client_id == client_id, KMP.is_active == True).all()
    projs = project_service.list_projects(db, client_id=client_id)
    return templates.TemplateResponse(request, "client_dashboard.html", {
        "client": client, "projects": projs,
        "directors": [{"id": d.id, "name": d.name, "din": d.din, "designation": d.designation} for d in dirs],
        "kmp_list": [{"id": k.id, "name": k.name, "designation": k.designation, "pan": k.pan} for k in kmps]})


# ============= LEVEL 3: PROJECT PAGES =============
@app.get("/project/{project_id}")
def project_dashboard(request: Request, project_id: int, db: Session = Depends(get_db)):
    ctx = _project_context(db, project_id)
    return templates.TemplateResponse(request, "project_dashboard.html", ctx)

@app.get("/project/{project_id}/upload")
def upload_page(request: Request, project_id: int, db: Session = Depends(get_db)):
    ctx = _project_context(db, project_id)
    tb = db.query(TrialBalance).filter(TrialBalance.project_id == project_id).all()
    ae = db.query(AuditEntry).filter(AuditEntry.project_id == project_id).all()
    return templates.TemplateResponse(request, "upload_mapping.html", {**ctx, "tb_rows": tb, "summary": ctx["mapping"], "audit_entries": ae})

@app.get("/project/{project_id}/data")
def data_page(request: Request, project_id: int, db: Session = Depends(get_db)):
    ctx = _project_context(db, project_id)
    po = ctx["proj_obj"]
    cs = closing_stock_service.get_closing_stock(db, project_id)
    st = closing_stock_service.get_applicable_stock_types(po.company_type)
    ppe = ppe_service.get_ppe_schedule(db, project_id)
    from app.models import RatioPriorYear
    rpy = db.query(RatioPriorYear).filter(RatioPriorYear.project_id == project_id).first()
    rpy_data = {}
    if rpy:
        for k in ['total_equity_py1','total_debt_py1','total_current_assets_py1','total_current_liabilities_py1',
                   'trade_receivables_py1','trade_payables_py1','inventory_py1','net_worth_py1','capital_employed_py1']:
            rpy_data[k] = getattr(rpy, k, 0)
    return templates.TemplateResponse(request, "data_entry.html", {
        **ctx, "closing_stock": cs, "stock_types": st, "ppe": ppe, "ratio_py1": rpy_data})

@app.get("/project/{project_id}/enrich")
def enrich_page(request: Request, project_id: int, db: Session = Depends(get_db)):
    ctx = _project_context(db, project_id)
    return templates.TemplateResponse(request, "enrich.html", {
        **ctx, "enrichments": note_enrichment_service.get_note_enrichments(db, project_id),
        "policies": disclosure_engine.get_policies(db, project_id),
        "disclosures": disclosure_engine.get_disclosures(db, project_id),
        "audit_entries": db.query(AuditEntry).filter(AuditEntry.project_id == project_id).all()})

@app.get("/project/{project_id}/preview")
def preview_page(request: Request, project_id: int, db: Session = Depends(get_db)):
    ctx = _project_context(db, project_id)
    try:
        pl = financial_engine.generate_pl(db, project_id)
        bs = financial_engine.generate_bs(db, project_id)
        notes = notes_engine.generate_all_notes(db, project_id)
    except Exception:
        pl = bs = notes = None
    return templates.TemplateResponse(request, "preview.html", {**ctx, "pl": pl, "bs": bs, "notes": notes})
