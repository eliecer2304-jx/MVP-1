from io import BytesIO
from pathlib import Path
import hashlib
import streamlit as st
from services.excel_service import read_payroll, report_frame, export_report
from services.anomaly_service import analyze, summary, RISK_ORDER

st.set_page_config(page_title='Control Inteligente de Planillas', page_icon='📋', layout='wide')
st.markdown('''<style>
.block-container {max-width:1250px;padding-top:2.5rem;}
h1 {letter-spacing:-1px;} h2 {font-size:1.4rem;}
[data-testid="stMetric"] {background:#14243b;border:1px solid #294159;border-radius:14px;padding:20px;}
[data-testid="stMetricValue"] {color:#52e0c4;}
[data-testid="stFileUploader"] {border:1px solid #294159;border-radius:14px;padding:12px;}
.stButton button[kind="primary"] {font-weight:700;}
</style>''', unsafe_allow_html=True)
st.caption('CONTROL DE PLANILLAS  /  REVISIÓN PREVIA')
st.title('Control Inteligente de Planillas')
st.markdown('### Revisión por excepciones antes de SIPE')
st.caption('Compara dos períodos y concentra la revisión en los registros que requieren atención.')
st.info('El sistema detecta excepciones. La decisión final corresponde al usuario.')
left, right = st.columns(2)
with left:
    previous_file = st.file_uploader('Planilla anterior', type=['xlsx'], key='previous_file')
with right:
    current_file = st.file_uploader('Planilla actual', type=['xlsx'], key='current_file')
with st.expander('Archivos de demostración y formato requerido'):
    st.write('Columnas: cedula, nombre, salario, horas_extra. Valores numéricos no negativos; primera hoja del Excel. Cédulas como texto.')
    for name in ['planilla_anterior.xlsx', 'planilla_actual.xlsx']:
        path = Path(__file__).parent / 'data' / name
        if path.exists():
            st.download_button(f'Descargar {name}', path.read_bytes(), name,
                               mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key=name)
    st.caption('La muestra contiene 25 empleados anteriores, 25 actuales únicos y un registro duplicado.')

# Replacing either input invalidates the previous result and manual review.
fingerprint = hashlib.sha256((previous_file.getvalue() if previous_file else b'') + b'\x00' +
                             (current_file.getvalue() if current_file else b'')).hexdigest()
if st.session_state.get('input_fingerprint') != fingerprint:
    for key in list(st.session_state):
        if key.startswith('review:') or key in ['result', 'statuses', 'selected_alert', 'risk_filter', 'type_filter']:
            del st.session_state[key]
    st.session_state.input_fingerprint = fingerprint

if st.button('Analizar planillas', type='primary', use_container_width=True):
    if previous_file is None or current_file is None:
        st.error('Carga la planilla anterior y la actual antes de analizar.')
    else:
        try:
            previous = read_payroll(BytesIO(previous_file.getvalue()), 'Planilla anterior')
            current = read_payroll(BytesIO(current_file.getvalue()), 'Planilla actual')
            alerts = analyze(previous, current)
            st.session_state.result = (previous, current, alerts)
            if 'statuses' not in st.session_state:
                st.session_state.statuses = {}
        except ValueError as exc:
            st.error(str(exc))

if 'result' in st.session_state:
    previous, current, alerts = st.session_state.result
    statuses = st.session_state.statuses
    st.divider()
    for col, label, value in zip(st.columns(4), ['Empleados actuales', 'Alertas detectadas', 'Casos críticos', 'Casos sin observaciones'], summary(current, alerts)):
        col.metric(label, value)
    st.caption('Empleados y casos sin observaciones cuentan cédulas únicas. Casos críticos cuenta alertas críticas; los ausentes no cuentan como empleados actuales.')
    if previous.cedula.duplicated().any():
        st.warning('La planilla anterior contiene cédulas repetidas. No se comparan salarios para esas cédulas porque no existe un valor anterior único.')
    if current.cedula.duplicated().any():
        st.warning('Las cédulas duplicadas actuales generan una alerta. Su comparación salarial se omite hasta resolver la duplicidad; las horas extra se revisan por registro.')
    st.subheader('Alertas encontradas')
    a, b, c = st.columns([2, 2, 1])
    risks = a.multiselect('Nivel de riesgo', list(RISK_ORDER), key='risk_filter')
    kinds = b.multiselect('Tipo de alerta', sorted({x.kind for x in alerts}), key='type_filter')
    only_anomalies = c.checkbox('Mostrar solo anomalías', value=False,
                                help='Oculta las altas informativas de empleados nuevos.')
    visible = [x for x in alerts if (not risks or x.risk in risks) and (not kinds or x.kind in kinds)
               and (not only_anomalies or x.risk != 'INFORMATIVO')]
    st.caption('Desmarca «Mostrar solo anomalías» para incluir empleados nuevos. El reporte siempre incluye todas las alertas.')
    if not alerts:
        st.success('No se detectaron excepciones con las cinco reglas del MVP. La revisión final corresponde al usuario.')
    elif not visible:
        st.info('No hay alertas para los filtros seleccionados.')
    else:
        st.dataframe(report_frame(visible, statuses).drop(columns=['Diferencia']), hide_index=True, use_container_width=True)
        by_id = {x.id: x for x in visible}
        if st.session_state.get('selected_alert') not in by_id:
            st.session_state.selected_alert = visible[0].id
        selected = st.selectbox('Seleccionar alerta para ver detalle y revisar', list(by_id),
                                format_func=lambda k: f'{by_id[k].risk} · {by_id[k].employee} · {by_id[k].kind}', key='selected_alert')
        alert = by_id[selected]
        with st.container(border=True):
            st.subheader(f'{alert.employee} · {alert.risk}')
            st.write(f'Cédula: {alert.cedula}')
            st.write(f'Regla activada: {alert.rule}')
            for col, label, value in zip(st.columns(3), ['Valor anterior', 'Valor actual', 'Diferencia'], [alert.previous, alert.current, alert.difference]):
                col.metric(label, value)
            st.write(alert.explanation)
            review_key = f'review:{alert.id}'
            if review_key not in st.session_state:
                st.session_state[review_key] = statuses.get(alert.id, 'Pendiente')
            def save_review():
                st.session_state.statuses[alert.id] = st.session_state[review_key]
            st.selectbox('Estado de revisión', ['Pendiente', 'Revisada', 'Aceptada'], key=review_key, on_change=save_review)
            st.caption('El estado se conserva durante esta sesión y se incluye en el reporte. Al cambiar los archivos se inicia una nueva revisión.')
    st.download_button('Descargar reporte de revisión', export_report(alerts, statuses),
                       file_name='reporte_revision_planilla.xlsx',
                       mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', type='primary')
