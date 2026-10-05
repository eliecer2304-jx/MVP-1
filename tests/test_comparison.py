import pandas as pd
from services.comparison_service import compare


def test_new_absent_and_duplicate():
    previous = pd.DataFrame({'cedula': ['A', 'B']})
    current = pd.DataFrame({'cedula': ['B', 'B', 'C']})
    result = compare(previous, current)
    assert result == {'new': {'C'}, 'absent': {'A'}, 'common': {'B'}, 'duplicates': {'B'}}
