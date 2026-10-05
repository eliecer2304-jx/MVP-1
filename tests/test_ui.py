from pathlib import Path
from streamlit.testing.v1 import AppTest
from services.excel_service import read_payroll
from services.anomaly_service import analyze

ROOT = Path(__file__).resolve().parents[1]


def test_initial_screen_and_missing_uploads():
    app = AppTest.from_file(str(ROOT / 'app.py')).run()
    assert not app.exception
    assert app.title[0].value == 'Control Inteligente de Planillas'
    app.button[0].click().run()
    assert not app.exception
    assert 'Carga la planilla' in app.error[0].value


def test_results_filters_review_and_detail():
    # AppTest does not support file upload; inject the validated analysis result.
    app = AppTest.from_file(str(ROOT / 'app.py')).run()
    previous = read_payroll(ROOT / 'data/planilla_anterior.xlsx', 'Anterior')
    current = read_payroll(ROOT / 'data/planilla_actual.xlsx', 'Actual')
    alerts = analyze(previous, current)
    app.session_state['result'] = (previous, current, alerts)
    app.session_state['statuses'] = {}
    app.run()
    assert not app.exception
    assert [m.value for m in app.metric[:4]] == ['25', '5', '1', '21']
    assert len(app.dataframe[0].value) == 5
    app.checkbox[0].check().run()
    assert len(app.dataframe[0].value) == 4
    app.checkbox[0].uncheck().run()
    assert len(app.dataframe[0].value) == 5
    app.selectbox(key=f'review:{alerts[0].id}').select('Revisada').run()
    assert app.session_state['statuses'][alerts[0].id] == 'Revisada'
    app.multiselect(key='risk_filter').select('INFORMATIVO').run()
    assert len(app.dataframe[0].value) == 1
    assert app.dataframe[0].value.iloc[0]['Tipo de alerta'] == 'Empleado nuevo'
    app.multiselect(key='type_filter').select('Cambio salarial').run()
    assert app.info
    assert not app.exception
