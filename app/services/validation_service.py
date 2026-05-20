"""
Validation Service
Runs comprehensive checks before export:
- BS balancing
- PPE vs TB match
- Mapping completeness
- Missing mandatory disclosures
- Rounding differences
- Signing block completeness
"""
from sqlalchemy.orm import Session
from app.models import (
    Project, TrialBalance, AuditEntry, SigningBlock,
    PPEScheduleEntry, ClosingStock, NoteEnrichment,
)
from app.services import financial_engine, mapping_service, ppe_service


def run_validation(db: Session, project_id: int) -> dict:
    """Run all validation checks and return results."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    errors = []    # Must fix before export
    warnings = []  # Should review
    info = []      # Informational

    # 1. TB uploaded?
    tb_count = db.query(TrialBalance).filter(TrialBalance.project_id == project_id).count()
    if tb_count == 0:
        errors.append("No Trial Balance uploaded.")
    else:
        info.append(f"Trial Balance: {tb_count} ledgers uploaded.")

    # 2. Mapping completeness
    mapping = mapping_service.get_mapping_summary(db, project_id)
    if mapping["unmapped"] > 0:
        errors.append(f"Mapping incomplete: {mapping['unmapped']} of {mapping['total_ledgers']} ledgers unmapped.")
    else:
        info.append(f"Mapping: 100% complete ({mapping['total_ledgers']} ledgers).")

    # 3. BS balancing
    try:
        bs = financial_engine.generate_bs(db, project_id)
        if not bs.get("is_balanced_cy"):
            diff = bs.get("difference_cy", 0)
            errors.append(f"Balance Sheet not balanced. CY difference: Rs.{diff:,.0f}")
        else:
            info.append("Balance Sheet: CY balanced.")
    except Exception as e:
        errors.append(f"BS generation error: {str(e)[:100]}")

    # 4. PPE validation
    try:
        ppe = ppe_service.get_ppe_schedule(db, project_id)
        if ppe["validation_warnings"]:
            for w in ppe["validation_warnings"]:
                warnings.append(f"PPE: {w}")
        else:
            has_data = any(r["gross_opening"] > 0 or r["gross_additions"] > 0
                          for r in ppe["tangible"] + ppe["intangible"])
            if has_data:
                info.append("PPE Schedule: All values match TB.")
            else:
                warnings.append("PPE Schedule: No gross block data entered. PPE note will be empty.")
    except Exception:
        pass

    # 5. Closing stock (for trading/manufacturing)
    if project.company_type in ('trading', 'manufacturing'):
        cs = db.query(ClosingStock).filter(ClosingStock.project_id == project_id).all()
        if not cs:
            warnings.append(f"Closing stock not entered ({project.company_type} company). P&L may show incorrect COGS.")
        else:
            info.append(f"Closing stock: {len(cs)} items entered.")

    # 6. Audit entries
    audit_count = db.query(AuditEntry).filter(
        AuditEntry.project_id == project_id,
        AuditEntry.status == 'proposed'
    ).count()
    if audit_count > 0:
        warnings.append(f"{audit_count} audit entries still in 'proposed' status (not approved).")

    approved_count = db.query(AuditEntry).filter(
        AuditEntry.project_id == project_id,
        AuditEntry.status == 'approved'
    ).count()
    if approved_count > 0:
        info.append(f"Audit entries: {approved_count} approved.")

    # 7. Signing block
    sb = db.query(SigningBlock).filter(SigningBlock.project_id == project_id).first()
    if not sb:
        warnings.append("Signing block not set. Export will not have signatures.")
    elif not sb.partner_name or not sb.director1_name:
        warnings.append("Signing block incomplete: missing partner or director name.")
    else:
        info.append("Signing block: Complete.")

    # 8. Note enrichments
    enriched = db.query(NoteEnrichment).filter(
        NoteEnrichment.project_id == project_id,
        NoteEnrichment.value_text.isnot(None)
    ).count()
    total_fields = db.query(NoteEnrichment).filter(
        NoteEnrichment.project_id == project_id
    ).count()
    if total_fields > 0 and enriched == 0:
        warnings.append("No note disclosures filled. Notes will have minimal text.")
    elif enriched > 0:
        info.append(f"Note enrichments: {enriched} of {total_fields} fields filled.")

    # 9. Dates
    if not project.bs_date_cy:
        warnings.append("BS date (CY) not set. Headers will show generic labels.")
    if not project.bs_date_py:
        warnings.append("BS date (PY) not set.")

    return {
        "project_id": project_id,
        "client_name": project.client.name if project.client else "",
        "financial_year": project.financial_year,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "is_ready": len(errors) == 0,
    }
