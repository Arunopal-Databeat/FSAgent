Tables available:
    Sales: sales_opportunity, sales_account, sales_user
    Finance: financial_clientportfoliomapping, financial_cliententitymapping, financial_mmactualbacklog, financial_mmplan, financial_mmtargetportfolio, financial_dbactualbacklog, financial_dbplantarget, financial_takticalactualbacklog, financial_tdplantarget

All column names below are case-sensitive and contain spaces/mixed case in several tables — always double-quote them in SQL, e.g. "Client Name", "Apr-26".

IMPORTANT — data quality: financial_mmactualbacklog, financial_mmplan, financial_mmtargetportfolio, financial_dbactualbacklog, financial_dbplantarget, financial_takticalactualbacklog, and financial_tdplantarget all mix real client rows with rollup/placeholder rows (e.g. "Board Plan NC", "Board Plan EC", "Target", "NC Target", "EC Target"). Each of these tables has an is_aggregate boolean column that flags these rows directly — always filter WHERE is_aggregate = false (or = FALSE) before doing any client-level sum, average, or join. Do not fall back to name-pattern matching (ILIKE '%target%'/'%board%') to find these rows — is_aggregate already does it reliably.

Examples:

- Wrong (includes placeholder rows, double-counts against real clients):
  SELECT SUM("FY27 Total") FROM financial_mmtargetportfolio;

- Right (client-level total, placeholders excluded):
  SELECT SUM("FY27 Total") FROM financial_mmtargetportfolio WHERE is_aggregate = false;

- Wrong (fragile, will miss/mismatch rows like "EC Target" or catch legitimate client names containing "target"):
  SELECT * FROM financial_dbplantarget WHERE "Account" NOT ILIKE '%target%' AND "Account" NOT ILIKE '%board%';

- Right (same intent, reliable):
  SELECT * FROM financial_dbplantarget WHERE is_aggregate = false;

- If you actually want the pre-computed rollup/company-wide total (e.g. "what's the total NC target across all clients"), query the is_aggregate = true row directly instead of summing client rows yourself:
  SELECT "FY27 Total" FROM financial_mmtargetportfolio WHERE is_aggregate = true AND "Client Name" = 'NC Target';

- Joining to the mapping table should also filter first, so placeholder rows don't produce spurious/null-matched join rows:
  SELECT b."Client Name", b."Total", m."Portfolio Lead"
  FROM financial_mmactualbacklog b
  JOIN financial_clientportfoliomapping m ON m."Client Name" = b."Client Name"
  WHERE b.is_aggregate = false;

## Table: public.sales_opportunity

| Column | Type |
|---|---|
| id | bigint |
| snapshot_date | date |
| Id | text |
| AccountId | text |
| Name | text |
| Description | text |
| StageName | text |
| Probability | double precision |
| CloseDate | date |
| IsClosed | boolean |
| OwnerId | text |
| CreatedDate | timestamptz |
| Annual_Contracted_Value__c | double precision |
| LeadSource | text |
| Company_Group__c | text |
| Go_Live_Date__c | text |
| HeadCount__c | text |
| Resource_Type__c | text |
| Service_Delivery_Model__c | text |
| LastStageChangeInDays | integer |
| Revenue_Type__c | text |
| LastActivityInDays | integer |
| Project_Duration__c | text |

## Table: public.sales_account

| Column | Type |
|---|---|
| id | bigint |
| snapshot_date | date |
| Id | text |
| Name | text |
| Status__c | text (Active / Deactivated / Inactive) |
| Type | text (Prospect / Other / New Business / Partner / Customer / '') |
| Industry | text |
| Account_Type__c | text (Existing Client / New Client) |
| OwnerId | text |
| Primary_Account_Lead_Source__c | text |
| Client_ID__c | text (join key: MM ID, blank for many rows) |

## Table: public.sales_user

| Column | Type |
|---|---|
| id | bigint |
| snapshot_date | date |
| Id | text |
| Name | text |
| IsActive | boolean |

## Table: public.financial_clientportfoliomapping

Central mapping sheet: Client ↔ Portfolio Lead ↔ Entity

| Column | Type |
|---|---|
| id | bigint |
| snapshot_date | date |
| Client Name | text |
| Portfolio Lead | text |
| Client Partner | text |
| Client Entity | text |
| MM ID | text |
| Operational Group | text (Mediamint / DataBeat / Taktical) |
| Portfolio Lead Email | text |
| Client Partner Email | text |
| Client Type | text (Existing Client / New Client) |
| SF Client Name | text |

## Table: public.financial_cliententitymapping

Client partnership tier mapping

| Column | Type |
|---|---|
| id | bigint |
| snapshot_date | date |
| Client | text |
| Partnership Level | text (1. Mint Platinum / 2. Mint Elite / 3. Mint Core / 4. Mint Agencies / 5. Mint SMB) |

## Table: public.financial_mmactualbacklog

Mediamint Actual & Backlog by client

| Column | Type |
|---|---|
| id | bigint |
| Apr-26 ... Mar-27 | integer (monthly values) |
| snapshot_date | date |
| Client Name | text |
| is_aggregate | boolean (true = rollup/placeholder row, e.g. "Board Plan NC" — exclude for client-level analysis) |
| Total | integer |

## Table: public.financial_mmplan

Mediamint FY27 Board Plan by client

| Column | Type |
|---|---|
| id | bigint |
| Apr-26 ... Mar-27 | integer (monthly values) |
| snapshot_date | date |
| Client Name | text |
| is_aggregate | boolean (true = rollup/placeholder row, e.g. "Board Plan NC" — exclude for client-level analysis) |
| FY27 Total | integer |

## Table: public.financial_mmtargetportfolio

Mediamint FY27 Target by client, w/ portfolio

| Column | Type |
|---|---|
| id | bigint |
| Apr-26 ... Mar-27 | integer (monthly values) |
| snapshot_date | date |
| Client Name | text |
| is_aggregate | boolean (true = rollup/placeholder row, e.g. "NC Target" — exclude for client-level analysis) |
| FY27 Total | integer |

## Table: public.financial_dbactualbacklog

DataBeat Actual & Backlog by client

| Column | Type |
|---|---|
| id | bigint |
| Apr-26 ... Mar-27 | integer (monthly values) |
| snapshot_date | date |
| Account | text |
| is_aggregate | boolean |
| Total | integer |

## Table: public.financial_dbplantarget

DataBeat FY27 Plan & Target

| Column | Type |
|---|---|
| id | bigint |
| Apr-26 ... Mar-27 | integer (monthly values) |
| snapshot_date | date |
| Account | text |
| is_aggregate | boolean (true = rollup/placeholder row, e.g. "Board Plan NC", "Target" — exclude for client-level analysis) |
| FY27 | integer |

## Table: public.financial_takticalactualbacklog

Taktical Digital Actual & Backlog by client

| Column | Type |
|---|---|
| id | bigint |
| Apr-26 ... Mar-27 | integer (monthly values) |
| snapshot_date | date |
| Client Name | text |
| is_aggregate | boolean |
| Total | integer |

## Table: public.financial_tdplantarget

Taktical FY27 Plan & Target

| Column | Type |
|---|---|
| id | bigint |
| Apr-26 ... Mar-27 | integer (monthly values) |
| snapshot_date | date |
| Client | text |
| is_aggregate | boolean (true = rollup/placeholder row, e.g. "Target" — exclude for client-level analysis) |
| FY 27 | integer |

## Relationships

### Core Sales Tables

| Table A | Column A | Table B | Column B | Relationship |
|---|---|---|---|---|
| sales_opportunity | AccountId | sales_account | Id | Deal -> owning Account |
| sales_opportunity | OwnerId | sales_user | Id | Deal -> Opportunity Owner (rep) |
| sales_account | OwnerId | sales_user | Id | Account -> Account Owner |

### Sales ↔ Finance Bridge (the "Waterfall" logic)

| Table A | Column A | Table B | Column B | Relationship / Match Priority |
|---|---|---|---|---|
| sales_account | Client_ID__c | financial_clientportfoliomapping | MM ID | Step 1 (most reliable) - ID match |
| sales_account | Name | financial_clientportfoliomapping | SF Client Name | Step 2 - verified SF spelling match |
| sales_account | Name | financial_clientportfoliomapping | Client Entity | Step 3 - direct entity name match |
| sales_opportunity | Company_Group__c | financial_clientportfoliomapping | Operational Group | Step 4 (last resort, group-level only) |

Steps 1-3 apply to specific account attribution (Use Case B). All 4 steps apply to broad group/entity classification (Use Case A) — stop at the first step that returns a match.

### Finance Tables ↔ Central Mapping Sheet

All finance tables join back to financial_clientportfoliomapping using client name (and MM ID where available) as the key:

| Table A | Column A | Table B | Column B |
|---|---|---|---|
| financial_mmactualbacklog | Client Name | financial_clientportfoliomapping | Client Name |
| financial_mmplan | Client Name | financial_clientportfoliomapping | Client Name |
| financial_mmtargetportfolio | Client Name | financial_clientportfoliomapping | Client Name |
| financial_dbactualbacklog | Account | financial_clientportfoliomapping | Client Name |
| financial_dbplantarget | Account | financial_clientportfoliomapping | Client Name * |
| financial_takticalactualbacklog | Client Name | financial_clientportfoliomapping | Client Name |
| financial_tdplantarget | Client | financial_clientportfoliomapping | Client Name * |
| financial_cliententitymapping | Client | financial_clientportfoliomapping | Client Name |

\* DB and TD Plan & Target tables mix per-client rows with cumulative/rollup rows flagged by is_aggregate = true (e.g. "Board Plan NC", "Target") — filter these out (WHERE is_aggregate = false) before doing client-level Target attribution.

### Key Notes on the Relationships

- Client_ID__c / MM ID is the most reliable join key wherever it's populated — it directly links sales_account.Client_ID__c to every finance table's client name field via the mapping sheet. It is blank for many sales_account rows.
- Client Entity in the mapping sheet serves double duty: it rolls up subsidiary companies under one parent for reporting, and acts as a fallback match key against sales_account.Name.
- Operational Group in the mapping sheet is the field that ultimately decides whether a client/deal counts under Mediamint, DataBeat, or Taktical for entity-level rollups.
- is_aggregate = true rows are pre-flagged rollup/placeholder rows (parent totals, "Board Plan NC/EC", "Target", "NC Target") mixed into the plan/target/backlog tables — always filter WHERE is_aggregate = false for client-level math; leave them in only when you deliberately want the pre-computed rollup total.
- financial_cliententitymapping gives each client's Partnership Level tier (1. Mint Platinum highest ... 5. Mint SMB lowest), separate from the client_type Existing/New flag in financial_clientportfoliomapping.
