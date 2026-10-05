from dataclasses import dataclass


@dataclass(frozen=True)
class Anomaly:
    id: str
    risk: str
    kind: str
    cedula: str
    employee: str
    previous: str
    current: str
    difference: str
    rule: str
    explanation: str
