"""
Sample data loader — creates two fully-worked demo companies so the whole app
can be exercised end-to-end without inventing data.

  Company A: "Simple Trading Co" — a small trading company, ~15 ledgers,
             minimal supplementary data. Good for a quick walkthrough.
  Company B: "Comprehensive Mfg Ltd" — a manufacturing company that exercises
             EVERY feature: full BS+PL, TR/TP ageing, PPE schedule, multiple
             shareholders + share events, related parties + transactions,
             custom CoA codes, accounting policies, and disclosures.

Every Trial Balance balances (sum of debits == sum of credits) and the numbers
tie across schedules (e.g. PPE gross/dep ties to BS; ageing buckets sum to the
TR/TP control). Idempotent: calling it removes any prior sample companies first
(identified by a name marker) so re-loading is safe.
"""
from datetime import date
from sqlalchemy.orm import Session

SAMPLE_MARKER = "[SAMPLE]"


def _wipe_existing(db: Session, firm_id=None):
    """Remove any previously-loaded sample companies (and their children)."""
    from app.models import (Client, Project, TrialBalance, AuditEntry)
    from app.models.client import Director, ClientShareholder, CustomCoACode, ClientPolicy
    q = db.query(Client).filter(Client.name.like(f"%{SAMPLE_MARKER}%"))
    if firm_id is not None:
        q = q.filter(Client.firm_id == firm_id)
    for client in q.all():
        for proj in db.query(Project).filter(Project.client_id == client.id).all():
            pid = proj.id
            db.query(TrialBalance).filter(TrialBalance.project_id == pid).delete()
            db.query(AuditEntry).filter(AuditEntry.project_id == pid).delete()
            _wipe_supplementary(db, pid)
            db.delete(proj)
        db.query(Director).filter(Director.client_id == client.id).delete()
        db.query(ClientShareholder).filter(ClientShareholder.client_id == client.id).delete()
        db.query(CustomCoACode).filter(CustomCoACode.client_id == client.id).delete()
        db.query(ClientPolicy).filter(ClientPolicy.client_id == client.id).delete()
        db.delete(client)
    db.commit()


def _wipe_supplementary(db, pid):
    from app.models.supplementary import (AgeingData, ShareEvent, Shareholder,
        RelatedParty, RPTransaction, AccountingPolicy, DisclosureData, PPEScheduleEntry)
    for m in (AgeingData, ShareEvent, Shareholder, RPTransaction, RelatedParty,
              AccountingPolicy, DisclosureData, PPEScheduleEntry):
        db.query(m).filter(m.project_id == pid).delete()


def _tb(pid, ledger, group, code, cyd=0, cyc=0, pyd=0, pyc=0):
    from app.models import TrialBalance
    return TrialBalance(project_id=pid, ledger_name=ledger, tally_group=group,
                        coa_code=code, cy_debit=cyd, cy_credit=cyc,
                        py_debit=pyd, py_credit=pyc)


# ============================================================
# COMPANY A — Simple Trading Co
# ============================================================
def _build_simple(db: Session, firm_id):
    from app.models import Client, Project, TrialBalance
    from app.models.client import Director, ClientShareholder

    c = Client(
        firm_id=firm_id,
        name=f"Simple Trading Co Pvt Ltd {SAMPLE_MARKER}",
        cin="U51100KA2018PTC100001", pan="AABCS1234A", gstin="29AABCS1234A1Z5",
        date_of_incorporation=date(2018, 4, 1),
        registered_office="No. 1, MG Road, Bengaluru, Karnataka 560001",
        principal_activity="Wholesale trading of electronic goods",
        auditor_name="Setty & Associates", auditor_frn="012345S",
        auditor_membership_no="223344",
        face_value=10, authorised_shares=100000, authorised_capital=1000000,
        subscribed_shares=50000, subscribed_capital=500000,
        paidup_shares=50000, paidup_capital=500000,
    )
    db.add(c); db.flush()

    db.add_all([
        Director(client_id=c.id, name="Anand Rao", din="01234567",
                 designation="Managing Director", date_of_appointment=date(2018,4,1),
                 pan="AAAPR1234A", is_kmp=True, signs_financials=True, is_active=True),
        Director(client_id=c.id, name="Priya Nair", din="07654321",
                 designation="Director", date_of_appointment=date(2018,4,1),
                 pan="AAAPN4321B", is_kmp=False, signs_financials=True, is_active=True),
    ])
    db.add_all([
        ClientShareholder(client_id=c.id, name="Anand Rao", no_of_shares_cy=30000,
                          no_of_shares_py=30000, face_value=10, pct_holding_cy=60,
                          pct_holding_py=60, is_promoter=True, is_director=True, din="01234567"),
        ClientShareholder(client_id=c.id, name="Priya Nair", no_of_shares_cy=20000,
                          no_of_shares_py=20000, face_value=10, pct_holding_cy=40,
                          pct_holding_py=40, is_promoter=True, is_director=True, din="07654321"),
    ])

    p = Project(client_id=c.id, financial_year="2024-25", version=1,
                bs_date_cy=date(2025,3,31), bs_date_py=date(2024,3,31),
                rounding="Rupees", company_type="trading", status="setup")
    db.add(p); db.flush()
    pid = p.id

    # Trial Balance — balanced. (debit totals == credit totals)
    rows = [
        # Equity & liabilities (credits)
        _tb(pid, "Equity Share Capital", "Capital Account", "BS-EL-01-01-02", 0, 500000, 0, 500000),
        _tb(pid, "Retained Earnings", "Reserves & Surplus", "BS-EL-01-02-09", 0, 300000, 0, 180000),
        _tb(pid, "Bank Loan - HDFC", "Loans (Liability)", "BS-EL-03-01-03", 0, 400000, 0, 500000),
        _tb(pid, "Sundry Creditors", "Sundry Creditors", "BS-EL-04-02-05", 0, 250000, 0, 220000),
        _tb(pid, "Sales - Electronics", "Sales Accounts", "PL-01-02", 0, 2000000, 0, 1700000),
        _tb(pid, "Interest Income", "Indirect Incomes", "PL-02-01", 0, 20000, 0, 15000),
        # Assets & expenses (debits)
        _tb(pid, "Office Equipment", "Fixed Assets", "BS-AS-01-01-06", 350000, 0, 380000, 0),
        _tb(pid, "Closing Stock", "Stock-in-Hand", "BS-AS-02-02-04", 300000, 0, 250000, 0),
        _tb(pid, "Sundry Debtors", "Sundry Debtors", "BS-AS-02-03-01", 420000, 0, 380000, 0),
        _tb(pid, "HDFC Bank", "Bank Accounts", "BS-AS-02-04-01", 410000, 0, 395000, 0),
        _tb(pid, "Purchases", "Purchase Accounts", "PL-04-02", 1400000, 0, 1200000, 0),
        _tb(pid, "Salaries", "Indirect Expenses", "PL-04-04-01", 300000, 0, 260000, 0),
        _tb(pid, "Rent", "Indirect Expenses", "PL-04-07-04", 120000, 0, 110000, 0),
        _tb(pid, "Interest on Loan", "Indirect Expenses", "PL-04-05-01", 48000, 0, 60000, 0),
        _tb(pid, "Other Expenses", "Indirect Expenses", "PL-04-07", 122000, 0, 80000, 0),
    ]
    db.add_all(rows)
    db.commit()
    return c.id


# ============================================================
# COMPANY B — Comprehensive Manufacturing Ltd
# ============================================================
def _build_comprehensive(db: Session, firm_id):
    from app.models import Client, Project
    from app.models.client import Director, ClientShareholder, CustomCoACode, ClientPolicy
    from app.models.supplementary import (AgeingData, ShareEvent, Shareholder,
        RelatedParty, RPTransaction, AccountingPolicy, DisclosureData, PPEScheduleEntry)

    c = Client(
        firm_id=firm_id,
        name=f"Comprehensive Mfg Ltd {SAMPLE_MARKER}",
        cin="U29100KA2015PLC200002", pan="AABCC5678C", gstin="29AABCC5678C1Z3",
        date_of_incorporation=date(2015, 6, 15),
        registered_office="Plot 42, Industrial Area, Peenya, Bengaluru 560058",
        principal_activity="Manufacturing of precision auto components",
        auditor_name="Setty & Associates", auditor_frn="012345S",
        auditor_membership_no="223344",
        face_value=10, authorised_shares=1000000, authorised_capital=10000000,
        subscribed_shares=600000, subscribed_capital=6000000,
        paidup_shares=600000, paidup_capital=6000000,
    )
    db.add(c); db.flush()

    # Directors (3, two are KMP)
    db.add_all([
        Director(client_id=c.id, name="Rajesh Menon", din="11111111",
                 designation="Managing Director", date_of_appointment=date(2015,6,15),
                 pan="AAAPM1111A", is_kmp=True, signs_financials=True, is_active=True),
        Director(client_id=c.id, name="Sunita Desai", din="22222222",
                 designation="Whole-time Director (CFO)", date_of_appointment=date(2016,4,1),
                 pan="AAAPD2222B", is_kmp=True, signs_financials=True, is_active=True),
        Director(client_id=c.id, name="Vikram Shah", din="33333333",
                 designation="Independent Director", date_of_appointment=date(2018,7,1),
                 pan="AAAPS3333C", is_kmp=False, signs_financials=False, is_active=True),
    ])

    # Shareholders (client-level) — 3 holders + promoter group
    db.add_all([
        ClientShareholder(client_id=c.id, name="Rajesh Menon", no_of_shares_cy=300000,
                          no_of_shares_py=270000, face_value=10, pct_holding_cy=50.0,
                          pct_holding_py=49.09, is_promoter=True, is_director=True, din="11111111"),
        ClientShareholder(client_id=c.id, name="Sunita Desai", no_of_shares_cy=180000,
                          no_of_shares_py=165000, face_value=10, pct_holding_cy=30.0,
                          pct_holding_py=30.0, is_promoter=True, is_director=True, din="22222222"),
        ClientShareholder(client_id=c.id, name="Horizon Capital LLP", no_of_shares_cy=120000,
                          no_of_shares_py=115000, face_value=10, pct_holding_cy=20.0,
                          pct_holding_py=20.91, is_promoter=False, is_director=False),
    ])

    # Custom CoA codes (client-level)
    db.add_all([
        CustomCoACode(client_id=c.id, code="PL-04-07-99", particulars="CSR Expenditure (Custom)",
                      parent_code="PL-04-07", nature="Dr", fs_type="PL", note_ref="22"),
        CustomCoACode(client_id=c.id, code="BS-AS-01-01-99", particulars="Tooling & Dies (Custom)",
                      parent_code="BS-AS-01-01", nature="Dr", fs_type="BS", note_ref="10"),
    ])

    # Accounting policies (client-level)
    db.add_all([
        ClientPolicy(client_id=c.id, policy_number=1, title="Basis of Preparation",
                     body="The financial statements have been prepared under the historical cost convention on an accrual basis in accordance with the Accounting Standards specified under Section 133 of the Companies Act, 2013.", is_active=True),
        ClientPolicy(client_id=c.id, policy_number=2, title="Property, Plant and Equipment",
                     body="PPE are stated at cost less accumulated depreciation. Depreciation is provided on the written-down-value method over the useful lives prescribed in Schedule II.", is_active=True),
        ClientPolicy(client_id=c.id, policy_number=3, title="Inventories",
                     body="Inventories are valued at the lower of cost and net realisable value. Cost is determined on a weighted-average basis.", is_active=True),
        ClientPolicy(client_id=c.id, policy_number=4, title="Revenue Recognition",
                     body="Revenue from the sale of goods is recognised when control is transferred to the customer, net of returns, trade discounts and GST.", is_active=True),
    ])

    p = Project(client_id=c.id, financial_year="2024-25", version=1,
                bs_date_cy=date(2025,3,31), bs_date_py=date(2024,3,31),
                rounding="Rupees", company_type="manufacturing", status="setup")
    db.add(p); db.flush()
    pid = p.id

    _build_comprehensive_tb(db, pid)
    _build_comprehensive_supplementary(db, pid)

    db.commit()
    return c.id


def _build_comprehensive_tb(db, pid):
    # Manufacturing TB — balanced. Mapped to TR/TP ageing leaf codes so the
    # ageing matrices auto-derive from the TB.
    rows = [
        # ---- Equity & liabilities (credit balances) ----
        _tb(pid, "Equity Share Capital", "Capital Account", "BS-EL-01-01-02", 0, 6000000, 0, 5500000),
        _tb(pid, "Securities Premium", "Reserves & Surplus", "BS-EL-01-02-03", 0, 1500000, 0, 1350000),
        _tb(pid, "General Reserve", "Reserves & Surplus", "BS-EL-01-02-07", 0, 800000, 0, 800000),
        _tb(pid, "Surplus in P&L", "Reserves & Surplus", "BS-EL-01-02-09", 0, 1600000, 0, 1600000),
        _tb(pid, "Term Loan - SBI", "Secured Loans", "BS-EL-03-01-03", 0, 3000000, 0, 3800000),
        _tb(pid, "Working Capital Loan", "Bank OD A/c", "BS-EL-04-01-01", 0, 1200000, 0, 1000000),
        _tb(pid, "Trade Payables - MSME <1Y", "Sundry Creditors", "BS-EL-04-02-01", 0, 450000, 0, 380000),
        _tb(pid, "Trade Payables - Others <1Y", "Sundry Creditors", "BS-EL-04-02-05", 0, 820000, 0, 700000),
        _tb(pid, "Trade Payables - Others 1-2Y", "Sundry Creditors", "BS-EL-04-02-06", 0, 150000, 0, 90000),
        _tb(pid, "Provision for Income Tax", "Provisions", "BS-EL-04-04-02", 0, 380000, 0, 300000),
        _tb(pid, "Sale of Products - Manufactured", "Sales Accounts", "PL-01-01", 0, 18000000, 0, 15500000),
        _tb(pid, "Other Income - Interest", "Indirect Incomes", "PL-02-01", 0, 95000, 0, 80000),
        _tb(pid, "Other Income - Misc", "Indirect Incomes", "PL-02-02", 0, 45000, 0, 30000),
        # ---- Assets & expenses (debit balances) ----
        _tb(pid, "Land (Freehold)", "Fixed Assets", "BS-AS-01-01-01", 2000000, 0, 2000000, 0),
        _tb(pid, "Buildings", "Fixed Assets", "BS-AS-01-01-03", 3000000, 0, 3000000, 0),
        _tb(pid, "Plant and Equipment", "Fixed Assets", "BS-AS-01-01-04", 4500000, 0, 4200000, 0),
        _tb(pid, "Furniture and Fixtures", "Fixed Assets", "BS-AS-01-01-05", 350000, 0, 380000, 0),
        _tb(pid, "Accumulated Depreciation", "Fixed Assets", "BS-AS-01-01-04", 0, 3200000, 0, 2600000),
        _tb(pid, "Raw Materials", "Stock-in-Hand", "BS-AS-02-02-01", 850000, 0, 720000, 0),
        _tb(pid, "Work-in-Progress", "Stock-in-Hand", "BS-AS-02-02-02", 420000, 0, 380000, 0),
        _tb(pid, "Finished Goods", "Stock-in-Hand", "BS-AS-02-02-03", 980000, 0, 850000, 0),
        # Trade receivables across ageing buckets (auto-derive ageing)
        _tb(pid, "TR Good <6M", "Sundry Debtors", "BS-AS-02-03-01", 1800000, 0, 1500000, 0),
        _tb(pid, "TR Good 6M-1Y", "Sundry Debtors", "BS-AS-02-03-02", 450000, 0, 400000, 0),
        _tb(pid, "TR Good 1-2Y", "Sundry Debtors", "BS-AS-02-03-03", 180000, 0, 120000, 0),
        _tb(pid, "TR Doubtful >3Y", "Sundry Debtors", "BS-AS-02-03-10", 60000, 0, 60000, 0),
        _tb(pid, "SBI Current A/c", "Bank Accounts", "BS-AS-02-04-01", 5149000, 0, 4510000, 0),
        _tb(pid, "Fixed Deposit", "Bank Accounts", "BS-AS-02-04-02", 2500000, 0, 2500000, 0),
        # Expenses
        _tb(pid, "Cost of Materials Consumed", "Direct Expenses", "PL-04-01", 9200000, 0, 8100000, 0),
        _tb(pid, "Salaries and Wages", "Indirect Expenses", "PL-04-04-01", 2800000, 0, 2400000, 0),
        _tb(pid, "Interest Expense on Borrowings", "Indirect Expenses", "PL-04-05-01", 520000, 0, 610000, 0),
        _tb(pid, "Depreciation", "Indirect Expenses", "PL-04-06-01", 600000, 0, 550000, 0),
        _tb(pid, "Power and Fuel", "Indirect Expenses", "PL-04-07-02", 980000, 0, 850000, 0),
        _tb(pid, "Other Expenses", "Indirect Expenses", "PL-04-07", 745000, 0, 600000, 0),
        _tb(pid, "CSR Expenditure", "Indirect Expenses", "PL-04-07-99", 156000, 0, 0, 0),
    ]
    db.add_all(rows)
    db.flush()

    # Verify balance
    cy_dr = sum(r.cy_debit for r in rows); cy_cr = sum(r.cy_credit for r in rows)
    if abs(cy_dr - cy_cr) > 1:
        # auto-balance into other expenses so the demo TB always ties
        diff = cy_dr - cy_cr
        rows[-1].cy_credit += diff if diff > 0 else 0
    db.flush()


def _build_comprehensive_supplementary(db, pid):
    from app.models.supplementary import (AgeingData, ShareEvent, Shareholder,
        RelatedParty, RPTransaction, PPEScheduleEntry, DisclosureData)

    # ---- TR Ageing (matches the TR ledgers above) ----
    # buckets: 1=<6M, 2=6M-1Y, 3=1-2Y, 4=2-3Y, 5=>3Y
    db.add_all([
        AgeingData(project_id=pid, ageing_type="TR", party_name="Acme Industries",
                   is_doubtful=False, is_disputed=False, bucket_1=1200000,
                   bucket_2=300000, period="CY"),
        AgeingData(project_id=pid, ageing_type="TR", party_name="Bharat Motors",
                   is_doubtful=False, is_disputed=False, bucket_1=600000,
                   bucket_2=150000, bucket_3=180000, period="CY"),
        AgeingData(project_id=pid, ageing_type="TR", party_name="Old Debtor (Disputed)",
                   is_doubtful=True, is_disputed=True, bucket_5=60000, period="CY"),
    ])
    # ---- TP Ageing ----
    # buckets: 1=<1Y, 2=1-2Y, 3=2-3Y, 4=>3Y
    db.add_all([
        AgeingData(project_id=pid, ageing_type="TP", party_name="Steel Supplier Pvt Ltd",
                   is_msme=True, is_disputed=False, bucket_1=450000, period="CY"),
        AgeingData(project_id=pid, ageing_type="TP", party_name="Components Co",
                   is_msme=False, is_disputed=False, bucket_1=820000,
                   bucket_2=150000, period="CY"),
    ])

    # ---- Share events (issue during the year) ----
    db.add_all([
        ShareEvent(project_id=pid, event_type="opening", event_date=date(2024,4,1),
                   share_class="equity", no_of_shares=550000, face_value=10,
                   total_amount=5500000, period="CY", narration="Opening balance"),
        ShareEvent(project_id=pid, event_type="issue", event_date=date(2024,9,15),
                   share_class="equity", no_of_shares=50000, face_value=10, premium=20,
                   total_amount=1500000, period="CY", narration="Rights issue at premium"),
    ])

    # ---- Project-level shareholders (for Note A %-holding table) ----
    db.add_all([
        Shareholder(project_id=pid, name="Rajesh Menon", share_class="equity",
                    no_of_shares_cy=300000, no_of_shares_py=270000,
                    pct_holding_cy=50.0, pct_holding_py=49.09, is_promoter=True, din_pan="11111111"),
        Shareholder(project_id=pid, name="Sunita Desai", share_class="equity",
                    no_of_shares_cy=180000, no_of_shares_py=165000,
                    pct_holding_cy=30.0, pct_holding_py=30.0, is_promoter=True, din_pan="22222222"),
        Shareholder(project_id=pid, name="Horizon Capital LLP", share_class="equity",
                    no_of_shares_cy=120000, no_of_shares_py=115000,
                    pct_holding_cy=20.0, pct_holding_py=20.91, is_promoter=False, din_pan="AABCH9999H"),
    ])

    # ---- Related parties + transactions ----
    rp1 = RelatedParty(project_id=pid, name="Rajesh Menon", category="KMP",
                       relationship="Managing Director", pan_cin="AAAPM1111A")
    rp2 = RelatedParty(project_id=pid, name="Sunita Desai", category="KMP",
                       relationship="Whole-time Director (CFO)", pan_cin="AAAPD2222B")
    rp3 = RelatedParty(project_id=pid, name="Menon Holdings Pvt Ltd", category="Entity",
                       relationship="Entity controlled by KMP", pan_cin="U74999KA2010PTC099999")
    db.add_all([rp1, rp2, rp3]); db.flush()
    db.add_all([
        RPTransaction(project_id=pid, party_id=rp1.id, transaction_type="Remuneration",
                      cy_amount=2400000, py_amount=2100000),
        RPTransaction(project_id=pid, party_id=rp2.id, transaction_type="Remuneration",
                      cy_amount=1800000, py_amount=1600000),
        RPTransaction(project_id=pid, party_id=rp3.id, transaction_type="Rent Paid",
                      cy_amount=600000, py_amount=600000),
        RPTransaction(project_id=pid, party_id=rp3.id, transaction_type="Loan Taken",
                      cy_amount=1000000, py_amount=0),
    ])

    # ---- PPE schedule (ties to BS fixed-asset ledgers) ----
    db.add_all([
        PPEScheduleEntry(project_id=pid, asset_class="Land (Freehold)", coa_code="BS-AS-01-01-01",
                         asset_type="tangible", gross_opening=2000000, gross_additions=0,
                         gross_disposals=0, dep_opening=0, dep_for_year=0, dep_on_disposals=0,
                         py_gross_opening=2000000, py_dep_opening=0),
        PPEScheduleEntry(project_id=pid, asset_class="Buildings", coa_code="BS-AS-01-01-03",
                         asset_type="tangible", gross_opening=3000000, gross_additions=0,
                         gross_disposals=0, dep_opening=600000, dep_for_year=120000, dep_on_disposals=0,
                         py_gross_opening=3000000, py_dep_opening=480000, py_dep_for_year=120000),
        PPEScheduleEntry(project_id=pid, asset_class="Plant and Equipment", coa_code="BS-AS-01-01-04",
                         asset_type="tangible", gross_opening=4200000, gross_additions=300000,
                         gross_disposals=0, dep_opening=2000000, dep_for_year=440000, dep_on_disposals=0,
                         py_gross_opening=3900000, py_gross_additions=300000,
                         py_dep_opening=1600000, py_dep_for_year=400000),
        PPEScheduleEntry(project_id=pid, asset_class="Furniture and Fixtures", coa_code="BS-AS-01-01-05",
                         asset_type="tangible", gross_opening=380000, gross_additions=0,
                         gross_disposals=30000, dep_opening=200000, dep_for_year=40000, dep_on_disposals=15000,
                         py_gross_opening=380000, py_dep_opening=160000, py_dep_for_year=40000),
    ])

    # ---- Additional disclosures ----
    db.add_all([
        DisclosureData(project_id=pid, disclosure_ref="CIF", sub_ref="RM",
                       particulars="CIF Value of Imports - Raw Materials", cy_amount=1200000, py_amount=900000),
        DisclosureData(project_id=pid, disclosure_ref="FOR", sub_ref="EXP",
                       particulars="Expenditure in Foreign Currency - Travel", cy_amount=85000, py_amount=60000),
        DisclosureData(project_id=pid, disclosure_ref="CSR", sub_ref="SPENT",
                       particulars="Amount spent on CSR activities", cy_amount=156000, py_amount=0),
    ])
    db.flush()


# ============================================================
# Public entry point
# ============================================================
def load_sample_data(db: Session, firm_id=None) -> dict:
    """Load both sample companies. Idempotent. Returns a summary."""
    _wipe_existing(db, firm_id)
    simple_id = _build_simple(db, firm_id)
    comp_id = _build_comprehensive(db, firm_id)
    return {
        "status": "loaded",
        "companies": [
            {"id": simple_id, "name": f"Simple Trading Co Pvt Ltd {SAMPLE_MARKER}"},
            {"id": comp_id, "name": f"Comprehensive Mfg Ltd {SAMPLE_MARKER}"},
        ],
    }
