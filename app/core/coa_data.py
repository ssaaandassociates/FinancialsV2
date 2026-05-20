"""
Complete Chart of Accounts - Schedule III Division I
Each entry: (code, level, particulars, schedule_ref, nature, fs_type, note_ref, tally_group, parent_code, remarks)
"""

COA_MASTER_DATA = [
    # ====================== BALANCE SHEET: EQUITY & LIABILITIES ======================
    # Share Capital (Note A)
    ("BS-EL-01-01", 3, "Share Capital", "1(a)", "Cr", "BS", "A", "Share Capital", "BS-EL-01", ""),
    ("BS-EL-01-01-01", 4, "Equity Share Capital - Authorised", "A(a)", "Cr", "BS", "A", "Share Capital", "BS-EL-01-01", ""),
    ("BS-EL-01-01-02", 4, "Equity Share Capital - Issued & Paid Up", "A(b)", "Cr", "BS", "A", "Share Capital", "BS-EL-01-01", ""),
    ("BS-EL-01-01-03", 4, "Equity Share Capital - Subscribed Not Paid", "A(b)", "Cr", "BS", "A", "Share Capital", "BS-EL-01-01", ""),
    ("BS-EL-01-01-04", 4, "Preference Share Capital - Authorised", "A(a)", "Cr", "BS", "A", "Share Capital", "BS-EL-01-01", "Each class separately"),
    ("BS-EL-01-01-05", 4, "Preference Share Capital - Issued & Paid Up", "A(b)", "Cr", "BS", "A", "Share Capital", "BS-EL-01-01", ""),
    ("BS-EL-01-01-06", 4, "Calls Unpaid", "A(k)", "Dr", "BS", "A", "Share Capital", "BS-EL-01-01", "Contra - deduction"),
    ("BS-EL-01-01-07", 4, "Forfeited Shares", "A(l)", "Cr", "BS", "A", "Share Capital", "BS-EL-01-01", "Amount originally paid up"),

    # Reserves & Surplus (Note B)
    ("BS-EL-01-02", 3, "Reserves and Surplus", "1(b)", "Cr", "BS", "B", "Reserves & Surplus", "BS-EL-01", ""),
    ("BS-EL-01-02-01", 4, "Capital Reserves", "B(i)(a)", "Cr", "BS", "B", "Capital Reserve", "BS-EL-01-02", ""),
    ("BS-EL-01-02-02", 4, "Capital Redemption Reserve", "B(i)(b)", "Cr", "BS", "B", "Capital Redemption Reserve", "BS-EL-01-02", ""),
    ("BS-EL-01-02-03", 4, "Securities Premium", "B(i)(c)", "Cr", "BS", "B", "Securities Premium", "BS-EL-01-02", ""),
    ("BS-EL-01-02-04", 4, "Debenture Redemption Reserve", "B(i)(d)", "Cr", "BS", "B", "Debenture Redemption Reserve", "BS-EL-01-02", ""),
    ("BS-EL-01-02-05", 4, "Revaluation Reserve", "B(i)(e)", "Cr", "BS", "B", "Revaluation Reserve", "BS-EL-01-02", ""),
    ("BS-EL-01-02-06", 4, "Share Options Outstanding Account", "B(i)(f)", "Cr", "BS", "B", "ESOP Reserve", "BS-EL-01-02", ""),
    ("BS-EL-01-02-07", 4, "General Reserve", "B(i)(g)", "Cr", "BS", "B", "General Reserve", "BS-EL-01-02", ""),
    ("BS-EL-01-02-08", 4, "Other Reserves (Specify Nature)", "B(i)(g)", "Cr", "BS", "B", "Other Reserves", "BS-EL-01-02", ""),
    ("BS-EL-01-02-09", 4, "Surplus - Balance in P&L", "B(i)(h)", "Cr", "BS", "B", "Profit & Loss A/c", "BS-EL-01-02", "Debit = negative"),

    # Money Against Share Warrants
    ("BS-EL-01-03", 3, "Money Received Against Share Warrants", "1(c)", "Cr", "BS", "A", "Share Capital", "BS-EL-01", ""),

    # Share Application Money
    ("BS-EL-02", 2, "Share Application Money Pending Allotment", "2", "Cr", "BS", "", "Share Application Money", "BS-EL", ""),

    # ---- Non-Current Liabilities ----
    # Long-Term Borrowings (Note C)
    ("BS-EL-03-01", 3, "Long-Term Borrowings", "3(a)", "Cr", "BS", "C", "Loans (Liability)", "BS-EL-03", ""),
    ("BS-EL-03-01-01", 4, "Bonds/Debentures - Secured", "C(a)", "Cr", "BS", "C", "Secured Loans", "BS-EL-03-01", ""),
    ("BS-EL-03-01-02", 4, "Bonds/Debentures - Unsecured", "C(a)", "Cr", "BS", "C", "Unsecured Loans", "BS-EL-03-01", ""),
    ("BS-EL-03-01-03", 4, "Term Loans from Banks - Secured", "C(b)(A)", "Cr", "BS", "C", "Secured Loans", "BS-EL-03-01", ""),
    ("BS-EL-03-01-04", 4, "Term Loans from Banks - Unsecured", "C(b)(A)", "Cr", "BS", "C", "Unsecured Loans", "BS-EL-03-01", ""),
    ("BS-EL-03-01-05", 4, "Term Loans from Others - Secured", "C(b)(B)", "Cr", "BS", "C", "Secured Loans", "BS-EL-03-01", ""),
    ("BS-EL-03-01-06", 4, "Term Loans from Others - Unsecured", "C(b)(B)", "Cr", "BS", "C", "Unsecured Loans", "BS-EL-03-01", ""),
    ("BS-EL-03-01-07", 4, "Deferred Payment Liabilities", "C(c)", "Cr", "BS", "C", "Unsecured Loans", "BS-EL-03-01", ""),
    ("BS-EL-03-01-08", 4, "Deposits (Long-Term)", "C(d)", "Cr", "BS", "C", "Current Liabilities", "BS-EL-03-01", ""),
    ("BS-EL-03-01-09", 4, "Loans from Related Parties (LT)", "C(e)", "Cr", "BS", "C", "Unsecured Loans", "BS-EL-03-01", ""),
    ("BS-EL-03-01-10", 4, "Finance Lease Obligations (LT)", "C(f)", "Cr", "BS", "C", "Unsecured Loans", "BS-EL-03-01", ""),
    ("BS-EL-03-01-11", 4, "Other Loans & Advances (LT)", "C(g)", "Cr", "BS", "C", "Unsecured Loans", "BS-EL-03-01", ""),

    # Deferred Tax Liabilities
    ("BS-EL-03-02", 3, "Deferred Tax Liabilities (Net)", "3(b)", "Cr", "BS", "", "Duties & Taxes", "BS-EL-03", ""),

    # Other Long-Term Liabilities (Note D)
    ("BS-EL-03-03", 3, "Other Long-Term Liabilities", "3(c)", "Cr", "BS", "D", "Current Liabilities", "BS-EL-03", ""),
    ("BS-EL-03-03-01", 4, "Trade Payables (Long-Term)", "D(a)", "Cr", "BS", "D", "Sundry Creditors", "BS-EL-03-03", ""),
    ("BS-EL-03-03-02", 4, "Others (Long-Term Liabilities)", "D(b)", "Cr", "BS", "D", "Current Liabilities", "BS-EL-03-03", ""),

    # Long-Term Provisions (Note E)
    ("BS-EL-03-04", 3, "Long-Term Provisions", "3(d)", "Cr", "BS", "E", "Provisions", "BS-EL-03", ""),
    ("BS-EL-03-04-01", 4, "Employee Benefits (LT)", "E(a)", "Cr", "BS", "E", "Provisions", "BS-EL-03-04", "Gratuity, Leave Encashment"),
    ("BS-EL-03-04-02", 4, "Other Provisions (LT)", "E(b)", "Cr", "BS", "E", "Provisions", "BS-EL-03-04", ""),

    # ---- Current Liabilities ----
    # Short-Term Borrowings (Note F)
    ("BS-EL-04-01", 3, "Short-Term Borrowings", "4(a)", "Cr", "BS", "F", "Loans (Liability)", "BS-EL-04", ""),
    ("BS-EL-04-01-01", 4, "Loans on Demand - Banks Secured", "F(a)(A)", "Cr", "BS", "F", "Bank OD/CC", "BS-EL-04-01", ""),
    ("BS-EL-04-01-02", 4, "Loans on Demand - Banks Unsecured", "F(a)(A)", "Cr", "BS", "F", "Unsecured Loans", "BS-EL-04-01", ""),
    ("BS-EL-04-01-03", 4, "Loans on Demand - Others Secured", "F(a)(B)", "Cr", "BS", "F", "Secured Loans", "BS-EL-04-01", ""),
    ("BS-EL-04-01-04", 4, "Loans on Demand - Others Unsecured", "F(a)(B)", "Cr", "BS", "F", "Unsecured Loans", "BS-EL-04-01", ""),
    ("BS-EL-04-01-05", 4, "Loans from Related Parties (ST)", "F(b)", "Cr", "BS", "F", "Unsecured Loans", "BS-EL-04-01", ""),
    ("BS-EL-04-01-06", 4, "Deposits (Short-Term)", "F(c)", "Cr", "BS", "F", "Current Liabilities", "BS-EL-04-01", ""),
    ("BS-EL-04-01-07", 4, "Other Short-Term Loans", "F(d)", "Cr", "BS", "F", "Current Liabilities", "BS-EL-04-01", ""),

    # Trade Payables with Ageing (Note FA)
    ("BS-EL-04-02", 3, "Trade Payables", "4(b)", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04", "MSME split mandatory"),
    ("BS-EL-04-02-01", 4, "TP MSME Undisputed <1Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-02", 4, "TP MSME Undisputed 1-2Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-03", 4, "TP MSME Undisputed 2-3Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-04", 4, "TP MSME Undisputed >3Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-05", 4, "TP Other Undisputed <1Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-06", 4, "TP Other Undisputed 1-2Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-07", 4, "TP Other Undisputed 2-3Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-08", 4, "TP Other Undisputed >3Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-09", 4, "TP MSME Disputed <1Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-10", 4, "TP MSME Disputed 1-2Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-11", 4, "TP MSME Disputed 2-3Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-12", 4, "TP MSME Disputed >3Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-13", 4, "TP Other Disputed <1Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-14", 4, "TP Other Disputed 1-2Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-15", 4, "TP Other Disputed 2-3Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-16", 4, "TP Other Disputed >3Y", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),
    ("BS-EL-04-02-17", 4, "TP Unbilled Dues", "FA", "Cr", "BS", "FA", "Sundry Creditors", "BS-EL-04-02", ""),

    # Other Current Liabilities (Note G)
    ("BS-EL-04-03", 3, "Other Current Liabilities", "4(c)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04", ""),
    ("BS-EL-04-03-01", 4, "Current Maturities of LT Debt", "G(a)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),
    ("BS-EL-04-03-02", 4, "Current Maturities of Finance Lease", "G(b)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),
    ("BS-EL-04-03-03", 4, "Interest Accrued but Not Due", "G(c)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),
    ("BS-EL-04-03-04", 4, "Interest Accrued and Due", "G(d)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),
    ("BS-EL-04-03-05", 4, "Income Received in Advance", "G(e)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),
    ("BS-EL-04-03-06", 4, "Unpaid Dividends", "G(f)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),
    ("BS-EL-04-03-07", 4, "Share Application Money Refundable", "G(g)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),
    ("BS-EL-04-03-08", 4, "Unpaid Matured Deposits & Interest", "G(h)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),
    ("BS-EL-04-03-09", 4, "Unpaid Matured Debentures & Interest", "G(i)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),
    ("BS-EL-04-03-10", 4, "Statutory Dues (TDS/GST/PF/ESI)", "G(j)", "Cr", "BS", "G", "Duties & Taxes", "BS-EL-04-03", ""),
    ("BS-EL-04-03-11", 4, "Other Payables (Specify Nature)", "G(j)", "Cr", "BS", "G", "Current Liabilities", "BS-EL-04-03", ""),

    # Short-Term Provisions (Note H)
    ("BS-EL-04-04", 3, "Short-Term Provisions", "4(d)", "Cr", "BS", "H", "Provisions", "BS-EL-04", ""),
    ("BS-EL-04-04-01", 4, "Employee Benefits (ST)", "H(a)", "Cr", "BS", "H", "Provisions", "BS-EL-04-04", "Bonus, Leave"),
    ("BS-EL-04-04-02", 4, "Provision for Income Tax (Net)", "H(b)", "Cr", "BS", "H", "Provisions", "BS-EL-04-04", ""),
    ("BS-EL-04-04-03", 4, "Proposed Dividend", "H(b)", "Cr", "BS", "H", "Provisions", "BS-EL-04-04", ""),
    ("BS-EL-04-04-04", 4, "Tax on Proposed Dividend", "H(b)", "Cr", "BS", "H", "Provisions", "BS-EL-04-04", ""),
    ("BS-EL-04-04-05", 4, "Other Short-Term Provisions", "H(b)", "Cr", "BS", "H", "Provisions", "BS-EL-04-04", ""),

    # ====================== BALANCE SHEET: ASSETS ======================
    # Tangible Assets (Note I)
    ("BS-AS-01-01", 3, "Property, Plant and Equipment", "1(a)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01", ""),
    ("BS-AS-01-01-01", 4, "Land (Freehold)", "I(a)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-02", 4, "Land (Leasehold)", "I(a)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-03", 4, "Buildings", "I(b)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-04", 4, "Plant and Equipment", "I(c)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-05", 4, "Furniture and Fixtures", "I(d)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-06", 4, "Vehicles", "I(e)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-07", 4, "Office Equipment", "I(f)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-08", 4, "Computers", "I(f)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-09", 4, "Other Tangible Assets", "I(g)", "Dr", "BS", "I", "Fixed Assets", "BS-AS-01-01", ""),

    # Intangible Assets (Note J)
    ("BS-AS-01-01-10", 4, "Goodwill", "J(a)", "Dr", "BS", "J", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-11", 4, "Computer Software", "J(c)", "Dr", "BS", "J", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-12", 4, "Brands / Trademarks", "J(b)", "Dr", "BS", "J", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-13", 4, "Copyrights / Patents / IP", "J(f)", "Dr", "BS", "J", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-14", 4, "Other Intangible Assets", "J(i)", "Dr", "BS", "J", "Fixed Assets", "BS-AS-01-01", ""),

    # CWIP & Intangible Under Dev
    ("BS-AS-01-01-15", 4, "Capital Work-in-Progress", "1(a)(iii)", "Dr", "BS", "", "Fixed Assets", "BS-AS-01-01", ""),
    ("BS-AS-01-01-16", 4, "Intangible Assets Under Development", "1(a)(iv)", "Dr", "BS", "", "Fixed Assets", "BS-AS-01-01", ""),

    # Non-Current Investments (Note K)
    ("BS-AS-01-02", 3, "Non-Current Investments", "1(b)", "Dr", "BS", "K", "Investments", "BS-AS-01", ""),
    ("BS-AS-01-02-01", 4, "Investment Property", "K(a)", "Dr", "BS", "K", "Investments", "BS-AS-01-02", ""),
    ("BS-AS-01-02-02", 4, "Investments in Equity Instruments", "K(b)", "Dr", "BS", "K", "Investments", "BS-AS-01-02", ""),
    ("BS-AS-01-02-03", 4, "Investments in Preference Shares", "K(c)", "Dr", "BS", "K", "Investments", "BS-AS-01-02", ""),
    ("BS-AS-01-02-04", 4, "Investments in Govt/Trust Securities", "K(d)", "Dr", "BS", "K", "Investments", "BS-AS-01-02", ""),
    ("BS-AS-01-02-05", 4, "Investments in Debentures/Bonds", "K(e)", "Dr", "BS", "K", "Investments", "BS-AS-01-02", ""),
    ("BS-AS-01-02-06", 4, "Investments in Mutual Funds", "K(f)", "Dr", "BS", "K", "Investments", "BS-AS-01-02", ""),
    ("BS-AS-01-02-07", 4, "Investments in Partnership Firms", "K(g)", "Dr", "BS", "K", "Investments", "BS-AS-01-02", ""),
    ("BS-AS-01-02-08", 4, "Other Non-Current Investments", "K(h)", "Dr", "BS", "K", "Investments", "BS-AS-01-02", ""),

    # Deferred Tax Assets
    ("BS-AS-01-03", 3, "Deferred Tax Assets (Net)", "1(c)", "Dr", "BS", "", "Duties & Taxes", "BS-AS-01", ""),

    # Long-Term Loans & Advances (Note L)
    ("BS-AS-01-04", 3, "Long-Term Loans and Advances", "1(d)", "Dr", "BS", "L", "Loans & Advances (Asset)", "BS-AS-01", ""),
    ("BS-AS-01-04-01", 4, "Capital Advances", "L(a)", "Dr", "BS", "L", "Loans & Advances (Asset)", "BS-AS-01-04", ""),
    ("BS-AS-01-04-02", 4, "Security Deposits (LT)", "L(b)", "Dr", "BS", "L", "Loans & Advances (Asset)", "BS-AS-01-04", ""),
    ("BS-AS-01-04-03", 4, "Loans to Related Parties (LT)", "L(c)", "Dr", "BS", "L", "Loans & Advances (Asset)", "BS-AS-01-04", ""),
    ("BS-AS-01-04-04", 4, "Other Long-Term Loans & Advances", "L(d)", "Dr", "BS", "L", "Loans & Advances (Asset)", "BS-AS-01-04", ""),

    # Other Non-Current Assets (Note M)
    ("BS-AS-01-05", 3, "Other Non-Current Assets", "1(e)", "Dr", "BS", "M", "Current Assets", "BS-AS-01", ""),
    ("BS-AS-01-05-01", 4, "Long-Term Trade Receivables", "M(i)", "Dr", "BS", "M", "Sundry Debtors", "BS-AS-01-05", ""),
    ("BS-AS-01-05-02", 4, "Other Non-Current Assets (Specify)", "M(ii)", "Dr", "BS", "M", "Current Assets", "BS-AS-01-05", ""),

    # Current Investments (Note N)
    ("BS-AS-02-01", 3, "Current Investments", "2(a)", "Dr", "BS", "N", "Investments", "BS-AS-02", ""),
    ("BS-AS-02-01-01", 4, "Equity Instruments (Current)", "N(a)", "Dr", "BS", "N", "Investments", "BS-AS-02-01", ""),
    ("BS-AS-02-01-02", 4, "Mutual Funds (Current)", "N(e)", "Dr", "BS", "N", "Investments", "BS-AS-02-01", ""),
    ("BS-AS-02-01-03", 4, "Other Current Investments", "N(g)", "Dr", "BS", "N", "Investments", "BS-AS-02-01", ""),

    # Inventories (Note O)
    ("BS-AS-02-02", 3, "Inventories", "2(b)", "Dr", "BS", "O", "Stock-in-Hand", "BS-AS-02", ""),
    ("BS-AS-02-02-01", 4, "Raw Materials", "O(a)", "Dr", "BS", "O", "Stock-in-Hand", "BS-AS-02-02", ""),
    ("BS-AS-02-02-02", 4, "Work-in-Progress", "O(b)", "Dr", "BS", "O", "Stock-in-Hand", "BS-AS-02-02", ""),
    ("BS-AS-02-02-03", 4, "Finished Goods", "O(c)", "Dr", "BS", "O", "Stock-in-Hand", "BS-AS-02-02", ""),
    ("BS-AS-02-02-04", 4, "Stock-in-Trade", "O(d)", "Dr", "BS", "O", "Stock-in-Hand", "BS-AS-02-02", ""),
    ("BS-AS-02-02-05", 4, "Stores and Spares", "O(e)", "Dr", "BS", "O", "Stock-in-Hand", "BS-AS-02-02", ""),
    ("BS-AS-02-02-06", 4, "Loose Tools", "O(f)", "Dr", "BS", "O", "Stock-in-Hand", "BS-AS-02-02", ""),

    # Trade Receivables with Ageing (Note P)
    ("BS-AS-02-03", 3, "Trade Receivables", "2(c)", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02", ""),
    ("BS-AS-02-03-01", 4, "TR Undisputed Good <6M", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-02", 4, "TR Undisputed Good 6M-1Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-03", 4, "TR Undisputed Good 1-2Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-04", 4, "TR Undisputed Good 2-3Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-05", 4, "TR Undisputed Good >3Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-06", 4, "TR Undisputed Doubtful <6M", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-07", 4, "TR Undisputed Doubtful 6M-1Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-08", 4, "TR Undisputed Doubtful 1-2Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-09", 4, "TR Undisputed Doubtful 2-3Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-10", 4, "TR Undisputed Doubtful >3Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-11", 4, "TR Disputed Good <6M", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-12", 4, "TR Disputed Good 6M-1Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-13", 4, "TR Disputed Good 1-2Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-14", 4, "TR Disputed Good 2-3Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-15", 4, "TR Disputed Good >3Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-16", 4, "TR Disputed Doubtful <6M", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-17", 4, "TR Disputed Doubtful 6M-1Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-18", 4, "TR Disputed Doubtful 1-2Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-19", 4, "TR Disputed Doubtful 2-3Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-20", 4, "TR Disputed Doubtful >3Y", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-21", 4, "TR Others", "P", "Dr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", ""),
    ("BS-AS-02-03-22", 4, "Less: Allowance for Bad & Doubtful Debts", "P(iii)", "Cr", "BS", "P", "Sundry Debtors", "BS-AS-02-03", "Contra"),

    # Cash and Cash Equivalents (Note Q)
    ("BS-AS-02-04", 3, "Cash and Cash Equivalents", "2(d)", "Dr", "BS", "Q", "Bank Accounts", "BS-AS-02", ""),
    ("BS-AS-02-04-01", 4, "Bank - Current Accounts", "Q(a)", "Dr", "BS", "Q", "Bank Accounts", "BS-AS-02-04", ""),
    ("BS-AS-02-04-02", 4, "Bank - Deposits (<12 Months)", "Q(a)", "Dr", "BS", "Q", "Bank Accounts", "BS-AS-02-04", ""),
    ("BS-AS-02-04-03", 4, "Bank - Deposits (>12 Months)", "Q(v)", "Dr", "BS", "Q", "Bank Accounts", "BS-AS-02-04", "Separately disclosed"),
    ("BS-AS-02-04-04", 4, "Bank - Earmarked (Unpaid Dividend etc.)", "Q(ii)", "Dr", "BS", "Q", "Bank Accounts", "BS-AS-02-04", ""),
    ("BS-AS-02-04-05", 4, "Bank - Margin Money / Security", "Q(iii)", "Dr", "BS", "Q", "Bank Accounts", "BS-AS-02-04", ""),
    ("BS-AS-02-04-06", 4, "Cheques / Drafts on Hand", "Q(b)", "Dr", "BS", "Q", "Cash-in-Hand", "BS-AS-02-04", ""),
    ("BS-AS-02-04-07", 4, "Cash on Hand", "Q(c)", "Dr", "BS", "Q", "Cash-in-Hand", "BS-AS-02-04", ""),

    # Short-Term Loans & Advances (Note R)
    ("BS-AS-02-05", 3, "Short-Term Loans and Advances", "2(e)", "Dr", "BS", "R", "Loans & Advances (Asset)", "BS-AS-02", ""),
    ("BS-AS-02-05-01", 4, "Loans to Related Parties (ST)", "R(a)", "Dr", "BS", "R", "Loans & Advances (Asset)", "BS-AS-02-05", ""),
    ("BS-AS-02-05-02", 4, "Secured, Considered Good", "R(a)", "Dr", "BS", "R", "Loans & Advances (Asset)", "BS-AS-02-05", ""),
    ("BS-AS-02-05-03", 4, "Unsecured, Considered Good", "R(b)", "Dr", "BS", "R", "Loans & Advances (Asset)", "BS-AS-02-05", ""),
    ("BS-AS-02-05-04", 4, "Doubtful", "R(c)", "Dr", "BS", "R", "Loans & Advances (Asset)", "BS-AS-02-05", ""),
    ("BS-AS-02-05-05", 4, "Less: Allowance for Bad Advances", "R(iii)", "Cr", "BS", "R", "Loans & Advances (Asset)", "BS-AS-02-05", "Contra"),
    ("BS-AS-02-05-06", 4, "Advance Income Tax / TDS Receivable", "R", "Dr", "BS", "R", "Loans & Advances (Asset)", "BS-AS-02-05", ""),
    ("BS-AS-02-05-07", 4, "GST Input Credit / Govt Balances", "R", "Dr", "BS", "R", "Duties & Taxes", "BS-AS-02-05", ""),
    ("BS-AS-02-05-08", 4, "Prepaid Expenses", "R", "Dr", "BS", "R", "Loans & Advances (Asset)", "BS-AS-02-05", ""),
    ("BS-AS-02-05-09", 4, "Advance to Suppliers", "R", "Dr", "BS", "R", "Loans & Advances (Asset)", "BS-AS-02-05", ""),

    # Other Current Assets (Note S)
    ("BS-AS-02-06", 3, "Other Current Assets", "2(f)", "Dr", "BS", "S", "Current Assets", "BS-AS-02", ""),
    ("BS-AS-02-06-01", 4, "Accrued Income / Interest Receivable", "S", "Dr", "BS", "S", "Current Assets", "BS-AS-02-06", ""),
    ("BS-AS-02-06-02", 4, "Other Current Assets (Specify)", "S", "Dr", "BS", "S", "Current Assets", "BS-AS-02-06", ""),

    # ====================== PROFIT & LOSS ======================
    # Revenue from Operations
    ("PL-01", 2, "Revenue from Operations", "Part II-I", "Cr", "PL", "Rev", "Sales Accounts", "PL", ""),
    ("PL-01-01", 3, "Sale of Products - Manufactured", "2A(a)", "Cr", "PL", "Rev", "Sales Accounts", "PL-01", ""),
    ("PL-01-02", 3, "Sale of Products - Traded", "2A(a)", "Cr", "PL", "Rev", "Sales Accounts", "PL-01", ""),
    ("PL-01-03", 3, "Sale of Services", "2A(b)", "Cr", "PL", "Rev", "Sales Accounts", "PL-01", ""),
    ("PL-01-04", 3, "Other Operating Revenue", "2A(c)", "Cr", "PL", "Rev", "Sales Accounts", "PL-01", "Scrap, export incentives"),

    # Other Income
    ("PL-02", 2, "Other Income", "Part II-II", "Cr", "PL", "OI", "Indirect Income", "PL", ""),
    ("PL-02-01", 3, "Interest Income - Fixed Deposits", "4(a)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),
    ("PL-02-02", 3, "Interest Income - Others", "4(a)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),
    ("PL-02-03", 3, "Dividend Income", "4(b)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),
    ("PL-02-04", 3, "Net Gain on Sale of Investments", "4(c)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),
    ("PL-02-05", 3, "Profit on Sale of Fixed Assets", "4(d)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),
    ("PL-02-06", 3, "Rent Received", "4(d)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),
    ("PL-02-07", 3, "Bad Debts Recovered", "4(d)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),
    ("PL-02-08", 3, "Liabilities / Provisions Written Back", "4(d)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),
    ("PL-02-09", 3, "Foreign Exchange Gain (Non-Finance)", "4(d)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),
    ("PL-02-10", 3, "Miscellaneous Income", "4(d)", "Cr", "PL", "OI", "Indirect Income", "PL-02", ""),

    # Cost of Materials Consumed
    ("PL-04-01", 3, "Cost of Materials Consumed", "Part II-IV", "Dr", "PL", "Exp", "Purchase Accounts", "PL-04", "Op+Pur-Cl"),
    ("PL-04-01-01", 4, "Opening Stock - Raw Materials", "", "Dr", "PL", "Exp", "Stock-in-Hand", "PL-04-01", ""),
    ("PL-04-01-02", 4, "Purchases - Raw Materials", "", "Dr", "PL", "Exp", "Purchase Accounts", "PL-04-01", ""),
    ("PL-04-01-03", 4, "Closing Stock - Raw Materials", "", "Cr", "PL", "Exp", "Stock-in-Hand", "PL-04-01", "Deduction"),

    # Purchases of Stock-in-Trade
    ("PL-04-02", 3, "Purchases of Stock-in-Trade", "Part II-IV", "Dr", "PL", "Exp", "Purchase Accounts", "PL-04", ""),

    # Changes in Inventories
    ("PL-04-03", 3, "Changes in Inventories of FG, WIP & SIT", "Part II-IV", "Dr", "PL", "Exp", "Stock-in-Hand", "PL-04", ""),
    ("PL-04-03-01", 4, "Opening Stock - Finished Goods", "", "Dr", "PL", "", "Stock-in-Hand", "PL-04-03", ""),
    ("PL-04-03-02", 4, "Opening Stock - WIP", "", "Dr", "PL", "", "Stock-in-Hand", "PL-04-03", ""),
    ("PL-04-03-03", 4, "Opening Stock - Stock-in-Trade", "", "Dr", "PL", "", "Stock-in-Hand", "PL-04-03", ""),
    ("PL-04-03-04", 4, "Closing Stock - Finished Goods", "", "Cr", "PL", "", "Stock-in-Hand", "PL-04-03", ""),
    ("PL-04-03-05", 4, "Closing Stock - WIP", "", "Cr", "PL", "", "Stock-in-Hand", "PL-04-03", ""),
    ("PL-04-03-06", 4, "Closing Stock - Stock-in-Trade", "", "Cr", "PL", "", "Stock-in-Hand", "PL-04-03", ""),

    # Employee Benefits Expense
    ("PL-04-04", 3, "Employee Benefits Expense", "Part II-IV", "Dr", "PL", "Emp", "Indirect Expenses", "PL-04", ""),
    ("PL-04-04-01", 4, "Salaries and Wages", "5(i)(a)(i)", "Dr", "PL", "Emp", "Indirect Expenses", "PL-04-04", ""),
    ("PL-04-04-02", 4, "Contribution to PF & Other Funds", "5(i)(a)(ii)", "Dr", "PL", "Emp", "Indirect Expenses", "PL-04-04", ""),
    ("PL-04-04-03", 4, "ESOP / ESPP Expense", "5(i)(a)(iii)", "Dr", "PL", "Emp", "Indirect Expenses", "PL-04-04", ""),
    ("PL-04-04-04", 4, "Gratuity Expense", "5(i)(a)(ii)", "Dr", "PL", "Emp", "Indirect Expenses", "PL-04-04", ""),
    ("PL-04-04-05", 4, "Staff Welfare Expenses", "5(i)(a)(iv)", "Dr", "PL", "Emp", "Indirect Expenses", "PL-04-04", ""),
    ("PL-04-04-06", 4, "Directors' Remuneration", "5(i)(a)(i)", "Dr", "PL", "Emp", "Indirect Expenses", "PL-04-04", ""),

    # Finance Costs
    ("PL-04-05", 3, "Finance Costs", "Part II-IV", "Dr", "PL", "Fin", "Indirect Expenses", "PL-04", ""),
    ("PL-04-05-01", 4, "Interest Expense on Borrowings", "3(a)", "Dr", "PL", "Fin", "Indirect Expenses", "PL-04-05", ""),
    ("PL-04-05-02", 4, "Other Borrowing Costs", "3(b)", "Dr", "PL", "Fin", "Indirect Expenses", "PL-04-05", ""),
    ("PL-04-05-03", 4, "Forex Loss on Borrowings", "3(c)", "Dr", "PL", "Fin", "Indirect Expenses", "PL-04-05", ""),

    # Depreciation & Amortization
    ("PL-04-06", 3, "Depreciation and Amortization", "Part II-IV", "Dr", "PL", "Dep", "Indirect Expenses", "PL-04", ""),
    ("PL-04-06-01", 4, "Depreciation on Tangible Assets", "5(i)(b)", "Dr", "PL", "Dep", "Indirect Expenses", "PL-04-06", ""),
    ("PL-04-06-02", 4, "Amortization of Intangible Assets", "5(i)(b)", "Dr", "PL", "Dep", "Indirect Expenses", "PL-04-06", ""),

    # Other Expenses
    ("PL-04-07", 3, "Other Expenses", "Part II-IV", "Dr", "PL", "OE", "Indirect Expenses", "PL-04", ""),
    ("PL-04-07-01", 4, "Consumption of Stores & Spare Parts", "5(vi)(a)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-02", 4, "Power and Fuel", "5(vi)(b)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-03", 4, "Rent (Including Lease Rentals)", "5(vi)(c)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-04", 4, "Repairs to Buildings", "5(vi)(d)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-05", 4, "Repairs to Machinery", "5(vi)(e)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-06", 4, "Insurance", "5(vi)(f)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-07", 4, "Rates & Taxes (Excl. Income Tax)", "5(vi)(g)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-08", 4, "Communication Expenses", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-09", 4, "Travelling and Conveyance", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-10", 4, "Printing and Stationery", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-11", 4, "Legal and Professional Fees", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-12", 4, "Audit Fee - Statutory Audit", "5(i)(j)(a)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-13", 4, "Audit Fee - Tax Matters", "5(i)(j)(b)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-14", 4, "Audit Fee - Company Law Matters", "5(i)(j)(c)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-15", 4, "Audit Fee - Other Services", "5(i)(j)(e)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-16", 4, "Audit Fee - Reimbursement of Expenses", "5(i)(j)(f)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-17", 4, "Bad Debts Written Off", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-18", 4, "Provision for Doubtful Debts / Advances", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-19", 4, "Loss on Sale / Disposal of Fixed Assets", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-20", 4, "Foreign Exchange Loss (Non-Finance)", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-21", 4, "CSR Expenditure", "5(i)(k)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", "If u/s 135"),
    ("PL-04-07-22", 4, "Donations", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-23", 4, "Freight and Forwarding", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-24", 4, "Commission / Brokerage", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-25", 4, "Advertisement and Business Promotion", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-26", 4, "Directors' Sitting Fees", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),
    ("PL-04-07-27", 4, "Miscellaneous Expenses", "5(vi)(h)", "Dr", "PL", "OE", "Indirect Expenses", "PL-04-07", ""),

    # Tax
    ("PL-10-01", 3, "Current Tax", "Part II-X(1)", "Dr", "PL", "Tax", "Duties & Taxes", "PL-10", ""),
    ("PL-10-02", 3, "Deferred Tax", "Part II-X(2)", "Dr", "PL", "Tax", "Duties & Taxes", "PL-10", ""),
    ("PL-10-03", 3, "MAT Credit Entitlement", "Part II-X", "Cr", "PL", "Tax", "Duties & Taxes", "PL-10", ""),

    # Exceptional / Extraordinary
    ("PL-06", 2, "Exceptional Items", "Part II-VI", "Dr", "PL", "", "Indirect Expenses", "PL", ""),
    ("PL-08", 2, "Extraordinary Items", "Part II-VIII", "Dr", "PL", "", "Indirect Expenses", "PL", ""),
]

# Tally group → CoA code auto-mapping rules
TALLY_MAPPING_RULES = [
    ("Sales Accounts", "PL-01-01", 0.9),
    ("Purchase Accounts", "PL-04-01-02", 0.9),
    ("Direct Expenses", "PL-04-07-01", 0.6),
    ("Direct Incomes", "PL-01-04", 0.6),
    ("Indirect Expenses", "PL-04-07-27", 0.5),
    ("Indirect Incomes", "PL-02-10", 0.5),
    ("Fixed Assets", "BS-AS-01-01-04", 0.5),
    ("Investments", "BS-AS-01-02-02", 0.5),
    ("Bank Accounts", "BS-AS-02-04-01", 0.9),
    ("Bank OD Accounts", "BS-EL-04-01-01", 0.9),
    ("Bank OCC Accounts", "BS-EL-04-01-01", 0.9),
    ("Cash-in-Hand", "BS-AS-02-04-07", 0.95),
    ("Deposits (Asset)", "BS-AS-01-04-02", 0.7),
    ("Stock-in-Hand", "BS-AS-02-02-04", 0.7),
    ("Sundry Debtors", "BS-AS-02-03-01", 0.8),
    ("Sundry Creditors", "BS-EL-04-02-05", 0.8),
    ("Duties & Taxes", "BS-EL-04-03-10", 0.6),
    ("Loans & Advances (Asset)", "BS-AS-02-05-03", 0.6),
    ("Loans (Liability)", "BS-EL-03-01-06", 0.5),
    ("Secured Loans", "BS-EL-03-01-03", 0.7),
    ("Unsecured Loans", "BS-EL-03-01-06", 0.7),
    ("Current Liabilities", "BS-EL-04-03-11", 0.5),
    ("Current Assets", "BS-AS-02-06-02", 0.5),
    ("Provisions", "BS-EL-04-04-05", 0.6),
    ("Reserves & Surplus", "BS-EL-01-02-07", 0.5),
    ("Capital Account", "BS-EL-01-01-02", 0.8),
    ("Share Capital", "BS-EL-01-01-02", 0.9),
    ("Profit & Loss A/c", "BS-EL-01-02-09", 0.95),
    ("Suspense A/c", "BS-AS-02-06-02", 0.3),
    ("Branch / Divisions", "BS-AS-02-06-02", 0.3),
    ("Misc. Expenses (ASSET)", "BS-AS-02-06-02", 0.5),
]
