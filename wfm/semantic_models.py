import ibis
import ibis.expr.datatypes as dt
from boring_semantic_layer import SemanticModel

# =============================================================================
# WFM Semantic Models (Underscore Names for HANA Compatibility)
# =============================================================================

SCHEMA_NAME = "WFMSCH_1"

# 1. Define virtual tables
t_users = ibis.table(
    {"ID": "string", "USERNAME": "string", "FULL_NAME": "string",
     "IS_ACTIVE": "boolean", "TEAM_ID": "int32"},
    name="USERS",
    database=SCHEMA_NAME
)

t_depts = ibis.table(
    {"DEPARTMENTID": "string", "DEPARTMENTDESC": "string", "STATUS": "string"},
    name="DEPARTMENT",
    database=SCHEMA_NAME
)

t_profiles = ibis.table(
    {"ID": "string", "USER_ID": "int64", "DESIGNATION": "string",
     "DEPARTMENT": "string", "STATUS": "string"},
    name="EMPLOYEE_PROFILES",
    database=SCHEMA_NAME
)

t_shifts = ibis.table(
    {"ID": "string", "USER_ID": "int64", "DATE": "date",
     "SHIFT_TYPE": "string", "STATUS": "string",
     "CHECKED_IN_AT": "timestamp", "CHECKED_OUT_AT": "timestamp"},
    name="SHIFTS",
    database=SCHEMA_NAME
)

# 2. Define Semantic Models
# Note: Using names like "shifts_shift_type" instead of "shifts.shift_type"
# is safer for HANA SQL compilation.

departments_model = SemanticModel(
    name="departments",
    table=t_depts,
    dimensions={
        "dept_id": lambda t: t.DEPARTMENTID,
        "name": lambda t: t.DEPARTMENTDESC,
        "status": lambda t: t.STATUS
    }
)

employees_model = SemanticModel(
    name="employees",
    table=t_profiles,
    dimensions={
        "emp_id": lambda t: t.USER_ID,
        "designation": lambda t: t.DESIGNATION,
        "dept_name": lambda t: t.DEPARTMENT,
        "status": lambda t: t.STATUS
    }
).join_one(
    departments_model,
    on=lambda left, right: left.DEPARTMENT == right.DEPARTMENTID
)

# Main Shift Model
shifts_model = SemanticModel(
    name="shifts",
    table=t_shifts,
    dimensions={
        "shift_date": lambda t: t.DATE,
        "shift_type": lambda t: t.SHIFT_TYPE,
        "status": lambda t: t.STATUS
    },
    measures={
        "shift_count": lambda t: t.count()
    }
).join_one(
    employees_model,
    on=lambda left, right: left.USER_ID == right.USER_ID
)

# Export models
models = {
    "departments": departments_model,
    "employees": employees_model,
    "shifts": shifts_model
}
