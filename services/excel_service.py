from io import BytesIO
import pandas as pd
from utils.validators import validate


def read_payroll(source, label):
    try:
        df = pd.read_excel(source, engine='openpyxl', dtype={'cedula': str})
    except Exception as exc:
        raise ValueError(f'{label}: no se pudo leer el Excel. Verifica que sea un archivo .xlsx válido.') from exc
    return validate(df, label)


def report_frame(alerts, statuses):
    return pd.DataFrame([{
        'Riesgo': a.risk, 'Tipo de alerta': a.kind, 'Cédula': a.cedula,
        'Empleado': a.employee, 'Valor anterior': a.previous, 'Valor actual': a.current,
        'Diferencia': a.difference, 'Descripción': a.explanation,
        'Estado': statuses.get(a.id, 'Pendiente'),
    } for a in alerts], columns=['Riesgo', 'Tipo de alerta', 'Cédula', 'Empleado',
                               'Valor anterior', 'Valor actual', 'Diferencia', 'Descripción', 'Estado'])


def export_report(alerts, statuses):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        frame = report_frame(alerts, statuses)
        # User-supplied Excel text must remain text, never a formula.
        frame.to_excel(writer, index=False, sheet_name='Revisión')
        sheet = writer.sheets['Revisión']
        sheet.freeze_panes = 'A2'
        sheet.auto_filter.ref = sheet.dimensions
        for row in sheet:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.data_type = 's'
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = min(65, max(16, max(len(str(c.value or '')) for c in column) + 2))
    return output.getvalue()
