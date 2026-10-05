from models.anomaly import Anomaly
from services.comparison_service import compare

RISK_ORDER = {'CRÍTICO': 0, 'ALTO': 1, 'MEDIO': 2, 'INFORMATIVO': 3}


def analyze(previous, current):
    groups = compare(previous, current)
    alerts = []

    def add(risk, kind, row, before, after, difference, rule, explanation, suffix=''):
        alerts.append(Anomaly(f'{kind}:{row.cedula}:{suffix}', risk, kind, row.cedula,
                              row.nombre, str(before), str(after), difference, rule, explanation))

    for cedula in sorted(groups['duplicates']):
        rows = current[current.cedula == cedula]
        row = rows.iloc[0]
        add('ALTO', 'Empleado duplicado', row, '—', f'{len(rows)} registros', '—',
            'Cédula repetida en la planilla actual',
            f'La cédula aparece {len(rows)} veces. Nombres: {", ".join(rows.nombre.unique())}. Revisar los registros antes de comparar salarios.')
    for cedula in sorted(groups['new']):
        row = current[current.cedula == cedula].iloc[0]
        add('INFORMATIVO', 'Empleado nuevo', row, 'No aparece', 'Presente', '—',
            'Cédula nueva respecto al período anterior', 'El empleado aparece por primera vez en esta comparación.')
    for cedula in sorted(groups['absent']):
        row = previous[previous.cedula == cedula].iloc[0]
        add('MEDIO', 'Empleado ausente', row, 'Presente', 'No aparece', '—',
            'Cédula ausente en la planilla actual', 'Empleado ausente respecto al período anterior. Esto no implica que fue despedido.')
    for cedula in sorted(groups['common'] - groups['duplicates']):
        old = previous[previous.cedula == cedula]
        if len(old) != 1:
            continue
        row = current[current.cedula == cedula].iloc[0]
        before, after = float(old.iloc[0].salario), float(row.salario)
        if before == 0:
            if after == 0:
                continue
            add('CRÍTICO', 'Cambio salarial', row, f'${before:,.2f}', f'${after:,.2f}',
                'Porcentaje no calculable (base cero)', 'Cambio salarial superior al 30%',
                'El salario pasó de cero a un valor positivo. No es posible calcular el porcentaje; requiere revisión.')
            continue
        delta = (after - before) / before * 100
        if abs(delta) > 30 + 1e-9:
            add('CRÍTICO' if abs(delta) > 100 + 1e-9 else 'ALTO', 'Cambio salarial', row,
                f'${before:,.2f}', f'${after:,.2f}', f'{delta:+.2f}%', 'Cambio salarial superior al 30%',
                f'El salario {"aumentó" if delta > 0 else "disminuyó"} {abs(delta):.2f}% respecto al período anterior.')
    for index, row in current.iterrows():
        if row.horas_extra > 20:
            old = previous[previous.cedula == row.cedula]
            before = f'{old.iloc[0].horas_extra:g} horas' if len(old) == 1 else '—'
            diff = f'{row.horas_extra - old.iloc[0].horas_extra:+g} horas' if len(old) == 1 else '—'
            add('MEDIO', 'Horas extra atípicas', row, before, f'{row.horas_extra:g} horas', diff,
                'Horas extra superiores a 20', f'Se encontraron {row.horas_extra:g} horas extra; el umbral es 20.', str(index))
    return sorted(alerts, key=lambda a: (RISK_ORDER[a.risk], a.cedula, a.kind))


def summary(current, alerts):
    employees = set(current.cedula)
    observed = {a.cedula for a in alerts}
    return (len(employees), len(alerts), sum(a.risk == 'CRÍTICO' for a in alerts), len(employees - observed))
