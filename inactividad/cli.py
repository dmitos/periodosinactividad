"""
Interfaz de línea de comandos interactiva usando prompt_toolkit y rich.
"""
from datetime import date, datetime
from typing import List, Optional
import json
import os

from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from modelos import Cargo
from logica import (
    calcular_inactividad_administracion_publica,
    calcular_inactividad_docencia,
    obtener_primera_fecha_ingreso_admin,
    obtener_primera_fecha_ingreso_docencia
)


# Estilos para prompt_toolkit
style = Style.from_dict({
    'prompt': 'ansicyan bold',
    'error': 'ansired bold',
    'success': 'ansigreen bold',
})

console = Console()


class FechaValidator(Validator):
    """Valida que la entrada sea una fecha en formato dd/mm/aaaa."""
    
    def validate(self, document):
        text = document.text.strip()
        
        if not text:
            raise ValidationError(message="La fecha no puede estar vacía")
        
        # Permitir "actualidad" como valor especial
        if text.lower() == "actualidad":
            return
        
        try:
            datetime.strptime(text, "%d/%m/%Y")
        except ValueError:
            raise ValidationError(
                message="Formato inválido. Use dd/mm/aaaa (ej: 15/03/2024)"
            )


def parsear_fecha(texto: str, fecha_referencia: date) -> Optional[date]:
    """Convierte texto a fecha, manejando 'actualidad'."""
    texto = texto.strip().lower()
    if texto == "actualidad":
        return fecha_referencia
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None


def solicitar_fecha(mensaje: str, fecha_referencia: date, permitir_actualidad: bool = True) -> date:
    """Solicita una fecha al usuario con validación."""
    while True:
        if permitir_actualidad:
            texto = prompt(
                f"{mensaje} (dd/mm/aaaa o 'actualidad'): ",
                validator=FechaValidator(),
                style=style
            )
        else:
            # Validador simplificado sin 'actualidad'
            class SoloFechaValidator(Validator):
                def validate(self, doc):
                    try:
                        datetime.strptime(doc.text.strip(), "%d/%m/%Y")
                    except ValueError:
                        raise ValidationError(message="Use dd/mm/aaaa")
            
            texto = prompt(
                f"{mensaje} (dd/mm/aaaa): ",
                validator=SoloFechaValidator(),
                style=style
            )
        
        resultado = parsear_fecha(texto, fecha_referencia)
        if resultado:
            return resultado
        
        console.print("[red]Fecha inválida. Intente nuevamente.[/red]")


def solicitar_cargo(fecha_referencia: date, numero: int) -> Optional[Cargo]:
    """Solicita los datos de un cargo al usuario."""
    console.print(Panel(f"[bold cyan]--- Cargo #{numero} ---[/bold cyan]"))
    
    # Institución
    institucion = prompt(
        "Institución (ej. UDELAR, MEC, ANEP): ",
        style=style
    ).strip().upper()
    
    if not institucion:
        console.print("[red]La institución es obligatoria.[/red]")
        return None
    
    # Tipo
    completador_tipo = WordCompleter(['TAS', 'Docente'], ignore_case=True)
    tipo = prompt(
        "Tipo (TAS / Docente): ",
        completer=completador_tipo,
        style=style
    ).strip()
    
    # Normalizar tipo
    if tipo.lower() == 'docente':
        tipo = 'Docente'
    elif tipo.upper() == 'TAS':
        tipo = 'TAS'
    else:
        console.print("[yellow]Tipo no reconocido, se usará 'TAS' por defecto.[/yellow]")
        tipo = 'TAS'
    
    # Dependencia (opcional)
    dependencia = prompt(
        "Dependencia (opcional, ej. FIC, Oficinas): ",
        style=style
    ).strip() or None
    
    # Fechas
    fecha_inicio = solicitar_fecha("Fecha de inicio", fecha_referencia, permitir_actualidad=False)
    fecha_fin = solicitar_fecha("Fecha de fin", fecha_referencia, permitir_actualidad=True)
    
    # Descripción opcional
    descripcion = prompt(
        "Descripción adicional (opcional): ",
        style=style
    ).strip()
    
    return Cargo(
        institucion=institucion,
        tipo=tipo,
        dependencia=dependencia,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin if fecha_fin != fecha_referencia else None,  # Guardar None si es vigencia
        descripcion=descripcion
    )


def mostrar_resultados(
    nombre: str,
    ci: str,
    cargos: List[Cargo],
    fecha_referencia: date
):
    """Muestra los resultados del cálculo en consola con formato bonito."""
    console.print("\n[bold green]=== RESULTADOS DEL CÁLCULO ===[/bold green]\n")
    
    # Calcular fechas de ingreso
    fecha_ingreso_admin = obtener_primera_fecha_ingreso_admin(cargos, fecha_referencia)
    fecha_ingreso_doc = obtener_primera_fecha_ingreso_docencia(cargos, fecha_referencia)
    
    # Calcular períodos de inactividad
    inactividad_admin = calcular_inactividad_administracion_publica(cargos, fecha_referencia)
    inactividad_doc = calcular_inactividad_docencia(cargos, fecha_referencia)
    
    # Tabla de resumen
    tabla_resumen = Table(title="Resumen de Ingresos")
    tabla_resumen.add_column("Indicador", style="cyan")
    tabla_resumen.add_column("Fecha de Primer Ingreso", style="green")
    
    tabla_resumen.add_row(
        "Administración Pública",
        fecha_ingreso_admin.strftime("%d/%m/%Y") if fecha_ingreso_admin else "No registra"
    )
    tabla_resumen.add_row(
        "Docencia (UDELAR)",
        fecha_ingreso_doc.strftime("%d/%m/%Y") if fecha_ingreso_doc else "No registra"
    )
    
    console.print(tabla_resumen)
    console.print()
    
    # Tabla de inactividad Administración Pública
    tabla_admin = Table(title="ADMINISTRACIÓN PÚBLICA - Períodos de Inactividad")
    tabla_admin.add_column("Período", style="yellow")
    tabla_admin.add_column("Entre cargos", style="magenta")
    
    if inactividad_admin:
        for periodo in inactividad_admin:
            tabla_admin.add_row(
                str(periodo),
                periodo.descripcion_completa()
            )
    else:
        tabla_admin.add_row("No registra", "")
    
    console.print(tabla_admin)
    console.print()
    
    # Tabla de inactividad Docencia
    tabla_doc = Table(title="DOCENCIA - Períodos de Inactividad")
    tabla_doc.add_column("Período", style="yellow")
    tabla_doc.add_column("Entre cargos", style="magenta")
    
    if inactividad_doc:
        for periodo in inactividad_doc:
            tabla_doc.add_row(
                str(periodo),
                periodo.descripcion_completa()
            )
    else:
        tabla_doc.add_row("No registra", "")
    
    console.print(tabla_doc)
    
    return {
        'nombre': nombre,
        'ci': ci,
        'fecha_referencia': fecha_referencia,
        'fecha_ingreso_admin': fecha_ingreso_admin,
        'fecha_ingreso_doc': fecha_ingreso_doc,
        'inactividad_admin': inactividad_admin,
        'inactividad_doc': inactividad_doc
    }


def generar_comunicado(resultados: dict, es_actualizacion: bool) -> str:
    """Genera el texto del comunicado según corresponda."""
    nombre = resultados['nombre']
    ci = resultados['ci']
    
    if es_actualizacion:
        encabezado = f"""Se informa que se modifican las fechas de ingreso a la administración 
pública, docencia, y se agregan fechas de períodos de inactividad según 
nuevas constancias recibidas del funcionario {nombre}, c.i {ci}."""
    else:
        encabezado = f"""Se informa el ingreso a la administración pública, docencia, según 
constancias recibidas del funcionario {nombre}, c.i {ci}."""
    
    # Formatear períodos de inactividad
    def format_huecos(huecos):
        if not huecos:
            return "No registra"
        return "; ".join(str(h) for h in huecos)
    
    cuerpo = f"""
Por lo que queda ingresado:
Ing. Adm. Pública: {resultados['fecha_ingreso_admin'].strftime('%d/%m/%Y') if resultados['fecha_ingreso_admin'] else 'No registra'}
Ing. Doc.: {resultados['fecha_ingreso_doc'].strftime('%d/%m/%Y') if resultados['fecha_ingreso_doc'] else 'No registra'}
P. Inactividad Adm. Pública: {format_huecos(resultados['inactividad_admin'])}
P. Inactividad Doc.: {format_huecos(resultados['inactividad_doc'])}
"""
    
    return encabezado + cuerpo


def guardar_archivo(contenido: str, extension: str, prefix: str = "resultado"):
    """Guarda el contenido en un archivo."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.{extension}"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    console.print(f"[green]Archivo guardado: {filename}[/green]")
    return filename


def ejecutar():
    """Función principal que ejecuta la interfaz interactiva."""
    console.print(Panel.fit(
        "[bold blue]Calculadora de Períodos de Inactividad[/bold blue]\n"
        "Sistema de gestión de cargos funcionariales",
        style="bold white on blue"
    ))
    
    # Solicitar fecha de referencia
    console.print("\n[cyan]¿Fecha de referencia para 'actualidad'?[/cyan]")
    hoy = date.today()
    fecha_input = prompt(
        f"[hoy: {hoy.strftime('%d/%m/%Y')}] (Enter para aceptar o ingrese nueva fecha): ",
        style=style
    )
    
    if fecha_input.strip():
        try:
            fecha_referencia = datetime.strptime(fecha_input.strip(), "%d/%m/%Y").date()
        except ValueError:
            console.print(f"[yellow]Fecha inválida, se usará la fecha de hoy: {hoy.strftime('%d/%m/%Y')}[/yellow]")
            fecha_referencia = hoy
    else:
        fecha_referencia = hoy
    
    console.print(f"[green]Fecha de referencia establecida: {fecha_referencia.strftime('%d/%m/%Y')}[/green]")
    
    # Datos del funcionario
    console.print("\n[bold]Datos del Funcionario[/bold]")
    nombre = prompt("Nombre completo: ", style=style)
    ci = prompt("Cédula de Identidad: ", style=style)
    
    # Carga de cargos
    cargos = []
    numero_cargo = 1
    
    while True:
        cargo = solicitar_cargo(fecha_referencia, numero_cargo)
        if cargo:
            cargos.append(cargo)
            console.print(f"[green]✓ Cargo #{numero_cargo} agregado correctamente[/green]")
        
        continuar = Confirm.ask("¿Agregar otro cargo?", default=False)
        if not continuar:
            break
        
        numero_cargo += 1
    
    if not cargos:
        console.print("[red]No se cargaron cargos. Finalizando.[/red]")
        return
    
    # Mostrar resultados
    resultados = mostrar_resultados(nombre, ci, cargos, fecha_referencia)
    
    # Generar comunicado
    console.print("\n[yellow]¿Este funcionario ya tenía cálculos previos?[/yellow]")
    es_actualizacion = Confirm.ask("¿Es una actualización?", default=False)
    
    comunicado = generar_comunicado(resultados, es_actualizacion)
    
    console.print("\n[bold]=== COMUNICADO GENERADO ===[/bold]")
    console.print(Panel(comunicado, style="white"))
    
    # Opciones de guardado
    console.print("\n[cyan]Opciones de guardado:[/cyan]")
    if Confirm.ask("¿Guardar comunicado en archivo .txt?", default=True):
        guardar_archivo(comunicado, "txt", "comunicado")
    
    if Confirm.ask("¿Guardar resultados detallados en .txt?", default=False):
        # Formato detallado
        detalle = f"""RESULTADOS DETALLADOS
=====================
Funcionario: {nombre}
CI: {ci}
Fecha de referencia: {fecha_referencia.strftime('%d/%m/%Y')}

{comunicado}

CARGOS REGISTRADOS:
"""
        for i, c in enumerate(cargos, 1):
            detalle += f"\n{i}. {c.institucion} - {c.tipo} ({c.dependencia or 'N/A'})"
            detalle += f"\n   Inicio: {c.fecha_inicio.strftime('%d/%m/%Y')} | Fin: {c.fecha_fin.strftime('%d/%m/%Y') if c.fecha_fin else 'Vigente'}"
        
        guardar_archivo(detalle, "txt", "detalle_resultados")
    
    console.print("\n[green]¡Proceso completado![/green]")
