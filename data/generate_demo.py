from pathlib import Path
import pandas as pd


def generate():
    folder = Path(__file__).parent
    names = ['Juan Pérez', 'María Gómez', 'Carlos Rodríguez', 'Ana González', 'Luis Martínez',
             'Laura Sánchez', 'Pedro Díaz', 'Sofía López', 'José Castillo', 'Carmen Moreno',
             'David Vega', 'Isabel Torres', 'Miguel Flores', 'Elena Ruiz', 'Andrés Ramos',
             'Paula Jiménez', 'Jorge Mendoza', 'Lucía Herrera', 'Ricardo Ortiz', 'Daniela Castro',
             'Fernando Ríos', 'Valeria Vargas', 'Manuel Reyes', 'Gabriela León', 'Raúl Navarro']
    previous = pd.DataFrame([{'cedula': f'8-123-{456+i}', 'nombre': name,
                              'salario': 900 + 50*i, 'horas_extra': 4} for i, name in enumerate(names)])
    current = previous.iloc[:-1].copy()
    current.loc[0, 'salario'] = 9000
    current.loc[2, 'horas_extra'] = 38
    current = pd.concat([current, current.iloc[[1]], pd.DataFrame([
        {'cedula': '8-999-111', 'nombre': 'Patricia Álvarez', 'salario': 1100, 'horas_extra': 3}])], ignore_index=True)
    previous.to_excel(folder / 'planilla_anterior.xlsx', index=False)
    current.to_excel(folder / 'planilla_actual.xlsx', index=False)


if __name__ == '__main__':
    generate()
