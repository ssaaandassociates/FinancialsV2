"""
PDF Export Service
Generates A4 PDF of key financial statements: BS, PL, Notes, Cash Flow.
Uses reportlab for PDF generation.
Includes signing block at the bottom of BS and PL pages.
"""
import os
from sqlalchemy.orm import Session
from app.models import Project, Client, SigningBlock
from app.services import financial_engine, notes_engine, cashflow_engine
from app.config import OUTPUT_DIR


def generate_pdf(db: Session, project_id: int) -> str:
    """Generate PDF financial statements."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        raise ImportError("reportlab not installed. Run: pip install reportlab")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")
    client = project.client
    company = client.name

    # Generate data
    bs = financial_engine.generate_bs(db, project_id)
    pl = financial_engine.generate_pl(db, project_id)
    notes = notes_engine.generate_all_notes(db, project_id)

    # Signing block
    sb = db.query(SigningBlock).filter(SigningBlock.project_id == project_id).first()

    # Setup PDF
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"FS_{client.name[:20]}_{project.financial_year}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename.replace(" ", "_"))

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=14,
                                  spaceAfter=4, textColor=colors.HexColor('#1a2744'))
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10,
                                     alignment=1, textColor=colors.HexColor('#2d3f5e'))
    normal_style = styles['Normal']
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8)

    elements = []

    def fmt(val):
        if val is None or val == 0:
            return "-"
        return f"{val:,.0f}"

    navy = colors.HexColor('#1a2744')
    gold = colors.HexColor('#c8973e')
    light = colors.HexColor('#e8ecf3')

    def add_fs_table(title, subtitle, headers, rows, col_widths):
        """Add a financial statement table to the PDF."""
        elements.append(Paragraph(company, title_style))
        elements.append(Paragraph(subtitle, subtitle_style))
        elements.append(Spacer(1, 8))

        data = [headers]
        for row in rows:
            data.append(row)

        table = Table(data, colWidths=col_widths, repeatRows=1)
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light]),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]

        # Bold total rows
        for i, row in enumerate(rows, 1):
            if isinstance(row[1], str) and ('TOTAL' in row[1].upper() or 'PROFIT' in row[1].upper()):
                style.append(('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'))
                style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#e8ecf3')))

        table.setStyle(TableStyle(style))
        elements.append(table)

    def add_signing():
        if not sb:
            return
        elements.append(Spacer(1, 20))
        sign_data = [
            [f"For {sb.auditor_firm or ''}", "", f"For and on behalf of Board of Directors of"],
            ["Chartered Accountants", "", company],
            [f"FRN: {sb.auditor_frn or ''}", "", ""],
            ["", "", ""],
            [sb.partner_name or "", "", f"{sb.director1_name or ''}          {sb.director2_name or ''}"],
            ["Partner", "", f"{sb.director1_designation or 'Director'}          {sb.director2_designation or 'Director'}"],
            [f"M.No.: {sb.partner_membership_no or ''}", "", f"DIN: {sb.director1_din or ''}          DIN: {sb.director2_din or ''}"],
            ["", "", ""],
            [f"Place: {sb.place or ''}", "", f"Place: {sb.place or ''}"],
            [f"Date: {sb.signing_date or ''}", "", f"Date: {sb.signing_date or ''}"],
            [f"UDIN: {sb.partner_udin or ''}", "", ""],
        ]
        st = Table(sign_data, colWidths=[180, 60, 280])
        st.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        elements.append(st)

    # ===== BALANCE SHEET =====
    bs_rows = []
    for item in bs["line_items"]:
        sno, text, note_ref, cy, py, level, is_total = item
        bs_rows.append([sno or "", text or "", note_ref or "", fmt(cy), fmt(py)])

    add_fs_table(
        "Balance Sheet", f"Balance Sheet {project.bs_header_cy}",
        ["", "Particulars", "Note", project.bs_header_cy, project.bs_header_py],
        bs_rows, [20, 220, 30, 80, 80]
    )
    add_signing()
    elements.append(PageBreak())

    # ===== PROFIT & LOSS =====
    pl_rows = []
    for item in pl["line_items"]:
        sno, text, note_ref, cy, py, level, is_total = item
        pl_rows.append([sno or "", text or "", note_ref or "", fmt(cy), fmt(py)])

    add_fs_table(
        "Profit & Loss", f"Statement of Profit and Loss {project.pl_header_cy}",
        ["", "Particulars", "Note", project.pl_header_cy, project.pl_header_py],
        pl_rows, [20, 220, 30, 80, 80]
    )
    add_signing()

    # Build PDF
    doc.build(elements)
    return filepath
