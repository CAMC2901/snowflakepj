# Política de tareas de la IA

Las seis pautas del ejercicio se aplican al catálogo de diez tareas del agente
en `backend/app/agent/task_policy.py`, no a diez solicitudes de ciudadanos.

1. Cada tarea declara tiempo estimado (minutos de trabajo humano equivalente),
   frecuencia por evento, riesgo y valor. No son métricas de producción.
2. Riesgo y valor usan una escala de 1 (bajo) a 3 (alto).
3. La matriz considera esfuerzo alto por encima de cinco minutos e impacto
   alto a partir de valor 2. Estos umbrales son decisiones iniciales ajustables.
4. Por solicitud, el nodo de planificación selecciona hasta tres tareas aplicables:
   mayor valor, menor riesgo, menor tiempo y finalmente ID para desempatar.
   Las tareas de riesgo 3 requieren decisión humana y no compiten como
   candidatas de automatización. El ranking no omite pasos del flujo existente,
   no reduce prioridad de atención ciudadana y no evita escalamientos.
5. Cada resultado tiene un rol revisor y estado `PENDING_REVIEW`.
   Asignar un rol NO significa que una persona haya revisado o aprobado algo;
   esta versión no implementa un circuito de aprobación ni asignación individual.
6. Se genera un guion breve de las elecciones, pensado para una exposición
   de hasta dos minutos; no se garantiza ni mide su duración oral.

## Consulta

- `GET /api/agent/task_policy`: catálogo y prioridades generales.
- `POST /api/agent/chat`: incluye `task_policy` para la intención detectada.
- El registro de pasos del agente incluye la explicación de priorización.

Las decisiones administrativas de fondo siguen reservadas a funcionarios.
Los parámetros del catálogo deben ser revisados por responsables institucionales
antes de utilizarse como evaluación formal de riesgos o valores públicos.

## Pruebas

`python -m unittest backend.tests.test_task_policy`
