"""
Modelos de datos para el cálculo de períodos de inactividad.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List


@dataclass
class Cargo:
    """Representa un cargo de un funcionario."""
    institucion: str  # ej. "UDELAR", "MEC", "ANEP"
    tipo: str         # "TAS" o "Docente"
    dependencia: Optional[str] = None  # ej. "FIC", "Oficinas"
    fecha_inicio: date = field(default_factory=date.today)
    fecha_fin: Optional[date] = None  # None significa vigente
    descripcion: str = ""  # Descripción adicional opcional

    def es_docencia_udelar(self) -> bool:
        """Determina si este cargo cuenta para el bucket de Docencia."""
        return (
            self.institucion.upper() == "UDELAR" and 
            self.tipo.lower() == "docente"
        )

    def es_administracion_publica(self) -> bool:
        """Todos los cargos cuentan para Administración Pública."""
        return True

    def get_fecha_fin_real(self, fecha_referencia: date) -> date:
        """Obtiene la fecha de fin real, usando la referencia si es vigente."""
        return self.fecha_fin if self.fecha_fin else fecha_referencia

    def __str__(self) -> str:
        dep = f"-{self.dependencia}" if self.dependencia else ""
        return f"{self.tipo}-{self.institucion}{dep}"


@dataclass
class PeriodoInactividad:
    """Representa un período de inactividad detectado."""
    fecha_inicio: date
    fecha_fin: date
    cargo_anterior: Optional[Cargo] = None
    cargo_siguiente: Optional[Cargo] = None

    def __str__(self) -> str:
        return f"{self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}"

    def descripcion_completa(self) -> str:
        ant = str(self.cargo_anterior) if self.cargo_anterior else "Inicio"
        sig = str(self.cargo_siguiente) if self.cargo_siguiente else "Actualidad"
        return f"{ant} → {sig}"
