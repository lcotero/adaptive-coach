# Adaptive Coach

Adaptive Coach es un entrenador adaptativo para running que transforma datos de entrenamiento
en análisis y recomendaciones explicables. La primera etapa utiliza COROS únicamente como fuente
de datos de solo lectura.

## Objetivo

El sistema busca construir un entrenador adaptativo basado en:

- datos reales de COROS;
- análisis de ejecución de sesiones;
- carga de entrenamiento;
- recuperación;
- feedback subjetivo;
- contexto del macrociclo.

Durante la etapa inicial, la integración con COROS es estrictamente read-only.

## Principios de arquitectura

1. COROS es una fuente de datos, no el dominio interno.
2. Los datos de COROS deben normalizarse mediante un adapter.
3. Los motores de decisión fisiológica deben ser determinísticos y testeables.
4. El LLM puede interpretar contexto y explicar decisiones, pero no saltarse las reglas del motor.
5. Las decisiones deben ser auditables.
6. Cuando una métrica agregada genere dudas y exista detalle disponible, deben analizarse laps,
   segmentos o FIT antes de concluir.
7. El sistema no debe modificar automáticamente entrenamientos en COROS durante la etapa
   read-only.

## Arquitectura conceptual

```text
COROS MCP
    |
    v
Coros Adapter
    |
    v
Internal Domain Models
    |
    +----------------------+
    |                      |
    v                      v
Activity Analysis      Athlete State
Engine                 Engine
    |                      |
    +----------+-----------+
               |
               v
        Adaptation Engine
               |
               v
          Safety Engine
               |
               v
           LLM Coach
               |
               v
          Shadow Coach
```

## Estado actual

Sprint 7 — Shadow Coach complete

## Desarrollo local

Se requiere Python 3.12.

```bash
python -m venv .venv
```

Activar el entorno en macOS o Linux:

```bash
source .venv/bin/activate
```

O en PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instalar el proyecto y las herramientas de desarrollo:

```bash
python -m pip install -e ".[dev]"
```

Ejecutar las validaciones:

```bash
python -m pytest
python -m ruff check .
python -m mypy app
```

También se pueden ejecutar todos los chequeos con `make check`.
