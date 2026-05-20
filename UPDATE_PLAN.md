# TCE ENGINE - CONSOLIDATED UPDATE PLAN
## Based on User Feedback + Reference Template Analysis

---

## REVISED WORKFLOW (Enforced Sequential Flow)

```
Step 1: SETUP (Mandatory)
  → Client name, CIN, address, auditor, capital, face value
  → FY, BS dates (CY & PY)
  → Cannot proceed without completing

Step 2: UPLOAD TB (Mandatory)
  → Upload Tally TB (Excel/CSV)
  → Show Dr/Cr balance check
  → Cannot proceed to Step 3 without balanced TB

Step 3: MAP CoA (Mandatory)
  → Auto-map first
  → TWO-COLUMN SELECTOR: Major Code dropdown → filtered Sub-code dropdown
  → Must reach 100% mapping before Step 4

Step 4: SUPPLEMENTARY DATA (New combined step)
  → PPE Gross Block + Accumulated Dep input (with TB validation)
  → Share Capital details (reconciliation, >5%, promoter holding)
  → Related Party master + transactions
  → Ageing data (TR + TP party-wise)
  → Each sub-section has mandatory/optional indicators

Step 5: NOTE ENRICHMENT (New step)
  → For each note: TB auto-values shown + edit capability
  → Schedule III required disclosures as Yes/No + input
  → Accounting Policies (predefined selection + free text)
  → Additional Disclosures (A-T structured input)
  → Audit Proposed Entries (moved here - after all data is in)

Step 6: PREVIEW & VALIDATE
  → Full BS, PL, Notes, CF, Ratios, EPS in browser
  → Validation checks (BS balances, PPE matches TB, etc.)
  → Red flags shown if any

Step 7: EXPORT
  → Generate 20-sheet Excel with actual dates and company name
  → Download
```

---

## FIX DETAILS

### FIX 1: Workflow Steps Clickable + Sequential Gate
- Each step is a link, but grayed out / disabled if prerequisite not met
- Status progression: setup → tb_uploaded → mapped → data_entered → enriched → previewed → exported
- Visual: completed=green, current=gold, locked=grey

### FIX 2: Audit Entry Form on Web
- Full modal form with Dr/Cr CoA code selectors, amount, narration, status
- Approve/Reject/Delete buttons per entry
- Balance check shown at bottom

### FIX 3: Two-Column Mapping Selector
- Column 1: Major Code dropdown (e.g., "BS-EL-01 Share Capital", "PL-04-07 Other Expenses")
  → Derived from level 2-3 CoA codes
- Column 2: Sub-code dropdown — FILTERED to show only children of selected major code
  → e.g., selecting "PL-04-07" shows only PL-04-07-01 through PL-04-07-27
- Much faster than scrolling through 248 codes

### FIX 4: Excel Header — Actual Company Name
- Replace "=Master!B5" formula with actual company name string in all sheets
- Company name comes from Client model, not a formula reference

### FIX 5: Proper Dates in Headers (Reference Template Format)
- BS: "As at 31 March 2025" / "As at 31 March 2024"
- PL: "For the year ended 31 March 2025" / "For the year ended 31 March 2024"
- CF: "For the Year Ended 31 March 2025" / "For the Year Ended 31 March 2024"
- Notes-BS: "As at 31 March 2025" / "As at 31 March 2024"
- Notes-PL: "For the year ended 31 March 2025" / "For the year ended 31 March 2024"
- Derived from project.bs_date_cy and project.bs_date_py

---

## FIX 6: NOTE ENRICHMENT SYSTEM (Per-Note Manual Edit + Schedule III Disclosures)

### Every Note gets:
1. TB auto-computed values (read-only display)
2. Manual override per line item (edit amount)
3. Add custom line items (label + amount)
4. Text disclosures (free text input per note)
5. Yes/No checklist for Schedule III requirements

### Note A — Share Capital (Reference: Notes_BS rows 6-110)
- [TB Auto] Authorised, Issued, Paid-up amounts
- [Manual] No. of shares per class with face value description
- [Table] Reconciliation: Opening → Issued → Bought back → Closing (Nos + Amount)
- [Table] Shareholders >5% (Name, Nos, %, CY and PY)
- [Table] Promoter Shareholding (Name, Nos, %, Change from PY)
- [Text] (b) Rights, preferences & restrictions attached
- [Text] (c) Terms of convertible securities
- [Table] (f) Shares held by holding/subsidiary companies
- [Table] (g) 5-year history: allotted without cash / bonus / buyback
- [Text] (h) Conversion details during the year
- [Text] (i) Outstanding convertible securities
- [Text] (j) Shares reserved for issue under options/contracts
- [Text] (k) Calls unpaid (aggregate + directors/officers separately)

### Note B — Reserves & Surplus
- [TB Auto] Capital Reserve, Securities Premium, General Reserve, P&L balance
- [Manual] Opening balance + Movement (additions/deductions) for each reserve
- [Auto] P&L surplus = Opening + PAT - Appropriations

### Note C — Long-Term Borrowings (Reference: Notes_BS rows 137-146)
- [TB Auto] Secured/Unsecured loan amounts
- [YES/NO] Is any loan secured? → If Yes:
  - [Text] Nature of security for each loan
  - [YES/NO] Any director guarantee? → [Text] Details
  - [Text] Terms of repayment
- [YES/NO] Any default on BS date? → [Amount + Period]
- [Text] Bonds/Debentures: rate, redemption terms

### Note D — Other LT Liabilities
- [TB Auto] Trade Payables LT, Others
- [Manual] Override/add

### Note E — LT Provisions
- [TB Auto] Employee Benefits, Other Provisions
- [Text] Nature of provisions

### Note F — ST Borrowings
- [TB Auto] Bank OD, Loans from Related Parties, Others
- [YES/NO] Secured? → Nature of security
- [YES/NO] Director guarantee? → Details
- [YES/NO] Default? → Amount + Period

### Note FA — Trade Payables
- [TB Auto] Total from ageing codes
- [Table] MSME disclosure (7 items per MSMED Act Sec 22)
- [Table] Ageing matrix (MSME/Other × Undisputed/Disputed × 4 buckets)

### Note G — Other Current Liabilities
- [TB Auto] All sub-items
- [Manual] Override/add custom items

### Note H — ST Provisions
- [TB Auto] Employee benefits, Tax provision, Proposed dividend
- [Manual] Override/add

### Note I — Tangible Assets (PPE Schedule)
- [Manual Input] Per asset class:
  - Opening Gross Block
  - Additions
  - Disposals
  - Closing Gross Block (auto-computed)
  - Opening Accumulated Depreciation
  - Depreciation for Year
  - Dep on Disposals
  - Closing Accumulated Dep (auto-computed)
  - Net CY (auto: Gross Close - Dep Close)
  - Net PY
- [Validation] Net CY must match TB balance for that asset code
- [Note] Leased assets separately identified
- [Text] Revaluation details if applicable

### Note J — Intangible Assets
- Same PPE schedule structure as Note I

### Note K — Non-Current Investments
- [TB Auto] Investment amounts
- [YES/NO] Any quoted investments? → Aggregate + Market Value
- [Manual] Unquoted aggregate
- [Manual] Provision for diminution
- [Table] Details per body corporate (Sub/Assoc/JV/SPE)
- [Manual] Trade vs Other classification

### Note L — LT Loans & Advances
- [TB Auto] Capital Advances, Security Deposits, etc.
- [Manual] Secured/Unsecured/Doubtful sub-classification
- [Manual] Dues from directors/officers (aggregate)

### Note M — Other NC Assets
- [TB Auto] values
- [Manual] Override/add

### Note N — Current Investments
- Similar to Note K

### Note O — Inventories
- [TB Auto] RM, WIP, FG, SIT, Stores, Loose Tools
- [Text] Mode of valuation stated
- [Manual] Goods-in-transit under relevant sub-head

### Note P — Trade Receivables
- [TB Auto] Total from ageing codes
- [Table] Ageing matrix (Undisputed/Disputed × Good/Doubtful × 5 buckets)
- [Manual] Secured/Unsecured classification
- [Manual] Dues from directors/officers (separately stated)
- [Manual] Debts >6 months from due date

### Note Q — Cash & Equivalents
- [TB Auto] Bank balances, Cash, Cheques
- [Text] Repatriation restrictions if any
- [Manual] Bank deposits >12 months separately shown

### Note R — ST Loans & Advances
- [TB Auto] All sub-items
- [Manual] Secured/Unsecured/Doubtful classification
- [Manual] Dues from directors/officers

### Note S — Other Current Assets
- [TB Auto] values
- [Manual] Override/add

### PL Notes (Rev, OI, Emp, Fin, Dep, OE, Tax)
- [TB Auto] All line items
- [Manual] Override/add custom items
- [OE Note] Auditor's Remuneration breakup as sub-note
- [Tax Note] Deferred Tax computation (Book vs IT depreciation)

---

## FIX 7: PPE Gross Block Input (Reference: Note_Dep sheet)

### Structure per asset class:
```
Asset          | GROSS BLOCK                           | DEPRECIATION                          | NET BLOCK
               | Open   | Add   | Disp  | Close       | Open   | For Yr | On Disp | Close    | CY    | PY
Land           |  [inp] | [inp] | [inp] | =auto       |  [inp] | [inp]  | [inp]   | =auto    | =auto | [inp]
Building       |  [inp] | [inp] | [inp] | =auto       |  [inp] | [inp]  | [inp]   | =auto    | =auto | [inp]
Plant & Equip  |  [inp] | [inp] | [inp] | =auto       |  [inp] | [inp]  | [inp]   | =auto    | =auto | [inp]
...
TOTAL TANGIBLE | =sum   | =sum  | =sum  | =sum        | =sum   | =sum   | =sum    | =sum     | =sum  | =sum
...Intangibles...
GRAND TOTAL    | =sum   | =sum  | =sum  | =sum        | =sum   | =sum   | =sum    | =sum     | =sum  | =sum
PREVIOUS YEAR  | [inp]  | [inp] | [inp] | =auto       | [inp]  | [inp]  | [inp]   | =auto    | =auto | 
```

### Validation Rules:
- Gross Close = Gross Open + Additions - Disposals
- Dep Close = Dep Open + For Year - On Disp
- Net CY = Gross Close - Dep Close
- Net CY MUST = TB balance for corresponding CoA code (warning if mismatch)
- Total Dep For Year MUST = PL-04-06-01 from TB (warning if mismatch)

---

## FIX 8: Accounting Policies (Predefined + Custom)

### Predefined options per policy:
1. Basis of Preparation → Fixed text (Indian GAAP, AS under Sec 133)
2. Revenue Recognition → Options: "As per AS-9" / "Percentage completion" / Custom
3. PPE → Options: "Cost model" / "Revaluation model" / Custom
4. Depreciation → Options: "WDV per Schedule II" / "SLM per Schedule II" / "Custom useful life"
5. Inventories → Options: "FIFO" / "Weighted Average" / "Specific Identification" + "Lower of cost & NRV"
6. Employee Benefits → Options: "Defined contribution: PF/ESI" / "Defined benefit: Actuarial" / Custom
7. Borrowing Costs → Options: "Capitalize per AS-16" / "Expense as incurred"
8. Taxation → Options: "Current + Deferred per AS-22" / Custom
...etc for all 16+ policies

### Each policy:
- Toggle active/inactive
- Select from predefined dropdown
- Edit/override with free text
- Add custom policies at end

---

## FIX 9: Additional Disclosures (Reference: Notes_Disc sheet)

### Full structured input (from reference template):

32. Opinion on assets valuation → [Text]
33. Operating leases → [YES/NO] → [Amount] rental expense
34. AS-15 Employee Benefits:
    - Defined Contribution: PF amount, ESI amount
    - Defined Benefit (Gratuity/Leave):
      - Actuarial assumptions table (discount rate, salary escalation, retirement age, mortality)
35. Related Party Disclosures (separate tab):
    - (i) Loans to promoters/directors/KMP with terms
    - (ii) Current account balances payable/receivable
    - (iii) Managerial Remuneration
    - (iv) All other transactions
36. CWIP Ageing (<1Y, 1-2Y, 2-3Y, >3Y) + projects in progress + overdue
37. Intangible Under Dev Ageing (same structure as CWIP)
38. Ratio Analysis (11 ratios + variance explanation)
39. Borrowings on basis of current assets → [YES/NO] + quarterly returns details
40. Wilful Defaulter → [YES/NO] + details
41. Benami Property → [YES/NO] + details
42. Struck-off Companies → [YES/NO] + Name/Nature/Balance
43. Registration of Charges → [YES/NO] + details
44. Compliance with Layers → [YES/NO]
45. Scheme of Arrangements → [YES/NO] + details
46. Utilisation of Borrowed Funds / Share Premium → [YES/NO] + purpose
47. Title deeds not in company name → [YES/NO] + details
48. Contingent Liabilities → [Table: Type, Forum, Amount Claimed, Provided, Assessment]
49. Commitments → [Table: Capital contracts, Uncalled liability, Other]
50. Earnings in Foreign Currency → [Table: Category × CY × PY]
51. Expenditure in Foreign Currency → [Table: Category × CY × PY]
52. Unhedged Foreign Currency Exposure → [Table: Currency × Amount in FC × Amount in INR × CY × PY]
53. EPS Computation (auto from engine)
54. Previous year regrouping note (standard text)
55. Signing block: Auditor firm + directors + place + date + UDIN

---

## FIX 10: Deferred Tax Computation (Reference: Def Tax sheet)

### Structure:
```
TAX RATE: [input]%

DEPRECIATION TIMING DIFFERENCE:
  WDV as per Books:  [auto from PPE]
  WDV as per IT:     [input IT dep rates]
  Difference:        [auto]
  DTL/DTA:           [auto = diff × tax rate]

SEC 43B DISALLOWANCES:
  Opening:              [input]
  Less: Reversed:       [input]
  Add: CY disallowance: [input]
  Net:                  [auto]
  DTA:                  [auto = net × tax rate]

SEC 40A(7) - GRATUITY:
  Same structure as 43B

LOSS CARRIED FORWARD:
  Amount: [input]
  DTA:    [auto = amount × tax rate]

NET DTA / (DTL): [auto sum]
```

---

## FIX 11: Signing Block in Excel Export (Reference: Notes_Disc rows 195-207)

### Structure:
```
As per our report of even date attached

For [Auditor Firm]                          For and on behalf of Board of Directors of
Chartered Accountants                        [Company Name]
FRN: [FRN]

[Partner Name]                              [Director 1]          [Director 2]
Partner                                     Director              Director
M.No.: [Membership No]                     DIN: [DIN]            DIN: [DIN]

Place: [Place]                              Place: [Place]
Dated: [Date]                               Dated: [Date]
UDIN: [UDIN]
```

---

## SEPARATE TABS/PAGES IN WEB UI

1. Dashboard
2. Project Overview (workflow tracker)
3. TB Upload
4. CoA Mapping (two-column)
5. Supplementary Data:
   - PPE Schedule (sub-tab)
   - Share Capital (sub-tab)
   - Related Party (sub-tab)
   - Ageing Data (sub-tab)
6. Note Enrichment:
   - BS Notes A-S (with Schedule III checklist per note)
   - PL Notes (with Auditor Remuneration sub-note)
   - Accounting Policies (predefined + custom)
   - Additional Disclosures (32-55)
   - Deferred Tax Computation
7. Audit Entries
8. Preview (BS / PL / Notes / CF / Ratios / EPS tabs)
9. Export (with signing block configuration)

---

## READY TO BUILD
