"""
BSL Dictionary for SAP HANA Workforce Management AI Query Agent.
Generated with production-grade mappings, metrics, dimensions, and business synonyms.
"""

BSL_MAPPING = {
    'tables': {
        'user_details': {
            'physical_name': 'WFMSCH_1.USER_DETAILS',
            'domain': 'HR',
            'description': 'Core employee profile table: names, demographics, role; job title column is JOB_TITLE (HANA), not JOBTITLE.',
            'primary_keys': ['USERID', 'COMPANYID'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier — used in every table for data isolation, not a join key'},
                'FIRSTNAME': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Employee first name'},
                'LASTNAME': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Employee last name'},
                'GENDER': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Gender of employee M or F'},
                'DOB': {'type': 'DATE', 'nullable': True, 'description': 'Date of Birth'},
                'ROLE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Internal system role E for Employee M for Manager'},
                'JOB_TITLE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Job title on USER_DETAILS — use this exact column name not JOBTITLE'},
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': True, 'description': 'ID of the physical store or office'},
                'EMPSTATUS': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Employee status'},
                'CREATEDBY': {'type': 'NVARCHAR', 'nullable': True, 'description': 'USERID of record creator'},
                'CREATEDON': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Timestamp of record creation'},
                'MODIFIEDBY': {'type': 'NVARCHAR', 'nullable': True, 'description': 'USERID of last modifier'},
                'MODIFYEDON': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Timestamp of last update'}
            },
            'warnings': []
        },
        'views_user_detail': {
            'physical_name': 'WFMSCH_1.views::USER_DETAIL',
            'domain': 'HR',
            'description': 'Canonical HR view: ROLE, LOCATIONID, manager routing — use for store managers with EFFECTIVE dates.',
            'primary_keys': [],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier — used in every table for data isolation, not a join key'},
                'FIRSTNAME': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Employee first name'},
                'LASTNAME': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Employee last name'},
                'GENDER': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Gender of employee M or F'},
                'DOB': {'type': 'DATE', 'nullable': True, 'description': 'Date of Birth'},
                'ROLE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Internal system role E for Employee M for Manager'},
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'ID of the physical store or office'},
                'JOBCODE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Code representing the employee job function'},
                'JOBTITLE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Job title description'},
                'EFFECTIVESTARTDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record becomes valid'},
                'EFFECTIVEENDDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record expires'}
            },
            'warnings': ['views::USER_DETAIL should be used for time-bound role and location queries with EFFECTIVE date filters.']
        },
        'views_v_master_org': {
            'physical_name': 'WFMSCH_1.views::V_MASTER_ORG',
            'domain': 'HR',
            'description': 'Organization hierarchy view: company through location columns for department/store names.',
            'primary_keys': [],
            'columns': {
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'COMPANYDESC': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Company name'},
                'DIVISIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Division identifier'},
                'DIVISIONDESC': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Division name'},
                'BUSINESSUNITID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Business unit identifier'},
                'BUSINESSUNITDESC': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Business unit name'},
                'DEPARTMENTID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Department identifier'},
                'DEPARTMENTDESC': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Department name'},
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Location identifier'},
                'LOCATIONDESC': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Location name'}
            },
            'warnings': []
        },
        'emp_hr': {
            'physical_name': 'WFMSCH_1.EMP_HR',
            'domain': 'HR',
            'description': 'Mapping between employees and their assigned HR representatives.',
            'primary_keys': ['USERID', 'COMPNAYID', 'HR_EMPID', 'EFFECTIVESTARTDATE', 'EFFECTIVEENDDATE'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPNAYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Typo in DB: should be COMPANYID. Multi-tenant company identifier'},
                'HR_EMPID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'The USERID of the assigned HR representative'},
                'EFFECTIVESTARTDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record becomes valid'},
                'EFFECTIVEENDDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record expires'}
            },
            'warnings': ['EMP_HR has a typo in the DB: the column is COMPNAYID not COMPANYID. Never filter EMP_HR by COMPANYID.']
        },
        'emp_manager': {
            'physical_name': 'WFMSCH_1.EMP_MANAGER',
            'domain': 'HR',
            'description': 'Organizational hierarchy mapping employees to their direct managers.',
            'primary_keys': ['USERID', 'COMPANYID', 'MANAGER_EMPID', 'EFFECTIVESTARTDATE', 'EFFECTIVEENDDATE'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'MANAGER_EMPID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'The USERID of the employee direct manager'},
                'EFFECTIVESTARTDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record becomes valid'},
                'EFFECTIVEENDDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record expires'}
            },
            'warnings': []
        },
        'emp_contract_details': {
            'physical_name': 'WFMSCH_1.EMP_CONTRACT_DETAILS',
            'domain': 'HR',
            'description': 'Employment contract specifics including job codes, location, and contract status.',
            'primary_keys': ['USERID', 'COMPANYID', 'EFFECTIVESTARTDATE', 'EFFECTIVEENDDATE', 'CONTRACTNUMBER', 'LOCATIONID'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'CONTRACTNUMBER': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique contract identifier'},
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'ID of the physical store or office'},
                'JOBCODE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Code representing the employee job function'},
                'CONTRACTTYPE': {'type': 'BIGINT', 'nullable': True, 'description': 'Type of employment contract'},
                'EFFECTIVESTARTDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record becomes valid'},
                'EFFECTIVEENDDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record expires'}
            },
            'warnings': []
        },
        'vacation_history': {
            'physical_name': 'WFMSCH_1.VACATION_HISTORY',
            'domain': 'HR',
            'description': 'Detailed log of vacation days gained, taken, and current balances.',
            'primary_keys': ['COMPANYID', 'USERID', 'YEAR', 'CONTRACTNUMBER'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'YEAR': {'type': 'NVARCHAR', 'nullable': False, 'description': "Calendar year as NVARCHAR(4) — always compare as string YEAR = '2026'"},
                'CONTRACTNUMBER': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Associated contract number'},
                'V_TAKEN': {'type': 'DECIMAL', 'nullable': True, 'description': 'Vacation days taken'},
                'V_GAIN': {'type': 'DECIMAL', 'nullable': True, 'description': 'Vacation days gained'},
                'BALANCE_TODAY': {'type': 'DECIMAL', 'nullable': True, 'description': 'Current vacation balance as of today'}
            },
            'warnings': ["YEAR column on VACATION_HISTORY is NVARCHAR(4). Always compare as string."]
        },
        'vacation_balance': {
            'physical_name': 'WFMSCH_1.VACATION_BALANCE',
            'domain': 'HR',
            'description': 'Simplified view of current year vacation balance for employees.',
            'primary_keys': ['COMPANYID', 'USERID', 'YEAR', 'CONTRACTNUMBER'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'YEAR': {'type': 'NVARCHAR', 'nullable': False, 'description': "Calendar year as NVARCHAR(4) — always compare as string YEAR = '2026'"},
                'BALANCE': {'type': 'DECIMAL', 'nullable': True, 'description': 'Current available leave balance'}
            },
            'warnings': ["YEAR column on VACATION_BALANCE is NVARCHAR(4). Always compare as string."]
        },
        'emp_requests': {
            'physical_name': 'WFMSCH_1.EMP_REQUESTS',
            'domain': 'HR',
            'description': 'Employee submissions for leave, overtime, or shift changes and their approval status.',
            'primary_keys': ['USERID', 'COMPANYID', 'WORKDATE', 'REQUESTTYPE', 'STATUS'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'WORKDATE': {'type': 'DATE', 'nullable': False, 'description': 'The specific date for the request'},
                'REQUESTTYPE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Type of request O for Overtime L for Leave'},
                'STATUS': {'type': 'NVARCHAR', 'nullable': False, 'description': 'General status A for Active P for Pending R for Rejected'},
                'REQUESTID': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Unique request identifier'}
            },
            'warnings': []
        },
        'skills_certificate': {
            'physical_name': 'WFMSCH_1.SKILLS_CERTIFICATE',
            'domain': 'HR',
            'description': 'Master catalog of skills, certifications, and their descriptions.',
            'primary_keys': ['COMPANYID', 'JOBCODE', 'TYPE', 'CODE'],
            'columns': {
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'TYPE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Skill type category'},
                'CODE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Skill or certificate code'},
                'CODEDESC': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Description of the skill/certificate'}
            },
            'warnings': []
        },
        'emp_skill_certificate': {
            'physical_name': 'WFMSCH_1.EMP_SKILL_CERTIFICATE',
            'domain': 'HR',
            'description': 'Records of specific skills and certifications earned by employees.',
            'primary_keys': ['COMPANYID', 'USERID', 'TYPE', 'CODE', 'EFFECTIVESTARTDATE'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'TYPE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Skill type category'},
                'CODE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Skill or certificate code'},
                'STATUS': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Status of the certification'}
            },
            'warnings': []
        },
        'role_defination': {
            'physical_name': 'WFMSCH_1.ROLE_DEFINATION',
            'domain': 'HR',
            'description': 'Detailed permission sets and access levels for various system roles.',
            'primary_keys': ['COMPANYID', 'ROLE_ID'],
            'columns': {
                'ROLE_ID': {'type': 'BIGINT', 'nullable': False, 'description': 'Internal role identifier'},
                'ROLE_NAME': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Name of the system role'}
            },
            'warnings': []
        },
        'position': {
            'physical_name': 'WFMSCH_1.POSITION',
            'domain': 'HR',
            'description': 'Organizational positions including titles, FTE requirements, and department alignment.',
            'primary_keys': ['COMPANYID', 'POSITIONID'],
            'columns': {
                'POSITIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique position identifier'},
                'POSITIONTITLE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Official title of the position'},
                'FTE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Full-time equivalent requirement'},
                'DEPARTMENTID': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Associated department ID'}
            },
            'warnings': []
        },
        'emp_planning': {
            'physical_name': 'WFMSCH_1.EMP_PLANNING',
            'domain': 'OPS',
            'description': 'The master schedule showing who is planned to work where and when.',
            'primary_keys': ['USERID', 'COMPANYID', 'LOCATIONID', 'JOBCODE', 'WORKDATE'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'ID of the physical store or office'},
                'JOBCODE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Job function code'},
                'WORKDATE': {'type': 'DATE', 'nullable': False, 'description': 'The planned date for the shift'},
                'SHIFT_CODE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Code for a specific work time window'}
            },
            'warnings': []
        },
        'emp_workslot': {
            'physical_name': 'WFMSCH_1.EMP_WORKSLOT',
            'domain': 'OPS',
            'description': 'Actual attendance logs with clock-in/out and geolocation data.',
            'primary_keys': ['USERID', 'COMPANYID', 'LOCATIONID', 'JOBCODE', 'WORKDATE', 'CHECKINTIME', 'CHECKOUTTIME'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'ID of the physical store or office'},
                'WORKDATE': {'type': 'DATE', 'nullable': False, 'description': 'The specific date for the log'},
                'CHECKINTIME': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Timestamp when employee clocked in'},
                'CHECKOUTTIME': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Timestamp when employee clocked out'},
                'OVERTIME': {'type': 'BOOLEAN', 'nullable': True, 'description': 'Boolean indicating if the entry is overtime'}
            },
            'warnings': []
        },
        'roster_header': {
            'physical_name': 'WFMSCH_1.ROSTER_HEADER',
            'domain': 'OPS',
            'description': 'Templates for recurring shift patterns.',
            'primary_keys': ['ROSTER_HEADER_ID'],
            'columns': {
                'ROSTER_HEADER_ID': {'type': 'BIGINT', 'nullable': False, 'description': 'Unique identifier for a roster template'},
                'ROSTER_NAME': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Name of the roster template'}
            },
            'warnings': []
        },
        'roster_item': {
            'physical_name': 'WFMSCH_1.ROSTER_ITEM',
            'domain': 'OPS',
            'description': 'Specific shift definitions within a roster template.',
            'primary_keys': ['ROSTER_HEADER_ID', 'ROSTER_ITEM_ID', 'DAY_NUMBER'],
            'columns': {
                'ROSTER_HEADER_ID': {'type': 'BIGINT', 'nullable': False, 'description': 'Unique identifier for a roster template'},
                'ROSTER_ITEM_ID': {'type': 'BIGINT', 'nullable': False, 'description': 'Unique identifier for a roster shift definition'},
                'DAY_NUMBER': {'type': 'INTEGER', 'nullable': False, 'description': 'The day index within the roster pattern'},
                'JOB_CODE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Job code with underscore in this table'},
                'SHIFT_CODE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Shift time window code'}
            },
            'warnings': ['ROSTER_ITEM uses JOB_CODE with underscore, not JOBCODE. Never join on job code between ROSTER_ITEM and other tables without aliasing.']
        },
        'locations': {
            'physical_name': 'WFMSCH_1.LOCATIONS',
            'domain': 'OPS',
            'description': 'Physical sites/stores with addresses and coordinates.',
            'primary_keys': ['COMPANYID', 'BUSINESSUNITID', 'DIVISIONID', 'DEPARTMENTID', 'SUBDEPARTMENTID', 'LOCATIONID'],
            'columns': {
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'ID of the physical store or office'},
                'LOCATIONDESC': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Name/Description of the location'},
                'ADDRESS': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Physical address'},
                'DEPARTMENTID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Associated department ID'}
            },
            'warnings': []
        },
        'workday_types': {
            'physical_name': 'WFMSCH_1.WORKDAY_TYPES',
            'domain': 'OPS',
            'description': 'Categorization of days such as Work Day, Flex Day, Holiday.',
            'primary_keys': ['COMPANYID', 'COUNTRYCODE', 'WORKDAYCODE'],
            'columns': {
                'WORKDAYCODE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Code for the workday type'},
                'LOOKUPNAME': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Business name of the day type (e.g. Work Day)'}
            },
            'warnings': []
        },
        'shiftcode_slotmapping': {
            'physical_name': 'WFMSCH_1.SHIFTCODE_SLOTMAPPING',
            'domain': 'OPS',
            'description': 'Shift code slot mapping with ACTUAL_SLOTS, BREAK_SLOTS, TOTAL_HOURS.',
            'primary_keys': ['COMPANYID', 'COUNTRYCODE', 'SHIFT_CODE'],
            'columns': {
                'SHIFT_CODE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Code for the specific shift window'},
                'ACTUAL_SLOTS': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Working time slots'},
                'BREAK_SLOTS': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Break time slots'},
                'TOTAL_HOURS': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Total duration of the shift'}
            },
            'warnings': ['SHIFTCODE_SLOTMAPPING has no START_TIME or END_TIME columns. Use ACTUAL_SLOTS instead.']
        },
        'views_v_planned_emp': {
            'physical_name': 'WFMSCH_1.views::V_PLANNED_EMP',
            'domain': 'OPS',
            'description': 'View showing planned vs actual employee staffing.',
            'primary_keys': [],
            'columns': {
                'EFFECTIVE_DATE': {'type': 'DATE', 'nullable': False, 'description': 'Planning date'},
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Location identifier'},
                'JOB_CODE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Job function code'}
            },
            'warnings': []
        },
        'views_v_roster_planned_emp': {
            'physical_name': 'WFMSCH_1.views::V_ROSTER_PLANNED_EMP',
            'domain': 'OPS',
            'description': 'View of employees assigned to specific roster templates.',
            'primary_keys': [],
            'columns': {
                'EFFECTIVE_DATE': {'type': 'DATE', 'nullable': False, 'description': 'Planning date'},
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Location identifier'},
                'ROSTER_HEADER_ID': {'type': 'BIGINT', 'nullable': True, 'description': 'Associated roster template'}
            },
            'warnings': []
        },
        'stores': {
            'physical_name': 'WFMSCH_1.STORES',
            'domain': 'OPS',
            'description': 'Detailed retail store metadata including manager and contact info.',
            'primary_keys': ['ID'],
            'columns': {
                'ID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique store identifier'},
                'NAME': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Store name'},
                'MANAGER_ID': {'type': 'NVARCHAR', 'nullable': True, 'description': 'USERID of the store manager'}
            },
            'warnings': []
        },
        'teams': {
            'physical_name': 'WFMSCH_1.TEAMS',
            'domain': 'OPS',
            'description': 'Functional groupings of employees within locations.',
            'primary_keys': ['ID'],
            'columns': {
                'ID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique team identifier'},
                'NAME': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Team name'},
                'MANAGER_ID': {'type': 'BIGINT', 'nullable': False, 'description': 'USERID of the team manager'}
            },
            'warnings': []
        }
    },
    'metrics': {
        'headcount': {
            'description': 'Total number of unique employees in the system',
            'table': 'user_details',
            'column': 'USERID',
            'aggregation': 'count'
        },
        'active_employees': {
            'description': 'Number of employees currently active (EMPSTATUS = A)',
            'table': 'user_details',
            'column': 'USERID',
            'aggregation': 'count'
        },
        'overtime_entries': {
            'description': 'Count of work slots flagged as overtime',
            'table': 'emp_workslot',
            'column': 'OVERTIME',
            'aggregation': 'count'
        },
        'planned_hours': {
            'description': 'Count of planned shift entries. Note: TOTAL_HOURS is NVARCHAR and cannot be summed directly.',
            'table': 'shiftcode_slotmapping',
            'column': 'TOTAL_HOURS',
            'aggregation': 'count'
        },
        'average_shift_hours': {
            'description': 'Count of shift definitions. Note: TOTAL_HOURS is NVARCHAR, direct averaging requires CAST.',
            'table': 'shiftcode_slotmapping',
            'column': 'TOTAL_HOURS',
            'aggregation': 'count'
        },
        'total_vacation_days_taken': {
            'description': 'Total vacation days consumed by employees',
            'table': 'vacation_history',
            'column': 'V_TAKEN',
            'aggregation': 'sum'
        },
        'total_vacation_balance': {
            'description': 'Current total available leave balance across all employees',
            'table': 'vacation_balance',
            'column': 'BALANCE',
            'aggregation': 'sum'
        },
        'leave_requests_count': {
            'description': 'Total number of leave requests submitted',
            'table': 'emp_requests',
            'column': 'REQUESTID',
            'aggregation': 'count'
        },
        'approved_requests_count': {
            'description': 'Number of employee requests with status Approved (A)',
            'table': 'emp_requests',
            'column': 'REQUESTID',
            'aggregation': 'count'
        },
        'pending_requests_count': {
            'description': 'Number of employee requests awaiting approval (P)',
            'table': 'emp_requests',
            'column': 'REQUESTID',
            'aggregation': 'count'
        },
        'employee_skills_count': {
            'description': 'Total count of skills and certifications registered to employees',
            'table': 'emp_skill_certificate',
            'column': 'CODE',
            'aggregation': 'count'
        },
        'roster_items_count': {
            'description': 'Total number of specific shift definitions in all rosters',
            'table': 'roster_item',
            'column': 'ROSTER_ITEM_ID',
            'aggregation': 'count'
        }
    },
    'dimensions': {
        'department': {
            'description': 'Organizational department identifier',
            'table': 'locations',
            'column': 'DEPARTMENTID'
        },
        'location': {
            'description': 'Physical store or office identifier',
            'table': 'locations',
            'column': 'LOCATIONID'
        },
        'job_title': {
            'description': 'Official employee job title',
            'table': 'user_details',
            'column': 'JOB_TITLE'
        },
        'employee_role': {
            'description': 'Internal system role (Employee or Manager)',
            'table': 'user_details',
            'column': 'ROLE'
        },
        'manager': {
            'description': 'Employee direct manager identifier',
            'table': 'emp_manager',
            'column': 'MANAGER_EMPID'
        },
        'shift_code': {
            'description': 'Code representing a specific shift time window',
            'table': 'emp_planning',
            'column': 'SHIFT_CODE'
        },
        'workday_type': {
            'description': 'Categorization of the day (Work, Holiday, etc.)',
            'table': 'workday_types',
            'column': 'WORKDAYCODE'
        },
        'contract_type': {
            'description': 'Type of employment contract',
            'table': 'emp_contract_details',
            'column': 'CONTRACTTYPE'
        },
        'skill_type': {
            'description': 'Category of skill or certificate',
            'table': 'emp_skill_certificate',
            'column': 'TYPE'
        },
        'team': {
            'description': 'Functional team name',
            'table': 'teams',
            'column': 'NAME'
        },
        'store': {
            'description': 'Retail store name',
            'table': 'stores',
            'column': 'NAME'
        },
        'year': {
            'description': 'Calendar year filter — apply to whichever table is being queried. Always compare as string.',
            'table': 'vacation_history',
            'column': 'YEAR'
        },
        'workdate': {
            'description': 'Specific date for attendance or planning',
            'table': 'emp_planning',
            'column': 'WORKDATE'
        }
    },
    'synonyms': {
        'staff count': 'headcount',
        'workers': 'headcount',
        'employee count': 'headcount',
        'clock in': 'checkintime',
        'clock out': 'checkouttime',
        'leave balance': 'total_vacation_balance',
        'holiday balance': 'total_vacation_balance',
        'overtime hours': 'overtime_entries',
        'skills count': 'employee_skills_count',
        'position': 'job_title',
        'vacation days': 'total_vacation_days_taken',
        'leave requests': 'leave_requests_count',
        'time off': 'total_vacation_balance',
        'roster shifts': 'roster_items_count',
        'attendance': 'headcount',
        'store manager': 'manager'
    }
}
