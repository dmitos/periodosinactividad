"""
Lógica de negocio para el cálculo de períodos de inactividad.
"""
from datetime import date, timedelta
from typing import List, Tuple, Optional
from .modelos import Cargo, PeriodoInactividad


def normalizar_cargos(cargos: List[Cargo], fecha_referencia: date) -> List[Cargo]:
    """
    Normaliza los cargos asegurando que las fechas fin vigentes 
    usen la fecha de referencia.
    """
    # Creamos copias para no modificar los originales
    cargos_normalizados = []
    for cargo in cargos:
        nuevo_cargo = Cargo(
            institucion=cargo.institucion,
            tipo=cargo.tipo,
            dependencia=cargo.dependencia,
            fecha_inicio=cargo.fecha_inicio,
            fecha_fin=cargo.get_fecha_fin_real(fecha_referencia),
            descripcion=cargo.descripcion
        )
        cargos_normalizados.append(nuevo_cargo)
    return cargos_normalizados


def fusionar_intervalos(intervalos: List[Tuple[date, date]]) -> List[Tuple[date, date]]:
    """
    Fusiona intervalos que se solapan o son contiguos.
    Los intervalos deben estar ordenados por fecha de inicio.
    """
    if not intervalos:
        return []
    
    # Ordenar por fecha de inicio
    intervalos_ordenados = sorted(intervalos, key=lambda x: x[0])
    
    fusionados = [intervalos_ordenados[0]]
    
    for inicio, fin in intervalos_ordenados[1:]:
        ultimo_inicio, ultimo_fin = fusionados[-1]
        
        # Si el intervalo actual comienza antes o justo después del último,
        # lo fusionamos (contiguo significa que si termina el 06/06 y empieza 07/06, hay hueco de 1 día)
        # Pero según el ejemplo, si termina 06/06 y empieza 07/06, hay continuidad? 
        # Revisando el ejemplo: cesa 06/06/2015, inicia 07/06/2016 -> hueco de un año
        # El hueco arranca al día siguiente del cese.
        # Si cesa 06/06/2015 y otro inicia 07/06/2015 -> hay 1 día de hueco? 
        # Asumimos que si es contiguo (fin + 1 día = inicio siguiente) se considera continuo.
        
        if inicio <= ultimo_fin + timedelta(days=1):
            # Fusionar
            fusionados[-1] = (ultimo_inicio, max(ultimo_fin, fin))
        else:
            fusionados.append((inicio, fin))
    
    return fusionados


def obtener_intervalos_actividad(
    cargos: List[Cargo], 
    filtro_func=None
) -> List[Tuple[date, date]]:
    """
    Obtiene la lista de intervalos de actividad aplicando un filtro opcional.
    """
    intervalos = []
    for cargo in cargos:
        if filtro_func is None or filtro_func(cargo):
            intervalos.append((cargo.fecha_inicio, cargo.fecha_fin))
    return intervalos


def calcular_huecos(
    intervalos_actividad: List[Tuple[date, date]],
    fecha_min: date,
    fecha_max: date
) -> List[Tuple[date, date]]:
    """
    Calcula los huecos (períodos de inactividad) dentro de una ventana [fecha_min, fecha_max].
    """
    if not intervalos_actividad:
        return [(fecha_min, fecha_max)]
    
    # Fusionar intervalos
    fusionados = fusionar_intervalos(intervalos_actividad)
    
    huecos = []
    cursor = fecha_min
    
    for inicio_act, fin_act in fusionados:
        if inicio_act > cursor:
            # Hay un hueco antes de este periodo de actividad
            huecos.append((cursor, inicio_act - timedelta(days=1)))
        
        # Avanzar el cursor
        cursor = max(cursor, fin_act + timedelta(days=1))
    
    # Si queda espacio después del último periodo de actividad
    if cursor <= fecha_max:
        huecos.append((cursor, fecha_max))
    
    return huecos


def calcular_inactividad_administracion_publica(
    cargos: List[Cargo], 
    fecha_referencia: date
) -> List[PeriodoInactividad]:
    """
    Calcula los períodos de inactividad para Administración Pública.
    Incluye TODOS los cargos.
    Ventana: desde el primer cargo hasta la fecha de referencia.
    """
    if not cargos:
        return []
    
    cargos_norm = normalizar_cargos(cargos, fecha_referencia)
    
    # Todos los cargos cuentan
    intervalos = obtener_intervalos_actividad(cargos_norm)
    
    if not intervalos:
        return []
    
    # Ventana: min inicio a fecha_referencia
    fecha_min = min(c.fecha_inicio for c in cargos_norm)
    fecha_max = fecha_referencia
    
    huecos = calcular_huecos(intervalos, fecha_min, fecha_max)
    
    # Construir objetos PeriodoInactividad con contexto de cargos
    periodos = []
    for inicio_hueco, fin_hueco in huecos:
        # Buscar cargo anterior (el que termina antes o en el inicio del hueco)
        cargo_ant = None
        cargo_sig = None
        
        for cargo in cargos_norm:
            if cargo.fecha_fin < inicio_hueco and (cargo_ant is None or cargo.fecha_fin > cargo_ant.fecha_fin):
                cargo_ant = cargo
        
        for cargo in cargos_norm:
            if cargo.fecha_inicio > fin_hueco and (cargo_sig is None or cargo.fecha_inicio < cargo_sig.fecha_inicio):
                cargo_sig = cargo
        
        periodos.append(PeriodoInactividad(inicio_hueco, fin_hueco, cargo_ant, cargo_sig))
    
    return periodos


def calcular_inactividad_docencia(
    cargos: List[Cargo], 
    fecha_referencia: date
) -> List[PeriodoInactividad]:
    """
    Calcula los períodos de inactividad para Docencia.
    Solo incluye cargos Docente en UDELAR.
    Ventana: desde el primer cargo Docente-Udelar hasta la fecha de referencia.
    """
    cargos_norm = normalizar_cargos(cargos, fecha_referencia)
    
    # Filtrar solo Docencia Udelar
    cargos_docencia = [c for c in cargos_norm if c.es_docencia_udelar()]
    
    if not cargos_docencia:
        return []
    
    intervalos = obtener_intervalos_actividad(cargos_docencia)
    
    if not intervalos:
        return []
    
    # Ventana: desde el primer cargo docente-udelar
    fecha_min = min(c.fecha_inicio for c in cargos_docencia)
    fecha_max = fecha_referencia
    
    huecos = calcular_huecos(intervalos, fecha_min, fecha_max)
    
    # Construir objetos PeriodoInactividad con contexto
    periodos = []
    for inicio_hueco, fin_hueco in huecos:
        cargo_ant = None
        cargo_sig = None
        
        for cargo in cargos_docencia:
            if cargo.fecha_fin < inicio_hueco and (cargo_ant is None or cargo.fecha_fin > cargo_ant.fecha_fin):
                cargo_ant = cargo
        
        for cargo in cargos_docencia:
            if cargo.fecha_inicio > fin_hueco and (cargo_sig is None or cargo.fecha_inicio < cargo_sig.fecha_inicio):
                cargo_sig = cargo
        
        periodos.append(PeriodoInactividad(inicio_hueco, fin_hueco, cargo_ant, cargo_sig))
    
    return periodos


def obtener_primera_fecha_ingreso_admin(cargos: List[Cargo], fecha_referencia: date) -> Optional[date]:
    """Obtiene la primera fecha de ingreso a la administración pública."""
    if not cargos:
        return None
    cargos_norm = normalizar_cargos(cargos, fecha_referencia)
    return min(c.fecha_inicio for c in cargos_norm)


def obtener_primera_fecha_ingreso_docencia(cargos: List[Cargo], fecha_referencia: date) -> Optional[date]:
    """Obtiene la primera fecha de ingreso a la docencia (Udelar)."""
    cargos_norm = normalizar_cargos(cargos, fecha_referencia)
    cargos_doc = [c for c in cargos_norm if c.es_docencia_udelar()]
    if not cargos_doc:
        return None
    return min(c.fecha_inicio for c in cargos_doc)
