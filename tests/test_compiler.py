import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.schema import QueryPlan, FilterCondition, TimeRange
from src.engine.compiler import HanaQueryCompiler
from src.engine.bsl_dictionary import BSL_MAPPING

def test_single_metric_no_filter():
    print("Running: test_single_metric_no_filter")
    plan = QueryPlan(
        metrics=["headcount"],
        dimensions=[],
        filters=[],
        time_range=None,
        limit=100
    )
    sql = HanaQueryCompiler(plan, BSL_MAPPING).compile()
    print(f"SQL Output:\n{sql}\n")
    
    assert 'WFMSCH_1.USER_DETAILS' in sql
    assert 'count' in sql.lower()
    assert 'USERID' in sql

def test_metric_with_dimension():
    print("Running: test_metric_with_dimension")
    plan = QueryPlan(
        metrics=["headcount"],
        dimensions=["employee_role"],
        filters=[],
        time_range=None,
        limit=50
    )
    sql = HanaQueryCompiler(plan, BSL_MAPPING).compile()
    print(f"SQL Output:\n{sql}\n")
    
    assert 'GROUP BY' in sql
    assert 'ROLE' in sql

def test_metric_with_filter():
    print("Running: test_metric_with_filter")
    plan = QueryPlan(
        metrics=["total_vacation_days_taken"],
        dimensions=["year"],
        filters=[FilterCondition(field='YEAR', operator='eq', value='2026')],
        time_range=None,
        limit=10
    )
    sql = HanaQueryCompiler(plan, BSL_MAPPING).compile()
    print(f"SQL Output:\n{sql}\n")
    
    assert 'WHERE' in sql
    assert '2026' in sql
    assert 'VACATION_HISTORY' in sql

if __name__ == '__main__':
    test_single_metric_no_filter()
    test_metric_with_dimension()
    test_metric_with_filter()
    print('All tests passed.')
