from fastapi import FastAPI, Request, Depends, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import os, hashlib

import app.models  # noqa
from app.database import init_db, SessionLocal, get_db
from app.services.seed_service import seed_all
from app.routes import upload, projects, mapping, audit, generate, export, supplementary, data_entry, templates as templates_router
from app.models import (Client, Project, TrialBalance, AuditEntry, CoAMaster,
                         SigningBlock, CompanyProfile, ClientShareholder, CustomCoACode, ClientPolicy)
from app.models.client import Director
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://financialsv2-production.up.railway.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

# API routers
for r, p, t in [
    (projects.router, "/api", "Clients & Projects"), (upload.router, "/api", "TB Upload"),
    (mapping.router, "/api", "Mapping"), (audit.router, "/api", "Audit"),
    (generate.router, "/api", "Generation"), (export.router, "/api", "Export"),
    (supplementary.router, "/api", "Supplementary"), (data_entry.router, "/api", "Data Entry"),
    (templates_router.router, "/api", "Templates"),
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
        if any(path.startswith(s) for s in ["/login", "/static", "/docs", "/openapi.json", "/favicon", "/health"]):
            return await call_next(request)
        # When Supabase auth is enabled, an Authorization: Bearer token on an
        # /api request is a valid alternative to the legacy cookie. The per-route
        # get_current_firm_id dependency does the real verification + scoping;
        # here we just let it through so that dependency can run.
        from app.config import AUTH_ENABLED
        if AUTH_ENABLED and path.startswith("/api"):
            auth_header = request.headers.get("authorization", "")
            if auth_header.lower().startswith("bearer "):
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

    # Merge custom CoA codes from client into the code list
    if proj_obj:
        custom = db.query(CustomCoACode).filter(CustomCoACode.client_id == proj_obj.client_id).all()
        for cc in custom:
            # Create a CoA-like object for template compatibility
            class _Fake:
                pass
            f = _Fake()
            f.code = cc.code; f.particulars = cc.particulars; f.level = 5
            f.nature = cc.nature; f.fs_type = cc.fs_type; f.note_ref = cc.note_ref
            f.schedule_ref = None; f.tally_group = None; f.remarks = "Custom"
            coa.append(f)
        coa.sort(key=lambda c: c.code)

    # Build major dropdown = codes that are PARENTS of something (i.e. have children).
    # Avoids the prior bug where level-based logic missed PL-01-style parents whose
    # children are L3 leaves.
    parents_used = {c.parent_code for c in coa if c.parent_code}
    major = {c.code: c.particulars for c in coa if c.code in parents_used}

    # Build sub→major map directly from parent_code. Walk up the tree if the
    # immediate parent isn't itself in `major` (handles 3-level chains).
    code_by = {c.code: c for c in coa}
    s2m = {}
    for c in coa:
        if c.code in major:
            continue  # it's a parent itself, not a sub
        p = c.parent_code
        # Walk up until we find a code that's in the major set
        seen = 0
        while p and p not in major and seen < 6:
            parent_obj = code_by.get(p)
            p = parent_obj.parent_code if parent_obj else None
            seen += 1
        if p:
            s2m[c.code] = p
        # Codes with no traceable major parent get omitted from the sub dropdown.
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
    shareholders = db.query(ClientShareholder).filter(ClientShareholder.client_id == client_id).all()
    projs = project_service.list_projects(db, client_id=client_id)
    kmp_list = [d for d in dirs if d.is_kmp]
    custom_codes = db.query(CustomCoACode).filter(CustomCoACode.client_id == client_id).all()
    policies = db.query(ClientPolicy).filter(
        ClientPolicy.client_id == client_id, ClientPolicy.is_active == True
    ).order_by(ClientPolicy.policy_number).all()
    return templates.TemplateResponse(request, "client_dashboard.html", {
        "client": client, "projects": projs,
        "directors": [{"id": d.id, "name": d.name, "din": d.din, "designation": d.designation,
                        "is_kmp": d.is_kmp, "signs_financials": d.signs_financials} for d in dirs],
        "kmp_list": [{"id": d.id, "name": d.name, "designation": d.designation, "pan": d.pan, "din": d.din} for d in kmp_list],
        "shareholders": [{"id": s.id, "name": s.name, "no_of_shares_cy": s.no_of_shares_cy,
                           "no_of_shares_py": s.no_of_shares_py, "face_value": s.face_value,
                           "share_capital_cy": s.share_capital_cy, "share_capital_py": s.share_capital_py,
                           "pct_holding_cy": s.pct_holding_cy, "pct_holding_py": s.pct_holding_py,
                           "is_promoter": s.is_promoter, "is_director": s.is_director, "din": s.din} for s in shareholders],
        "custom_codes": [{"id": c.id, "code": c.code, "particulars": c.particulars,
                           "parent_code": c.parent_code, "nature": c.nature, "fs_type": c.fs_type} for c in custom_codes],
        "policies": [{"id": p.id, "policy_number": p.policy_number, "title": p.title,
                       "body": p.body, "is_active": p.is_active} for p in policies],
    })


# ============= LEVEL 3: PROJECT PAGES =============
@app.get("/project/{project_id}")
def project_dashboard(request: Request, project_id: int, db: Session = Depends(get_db)):
    ctx = _project_context(db, project_id)
    return templates.TemplateResponse(request, "project_dashboard.html", ctx)

@app.get("/project/{project_id}/audit")
def audit_page(request: Request, project_id: int, db: Session = Depends(get_db)):
    """Dedicated audit entries page (Section 2)."""
    ctx = _project_context(db, project_id)
    entries = db.query(AuditEntry).filter(AuditEntry.project_id == project_id).order_by(AuditEntry.entry_no).all()

    # Enrich with particulars from CoA
    coa_lookup = {c.code: c.particulars for c in ctx["coa_codes"]}
    audit_data = []
    for e in entries:
        audit_data.append({
            "id": e.id, "entry_no": e.entry_no, "date": e.date,
            "narration": e.narration, "amount": e.amount, "status": e.status,
            "dr_coa_code": e.dr_coa_code, "cr_coa_code": e.cr_coa_code,
            "dr_particulars": coa_lookup.get(e.dr_coa_code, ""),
            "cr_particulars": coa_lookup.get(e.cr_coa_code, ""),
        })

    return templates.TemplateResponse(request, "audit.html", {
        **ctx, "audit_entries": audit_data})


@app.get("/project/{project_id}/upload")
def upload_page(request: Request, project_id: int, db: Session = Depends(get_db)):
    ctx = _project_context(db, project_id)
    tb = db.query(TrialBalance).filter(TrialBalance.project_id == project_id).all()
    ae = db.query(AuditEntry).filter(AuditEntry.project_id == project_id).all()
    # C7: Unique Tally groups for filter dropdown
    tally_groups = sorted(set(r.tally_group for r in tb if r.tally_group))
    # Set of custom CoA codes (for "Custom CoA" filter pill)
    po = ctx["proj_obj"]
    custom_codes_set = set()
    if po:
        custom_codes_set = {cc.code for cc in db.query(CustomCoACode).filter(
            CustomCoACode.client_id == po.client_id).all()}
    return templates.TemplateResponse(request, "upload_mapping.html", {
        **ctx, "tb_rows": tb, "summary": ctx["mapping"], "audit_entries": ae,
        "tally_groups": tally_groups, "custom_codes_set": custom_codes_set})

@app.get("/project/{project_id}/data")
def data_page(request: Request, project_id: int, db: Session = Depends(get_db)):
    ctx = _project_context(db, project_id)
    po = ctx["proj_obj"]
    cs_list = closing_stock_service.get_closing_stock(db, project_id)
    st = closing_stock_service.get_applicable_stock_types(po.company_type)
    # Convert list to dict keyed by stock_type
    cs = {}
    for item in cs_list:
        cs[item['stock_type']] = {'cy': item.get('cy_amount', 0), 'py': item.get('py_amount', 0)}
    ppe = ppe_service.get_ppe_schedule(db, project_id)
    from app.models import RatioPriorYear
    rpy = db.query(RatioPriorYear).filter(RatioPriorYear.project_id == project_id).first()
    rpy_data = {}
    if rpy:
        for k in ['total_equity_py1','total_debt_py1','total_current_assets_py1','total_current_liabilities_py1',
                   'trade_receivables_py1','trade_payables_py1','inventory_py1','net_worth_py1','capital_employed_py1']:
            rpy_data[k] = getattr(rpy, k, 0)
    # Section 5 V9: TB-derived ageing matrices
    from app.services import ageing_engine
    tr_matrix = ageing_engine.derive_tr_matrix_from_tb(db, project_id)
    tp_matrix = ageing_engine.derive_tp_matrix_from_tb(db, project_id)
    ageing_status = ageing_engine.has_any_tr_tp_mapping(db, project_id)
    # Section 6 V9: company-type flag for service company UI gating
    is_service = (po.company_type or '').lower() == 'service'
    # Section 8 V9: compute ratios live for side-by-side display
    from app.services import ratio_engine
    try:
        ratios_result = ratio_engine.generate_ratios(db, project_id, py_minus_1_data=rpy_data or None)
    except Exception:
        ratios_result = {"ratios": [], "flagged_count": 0}
    return templates.TemplateResponse(request, "data_entry.html", {
        **ctx, "closing_stock": cs, "stock_types": st, "ppe": ppe, "ratio_py1": rpy_data,
        "tr_matrix": tr_matrix, "tp_matrix": tp_matrix, "ageing_status": ageing_status,
        "is_service_company": is_service, "ratios_result": ratios_result})

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

    # Section 9 V9 — additional preview tabs
    from app.services import cashflow_engine, ratio_engine, eps_engine
    from app.models import RatioPriorYear
    try:
        cashflow = cashflow_engine.generate_cashflow(db, project_id)
    except Exception:
        cashflow = None

    rpy = db.query(RatioPriorYear).filter(RatioPriorYear.project_id == project_id).first()
    rpy_data = {}
    if rpy:
        for k in ['total_equity_py1','total_debt_py1','total_current_assets_py1','total_current_liabilities_py1',
                  'trade_receivables_py1','trade_payables_py1','inventory_py1','net_worth_py1','capital_employed_py1']:
            rpy_data[k] = getattr(rpy, k, 0)
    try:
        ratios = ratio_engine.generate_ratios(db, project_id, py_minus_1_data=rpy_data or None)
    except Exception:
        ratios = None

    try:
        eps = eps_engine.generate_eps(db, project_id)
    except Exception:
        eps = None

    return templates.TemplateResponse(request, "preview.html",
        {**ctx, "pl": pl, "bs": bs, "notes": notes,
         "cashflow": cashflow, "ratios": ratios, "eps": eps})
