# Database Schema Manifest: Workforce Management (SAP HANA)

This document provides a zero-assumption breakdown of the database schema for the AI Query Agent, focusing on deterministic relationships and technical specifications.

## 1. Table Manifest
Exhaustive list of tables and views within the `WFMSCH_1` schema.

| Table Name | Primary Keys | Key Foreign Links (Employee Focus) | Field Types & Notes |
| :--- | :--- | :--- | :--- |
| `WFMSCH_1.USER_DETAILS` | `USERID`, `COMPANYID` | **Identity Source**: Joins to all `EMP_*` tables via `USERID`. | `NVARCHAR`, `DATE` (DOB), `TIMESTAMP`. |
| `WFMSCH_1.views::USER_DETAIL`| (None - View) | **Time-Aware Identity**: Effective-dated location/role info. | `DATE` (EFFECTIVE dates). |
| `WFMSCH_1.EMP_PLANNING` | `USERID`, `COMPANYID`, `LOCATIONID`, `JOBCODE`, `WORKDATE` | **Shift Source**: Links Employee to scheduled work via `USERID`. | `DATE` (WORKDATE). |
| `WFMSCH_1.EMP_WORKSLOT` | `USERID`, `COMPANYID`, `LOCATIONID`, `JOBCODE`, `WORKDATE`, `CHECKINTIME`, `CHECKOUTTIME` | **Attendance Source**: Links Employee to actual work logs. | `TIMESTAMP`, `BOOLEAN` (OVERTIME). |
| `WFMSCH_1.LOCATIONS` | `COMPANYID`, `LOCATIONID`, `BUSINESSUNITID`, `DIVISIONID`, `DEPARTMENTID`, `SUBDEPARTMENTID` | **Org Source**: Joins to `EMP_PLANNING`, `EMP_WORKSLOT` via `LOCATIONID`. | `NVARCHAR`. |
| `WFMSCH_1.EMP_HR` | `USERID`, `COMPNAYID`, `HR_EMPID`, `EFFECTIVESTARTDATE`, `EFFECTIVEENDDATE` | **HR Mapping**: Joins via `USERID`. Note typo `COMPNAYID`. | `NVARCHAR`. |
| `WFMSCH_1.EMP_MANAGER` | `USERID`, `COMPANYID`, `MANAGER_EMPID`, `EFFECTIVESTARTDATE`, `EFFECTIVEENDDATE` | **Hierarchy**: Subordinate (`USERID`) and Supervisor (`MANAGER_EMPID`). | `NVARCHAR`, `DATE`. |
| `WFMSCH_1.VACATION_HISTORY`| `COMPANYID`, `USERID`, `YEAR`, `CONTRACTNUMBER` | **Leave History**: Joins via `USERID` and `CONTRACTNUMBER`. | `DECIMAL` (Days), `NVARCHAR` (YEAR). |
| `WFMSCH_1.VACATION_BALANCE`| `COMPANYID`, `USERID`, `YEAR`, `CONTRACTNUMBER` | **Leave Balance**: Current available PTO. | `DECIMAL`, `NVARCHAR` (YEAR). |
| `WFMSCH_1.EMP_REQUESTS` | `USERID`, `COMPANYID`, `WORKDATE`, `REQUESTTYPE`, `STATUS` | **Requests**: PTO/OT applications. | `NVARCHAR`, `DATE`. |
| `WFMSCH_1.EMP_CONTRACT_DETAILS`| `USERID`, `COMPANYID`, `EFFECTIVESTARTDATE`, `EFFECTIVEENDDATE`, `CONTRACTNUMBER`, `LOCATIONID` | **Contract Junction**: Links Employee to Location/JobCode history. | `NVARCHAR`, `DATE`. |
| `WFMSCH_1.ROSTER_ITEM` | `ROSTER_HEADER_ID`, `ROSTER_ITEM_ID`, `DAY_NUMBER` | **Shift Templates**: Joins to `SHIFTCODE_SLOTMAPPING`. | `BIGINT`, `INTEGER`, `NVARCHAR` (JOB_CODE). |
| `WFMSCH_1.SHIFTCODE_SLOTMAPPING`| `COMPANYID`, `COUNTRYCODE`, `SHIFT_CODE` | **Shift Metadata**: Hours and slots for codes. | `NVARCHAR`. |

## 2. The Join Graph (Pathways)
Deterministically resolving paths between core entities.

| Source Entity | Target Entity | Pathway | Type |
| :--- | :--- | :--- | :--- |
| **Employee** | **Individual Shift** | `USER_DETAILS.USERID` → `EMP_PLANNING.USERID` | Direct (1:N) |
| **Branch Location** | **Individual Shift** | `LOCATIONS.LOCATIONID` → `EMP_PLANNING.LOCATIONID` | Direct (1:N) |
| **Employee** | **Payroll (Leave)** | `USER_DETAILS.USERID` → `VACATION_HISTORY.USERID` | Direct (1:N) |
| **Employee** | **Physical Location** | `USER_DETAILS` → `EMP_CONTRACT_DETAILS` → `LOCATIONS` | Junction (Contract) |
| **Employee** | **Skills** | `USER_DETAILS` → `EMP_SKILL_CERTIFICATE` → `SKILLS_CERTIFICATE` | Junction (Record) |

## 3. SQL Syntax Requirements
Identified from `src/engine/compiler.py` and successful HANA execution logs.

1.  **Quoting Strategy**: Double-quotes are mandatory for all identifiers to handle case-sensitivity and reserved words.
    *   *Correct*: `SELECT "USERID" FROM "WFMSCH_1"."USER_DETAILS"`
2.  **Date Functions**:
    *   HANA uses `TO_DATE('YYYY-MM-DD')` and `TO_TIMESTAMP('YYYY-MM-DD HH:MM:SS')`.
    *   The engine utilizes SQLAlchemy's `between()` and `literal_binds` for consistent date range filtering.
3.  **Pagination**:
    *   `LIMIT <X>` is the standard for row capping.
4.  **HANA Dialect**:
    *   The system uses `sqlalchemy-hana` (specifically `HANAHDBCLIDialect`).
5.  **Schema Prefixing**:
    *   All tables must be prefixed with the schema name (e.g., `WFMSCH_1`). The compiler handles this by splitting the BSL `physical_name`.

## 4. Error Analysis (Top 3 Reasons for Failure)
1.  **Missing Dependencies**: `ModuleNotFoundError: No module named 'sqlalchemy_hana'`.
    *   *Root Cause*: Running tests or the agent without activating the `venv`.
2.  **Schema Qualifiers**: "Invalid table name" errors.
    *   *Root Cause*: Failing to provide the `WFMSCH_1` prefix or incorrect splitting of the `physical_name` string.
3.  **Column Name Typos**: "Invalid column name" errors.
    *   *Root Cause*: Known DB inconsistencies (e.g., `COMPNAYID` in `EMP_HR`, `JOB_CODE` in `ROSTER_ITEM`). These must be mapped correctly in the `bsl_dictionary.py`.

---
*Note: This manifest is prepared for the Phase 2 deterministic translation engine.*
