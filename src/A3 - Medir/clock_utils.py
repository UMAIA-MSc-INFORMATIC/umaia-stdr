"""
Fonte temporal de alta resolução para as medições MQTT.
"""

import time

CLOCK_NAME = "perf_counter"


def now_ns() -> int:
    """
    Retorna o valor atual do contador monotónico de alta resolução
    expresso em nanossegundos.

    Este valor deve ser utilizado apenas para medir intervalos de tempo.
    Não representa data/hora UTC.
    """
    return time.perf_counter_ns()


def clock_metadata() -> dict:
    """
    Retorna informações sobre o relógio utilizado na medição.
    Estas informações serão armazenadas no metadata do experimento.
    """
    info = time.get_clock_info(CLOCK_NAME)

    return {
        "name": CLOCK_NAME,
        "implementation": info.implementation,
        "monotonic": info.monotonic,
        "adjustable": info.adjustable,
        "resolution_s": info.resolution,
        "resolution_ns": info.resolution * 1_000_000_000,
    }