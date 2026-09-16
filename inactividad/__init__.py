"""
Paquete de cálculo de períodos de inactividad funcional.
"""
from modelos import Cargo, PeriodoInactividad
from logica import (
    calcular_inactividad_administracion_publica,
    calcular_inactividad_docencia,
    obtener_primera_fecha_ingreso_admin,
    obtener_primera_fecha_ingreso_docencia
)

__version__ = "1.0.0"
__all__ = [
    'Cargo',
    'PeriodoInactividad',
    'calcular_inactividad_administracion_publica',
    'calcular_inactividad_docencia',
    'obtener_primera_fecha_ingreso_admin',
    'obtener_primera_fecha_ingreso_docencia'
]
