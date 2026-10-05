def compare(previous, current):
    old = set(previous.cedula)
    new = set(current.cedula)
    return {'new': new - old, 'absent': old - new, 'common': old & new,
            'duplicates': set(current.loc[current.cedula.duplicated(False), 'cedula'])}
