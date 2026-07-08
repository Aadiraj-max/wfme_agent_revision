"""
BSL Dictionary for SAP HANA Workforce Management AI Query Agent.
Rich Business Semantic Layer designed for advanced LLM reasoning, providing deep context,
source prioritization, and semantic boundaries to prevent hallucination.
"""

BSL_MAPPING = {
    'tables': {
        'user_details': {
            'physical_name': 'WFMSCH_1.USER_DETAILS',
            'domain': 'HR',
            'description': 'Core employee profile table: names, demographics, role; job title column is JOB_TITLE (HANA), not JOBTITLE.',
            'business_definition': 'The absolute source of truth for global employee identity and static demographic data. Contains one unique baseline record per employee per company.',
            'preferred_interpretation': 'Use for answering identity questions ("who is this employee"), birthdates, gender, or their current static EMPSTATUS. Do NOT use for historical job titles or past locations.',
            'common_confusions': 'The JOB_TITLE and LOCATIONID here might only reflect the employee\'s *current* or *hiring* state. For time-bound (historical/future) queries, use views_user_detail instead.',
            'reasoning_hints': 'If the user asks "how many employees are active", filter EMPSTATUS = \'A\' on this table. This is the canonical table for base headcount.',
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
                'EMPSTATUS': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Employee status. A=Active, I=Inactive, T=Terminated, L=On Leave'},
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
            'business_definition': 'A time-aware (effective-dated) view of an employee\'s organizational placement. Tracks their role, location, and job title accurately over time.',
            'preferred_interpretation': 'Use this when a query involves "currently", "last year", or "as of [date]". You MUST filter by EFFECTIVESTARTDATE and EFFECTIVEENDDATE to get the accurate snapshot for a given time.',
            'reasoning_hints': 'For "current workforce" queries involving location or job title, join to this view and filter where CURRENT SYSTEM DATE is between EFFECTIVESTARTDATE and EFFECTIVEENDDATE.',
            'primary_keys': [],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'FIRSTNAME': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Employee first name'},
                'LASTNAME': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Employee last name'},
                'GENDER': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Gender of employee M or F'},
                'DOB': {'type': 'DATE', 'nullable': True, 'description': 'Date of Birth'},
                'ROLE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Internal system role E for Employee M for Manager'},
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'ID of the physical store or office'},
                'JOBCODE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Code representing the employee job function'},
                'JOBTITLE': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Job title description'},
                'EFFECTIVESTARTDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record becomes valid'},
                'EFFECTIVEENDDATE': {'type': 'DATE', 'nullable': False, 'description': 'Date when this record expires'},
                'CONTRACTENDDATE': {'type': 'DATE', 'nullable': True, 'description': 'Date when the employee contract ends'},
                'CONTRACTSTARTDATE': {'type': 'DATE', 'nullable': True, 'description': 'Date when the employee contract starts'}
            },
            'warnings': ['views::USER_DETAIL should be used for time-bound role and location queries with EFFECTIVE date filters.']
        },
        'views_v_master_org': {
            'physical_name': 'WFMSCH_1.views::V_MASTER_ORG',
            'domain': 'HR',
            'description': 'Organization hierarchy view: company through location columns for department/store names.',
            'business_definition': 'The master hierarchy linking physical locations to their parent departments, business units, and divisions.',
            'reasoning_hints': 'Join this to LOCATIONID when the user asks to group metrics by "Department", "Division", or "Business Unit".',
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
            'business_definition': 'The central ledger for all employee-submitted requests. Predominantly used for tracking Time Off (Leave) and Overtime requests.',
            'reasoning_hints': 'Filter REQUESTTYPE = \'L\' for leave/vacation requests. Filter STATUS = \'A\' for approved, \'P\' for pending, \'R\' for rejected. WORKDATE is the date the time off occurs.',
            'primary_keys': ['USERID', 'COMPANYID', 'WORKDATE', 'REQUESTTYPE', 'STATUS'],
            'columns': {
                'USERID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Unique employee identifier'},
                'COMPANYID': {'type': 'BIGINT', 'nullable': False, 'description': 'Multi-tenant company identifier'},
                'WORKDATE': {'type': 'DATE', 'nullable': False, 'description': 'The specific date for the request (e.g. the day of leave)'},
                'REQUESTTYPE': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Type of request O for Overtime L for Leave'},
                'STATUS': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Approval status A for Approved P for Pending R for Rejected'},
                'REQUESTID': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Unique request identifier'}
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
            'business_definition': 'The authoritative list of physical operating entities. Also provides the bridge to the Department ID for an employee.',
            'primary_keys': ['COMPANYID', 'BUSINESSUNITID', 'DIVISIONID', 'DEPARTMENTID', 'SUBDEPARTMENTID', 'LOCATIONID'],
            'columns': {
                'LOCATIONID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'ID of the physical store or office'},
                'LOCATIONDESC': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Name/Description of the location'},
                'ADDRESS': {'type': 'NVARCHAR', 'nullable': True, 'description': 'Physical address'},
                'DEPARTMENTID': {'type': 'NVARCHAR', 'nullable': False, 'description': 'Associated department ID'}
            },
            'warnings': []
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
        }
    },
    'metrics': {
        'headcount': {
            'description': 'Total number of unique employees in the system, active or inactive',
            'business_definition': 'The absolute total count of distinct human beings registered in the workforce system, regardless of their current status or full-time/part-time employment.',
            'derivation_notes': 'Count distinct USERID from user_details. Does not require time bounding unless specifically asking for historical headcount.',
            'example_questions': ['What is our total headcount?', 'How many staff do we have on record?', 'Total number of employees'],
            'time_semantics': 'Defaults to current static state. For historical headcount, use views_user_detail with EFFECTIVE date filters.',
            'allowed_group_bys': ['department', 'location', 'job_title', 'employee_role'],
            'table': 'user_details',
            'column': 'USERID',
            'aggregation': 'count'
        },
        'active_employees': {
            'description': 'Number of employees currently actively working',
            'business_definition': 'The subset of total headcount that is currently active. These are people currently working and receiving pay.',
            'derivation_notes': 'Count distinct USERID from user_details where EMPSTATUS = "A".',
            'example_questions': ['How many active employees do we have right now?', 'Show me the current active workforce', 'Number of working staff'],
            'time_semantics': 'Represents the real-time "Now" state in the HR system.',
            'table': 'user_details',
            'column': 'USERID',
            'aggregation': 'count'
        },
        'total_vacation_balance': {
            'description': 'Current total available leave balance across all employees',
            'business_definition': 'The aggregate amount of unused paid time off remaining for the workforce in the current year.',
            'table': 'vacation_balance',
            'column': 'BALANCE',
            'aggregation': 'sum'
        },
        'leave_requests_count': {
            'description': 'Total number of leave requests submitted',
            'business_definition': 'The volume of time-off applications filed by employees, regardless of approval status.',
            'derivation_notes': 'Count of REQUESTID in emp_requests where REQUESTTYPE = "L".',
            'example_questions': ['How many leave requests were submitted last month?', 'Total vacation requests'],
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
        'roster_items_count': {
            'description': 'Total number of specific shift definitions in all rosters',
            'table': 'roster_item',
            'column': 'ROSTER_ITEM_ID',
            'aggregation': 'count'
        },
        'total_hours': {
            'description': 'Sum of work hours across shifts or roster items.',
            'business_definition': 'The aggregate duration of scheduled or worked time, typically calculated from roster items.',
            'table': 'roster_item',
            'column': 'TOTAL_HOURS',
            'aggregation': 'sum'
        },
        'average_fte': {
            'description': 'Average Full-Time Equivalent (FTE) across positions',
            'business_definition': 'The average Full-Time Equivalent requirement for roles and positions in the organization.',
            'table': 'position',
            'column': 'FTE',
            'aggregation': 'avg'
        },
        'contracts_count': {
            'description': 'Total count of employee contracts',
            'business_definition': 'The total count of distinct user contracts in views_user_detail.',
            'table': 'views_user_detail',
            'column': 'USERID',
            'aggregation': 'count'
        }
    },
    'dimensions': {
        'gender': {
            'description': 'Employee gender (M/F)',
            'table': 'user_details',
            'column': 'GENDER'
        },
        'planning_status': {
            'description': 'The status of a roster or planning item (e.g., Published, Draft).',
            'table': 'roster_item',
            'column': 'PLANNING_STATUS'
        },
        'department': {
            'description': 'Organizational department identifier',
            'business_definition': 'The high-level functional or operational group an employee belongs to (e.g., Sales, HR, IT).',
            'derivation_notes': 'Typically joined via LOCATIONID on the locations or views_v_master_org table.',
            'example_questions': ['Headcount by department', 'Show me active employees per department'],
            'table': 'locations',
            'column': 'DEPARTMENTID'
        },
        'location': {
            'description': 'Physical store or office identifier',
            'business_definition': 'The specific geographic site, retail store, or corporate office where an employee is stationed.',
            'example_questions': ['Staff count by location', 'Which location has the most overtime?'],
            'table': 'locations',
            'column': 'LOCATIONID'
        },
        'job_title': {
            'description': 'Official employee job title',
            'business_definition': 'The descriptive name of the employee\'s professional role (e.g., "Senior Developer", "Store Manager").',
            'common_confusions': 'Exists statically on user_details (JOB_TITLE), but is time-bound accurately on views_user_detail (JOBTITLE).',
            'example_questions': ['Headcount by job title', 'List all Store Managers'],
            'table': 'user_details',
            'column': 'JOB_TITLE'
        },
        'employee_role': {
            'description': 'Internal system role (Employee or Manager)',
            'business_definition': 'The broad software access and hierarchy tier assigned to the worker.',
            'table': 'user_details',
            'column': 'ROLE'
        },
        'contract_end_date': {
            'description': 'Date when the employee contract ends',
            'business_definition': 'The date marking the end of the employee contract.',
            'table': 'views_user_detail',
            'column': 'CONTRACTENDDATE'
        },
        'contract_start_date': {
            'description': 'Date when the employee contract starts',
            'business_definition': 'The date marking the start of the employee contract.',
            'table': 'views_user_detail',
            'column': 'CONTRACTSTARTDATE'
        }
    },
    'synonyms': {
        'staff count': 'headcount',
        'workers': 'headcount',
        'employee count': 'headcount',
        'number of employees': 'headcount',
        'total employees': 'headcount',
        'how many employees': 'headcount',
        'total staff': 'headcount',
        'workforce size': 'headcount',
        'how many staff': 'headcount',
        'number of staff': 'headcount',
        'total head count': 'headcount',
        'employee base': 'headcount',
        'total workforce': 'headcount',
        'staff size': 'headcount',
        'total employed': 'headcount',
        'people in the company': 'headcount',
        
        'status': 'planning_status',
        'roster status': 'planning_status',
        
        'active staff': 'active_employees',
        'currently active': 'active_employees',
        'active workforce': 'active_employees',
        'working employees': 'active_employees',
        'employees on active status': 'active_employees',
        'active headcount': 'active_employees',
        'present employees': 'active_employees',
        'non-terminated staff': 'active_employees',
        'current workforce': 'active_employees',
        'current employees': 'active_employees',
        
        'leave balance': 'total_vacation_balance',
        'holiday balance': 'total_vacation_balance',
        'vacation balance': 'total_vacation_balance',
        'remaining leave': 'total_vacation_balance',
        'available leave': 'total_vacation_balance',
        'time off balance': 'total_vacation_balance',
        'accrued leave': 'total_vacation_balance',
        'holiday entitlement': 'total_vacation_balance',
        
        'position': 'job_title',
        'job role': 'job_title',
        'designation': 'job_title',
        'title': 'job_title',
        
        'leave requests': 'leave_requests_count',
        'time off requests': 'leave_requests_count',
        'leave applications': 'leave_requests_count',
        'absence requests': 'leave_requests_count',
        'vacation applications': 'leave_requests_count',
        'sick leave': 'leave_requests_count',
        'pto': 'leave_requests_count',
        'paid time off': 'leave_requests_count',
        'holiday': 'leave_requests_count',
        
        'pending approvals': 'pending_requests_count',
        'awaiting approval': 'pending_requests_count',
        'unapproved requests': 'pending_requests_count',
        'queued requests': 'pending_requests_count',
        'requests waiting': 'pending_requests_count',
        
        'approved leave': 'approved_requests_count',
        'confirmed requests': 'approved_requests_count',
        'accepted leave': 'approved_requests_count',
        'sanctioned leave': 'approved_requests_count',
        'granted time off': 'approved_requests_count',
        
        'roster shifts': 'roster_items_count',
        'roster count': 'roster_items_count',
        'shift definitions': 'roster_items_count',
        'scheduled shifts': 'roster_items_count',
        'planned shift count': 'roster_items_count',
        
        'average fte': 'average_fte',
        'mean fte': 'average_fte',
        'avg fte': 'average_fte',
        'fte': 'average_fte',
        
        'store location': 'location',
        'store': 'location',
        'branch': 'location',
        'office': 'location',
        'site': 'location',
        'workplace': 'location',
        
        'employee contracts': 'contracts_count',
        'contracts': 'contracts_count',
        'number of contracts': 'contracts_count',
        
        'contract end date': 'contract_end_date',
        'contract ending': 'contract_end_date',
        'contracts ending': 'contract_end_date',
        
        'department name': 'department',
        'dept': 'department',
        'business department': 'department',
        'org unit': 'department',
        
        'user role': 'employee_role',
        'access level': 'employee_role',
        'system role': 'employee_role'
    },
    'filter_value_mappings': {
        'EMPSTATUS': {
            'active': 'A',
            'inactive': 'I',
            'terminated': 'T',
            'on leave': 'L',
            'suspended': 'S',
            'fired': 'T',
            'resigned': 'T',
            'quit': 'T'
        },
        'ROLE': {
            'employee': 'E',
            'manager': 'M',
            'admin': 'A'
        },
        'REQUESTTYPE': {
            'leave': 'L',
            'overtime': 'O',
            'shift change': 'S',
            'time off': 'L',
            'vacation': 'L',
            'pto': 'L'
        },
        'STATUS': {
            'approved': 'A',
            'active': 'A',
            'pending': 'P',
            'awaiting approval': 'P',
            'rejected': 'R',
            'declined': 'R'
        },
        'GENDER': {
            'male': 'M',
            'female': 'F',
            'man': 'M',
            'woman': 'F'
        }
    },
    'domain_keywords': {
        'HR': [
            'employee', 'staff', 'name', 'role', 'gender', 'dob',
            'date of birth', 'job title', 'position', 'headcount', 'active',
            'terminated', 'hr', 'human resources', 'profile', 'fired', 'resigned'
        ],
        'OPS': [
            'shift', 'roster', 'schedule', 'planning', 'location',
            'planned', 'actual', 'site', 'branch', 'operations',
            'assigned'
        ]
    }
}
