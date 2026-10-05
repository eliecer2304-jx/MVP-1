from io import BytesIO
from pathlib import Path
import pandas as pd
import pytest
from openpyxl import load_workbook
from services.anomaly_service import analyze, summary
from services.excel_service import read_payroll, export_report
from utils.validators import validate


def frame(salary=100, hours=4, cedula='A', name='Ana'):
    return pd.DataFrame([{'cedula': cedula, 'nombre': name, 'salario': salary, 'horas_extra': hours}])


@pytest.mark.parametrize('salary,risk', [(130, None), (70, None), (131, 'ALTO'), (69, 'ALTO'), (200, 'ALTO'), (201, 'CRÍTICO'), (0, 'ALTO')])
def test_salary_boundaries(salary, risk):
    alerts = analyze(frame(), frame(salary))
    assert [a.risk for a in alerts] == ([] if risk is None else [risk])


@pytest.mark.parametrize('hours,expected', [(20, 0), (20.1, 1), (38, 1)])
def test_hours_boundary(hours, expected):
    alerts = analyze(frame(), frame(hours=hours))
    assert len(alerts) == expected
    if expected:
        assert alerts[0].kind == 'Horas extra atípicas'
        assert str(hours) in alerts[0].current


def test_new_and_absent_do_not_compare_salary():
    alerts = analyze(frame(), frame(9000, cedula='B'))
    assert {a.kind for a in alerts} == {'Empleado nuevo', 'Empleado ausente'}
    assert next(a for a in alerts if a.kind == 'Empleado nuevo').risk == 'INFORMATIVO'
    assert 'no implica' in next(a for a in alerts if a.kind == 'Empleado ausente').explanation


def test_duplicate_does_not_create_arbitrary_salary_change():
    current = pd.concat([frame(9000), frame(8000)], ignore_index=True)
    alerts = analyze(frame(), current)
    assert len(alerts) == 1
    assert alerts[0].kind == 'Empleado duplicado'
    assert summary(current, alerts) == (1, 1, 0, 0)


def test_previous_duplicate_skips_salary():
    assert analyze(pd.concat([frame(), frame()], ignore_index=True), frame(9000)) == []


def test_zero_baseline():
    assert analyze(frame(0), frame(0)) == []
    alerts = analyze(frame(0), frame(100))
    assert len(alerts) == 1
    assert alerts[0].risk == 'CRÍTICO'
    assert 'no calculable' in alerts[0].difference


def test_missing_columns():
    with pytest.raises(ValueError, match='salario, horas_extra'):
        validate(pd.DataFrame({'cedula': ['A'], 'nombre': ['Ana']}), 'Actual')


@pytest.mark.parametrize('column,value', [('salario', 'abc'), ('salario', -1), ('salario', float('inf')),
                                         ('horas_extra', None), ('cedula', ''), ('nombre', None)])
def test_invalid_cells(column, value):
    df = frame().astype(object)
    df.loc[0, column] = value
    with pytest.raises(ValueError, match=column):
        validate(df, 'Actual')


def test_empty_and_invalid_file():
    with pytest.raises(ValueError, match='no contiene empleados'):
        validate(frame().iloc[:0], 'Actual')
    with pytest.raises(ValueError, match='no se pudo leer'):
        read_payroll(BytesIO(b'not an Excel'), 'Actual')


def test_demo_and_export():
    folder = Path(__file__).resolve().parents[1] / 'data'
    previous = read_payroll(folder / 'planilla_anterior.xlsx', 'Anterior')
    current = read_payroll(folder / 'planilla_actual.xlsx', 'Actual')
    alerts = analyze(previous, current)
    assert len(alerts) == 5
    assert {a.kind for a in alerts} == {'Cambio salarial', 'Empleado duplicado', 'Empleado nuevo', 'Empleado ausente', 'Horas extra atípicas'}
    assert summary(current, alerts) == (25, 5, 1, 21)
    critical = next(a for a in alerts if a.risk == 'CRÍTICO')
    assert critical.difference == '+900.00%'
    data = export_report(alerts, {critical.id: 'Revisada'})
    report = pd.read_excel(BytesIO(data))
    assert len(report) == 5
    assert report.loc[report.Riesgo == 'CRÍTICO', 'Estado'].iloc[0] == 'Revisada'


def test_export_keeps_user_text_as_text():
    alerts = analyze(frame(), frame(9000, name='=1+1'))
    workbook = load_workbook(BytesIO(export_report(alerts, {})))
    assert workbook.active['D2'].value == '=1+1'
    assert workbook.active['D2'].data_type == 's'
