# Calculadora de Períodos de Inactividad

Herramienta interactiva para calcular períodos de inactividad en la administración pública y docencia (UDELAR) basada en los cargos registrados de un funcionario.

## Características

- **Interfaz amigable**: Usa `rich` para mostrar resultados con colores y tablas, y `prompt_toolkit` para una entrada de datos robusta con validación en tiempo real.
- **Validación de fechas**: No permite fechas inválidas y acepta "actualidad" para cargos vigentes.
- **Cálculo automático**: Determina períodos de inactividad para:
  - **Administración Pública**: Todos los cargos sin importar institución o tipo.
  - **Docencia**: Solo cargos Docente en UDELAR.
- **Generación de reportes**: Crea archivos `.txt` con comunicados formales listos para usar.
- **Compatible Linux/Windows**: Funciona en cualquier terminal.

## Instalación

```bash
pip install rich prompt_toolkit
```

## Uso

### Opción 1: Ejecutar como módulo
```bash
python -m inactividad
```

### Opción 2: Ejecutar directamente (si agregas un script)
```bash
python main.py
```

## Flujo de trabajo

1. Ingresa la fecha de referencia para "actualidad" (por defecto hoy).
2. Completa los datos del funcionario (nombre y CI).
3. Agrega tantos cargos como necesites (en cualquier orden):
   - Institución (UDELAR, MEC, ANEP, etc.)
   - Tipo (TAS o Docente)
   - Dependencia (opcional)
   - Fecha de inicio (dd/mm/aaaa)
   - Fecha de fin (dd/mm/aaaa o "actualidad")
4. El programa calcula automáticamente los períodos de inactividad.
5. Genera un comunicado formal que puedes guardar en `.txt`.

## Ejemplo de salida

El programa muestra en consola:
- Resumen de fechas de primer ingreso
- Tabla de períodos de inactividad en Administración Pública
- Tabla de períodos de inactividad en Docencia
- Comunicado generado listo para guardar

## Estructura del proyecto

```
inactividad/
├── __init__.py       # Paquete principal
├── __main__.py       # Punto de entrada
├── modelos.py        # Clases Cargo y PeriodoInactividad
├── logica.py         # Algoritmos de cálculo
├── cli.py            # Interfaz interactiva
└── README.md         # Este archivo
```

## Reglas de negocio

### Administración Pública
- Incluye **todos** los cargos (TAS o Docente, en cualquier institución).
- La ventana de análisis comienza en el primer cargo registrado.

### Docencia
- Solo incluye cargos **Docente en UDELAR**.
- La ventana de análisis comienza en el primer cargo Docente-UDELAR.
- Si no hay cargos de este tipo, no se registran períodos de inactividad.

### Períodos de inactividad
- Se calculan como el complemento de la unión de intervalos de actividad.
- Los intervalos contiguos (fin + 1 día = inicio siguiente) se consideran continuos.
- Cada período muestra entre qué cargos ocurre el hueco.

## Autor

Herramienta desarrollada para gestión de cargos funcionariales.
