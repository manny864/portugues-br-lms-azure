# Directiva de Ejemplo (Plantilla Base SOP)

## 1. Objetivo
Definir de manera clara y determinista el propósito de la tarea, el problema que resuelve y el entregable esperado.

## 2. Entradas (Inputs)
- Variables de entorno requeridas en `.env`.
- Archivos de configuración o datos de origen (JSON, CSV, APIs).
- Parámetros de ejecución.

## 3. Lógica y Procedimiento Operativo Estándar (SOP)
1. **Validación de Entorno:** Verificar dependencias, directorios (`.tmp/`, salidas) y credenciales antes de ejecutar operaciones externas.
2. **Procesamiento Principal:** Ejecutar la lógica de negocio de forma modular e idempotente (ejecutar dos veces produce el mismo resultado limpio sin duplicar recursos).
3. **Verificación de Salidas:** Validar integridad de los archivos generados (sintaxis JSON, estructura de directorios, estados HTTP).
4. **Persistencia y Entregables:** Guardar datos intermedios en `.tmp/` y entregables finales en la estructura del proyecto o nube.

## 4. Salidas (Outputs)
- Archivos generados, rutas exactas y artefactos desplegados.

## 5. Restricciones y Casos Borde (Memoria Viva / Trampas Conocidas)
- *Nota:* Documentar aquí cualquier limitación técnica, de API o de plataforma descubierta durante la ejecución bajo el formato: *"Nota: No hacer X, porque causa el error Y. En su lugar, hacer Z."*
