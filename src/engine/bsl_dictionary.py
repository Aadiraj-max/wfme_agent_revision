from typing import Any

# Business Schema Language (BSL) Mapping
# This dictionary maps logical business concepts used by the AI Query Agent
# to the physical SAP HANA database schema.

BSL_MAPPING: dict[str, dict[str, Any]] = {
    "tables": {
        "employees": {
            "physical_name": "SAP_HR.EMPLOYEES",
            "primary_key": "EMP_ID"
        },
        "departments": {
            "physical_name": "SAP_HR.DEPARTMENTS",
            "primary_key": "DEPT_ID"
        },
        "timesheets": {
            "physical_name": "SAP_WFM.TIMESHEETS",
            "primary_key": "TS_ID"
        }
    },
    "metrics": {
        "headcount": {
            "table": "employees",
            "column": "EMP_ID",
            "aggregation": "count"
        },
        "overtime_hours": {
            "table": "timesheets",
            "column": "OT_HOURS",
            "aggregation": "sum"
        },
        "total_salary": {
            "table": "employees",
            "column": "ANNUAL_SALARY",
            "aggregation": "sum"
        }
    },
    "dimensions": {
        "department_name": {
            "table": "departments",
            "column": "DEPT_NAME"
        },
        "location": {
            "table": "employees",
            "column": "OFFICE_LOCATION"
        },
        "employee_role": {
            "table": "employees",
            "column": "JOB_TITLE"
        }
    }
}
