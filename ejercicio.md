# ⚡ SysWatch – Panel de Control del Servidor

> **Actividad personal** sobre la base del ejercicio de clase (panel de control del servidor Ollama).

## Descripción

SysWatch es un sistema de monitorización de **todos los recursos del servidor** (CPU, RAM, Disco, Red) —no solo Ollama—, que guarda histórico en SQLite y lo muestra en un dashboard web con Chart.js.

## Estructura

```
main.py                  ← Punto de entrada
requirements.txt
backend/
  monitor.py             ← Hilo de recolección (psutil + threading + multiprocessing)
  database.py            ← SQLite (metricas_raw, metricas_hora, alertas)
  servidor.py            ← Flask + Flask-SocketIO (REST + WebSocket)
frontend/
  index.html             ← Dashboard
  styles.css             ← Tema oscuro/claro
  app.js                 ← WebSocket cliente + Chart.js
  workers/
    stats_worker.js      ← Web Worker (estadísticas en segundo plano)
```

## Cómo ejecutar

```bash
pip install -r requirements.txt
python main.py
# Abrir: http://localhost:5000
```

## Conceptos de clase

| Unidad | Concepto | Archivo |
|--------|----------|---------|
| 1 – Multiproceso | `multiprocessing.Pool` | `monitor.py` |
| 1 – Multiproceso | Web Workers JS | `stats_worker.js` |
| 2 – Multihilo | `threading.Thread` + `Lock` + `Event` | `monitor.py`, `servidor.py` |
| 3 – Comunicaciones | WebSocket cliente/servidor | `servidor.py`, `app.js` |
| 4 – Servicios en red | REST API Flask | `servidor.py` |
| SQL (Ollama) | SQLite con 3 tablas + índices + ON CONFLICT | `database.py` |

## Mejoras personales

1. Monitorización por núcleo CPU con mini-grid visual
2. Sistema de alertas con umbrales configurables (CPU/RAM/Disco)
3. Ventanas temporales 1h / 6h / 24h / 7d / 30d
4. Limpieza automática de BD en hilo independiente (cada 24h)
5. Top 5 procesos en tiempo real
6. Exportación a CSV del histórico
7. Estadísticas p95 vía Web Worker
8. Tema claro/oscuro con variables CSS
9. Barras de progreso semáforo con animación CSS
10. Toast de notificaciones para alertas
