# Query Worker – JSON→SQL Component

This document focuses **only** on the Query Worker component that turns a user question into a **SAP HANA query** via:

1. Schema retrieval and pruning (Vector + Graph).
2. LLM intent parsing into JSON (Gemini Flash).
3. JSON→SQL translation via Boring Semantic Layer (BSL) + Ibis.
4. Execution on SAP HANA.

---

## 1. Responsibilities and Boundaries
Given a natural-language question about WFM data, return the relevant rows and aggregates from SAP HANA. It does **not** maintain conversation memory or generate narrative reports.

---

## 2. JSON Contract (Intent Schema)
The JSON schema is the **interface** between the LLM and the Semantic Layer.

```json
{
  "metrics": ["overtime_hours", "headcount"],
  "dimensions": ["employees.department_name", "wfm_timesheets.shift_date"],
  "filters": [
    {"field": "employees.region", "operator": "==", "value": "APAC"},
    {"field": "wfm_timesheets.shift_date", "operator": ">=", "value": "2025-01-01"}
  ],
  "order_by": [
    {"field": "overtime_hours", "direction": "desc"}
  ],
  "limit": 10
}
```

---

## 3. Semantic Model Definition (BSL + Ibis)
We use **BSL** to define semantic models that map Metrics and Dimensions to Ibis expressions, and Joins to relationships between tables.

```python
import ibis
from boring_semantic_layer import SemanticModel, Join

con = ibis.connect("hana://user:password@host:39015/DBNAME")
raw_timesheets = con.table("TIMESHEETS")

wfm_model = SemanticModel(
    name="wfm_timesheets",
    table=raw_timesheets,
    dimensions={
        "shift_date": lambda t: t.SHIFT_DATE,
        "status": lambda t: t.STATUS,
    },
    measures={
        "total_hours": lambda t: t.HOURS.sum(),
        "overtime_hours": lambda t: ibis.greatest(t.HOURS - 8, 0).sum(),
        "headcount": lambda t: t.EMP_ID.nunique(),
    }
)
```

---

## 4. JSON → Ibis Filters → SQL
1. **Validate** metrics/dimensions exist in the semantic model.
2. **Translate filters** using Python conditions (`col == val`, `col.isin(val)`).
3. **Construct base query** via BSL (`wfm_model.query(...)`).
4. **Compile** to HANA SQL (`ibis.to_sql(query, dialect="hana")`).

---

## 5. Testing Strategy
1. **Semantic Model Tests:** Hardcode metric/dimension lists and ensure `wfm_model.query()` compiles.
2. **Filter Builder Tests:** Test individual operators with sample JSON.
3. **End-to-End Query Tests:** Feed known `intent` JSON and assert the returned DataFrame matches expected results.
