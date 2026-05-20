"""Sign conventions and formatting constants for the financial engine"""

# Sign Convention:
# In Trial Balance: Debit = positive, Credit = negative (Dr - Cr)
# For display:
#   Assets (Dr balance) → show as positive
#   Liabilities (Cr balance) → TB gives negative, negate for positive display
#   Income (Cr balance) → TB gives negative, negate for positive display
#   Expenses (Dr balance) → show as positive

# Code prefix → sign multiplier for display
# TB stores Dr - Cr. For BS face:
#   Assets: display as is (positive Dr balance)
#   Liabilities: multiply by -1 (convert negative Cr balance to positive)
# For PL face:
#   Income: multiply by -1 (convert negative Cr balance to positive)
#   Expenses: display as is (positive Dr balance)

SIGN_MULTIPLIER = {
    "BS-EL": -1,   # Equity & Liabilities → negate TB value
    "BS-AS": 1,    # Assets → keep as is
    "PL-01": -1,   # Revenue → negate (Cr in TB)
    "PL-02": -1,   # Other Income → negate (Cr in TB)
    "PL-04": 1,    # Expenses → keep (Dr in TB)
    "PL-06": 1,    # Exceptional → keep
    "PL-08": 1,    # Extraordinary → keep
    "PL-10": 1,    # Tax → keep (mostly Dr)
}

def get_sign(code: str) -> int:
    for prefix, sign in SIGN_MULTIPLIER.items():
        if code.startswith(prefix):
            return sign
    return 1

# Rounding divisors
ROUNDING = {
    "Rupees": 1,
    "Thousands": 1000,
    "Lakhs": 100000,
    "Millions": 1000000,
    "Crores": 10000000,
}
