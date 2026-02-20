# ⚡ SysWatch – Panel de Control del Servidor

## Actividad Final - Segundo Trimestre: Monitorización de Recursos
**Asignatura:** Programación de Servicios y Procesos  
**Curso:** DAM-2

---

## 📋 Descripción del Proyecto

**SysWatch** es un sistema profesional de monitorización de recursos del servidor en tiempo real. Inspirado en el panel de control del servidor de inteligencia artificial trabajado en clase (Ollama), este proyecto extiende y personaliza esa base con:

- **Monitorización multirecurso**: CPU por núcleo, RAM, Disco I/O y Red
- **Base de datos SQLite** con histórico multi-granularidad
- **Dashboard web** con gráficas interactivas (Chart.js)
- **WebSockets** para actualizaciones en tiempo real

---

## 🏗️ Arquitectura del Proyecto

```
📦 101-Ejercicios/
├── main.py                 ← Punto de entrada principal
├── requirements.txt        ← Dependencias Python
├── syswatch.db             ← Base de datos SQLite (generada al arrancar)
│
├── backend/
│   ├── monitor.py          ← Recolección de métricas (threading + multiprocessing)
│   ├── database.py         ← Gestión SQLite (CRUD + consultas históricas)
│   └── servidor.py         ← Flask + Flask-SocketIO (REST API + WebSockets)
│
└── frontend/
    ├── index.html          ← Dashboard principal
    ├── styles.css          ← Tema oscuro / claro (variables CSS)
    ├── app.js              ← Lógica: WebSocket cliente + Chart.js + Web Worker
    └── workers/
        └── stats_worker.js ← Web Worker: estadísticas en segundo plano
```

---

## 🚀 Instalación y Ejecución

### 1. Instalar dependencias

```bash
cd "301-Actividades final de unidad - Segundo trimestre\003-Monitorización de recursos\101-Ejercicios"
pip install -r requirements.txt
```

### 2. Arrancar el servidor

```bash
python main.py
# Opciones:
#   --puerto   5000   (puerto HTTP, default 5000)
#   --intervalo 2     (segundos entre muestras, default 2)
#   --debug           (modo debug Flask)
```

### 3. Abrir el dashboard

Abrir en el navegador: **http://localhost:5000**

---

## 📚 Conceptos de Clase Implementados

### ✅ Unidad 1 – Programación Multiproceso

| Concepto | Implementación |
|---|---|
| `multiprocessing.Pool` | `monitor.py` → `calcular_estadisticas_paralelo()` calcula stats de N métricas en paralelo |
| Procesos paralelos | Pool crea 1 proceso por métrica (CPU, RAM, Disco, Red) |
| Web Workers | `stats_worker.js` ejecuta cálculos estadísticos en proceso paralelo del navegador |

### ✅ Unidad 2 – Programación Multihilo

| Concepto | Implementación |
|---|---|
| `threading.Thread` | `MonitorSistema` hereda de `Thread` → hilo demonio |
| `threading.Lock` | `_lock_callbacks`, `_lock_clientes`, `_lock_ultima` → sincronización |
| `threading.Event` | `_stop_event` → para parada limpia del hilo |
| Callbacks entre hilos | Lista de suscriptores notificada desde el hilo monitor |
| Hilo de limpieza | `_tarea_limpieza_periodica()` → hilo independiente cada 24h |

### ✅ Unidad 3 – Comunicaciones en Red

| Concepto | Implementación |
|---|---|
| WebSocket servidor | `Flask-SocketIO` en `servidor.py` |
| WebSocket cliente | `Socket.IO` en `app.js` |
| Comunicación bidireccional | Eventos: `metrica`, `historico`, `alertas`, `bienvenida` |
| Comunicación simultánea | N clientes conectados a la vez (broadcast) |

### ✅ Unidad 4 – Generación de Servicios en Red

| Concepto | Implementación |
|---|---|
| Servidor HTTP REST | Flask con endpoints `/api/historico`, `/api/alertas`, `/api/estado` |
| Servicio de ficheros estáticos | Flask sirve el frontend completo |
| Protocolo HTTP | GET con parámetros query string |
| CORS | `Flask-CORS` para peticiones cross-origin |

### ✅ Base de Datos SQL (Ejercicios Ollama/blog.sql)

| Concepto | Implementación |
|---|---|
| SQLite | `database.py` → `BaseDatosSysWatch` |
| DDL con `CREATE TABLE` | 3 tablas: `metricas_raw`, `metricas_hora`, `alertas` |
| Índices para rendimiento | `CREATE INDEX` por timestamp |
| `ON CONFLICT DO UPDATE` | Actualización incremental de estadísticas horarias |
| Consultas temporales | `WHERE timestamp >= ?` con ventanas de 1h/6h/24h/7d/30d |
| WAL mode | Mayor concurrencia de lectura/escritura |

---

## ✨ Mejoras Personales sobre el Ejercicio de Clase

El ejercicio de clase monitorizaba específicamente el servidor Ollama (IA). Este proyecto amplía la monitorización a **todos los recursos del sistema** con las siguientes mejoras funcionales:

### Funcionales (código)
1. **Monitorización por núcleo CPU** – grid visual con cada núcleo independiente
2. **Sistema de alertas con umbrales** – detecta y registra cuando CPU/RAM/Disco superan límites
3. **Múltiples ventanas temporales** – 1h / 6h / 24h / 7d / 30d con datos agregados por hora
4. **Limpieza automática de BD** – hilo que elimina datos >30 días cada 24h
5. **Top 5 procesos** – tabla en tiempo real de los procesos que más CPU consumen
6. **Exportación CSV** – descarga el histórico activo en formato CSV
7. **API REST completa** – endpoints para integración con otras herramientas
8. **Estadísticas p95** – percentil 95 calculado por Web Worker (no solo avg/max)

### Estéticas/Visuales
1. **Tema oscuro/claro** – toggle con variables CSS (sin recargar página)
2. **Barras de progreso semáforo** – verde/amarillo/rojo con animación en rojo crítico
3. **Toast de notificaciones** – notificaciones animadas para alertas y eventos
4. **Punto WS parpadeante** – indicador de conexión WebSocket con animación CSS
5. **Grid responsive** – se adapta a cualquier tamaño de pantalla

---

## 🗃️ Esquema de la Base de Datos

```sql
-- Muestras en bruto (~2s de granularidad)
CREATE TABLE metricas_raw (
    id, timestamp, cpu_global, mem_pct, mem_usado_mb,
    disco_pct, disco_lect, disco_escr, red_env, red_recv
);

-- Estadísticas agregadas por hora (para histórico largo)
CREATE TABLE metricas_hora (
    id, hora,
    cpu_avg, cpu_max, mem_avg, mem_max,
    disco_avg, disco_max, red_avg, red_max, muestras
);

-- Registro permanente de alertas
CREATE TABLE alertas (
    id, timestamp, metrica, valor, umbral, severidad, mensaje
);
```

---

## 📡 Endpoints REST

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Dashboard web |
| GET | `/api/historico?ventana=1h` | Datos históricos (1h/6h/24h/7d/30d) |
| GET | `/api/alertas?limite=20` | Alertas recientes |
| GET | `/api/estado` | Info del servidor y BD |
| GET | `/api/mantenimiento/limpiar?dias=30` | Limpieza de datos antiguos |

## 📡 Eventos WebSocket

| Evento | Dirección | Descripción |
|---|---|---|
| `metrica` | Server→Client | Muestra nueva cada 2s |
| `historico` | Server→Client | Respuesta al solicitar histórico |
| `alertas` | Server→Client | Lista de alertas |
| `bienvenida` | Server→Client | Al conectarse |
| `solicitar_historico` | Client→Server | Pedir datos históricos |
| `solicitar_alertas` | Client→Server | Pedir lista de alertas |
