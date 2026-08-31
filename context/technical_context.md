# Internal Sales & Finance Dashboard — Project Reference

## 1. What This Is

An internal Sales and Finance dashboard for **Mediamint** (parent company) and its subsidiaries, **DataBeat** and **Taktical Digital**. It blends Sales pipeline data with Finance actuals/plan data to give a unified view of revenue, pipeline, and target performance per client, portfolio lead, and entity.

The application only shows data for the current fiscal year: **April 2026 – March 2027 ("FY27")**.

---

## 2. Organizational Structure

- **Parent:** Mediamint (MM)
- **Subsidiaries:** DataBeat (DB), Taktical Digital (TD)
- These three are referred to as **Operational Groups** in the mapping sheet, and correspond to the entity-level filters/rollups in the app (also referred to as "Business Group" / "Biz Group").

---

## 3. Data Sources

### 3.1 Sales Tables:
- **Opportunity**
- **Account**
- **User**

### 3.2 Finance Tables:
- Taktical Actual & Backlog
- CP & portfolio lead mapped
- MM Actual & Backlog
- MM FY27 Plan
- MM Target with Portfolio FY27
- DB Actual & Backlog
- DB FY27 Plan & Target
- TD FY27 Plan & Target
- **Note:** Only Mediamint has a client-level breakdown for *Target*. DataBeat and Taktical only have client-level breakdown for *Plan* — but both still have a cumulative monthly Target across all clients.

---

## 4. Central Mapping Sheet — "CP & Portfolio Lead Mapped"

This is the tab used to tie together Client, Financial data, and Sales data. It has 11 columns; 10 are currently in use.

| Column | Purpose |
|---|---|
| Client Name | Join key to match clients across Actual, Backlog, Plan, and Target sheets |
| Portfolio Lead | Employee managing the client |
| Client Partner | Employee managing the client |
| Client Entity | Parent organization of the client; used to roll up related subsidiary companies under one cumulative number, and also used to map a client's Financial data to Sales data |
| MM ID | ID used to map a client's Financial data to Sales data |
| Operational Group | Entity name of the organization (MM / DB / TD) |
| Portfolio Lead Email | Employee email |
| Client Partner Email | Employee email |
| Client Type | Existing vs. New client |
| Client Tier | *Not currently used* — Client Tier is instead pulled from the Client Entity Mapping tab |
| SF Client Name | Manually verified alternate spelling used, after MM ID, to map Financial data to Sales data |

---

## 5. Client ↔ Deal Mapping ("Waterfall" / Fallback Logic)

**Problem:** The client/account name typed into Salesforce doesn't always match the name used internally in the Finance sheet (e.g. Salesforce "Amazon Web Services" vs. internal "Amazon"). Without a fallback, these deals show as **unmapped** and their dollars aren't counted toward that client.

**Solution:** Try matching methods in order of reliability; stop at the first one that finds a match; only fall through to the next step if the current one is empty.

### 5.1 The Steps

1. **Match by ID** (most reliable) — Opportunity's `AccountId` → Account table's `Client_id__c`, matched against **MM ID** in the mapping sheet.
2. **Match by "SF Client Name"** — the mapping sheet's manually-verified Salesforce spelling, matched against the Account table's `Name` column.
3. **Match by Client Entity name** — direct comparison of Client Entity to the Account table's `Name` column.
4. **Match by "Company Group" tag** (last resort) — the deal's own Company Group field (in the Opportunity table) matched against the mapping sheet's **Operational Group** column. This only reveals which broad group (Mediamint / DataBeat / Taktical) a deal belongs to — never a specific client.

A deal that fails every applicable step is correctly left **unmapped** rather than being force-matched.

### 5.2 Two Different Uses of the Same Logic

| Use Case | Steps Used | Why |
|---|---|---|
| **A — Business Group classification** (entity filters, "Biz Group" column, group summary tables) | 1, 2, 3, 4 | Only needs to answer "which group does this belong to" — the broad Company Group tag is good enough |
| **B — Specific client account attribution** (Portfolio Revenue account cards, account-level summaries) | 1, 2, 3 **only** | Step 4 can only identify a broad group, never a specific account, so it's skipped entirely here |

A deal can therefore be correctly counted at the group level (via Step 4) while still being unattributed to any one specific account (since Step 4 doesn't apply to use case B).

### 5.3 Known Gap
Some deals have no ID, no SF Client Name entry, and a Salesforce name that doesn't match the internal records at all. These can't be attributed to a specific account (Use Case B), even though they may still resolve correctly at the group level (Use Case A). Closing this gap means adding more entries to the SF Client Name column for the clients still falling through.

---

## 6. Key Metric Definitions

| Term | Definition |
|---|---|
| **Actual** | Amount already invoiced to the client. From the Actuals sheet, everything **up to and including last month**. |
| **Backlog** | Amount expected to be invoiced to the client. From the Actuals sheet, everything **from the current month onward**. |
| **Board Plan** | Pulled from the Plan Sheet. |
| **Target** | Pulled from the Plan Sheet. |
| **ACV** | Opportunity table's `Annual_Contracted_Value__c` column. |
| **Weighted Pipeline / Pipeline Revenue** | `Annual_Contracted_Value__c` × Opportunity `Probability`. |
| **Stage** | Opportunity table's `StageName`; probability (and therefore weighted pipeline) is derived from the stage a deal sits in. |
| **Line of Sight / Landing** | Actual + Backlog + Pipeline Revenue |
| **Win Rate** | Closed Won ÷ (Closed Won + Closed Lost + Withdrawn) |
| **Open Deal** | Any deal **not** in Closed Won / Closed Lost / Withdrawn stages |
| **Closed Deal** | Deal in Closed Won, Closed Lost, or Withdrawn stage |
| **Stuck Deal** | Deal age > 60 days |
| **Past Close Date Deal** | Deal whose close date has already passed |
| **Churn** | Comparison of a client's revenue this month vs. the prior month |

**Which pipeline figure is shown where:**
- **Revenue views** → Pipeline Revenue (weighted) blended with Actual + Backlog
- **Sales/Opportunity views** → ACV (unweighted)

---

## 7. Weighted Pipeline Spread Logic (Revenue Tabs)

Used wherever weighted pipeline is blended with Actual/Backlog to build revenue views. Two new fields are added alongside the existing **ACV** and **WTD Pipeline** fields on the Opportunity:

- **ACV FY27 (Current FY)** — ACV for the current financial year
- **WTD Pipeline FY27 (Current FY)** — WTD Pipeline for the current financial year

The same spreading logic applies to both ACV and WTD Pipeline; a deal's total value is spread across the months **following its close date**:

- **Close-date month:**
  - If close date is **on/after the 25th** of the month → contributes **0** for that month
  - If close date is **before the 25th** → contributes a prorated amount: `Monthly Amount × (Days in month − Close Date) ÷ Days in month` *(days-remaining share of that month)*
- **Every month after the close-date month** → full Monthly Amount (Total ACV or WTD Pipeline ÷ 12)

**Worked example:**

| | Opportunity 1 | Opportunity 2 |
|---|---|---|
| ACV | $1,000 | $800 |
| WTD Pipeline | $500 | $700 |
| Close Date | Jul 15, 2026 | Jul 26, 2026 |
| Monthly ACV (÷12) | $83.33 | $66.67 |
| Monthly WTD (÷12) | $41.67 | $58.33 |
| July contribution (WTD) | $21.51 (prorated — before the 25th; July has 31 days, 31−15=16 days remaining) | $0 (on/after the 25th) |
| Aug onward | Full $41.67/mo | Full $58.33/mo |

This per-opportunity logic is **summed across all opportunities** to produce the total spread shown in the Revenue tabs. (Reference: Weighted Pipeline Logic Google Sheet, and attached `Weighted_Pipeline_Logic.xlsx`.)

---

## 8. Dropdown / Filter Sourcing by Page

| Page | Dropdown | Source |
|---|---|---|
| Portfolio Revenue, Revenue DataPack | Portfolio Lead | CP & Portfolio Lead Mapped |
| Portfolio Revenue, Revenue DataPack | Client Partner | CP & Portfolio Lead Mapped |
| Portfolio Revenue, Revenue DataPack | Client Name | CP & Portfolio Lead Mapped, using **Client Entity** |
| Portfolio Pipeline | Opportunity Owner | **User** table, mapped via deal's `OwnerId` |
| Portfolio Pipeline | Client Name | CP & Portfolio Lead Mapped, using **Client Entity** |
---