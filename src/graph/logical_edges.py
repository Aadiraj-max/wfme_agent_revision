"""
These edges were verified against the live SAP HANA database column metadata. 
COMPANYID-based edges are intentionally excluded as they represent multi-tenancy scoping, 
not queryable join relationships.
"""

LOGICAL_EDGES = [
    # Identity edges (relationship_type = 'identity')
    {"from_table": "EMP_CONTRACT_DETAILS", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    
    # EMP_HR uses COMPNAYID (typo in DB), not COMPANYID. Never filter EMP_HR by COMPANYID.
    {"from_table": "EMP_HR", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    {"from_table": "EMP_HR", "from_column": "HR_EMPID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    
    {"from_table": "EMP_MANAGER", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    {"from_table": "EMP_MANAGER", "from_column": "MANAGER_EMPID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    {"from_table": "EMP_PLANNING", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    {"from_table": "EMP_REQUESTS", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    {"from_table": "EMP_SKILL_CERTIFICATE", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    {"from_table": "EMP_WORKSLOT", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    {"from_table": "VACATION_BALANCE", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    {"from_table": "VACATION_HISTORY", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},
    {"from_table": "USER_DETAIL", "from_column": "USERID", "to_table": "USER_DETAILS", "to_column": "USERID", "relationship_type": "identity"},

    # Location edges (relationship_type = 'location')
    {"from_table": "EMP_CONTRACT_DETAILS", "from_column": "LOCATIONID", "to_table": "LOCATIONS", "to_column": "LOCATIONID", "relationship_type": "location"},
    {"from_table": "EMP_PLANNING", "from_column": "LOCATIONID", "to_table": "LOCATIONS", "to_column": "LOCATIONID", "relationship_type": "location"},
    {"from_table": "EMP_WORKSLOT", "from_column": "LOCATIONID", "to_table": "LOCATIONS", "to_column": "LOCATIONID", "relationship_type": "location"},
    {"from_table": "USER_DETAIL", "from_column": "LOCATIONID", "to_table": "LOCATIONS", "to_column": "LOCATIONID", "relationship_type": "location"},
    {"from_table": "POSITION", "from_column": "BUSINESSUNITID", "to_table": "LOCATIONS", "to_column": "BUSINESSUNITID", "relationship_type": "location"},
    {"from_table": "POSITION", "from_column": "DIVISIONID", "to_table": "LOCATIONS", "to_column": "DIVISIONID", "relationship_type": "location"},
    {"from_table": "POSITION", "from_column": "DEPARTMENTID", "to_table": "LOCATIONS", "to_column": "DEPARTMENTID", "relationship_type": "location"},

    # Roster edges (relationship_type = 'roster')
    # ROSTER_ITEM uses JOB_CODE with underscore, not JOBCODE. Never join on job code between ROSTER_ITEM and other tables without aliasing.
    {"from_table": "ROSTER_ITEM", "from_column": "ROSTER_HEADER_ID", "to_table": "ROSTER_HEADER", "to_column": "ROSTER_HEADER_ID", "relationship_type": "roster"},
    {"from_table": "V_ROSTER_PLANNED_EMP", "from_column": "ROSTER_HEADER_ID", "to_table": "ROSTER_HEADER", "to_column": "ROSTER_HEADER_ID", "relationship_type": "roster"},

    # Shift edges (relationship_type = 'shift')
    {"from_table": "EMP_PLANNING", "from_column": "SHIFT_CODE", "to_table": "SHIFTCODE_SLOTMAPPING", "to_column": "SHIFT_CODE", "relationship_type": "shift"},
    {"from_table": "ROSTER_ITEM", "from_column": "SHIFT_CODE", "to_table": "SHIFTCODE_SLOTMAPPING", "to_column": "SHIFT_CODE", "relationship_type": "shift"},
    {"from_table": "EMP_PLANNING", "from_column": "WORKDAYCODE", "to_table": "WORKDAY_TYPES", "to_column": "WORKDAYCODE", "relationship_type": "shift"},
    {"from_table": "SHIFTCODE_SLOTMAPPING", "from_column": "COUNTRYCODE", "to_table": "WORKDAY_TYPES", "to_column": "COUNTRYCODE", "relationship_type": "shift"},

    # Skills edges (relationship_type = 'skills')
    {"from_table": "EMP_SKILL_CERTIFICATE", "from_column": "CODE", "to_table": "SKILLS_CERTIFICATE", "to_column": "CODE", "relationship_type": "skills"},
    {"from_table": "EMP_SKILL_CERTIFICATE", "from_column": "TYPE", "to_table": "SKILLS_CERTIFICATE", "to_column": "TYPE", "relationship_type": "skills"},

    # Contract edges (relationship_type = 'contract')
    {"from_table": "VACATION_BALANCE", "from_column": "CONTRACTNUMBER", "to_table": "EMP_CONTRACT_DETAILS", "to_column": "CONTRACTNUMBER", "relationship_type": "contract"},
    {"from_table": "VACATION_HISTORY", "from_column": "CONTRACTNUMBER", "to_table": "EMP_CONTRACT_DETAILS", "to_column": "CONTRACTNUMBER", "relationship_type": "contract"},
]

def get_edges_for_table(table_name: str) -> list:
    """
    Returns all edges where from_table OR to_table matches the given table name.
    """
    return [edge for edge in LOGICAL_EDGES if edge["from_table"] == table_name or edge["to_table"] == table_name]

def get_join_columns(from_table: str, to_table: str) -> dict | None:
    """
    Returns the edge dict if a direct edge exists between two tables in either direction.
    """
    for edge in LOGICAL_EDGES:
        if (edge["from_table"] == from_table and edge["to_table"] == to_table) or \
           (edge["from_table"] == to_table and edge["to_table"] == from_table):
            return edge
    return None
