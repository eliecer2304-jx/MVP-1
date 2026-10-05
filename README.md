# Control Inteligente de Planillas

MVP universitario de Ingeniería de Software para revisar excepciones entre dos períodos de planilla en Panamá, antes de continuar con SIPE. El sistema detecta excepciones. La decisión final corresponde al usuario.

## Alcance

Carga dos archivos Excel, valida su estructura y datos, compara empleados por cédula y presenta alertas con filtros, detalle y revisión humana. Exporta todas las alertas con su estado a `reporte_revision_planilla.xlsx`.

No reemplaza SIPE ni calcula nómina, cuotas CSS o ISR. No incluye integración con SIPE, APIs externas, IA, banca, cuentas de usuario ni autenticación.

## Requisitos e instalación

Python 3.10 o superior (validado con Python 3.12), pip y un navegador. Desde la raíz del proyecto:

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Los archivos de demostración ya están en `data/`. Para regenerarlos de forma intencional (sobrescribe solo estos dos archivos):

```bash
python data/generate_demo.py
```

## Demostración

1. Abrir la aplicación.
2. Cargar `data/planilla_anterior.xlsx` y `data/planilla_actual.xlsx`. También pueden descargarse desde la sección de demostración de la interfaz.
3. Pulsar **Analizar planillas**.
4. Ver las tarjetas: 25 empleados actuales únicos, 5 alertas, 1 crítica y 21 empleados actuales sin observaciones.
5. Ver las cinco alertas. Activar **Mostrar solo anomalías** si se desea ocultar el empleado nuevo informativo.
6. Seleccionar una alerta, ver el detalle y cambiar su estado a Pendiente, Revisada o Aceptada.
7. Filtrar por riesgo o tipo y descargar el reporte. El reporte incluye las cinco alertas aunque la tabla esté filtrada.

Los estados se conservan en la sesión activa; cambiar cualquiera de los archivos reinicia la revisión. No existe persistencia en base de datos. «Aceptada» expresa una decisión del usuario sobre una alerta; la aplicación no certifica la planilla.

## Excel de entrada

Se lee la primera hoja de cada archivo `.xlsx`. Columnas mínimas:

| cedula | nombre | salario | horas_extra |
| --- | --- | ---: | ---: |
| 8-123-456 | Juan Pérez | 900 | 5 |
| 8-222-333 | María Gómez | 1200 | 2 |

Guardar cédulas como texto para conservar ceros iniciales. Los nombres de columnas se normalizan a minúsculas y sin espacios externos; se permiten columnas adicionales. No se permiten identificadores o nombres vacíos, columnas repetidas ni valores numéricos vacíos, infinitos, negativos o texto no numérico. Salario y horas extra deben ser números Excel, sin símbolos monetarios. Los errores indican el archivo, la columna y, cuando aplica, las filas Excel afectadas.

## Las cinco reglas

| Regla | Condición | Riesgo |
| --- | --- | --- |
| Cambio salarial | Variación absoluta mayor al 30% | ALTO; CRÍTICO si supera 100% |
| Empleado duplicado | Cédula repetida en la actual | ALTO |
| Empleado nuevo | Solo aparece en la actual | INFORMATIVO |
| Empleado ausente | Solo aparece en la anterior | MEDIO |
| Horas extra atípicas | Valor actual mayor que 20 | MEDIO |

Los límites son estrictos: 30% y 20 horas no generan alertas; 100% es ALTO. El cambio salarial no se aplica a empleados nuevos. Si el salario anterior es cero y el actual positivo, se genera una excepción salarial CRÍTICA con porcentaje no calculable; cero a cero no genera alerta.

Una cédula duplicada actual genera una alerta por cédula. No se selecciona arbitrariamente un salario para comparar registros duplicados de ninguno de los períodos. La interfaz advierte esta limitación. Las horas extra se evalúan por fila actual, incluso para empleados nuevos o duplicados. La ausencia no implica despido.

Las tarjetas cuentan empleados únicos; «sin observaciones» incluye únicamente empleados actuales sin ninguna alerta. Casos críticos cuenta alertas críticas. La muestra contiene 25 filas anteriores y 26 actuales (25 cédulas únicas), y activa exactamente una alerta por cada regla: 900 a 9000, duplicidad, alta, ausencia y 38 horas extra.

## Pruebas

```bash
pytest
```

Se prueban las cinco reglas, límites, base salarial cero, entradas inválidas, duplicados ambiguos, archivos reales de demostración, exportación y controles de la interfaz con Streamlit AppTest. La prueba de interfaz inyecta el resultado validado porque AppTest no ofrece carga de archivos; la lectura real de los Excel se valida por separado.

## Estructura

- `app.py`: interfaz, sesión, filtros y revisión manual.
- `services/excel_service.py`: lectura y exportación segura a Excel.
- `services/comparison_service.py`: comparación por cédula.
- `services/anomaly_service.py`: cinco reglas y métricas.
- `models/anomaly.py`: modelo de alerta.
- `utils/validators.py`: validación de columnas y datos.
- `tests/`: pruebas unitarias, integración y controles de interfaz.
- `data/`: Excel de demostración y generador reproducible.
- `.streamlit/config.toml`: tema azul marino y menta.
