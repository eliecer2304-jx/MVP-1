import pandas as pd

REQUIRED = ['cedula', 'nombre', 'salario', 'horas_extra']


def validate(df: pd.DataFrame, label: str) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if df.columns.duplicated().any():
        raise ValueError(f'{label}: hay columnas repetidas.')
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f'{label}: faltan columnas: {", ".join(missing)}.')
    if df.empty:
        raise ValueError(f'{label}: el archivo no contiene empleados.')
    for c in ['cedula', 'nombre']:
        invalid = df[c].isna() | df[c].astype(str).str.strip().eq('')
        if invalid.any():
            raise ValueError(f'{label}: {c} vacío en filas Excel {list(df.index[invalid] + 2)}.')
        df[c] = df[c].astype(str).str.strip()
    for c in ['salario', 'horas_extra']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
        invalid = df[c].isna() | ~df[c].map(lambda x: float('-inf') < x < float('inf')) | (df[c] < 0)
        if invalid.any():
            raise ValueError(f'{label}: {c} debe ser un número finito no negativo; filas Excel {list(df.index[invalid] + 2)}.')
    return df
