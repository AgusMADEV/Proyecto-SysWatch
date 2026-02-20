# Reporte de proyecto

## Estructura del proyecto

```
C:\xampp\htdocs\GitHub\Proyecto-SysWatch
├── .gitignore
├── README.md
├── backend
│   ├── database.py
│   ├── monitor.py
│   └── servidor.py
├── ejercicio.md
├── frontend
│   ├── app.js
│   ├── index.html
│   ├── styles.css
│   └── workers
│       └── stats_worker.js
├── main.py
└── requirements.txt
```

## Código (intercalado)

# Proyecto-SysWatch
**README.md**
```markdown
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

```
**ejercicio.md**
```markdown
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

```
**main.py**
```python
"""
SysWatch - Monitor de Recursos del Servidor
main.py

Punto de entrada principal de la aplicación.
Arranca el hilo de monitorización y el servidor web.

Uso:
    python main.py [--puerto 5000] [--intervalo 2] [--debug]

Conceptos de clase integrados:
  - Multiproceso  (Unidad 1) → Pool en monitor.py para estadísticas
  - Multihilo     (Unidad 2) → MonitorSistema es un Thread demonio
  - Comunicaciones en red (Unidad 3) → WebSocket vía Flask-SocketIO
  - Servicios en red      (Unidad 4) → Servidor HTTP REST
  - Base de datos SQL     (Ollama/blog.sql) → SQLite en database.py
"""

import sys
import os
import argparse
import signal
import threading

# Añadir backend/ al PATH para importaciones
_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_DIR, "backend"))

from monitor  import MonitorSistema
from servidor import on_nueva_metrica, iniciar as iniciar_servidor, db


# ──────────────────────────────────────────────────────────────────────────
# Evento para limpiar la BD de forma programada (cada 24 h)
# ──────────────────────────────────────────────────────────────────────────

def _tarea_limpieza_periodica(intervalo_horas: int = 24) -> None:
    """
    Función que se ejecuta en un hilo separado y limpia la BD cada N horas,
    eliminando muestras con más de 30 días de antigüedad.
    """
    import time
    while True:
        time.sleep(intervalo_horas * 3600)
        eliminados = db.limpiar_datos_antiguos(dias=30)
        print(f"[Limpieza] {eliminados} filas antiguas eliminadas de la BD.")


# ──────────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SysWatch - Monitor de Recursos")
    parser.add_argument("--puerto",    type=int,   default=5000,  help="Puerto HTTP (default 5000)")
    parser.add_argument("--intervalo", type=float, default=2.0,   help="Segundos entre muestras (default 2)")
    parser.add_argument("--debug",     action="store_true",       help="Modo debug de Flask")
    args = parser.parse_args()

    print("=" * 60)
    print("  SysWatch - Monitor de Recursos del Servidor")
    print("=" * 60)
    print(f"  Puerto    : {args.puerto}")
    print(f"  Intervalo : {args.intervalo}s")
    print(f"  URL       : http://localhost:{args.puerto}")
    print("=" * 60)

    # 1. Hilo demonio de monitorización (Unidad 2 - Multihilo)
    monitor = MonitorSistema(intervalo=args.intervalo)
    monitor.suscribir(on_nueva_metrica)   # Conecta monitor → servidor
    monitor.start()
    print("[Main] Hilo de monitorización iniciado.")

    # 2. Hilo de limpieza periódica de la BD
    hilo_limpieza = threading.Thread(
        target=_tarea_limpieza_periodica,
        args=(24,),
        daemon=True,
        name="LimpiezaBD"
    )
    hilo_limpieza.start()
    print("[Main] Hilo de limpieza de BD iniciado.")

    # 3. Gestión de señal SIGINT (Ctrl+C) para apagado limpio
    def _apagado(sig, frame):
        print("\n[Main] Deteniendo SysWatch...")
        monitor.detener()
        monitor.join(timeout=5)
        print("[Main] Monitor detenido. ¡Hasta pronto!")
        sys.exit(0)

    signal.signal(signal.SIGINT,  _apagado)
    signal.signal(signal.SIGTERM, _apagado)

    # 4. Iniciar servidor Flask-SocketIO (bloquea el hilo principal)
    #    (Unidad 4 - Servicios en red)
    iniciar_servidor(host="0.0.0.0", puerto=args.puerto, debug=args.debug)


if __name__ == "__main__":
    main()

```
## backend
**database.py**
```python
"""
SysWatch - Monitor de Recursos del Servidor
backend/database.py

Gestión completa de la base de datos SQLite.
Almacena el histórico de métricas con múltiples granularidades
y gestiona el registro de alertas.

Conceptos de clase aplicados:
  - Base de datos SQLite  (ejercicios Ollama/blog.sql - Unidad 1)
  - threading.Lock        (Unidad 2 - Sincronización)
  - Consultas SQL avanzadas (agregaciones, filtros por tiempo)
"""
from __future__ import annotations  # Compatibilidad Python 3.9+

import sqlite3
import threading
import os
from datetime import datetime, timedelta
from typing import Optional


# Ruta de la base de datos (junto a este archivo)
_BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(_BASE_DIR, "..", "syswatch.db")


class BaseDatosSysWatch:
    """
    Clase que gestiona todas las operaciones sobre la base de datos SQLite.

    Utiliza un Lock para garantizar que los accesos desde múltiples
    hilos sean seguros (hilo del monitor + hilo del servidor Flask).
    """

    # ────────── DDL - Creación de tablas ──────────

    _SQL_CREAR_TABLAS = """
    -- Métricas en bruto (cada 2 s → ~43 mil filas/día)
    CREATE TABLE IF NOT EXISTS metricas_raw (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp    TEXT    NOT NULL,
        cpu_global   REAL    NOT NULL,
        mem_pct      REAL    NOT NULL,
        mem_usado_mb REAL    NOT NULL,
        disco_pct    REAL    NOT NULL,
        disco_lect   REAL    NOT NULL,  -- MB/s
        disco_escr   REAL    NOT NULL,  -- MB/s
        red_env      REAL    NOT NULL,  -- KB/s
        red_recv     REAL    NOT NULL   -- KB/s
    );

    -- Estadísticas agregadas por hora
    CREATE TABLE IF NOT EXISTS metricas_hora (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        hora         TEXT    NOT NULL UNIQUE,  -- "2024-02-20 14:00"
        cpu_avg      REAL, cpu_max  REAL,
        mem_avg      REAL, mem_max  REAL,
        disco_avg    REAL, disco_max REAL,
        red_avg      REAL, red_max  REAL,
        muestras     INTEGER
    );

    -- Registro de alertas
    CREATE TABLE IF NOT EXISTS alertas (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp  TEXT  NOT NULL,
        metrica    TEXT  NOT NULL,
        valor      REAL  NOT NULL,
        umbral     REAL  NOT NULL,
        severidad  TEXT  NOT NULL,
        mensaje    TEXT  NOT NULL
    );

    -- Índices para consultas rápidas por tiempo
    CREATE INDEX IF NOT EXISTS idx_raw_ts    ON metricas_raw  (timestamp);
    CREATE INDEX IF NOT EXISTS idx_alerta_ts ON alertas        (timestamp);
    """

    def __init__(self, db_path: str = DB_PATH):
        """
        Args:
            db_path: Ruta del archivo .db de SQLite.
        """
        self.db_path = db_path
        self._lock   = threading.Lock()   # Lock para acceso multi-hilo seguro

        # Crear directorio si no existe
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        # Inicializar esquema
        self._ejecutar_ddl()
        print(f"[BaseDatos] Base de datos lista → {self.db_path}")

    # ────────── Utilidades internas ──────────

    def _conectar(self) -> sqlite3.Connection:
        """Abre una conexión fresca a SQLite (thread-safe con Lock externo)."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")   # Mejor concurrencia
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _ejecutar_ddl(self) -> None:
        """Crea las tablas si no existen."""
        with self._lock:
            conn = self._conectar()
            try:
                conn.executescript(self._SQL_CREAR_TABLAS)
                conn.commit()
            finally:
                conn.close()

    # ────────── Inserción de métricas ──────────

    def insertar_metrica(self, metricas: dict) -> None:
        """
        Inserta una muestra nueva en metricas_raw y actualiza
        las estadísticas horarias de forma atómica.

        Args:
            metricas: Diccionario generado por MonitorSistema.
        """
        ts    = metricas["timestamp"]
        cpu   = metricas["cpu"]["global"]
        mem   = metricas["memoria"]["porcentaje"]
        mem_mb= metricas["memoria"]["usado_mb"]
        d_pct = metricas["disco"]["porcentaje"]
        d_lec = metricas["disco"]["lectura_mbs"]
        d_esc = metricas["disco"]["escritura_mbs"]
        r_env = metricas["red"]["enviado_kbs"]
        r_rec = metricas["red"]["recibido_kbs"]

        sql_raw = """
            INSERT INTO metricas_raw
                (timestamp, cpu_global, mem_pct, mem_usado_mb,
                 disco_pct, disco_lect, disco_escr, red_env, red_recv)
            VALUES (?,?,?,?,?,?,?,?,?)
        """

        # Clave de la hora actual → "2024-02-20 14:00"
        hora_key = ts[:13] + ":00"

        sql_hora = """
            INSERT INTO metricas_hora
                (hora, cpu_avg, cpu_max, mem_avg, mem_max,
                 disco_avg, disco_max, red_avg, red_max, muestras)
            VALUES (?, ?,?,?,?,?,?,?,?, 1)
            ON CONFLICT(hora) DO UPDATE SET
                cpu_avg   = (cpu_avg   * muestras + excluded.cpu_avg)   / (muestras + 1),
                cpu_max   = MAX(cpu_max,   excluded.cpu_max),
                mem_avg   = (mem_avg   * muestras + excluded.mem_avg)   / (muestras + 1),
                mem_max   = MAX(mem_max,   excluded.mem_max),
                disco_avg = (disco_avg * muestras + excluded.disco_avg) / (muestras + 1),
                disco_max = MAX(disco_max, excluded.disco_max),
                red_avg   = (red_avg   * muestras + excluded.red_avg)   / (muestras + 1),
                red_max   = MAX(red_max,   excluded.red_max),
                muestras  = muestras + 1
        """

        with self._lock:
            conn = self._conectar()
            try:
                conn.execute(sql_raw, (ts, cpu, mem, mem_mb, d_pct, d_lec, d_esc, r_env, r_rec))
                conn.execute(sql_hora, (hora_key, cpu, cpu, mem, mem, d_pct, d_pct,
                                        (r_env + r_rec), (r_env + r_rec)))
                conn.commit()
            finally:
                conn.close()

    def insertar_alertas(self, alertas: list[dict], timestamp: str) -> None:
        """
        Inserta una lista de alertas en la tabla alertas.

        Args:
            alertas:   Lista de dicts de alertas generada por MonitorSistema.
            timestamp: ISO timestamp de la muestra.
        """
        if not alertas:
            return
        sql = """
            INSERT INTO alertas (timestamp, metrica, valor, umbral, severidad, mensaje)
            VALUES (?,?,?,?,?,?)
        """
        with self._lock:
            conn = self._conectar()
            try:
                for a in alertas:
                    conn.execute(sql, (timestamp, a["metrica"], a["valor"],
                                       a["umbral"], a["severidad"], a["mensaje"]))
                conn.commit()
            finally:
                conn.close()

    # ────────── Consultas: datos en bruto ──────────

    def obtener_ultimos_minutos(self, minutos: int = 60) -> list[dict]:
        """
        Devuelve las muestras en bruto de los últimos N minutos.

        Args:
            minutos: Ventana temporal en minutos.

        Returns:
            Lista de dicts con las columnas de metricas_raw.
        """
        desde = (datetime.now() - timedelta(minutes=minutos)).isoformat(timespec='seconds')
        sql   = """
            SELECT timestamp, cpu_global, mem_pct, mem_usado_mb,
                   disco_pct, disco_lect, disco_escr, red_env, red_recv
            FROM   metricas_raw
            WHERE  timestamp >= ?
            ORDER  BY timestamp ASC
        """
        return self._query(sql, (desde,))

    def obtener_por_horas(self, horas: int = 24) -> list[dict]:
        """
        Devuelve estadísticas agregadas por hora para las últimas N horas.

        Args:
            horas: Número de horas hacia atrás.

        Returns:
            Lista de dicts de metricas_hora.
        """
        desde = (datetime.now() - timedelta(hours=horas)).strftime("%Y-%m-%d %H:00")
        sql   = """
            SELECT hora, cpu_avg, cpu_max, mem_avg, mem_max,
                   disco_avg, disco_max, red_avg, red_max, muestras
            FROM   metricas_hora
            WHERE  hora >= ?
            ORDER  BY hora ASC
        """
        return self._query(sql, (desde,))

    # ────────── Consultas: alertas ──────────

    def obtener_alertas_recientes(self, limite: int = 50) -> list[dict]:
        """
        Devuelve las alertas más recientes.

        Args:
            limite: Número máximo de alertas a retornar.

        Returns:
            Lista de dicts de la tabla alertas.
        """
        sql = """
            SELECT id, timestamp, metrica, valor, umbral, severidad, mensaje
            FROM   alertas
            ORDER  BY timestamp DESC
            LIMIT  ?
        """
        return self._query(sql, (limite,))

    def contar_alertas_hoy(self) -> dict:
        """
        Cuenta las alertas del día de hoy agrupadas por severidad.

        Returns:
            Dict {"advertencia": int, "critica": int}.
        """
        hoy  = datetime.now().strftime("%Y-%m-%d")
        sql  = """
            SELECT severidad, COUNT(*) AS total
            FROM   alertas
            WHERE  timestamp LIKE ?
            GROUP  BY severidad
        """
        rows = self._query(sql, (hoy + "%",))
        resultado = {"advertencia": 0, "critica": 0}
        for r in rows:
            resultado[r["severidad"]] = r["total"]
        return resultado

    # ────────── Mantenimiento ──────────

    def limpiar_datos_antiguos(self, dias: int = 30) -> int:
        """
        Elimina registros raw con más de N días de antigüedad
        para evitar que la base de datos crezca indefinidamente.

        Args:
            dias: Antigüedad máxima en días.

        Returns:
            Número de filas eliminadas.
        """
        limite = (datetime.now() - timedelta(days=dias)).isoformat(timespec='seconds')
        sql    = "DELETE FROM metricas_raw WHERE timestamp < ?"
        with self._lock:
            conn = self._conectar()
            try:
                cur = conn.execute(sql, (limite,))
                conn.commit()
                return cur.rowcount
            finally:
                conn.close()

    def estadisticas_generales(self) -> dict:
        """
        Retorna información general sobre el contenido de la BD.

        Returns:
            Dict con totales de filas por tabla y tamaño en MB.
        """
        sql_counts = """
            SELECT
              (SELECT COUNT(*) FROM metricas_raw)  AS raw,
              (SELECT COUNT(*) FROM metricas_hora) AS horas,
              (SELECT COUNT(*) FROM alertas)       AS alertas
        """
        rows = self._query(sql_counts, ())
        info = dict(rows[0]) if rows else {}
        try:
            info["tamaño_mb"] = round(os.path.getsize(self.db_path) / 1024**2, 3)
        except OSError:
            info["tamaño_mb"] = 0
        return info

    # ────────── Helper genérico ──────────

    def _query(self, sql: str, params: tuple) -> list[dict]:
        """
        Ejecuta una consulta SELECT y devuelve lista de dicts.
        Hilo-seguro gracias al Lock de clase.
        """
        with self._lock:
            conn = self._conectar()
            try:
                cur  = conn.execute(sql, params)
                rows = cur.fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

```
**monitor.py**
```python
"""
SysWatch - Monitor de Recursos del Servidor
backend/monitor.py

Módulo de recolección de métricas del sistema en tiempo real.
Utiliza psutil para leer CPU, RAM, Disco y Red.
Emplea threading para recolección periódica en segundo plano y
multiprocessing para el cálculo pesado de estadísticas agregadas.

Conceptos de clase aplicados:
  - threading.Thread  (Unidad 2 - Programación multihilo)
  - threading.Lock    (Unidad 2 - Sincronización de hilos)
  - multiprocessing.Pool  (Unidad 1 - Programación paralela)
  - Callbacks entre hilos  (Unidad 2 - Compartición de información)
"""
from __future__ import annotations  # Compatibilidad Python 3.9+

import threading
import time
import psutil
from multiprocessing import Pool
from datetime import datetime


# ──────────────────────────────────────────────────
# Funciones de cálculo estadístico (se ejecutan en
# procesos separados via multiprocessing.Pool)
# ──────────────────────────────────────────────────

def _calcular_estadisticas_chunk(valores: list[float]) -> dict:
    """
    Calcula estadísticas básicas de una lista de valores.
    Se ejecuta en un proceso hijo independiente (multiprocessing).

    Args:
        valores: Lista de valores numéricos.

    Returns:
        Diccionario con min, max, avg y p95.
    """
    if not valores:
        return {"min": 0, "max": 0, "avg": 0, "p95": 0}

    ordenados = sorted(valores)
    n = len(ordenados)
    idx_p95 = int(n * 0.95)

    return {
        "min": round(min(ordenados), 2),
        "max": round(max(ordenados), 2),
        "avg": round(sum(ordenados) / n, 2),
        "p95": round(ordenados[min(idx_p95, n - 1)], 2),
    }


def calcular_estadisticas_paralelo(datos: dict[str, list[float]]) -> dict:
    """
    Calcula estadísticas de múltiples métricas en paralelo usando
    un pool de procesos (multiprocessing.Pool).

    Args:
        datos: Diccionario {nombre_metrica: [lista de valores]}.

    Returns:
        Diccionario {nombre_metrica: {min, max, avg, p95}}.
    """
    claves = list(datos.keys())
    listas  = [datos[k] for k in claves]

    # Pool crea N procesos (uno por métrica) para calcular en paralelo
    with Pool(processes=min(len(claves), 4)) as pool:
        resultados = pool.map(_calcular_estadisticas_chunk, listas)

    return dict(zip(claves, resultados))


# ──────────────────────────────────────────────────
# Clase principal del monitor (hilo de fondo)
# ──────────────────────────────────────────────────

class MonitorSistema(threading.Thread):
    """
    Hilo demonio que recoge métricas del sistema de forma periódica.

    Cada `intervalo` segundos captura:
      - CPU global y por núcleo
      - Memoria RAM
      - Disco (lectura/escritura en MB/s)
      - Red (enviado/recibido en KB/s)
      - Top 5 procesos por CPU

    Notifica a los suscriptores mediante callbacks y puede emitir
    alertas cuando se superan los umbrales configurados.
    """

    # Umbrales de alerta por defecto (porcentaje / MB/s)
    UMBRALES_DEFAULT = {
        "cpu":     85.0,   # % de CPU
        "memoria": 90.0,   # % de RAM
        "disco":   95.0,   # % de uso del disco
        "red":    100.0,   # MB/s combinado (sent+recv)
    }

    def __init__(self, intervalo: float = 2.0, umbrales: dict | None = None):
        """
        Args:
            intervalo: Segundos entre cada muestra.
            umbrales: Diccionario opcional para sobreescribir los umbrales.
        """
        super().__init__(daemon=True, name="MonitorSistema")
        self.intervalo  = intervalo
        self.umbrales   = {**self.UMBRALES_DEFAULT, **(umbrales or {})}

        # Lista de callbacks para distribuir métricas
        self._callbacks: list = []
        self._lock_callbacks = threading.Lock()

        # Señal de parada
        self._stop_event = threading.Event()

        # Valores previos para calcular tasas de I/O
        self._io_disco_prev  = psutil.disk_io_counters()
        self._io_red_prev    = psutil.net_io_counters()
        self._tiempo_prev    = time.time()

    # ── Suscripción/desuscripción de callbacks ──

    def suscribir(self, callback) -> None:
        """Añade una función callback que recibirá cada muestra nueva."""
        with self._lock_callbacks:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def desuscribir(self, callback) -> None:
        """Elimina un callback registrado."""
        with self._lock_callbacks:
            self._callbacks.discard(callback) if hasattr(self._callbacks, 'discard') \
                else (self._callbacks.remove(callback) if callback in self._callbacks else None)

    def detener(self) -> None:
        """Señaliza el hilo para que se detenga limpiamente."""
        self._stop_event.set()

    # ── Lectura de métricas ──

    def _leer_cpu(self) -> dict:
        """Lee uso de CPU global y por núcleo."""
        global_pct  = psutil.cpu_percent(interval=None)
        por_nucleo  = psutil.cpu_percent(interval=None, percpu=True)
        freq = psutil.cpu_freq()
        return {
            "global":    round(global_pct, 1),
            "por_nucleo": [round(v, 1) for v in por_nucleo],
            "nucleos":    psutil.cpu_count(logical=True),
            "frecuencia_mhz": round(freq.current, 0) if freq else 0,
        }

    def _leer_memoria(self) -> dict:
        """Lee uso de memoria RAM y swap."""
        mem  = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "total_mb":  round(mem.total  / 1024**2, 1),
            "usado_mb":  round(mem.used   / 1024**2, 1),
            "libre_mb":  round(mem.available / 1024**2, 1),
            "porcentaje": mem.percent,
            "swap_total_mb": round(swap.total / 1024**2, 1),
            "swap_usado_mb": round(swap.used  / 1024**2, 1),
            "swap_pct":  swap.percent,
        }

    def _leer_disco(self, dt: float) -> dict:
        """Lee tasas de lectura/escritura en disco."""
        io = psutil.disk_io_counters()
        part = psutil.disk_usage('/')

        read_mb  = 0.0
        write_mb = 0.0
        if self._io_disco_prev and dt > 0:
            read_mb  = (io.read_bytes  - self._io_disco_prev.read_bytes)  / 1024**2 / dt
            write_mb = (io.write_bytes - self._io_disco_prev.write_bytes) / 1024**2 / dt

        self._io_disco_prev = io
        return {
            "lectura_mbs":   round(max(0.0, read_mb),  3),
            "escritura_mbs": round(max(0.0, write_mb), 3),
            "total_gb":  round(part.total / 1024**3, 1),
            "usado_gb":  round(part.used  / 1024**3, 1),
            "libre_gb":  round(part.free  / 1024**3, 1),
            "porcentaje": part.percent,
        }

    def _leer_red(self, dt: float) -> dict:
        """Lee tasas de tráfico de red."""
        io = psutil.net_io_counters()

        sent_kbs = 0.0
        recv_kbs = 0.0
        if self._io_red_prev and dt > 0:
            sent_kbs = (io.bytes_sent - self._io_red_prev.bytes_sent) / 1024 / dt
            recv_kbs = (io.bytes_recv - self._io_red_prev.bytes_recv) / 1024 / dt

        self._io_red_prev = io
        return {
            "enviado_kbs":   round(max(0.0, sent_kbs), 2),
            "recibido_kbs":  round(max(0.0, recv_kbs), 2),
            "total_enviado_mb":  round(io.bytes_sent / 1024**2, 1),
            "total_recibido_mb": round(io.bytes_recv / 1024**2, 1),
            "paquetes_enviados":  io.packets_sent,
            "paquetes_recibidos": io.packets_recv,
        }

    def _leer_procesos_top(self, n: int = 5) -> list[dict]:
        """Retorna los N procesos que más CPU consumen."""
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        # Ordenar por CPU descendente
        procs.sort(key=lambda x: x.get('cpu_percent') or 0, reverse=True)
        return procs[:n]

    def _detectar_alertas(self, metricas: dict) -> list[dict]:
        """
        Compara métricas con umbrales y genera lista de alertas.

        Returns:
            Lista de dicts {metrica, valor, umbral, severidad}.
        """
        alertas = []

        cpu_val = metricas["cpu"]["global"]
        if cpu_val >= self.umbrales["cpu"]:
            alertas.append({
                "metrica":   "CPU",
                "valor":     cpu_val,
                "umbral":    self.umbrales["cpu"],
                "severidad": "critica" if cpu_val >= 95 else "advertencia",
                "mensaje":   f"CPU al {cpu_val}%",
            })

        mem_val = metricas["memoria"]["porcentaje"]
        if mem_val >= self.umbrales["memoria"]:
            alertas.append({
                "metrica":   "Memoria",
                "valor":     mem_val,
                "umbral":    self.umbrales["memoria"],
                "severidad": "critica" if mem_val >= 95 else "advertencia",
                "mensaje":   f"RAM al {mem_val}%",
            })

        disco_val = metricas["disco"]["porcentaje"]
        if disco_val >= self.umbrales["disco"]:
            alertas.append({
                "metrica":   "Disco",
                "valor":     disco_val,
                "umbral":    self.umbrales["disco"],
                "severidad": "critica" if disco_val >= 99 else "advertencia",
                "mensaje":   f"Disco lleno al {disco_val}%",
            })

        return alertas

    # ── Bucle principal del hilo ──

    def run(self) -> None:
        """Bucle de recolección. Se ejecuta en el hilo secundario."""

        # Primera lectura para inicializar contadores de I/O
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)
        time.sleep(0.5)

        while not self._stop_event.is_set():
            inicio = time.time()

            # Calcular delta de tiempo desde última muestra
            dt = inicio - self._tiempo_prev
            self._tiempo_prev = inicio

            # Leer todas las métricas
            metricas = {
                "timestamp": datetime.now().isoformat(timespec='seconds'),
                "cpu":       self._leer_cpu(),
                "memoria":   self._leer_memoria(),
                "disco":     self._leer_disco(dt),
                "red":       self._leer_red(dt),
                "procesos":  self._leer_procesos_top(),
                "alertas":   [],
            }
            metricas["alertas"] = self._detectar_alertas(metricas)

            # Notificar a todos los callbacks (hilo seguro)
            with self._lock_callbacks:
                callbacks_actuales = list(self._callbacks)

            for cb in callbacks_actuales:
                try:
                    cb(metricas)
                except Exception as e:
                    print(f"[MonitorSistema] Error en callback: {e}")

            # Dormir el tiempo restante del intervalo
            elapsed = time.time() - inicio
            sleep_time = max(0.0, self.intervalo - elapsed)
            self._stop_event.wait(timeout=sleep_time)

        print("[MonitorSistema] Hilo detenido correctamente.")

```
**servidor.py**
```python
"""
SysWatch - Monitor de Recursos del Servidor
backend/servidor.py

Servidor Flask + Flask-SocketIO.
  - WebSocket: emite métricas en tiempo real a los clientes.
  - REST API:  devuelve histórico, alertas y estadísticas.
  - Sirve los ficheros estáticos del frontend.

Conceptos de clase aplicados:
  - WebSockets bidireccionales        (Unidad 3 - Comunicaciones en red)
  - Servidor HTTP con Flask            (Unidad 4 - Servicios en red)
  - Comunicación simultánea con hilos  (Unidad 3 - Sección 009)
  - Flask-SocketIO (equivalente a websockets del ejercicio clase)
"""
from __future__ import annotations  # Compatibilidad Python 3.9+

import os
import json
import threading
from flask import Flask, jsonify, send_from_directory, request
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS

from database import BaseDatosSysWatch


# ────────── Configuración ──────────────────────────────────────────────────

_BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
_FRONTEND    = os.path.join(_BASE_DIR, "..", "frontend")
DB_PATH      = os.path.join(_BASE_DIR, "..", "syswatch.db")

app        = Flask(__name__, static_folder=_FRONTEND)
CORS(app)                                        # Permite peticiones cross-origin
socketio   = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Base de datos compartida (thread-safe internamente)
db = BaseDatosSysWatch(DB_PATH)

# Contador de clientes conectados (protegido con Lock)
_clientes_conectados = 0
_lock_clientes       = threading.Lock()

# Última métrica recibida (para nuevos clientes)
_ultima_metrica: dict | None = None
_lock_ultima            = threading.Lock()


# ────────── Callback del monitor → envía por WebSocket ────────────────────

def on_nueva_metrica(metricas: dict) -> None:
    """
    Callback invocado por MonitorSistema en cada muestra.
    1. Persiste en la base de datos.
    2. Guarda y persiste alertas si las hay.
    3. Emite el evento 'metrica' a todos los clientes Socket.IO.
    """
    global _ultima_metrica

    # 1. Guardar en BD
    db.insertar_metrica(metricas)

    # 2. Guardar alertas
    if metricas.get("alertas"):
        db.insertar_alertas(metricas["alertas"], metricas["timestamp"])

    # 3. Actualizar caché de última métrica
    with _lock_ultima:
        _ultima_metrica = metricas

    # 4. Emitir a todos los clientes conectados por WebSocket
    with _lock_clientes:
        hay_clientes = _clientes_conectados > 0

    if hay_clientes:
        # Eliminar lista de procesos (puede ser grande) antes de enviar
        payload = {k: v for k, v in metricas.items() if k != "procesos"}
        payload["procesos"] = metricas["procesos"][:5]   # Solo top 5
        socketio.emit("metrica", payload)


# ────────── Eventos WebSocket ──────────────────────────────────────────────

@socketio.on("connect")
def ws_conectar():
    """Cliente se conecta por WebSocket."""
    global _clientes_conectados
    with _lock_clientes:
        _clientes_conectados += 1
        total = _clientes_conectados

    print(f"[WS] Cliente conectado. Total: {total}")

    # Enviar la última métrica disponible para que el panel no aparezca vacío
    with _lock_ultima:
        ultima = _ultima_metrica

    if ultima:
        emit("metrica", {k: v for k, v in ultima.items() if k != "procesos"} |
             {"procesos": ultima["procesos"][:5]})

    emit("bienvenida", {
        "mensaje": "Conectado a SysWatch",
        "clientes": total,
        "version": "1.0.0",
    })


@socketio.on("disconnect")
def ws_desconectar():
    """Cliente se desconecta."""
    global _clientes_conectados
    with _lock_clientes:
        _clientes_conectados = max(0, _clientes_conectados - 1)
    print(f"[WS] Cliente desconectado. Total: {_clientes_conectados}")


@socketio.on("solicitar_historico")
def ws_solicitar_historico(data: dict):
    """
    El cliente solicita datos históricos especificando ventana temporal.

    Payload esperado: { "ventana": "1h" | "6h" | "24h" | "7d" | "30d" }
    """
    ventana = data.get("ventana", "1h")
    filas   = _obtener_historico_por_ventana(ventana)
    emit("historico", {"ventana": ventana, "datos": filas})


@socketio.on("solicitar_alertas")
def ws_solicitar_alertas(data: dict):
    """El cliente solicita las alertas más recientes."""
    limite  = int(data.get("limite", 20))
    alertas = db.obtener_alertas_recientes(limite)
    emit("alertas", {"datos": alertas})


# ────────── REST API ──────────────────────────────────────────────────────

@app.route("/api/historico")
def api_historico():
    """
    GET /api/historico?ventana=6h
    Devuelve datos históricos según la ventana temporal solicitada.
    """
    ventana = request.args.get("ventana", "1h")
    filas   = _obtener_historico_por_ventana(ventana)
    return jsonify({"ventana": ventana, "total": len(filas), "datos": filas})


@app.route("/api/alertas")
def api_alertas():
    """
    GET /api/alertas?limite=20
    Devuelve las alertas más recientes.
    """
    limite  = int(request.args.get("limite", 20))
    alertas = db.obtener_alertas_recientes(limite)
    resumen = db.contar_alertas_hoy()
    return jsonify({"resumen_hoy": resumen, "datos": alertas})


@app.route("/api/estado")
def api_estado():
    """
    GET /api/estado
    Información general del servidor y base de datos.
    """
    stats = db.estadisticas_generales()
    with _lock_clientes:
        clientes = _clientes_conectados
    with _lock_ultima:
        ultima = _ultima_metrica

    return jsonify({
        "clientes_ws": clientes,
        "base_datos":  stats,
        "ultima_muestra": ultima["timestamp"] if ultima else None,
        "version": "1.0.0",
    })


@app.route("/api/mantenimiento/limpiar")
def api_limpiar():
    """
    GET /api/mantenimiento/limpiar?dias=30
    Elimina datos más antiguos de N días.
    """
    dias      = int(request.args.get("dias", 30))
    eliminados = db.limpiar_datos_antiguos(dias)
    return jsonify({"eliminados": eliminados, "dias": dias})


# ────────── Servir frontend estático ─────────────────────────────────────

@app.route("/")
def index():
    """Sirve el dashboard principal."""
    return send_from_directory(_FRONTEND, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    """Sirve cualquier fichero estático del frontend."""
    return send_from_directory(_FRONTEND, filename)


# ────────── Helper ────────────────────────────────────────────────────────

def _obtener_historico_por_ventana(ventana: str) -> list[dict]:
    """
    Traduce la clave de ventana a la consulta correspondiente.

    - "1h"  → últimos  60 minutos (datos raw)
    - "6h"  → últimas   6 horas   (datos raw)
    - "24h" → últimas  24 horas   (agregados por hora)
    - "7d"  → últimos   7 días    (agregados por hora)
    - "30d" → últimos  30 días    (agregados por hora)
    """
    if ventana == "1h":
        return db.obtener_ultimos_minutos(60)
    elif ventana == "6h":
        return db.obtener_ultimos_minutos(360)
    elif ventana == "24h":
        return db.obtener_por_horas(24)
    elif ventana == "7d":
        return db.obtener_por_horas(24 * 7)
    elif ventana == "30d":
        return db.obtener_por_horas(24 * 30)
    else:
        return db.obtener_ultimos_minutos(60)


# ────────── Arranque ──────────────────────────────────────────────────────

def iniciar(host: str = "0.0.0.0", puerto: int = 5000, debug: bool = False):
    """
    Inicia el servidor Flask-SocketIO.

    Args:
        host:   Dirección de escucha.
        puerto: Puerto TCP.
        debug:  Modo debug de Flask.
    """
    print(f"[Servidor] SysWatch escuchando en http://{host}:{puerto}")
    socketio.run(app, host=host, port=puerto, debug=debug, use_reloader=False)

```
## frontend
**app.js**
```js
/**
 * SysWatch - Monitor de Recursos del Servidor
 * frontend/app.js
 *
 * Lógica principal del dashboard:
 *   - Conexión WebSocket (Socket.IO) con el backend
 *   - Actualización en tiempo real de tarjetas y gráficas (Chart.js)
 *   - Peticiones REST para histórico y alertas
 *   - Delegación de cálculos pesados al Web Worker
 *   - Tema claro/oscuro
 *   - Exportación a CSV
 *
 * Conceptos de clase:
 *   - WebSocket cliente (Unidad 3 - Comunicaciones en red)
 *   - Web Worker       (Unidad 1 - Actividad Final EVAL)
 */

"use strict";

// ══════════════════════════════════════════════════════
// CONFIGURACIÓN
// ══════════════════════════════════════════════════════
const CONFIG = {
  socketUrl:       window.location.origin,
  maxPuntosLineales: 60,          // Puntos en gráficas en tiempo real
  ventanaDefault:  "1h",
  alertaMaxLista:  30,
};

// ══════════════════════════════════════════════════════
// ESTADO GLOBAL
// ══════════════════════════════════════════════════════
const estado = {
  conectado:      false,
  ventana:        CONFIG.ventanaDefault,
  ultimaMetrica:  null,
  historico:      [],            // Datos históricos actuales
  datos_rt: {                    // Buffers en tiempo real
    labels:  [],
    cpu:     [],
    mem:     [],
    discoLec:[],
    discoEsc:[],
    redEnv:  [],
    redRec:  [],
  },
  temaOscuro: true,
};

// ══════════════════════════════════════════════════════
// WEB WORKER (estadísticas en segundo plano)
// ══════════════════════════════════════════════════════
let worker       = null;
let workerIdSeq  = 0;
const workerCbs  = {};    // id → { resolve, reject }

function iniciarWorker() {
  try {
    worker = new Worker("workers/stats_worker.js");
    worker.onmessage = (e) => {
      const { tipo, id, resultado, mensaje } = e.data;
      if (workerCbs[id]) {
        if (tipo === "error") workerCbs[id].reject(new Error(mensaje));
        else                  workerCbs[id].resolve({ tipo, resultado });
        delete workerCbs[id];
      }
    };
    worker.onerror = (e) => console.error("[Worker] Error:", e.message);
    console.log("[Worker] Web Worker iniciado.");
  } catch (e) {
    console.warn("[Worker] No disponible:", e.message);
  }
}

function workerLlamar(tipo, payload) {
  return new Promise((resolve, reject) => {
    if (!worker) { resolve({}); return; }
    const id = ++workerIdSeq;
    workerCbs[id] = { resolve, reject };
    worker.postMessage({ tipo, payload, id });
    // Timeout de seguridad: 10 s
    setTimeout(() => {
      if (workerCbs[id]) {
        delete workerCbs[id];
        reject(new Error("Timeout Worker"));
      }
    }, 10000);
  });
}

// ══════════════════════════════════════════════════════
// WEBSOCKET (Socket.IO)
// ══════════════════════════════════════════════════════
let socket = null;

function conectarWebSocket() {
  socket = io(CONFIG.socketUrl, { transports: ["websocket", "polling"] });

  socket.on("connect", () => {
    estado.conectado = true;
    actualizarEstadoConexion(true);
    console.log("[WS] Conectado.");
    // Solicitar histórico al conectar
    socket.emit("solicitar_historico", { ventana: estado.ventana });
    socket.emit("solicitar_alertas",   { limite: CONFIG.alertaMaxLista });
  });

  socket.on("disconnect", () => {
    estado.conectado = false;
    actualizarEstadoConexion(false);
    console.warn("[WS] Desconectado.");
  });

  socket.on("bienvenida", (data) => {
    mostrarToast(`${data.mensaje} · v${data.version}`, "info");
  });

  socket.on("metrica", (m) => {
    estado.ultimaMetrica = m;
    actualizarTarjetas(m);
    agregarPuntoRT(m);
    if (m.alertas && m.alertas.length > 0) {
      procesarAlertasNuevas(m.alertas, m.timestamp);
    }
  });

  socket.on("historico", (data) => {
    estado.historico = data.datos;
    renderizarGraficasHistoricas(data.datos, data.ventana);
    // Delegar cálculo de estadísticas resumen al Web Worker
    workerLlamar("procesar_historico", { datos: data.datos })
      .then(({ resultado }) => resultado && actualizarResumenStats(resultado))
      .catch(console.warn);
  });

  socket.on("alertas", (data) => {
    renderizarListaAlertas(data.datos);
  });
}

// ══════════════════════════════════════════════════════
// GRÁFICAS (Chart.js)
// ══════════════════════════════════════════════════════
const charts = {};

function colorMetrica(metrica) {
  const mapa = {
    cpu:     "#4ade80",    // verde
    mem:     "#60a5fa",    // azul
    disco:   "#f97316",    // naranja
    red:     "#c084fc",    // violeta
    discoLec:"#f97316",
    discoEsc:"#fb923c",
    redEnv:  "#c084fc",
    redRec:  "#e879f9",
  };
  return mapa[metrica] || "#94a3b8";
}

function crearGraficaLinea(canvasId, etiquetas, datos_series, titulo) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  if (charts[canvasId]) charts[canvasId].destroy();

  const datasets = datos_series.map(s => ({
    label:       s.label,
    data:        s.datos,
    borderColor: colorMetrica(s.clave),
    backgroundColor: colorMetrica(s.clave) + "20",
    borderWidth: 2,
    pointRadius: etiquetas.length > 100 ? 0 : 2,
    tension:     0.3,
    fill:        s.fill ?? false,
  }));

  charts[canvasId] = new Chart(ctx, {
    type: "line",
    data: { labels: etiquetas, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation:  { duration: 200 },
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend:  { labels: { color: "#94a3b8", font: { size: 11 } } },
        title:   { display: !!titulo, text: titulo, color: "#e2e8f0" },
        tooltip: { backgroundColor: "#1e293b", titleColor: "#e2e8f0", bodyColor: "#94a3b8" },
      },
      scales: {
        x: {
          ticks:  { color: "#64748b", maxTicksLimit: 8, maxRotation: 0 },
          grid:   { color: "#1e293b" },
        },
        y: {
          min:    0,
          ticks:  { color: "#64748b" },
          grid:   { color: "#1e293b" },
        },
      },
    },
  });
  return charts[canvasId];
}

// ── Gráficas en tiempo real ────────────────────────────────────────────

function iniciarGraficasRT() {
  crearGraficaLinea("chart-cpu-rt", [], [
    { label: "CPU %",  clave: "cpu",  datos: [], fill: true }
  ]);
  crearGraficaLinea("chart-mem-rt", [], [
    { label: "RAM %",  clave: "mem",  datos: [], fill: true }
  ]);
  crearGraficaLinea("chart-disco-rt", [], [
    { label: "Lectura MB/s",   clave: "discoLec", datos: [] },
    { label: "Escritura MB/s", clave: "discoEsc", datos: [] },
  ]);
  crearGraficaLinea("chart-red-rt", [], [
    { label: "Enviado KB/s",   clave: "redEnv", datos: [] },
    { label: "Recibido KB/s",  clave: "redRec", datos: [] },
  ]);
}

function agregarPuntoRT(m) {
  const ts   = m.timestamp ? m.timestamp.slice(11, 19) : "--:--:--";
  const d    = estado.datos_rt;
  const MAX  = CONFIG.maxPuntosLineales;

  const push = (arr, val) => { arr.push(val); if (arr.length > MAX) arr.shift(); };

  push(d.labels,   ts);
  push(d.cpu,      m.cpu?.global        ?? 0);
  push(d.mem,      m.memoria?.porcentaje ?? 0);
  push(d.discoLec, m.disco?.lectura_mbs  ?? 0);
  push(d.discoEsc, m.disco?.escritura_mbs ?? 0);
  push(d.redEnv,   m.red?.enviado_kbs   ?? 0);
  push(d.redRec,   m.red?.recibido_kbs  ?? 0);

  // Actualizar datasets sin recrear la gráfica (más eficiente)
  const update = (id, ...series) => {
    const c = charts[id];
    if (!c) return;
    c.data.labels = [...d.labels];
    series.forEach((s, i) => { c.data.datasets[i].data = [...s]; });
    c.update("none");   // sin animación para tiempo real
  };

  update("chart-cpu-rt",   d.cpu);
  update("chart-mem-rt",   d.mem);
  update("chart-disco-rt", d.discoLec, d.discoEsc);
  update("chart-red-rt",   d.redEnv,   d.redRec);
}

// ── Gráficas históricas ───────────────────────────────────────────────

function renderizarGraficasHistoricas(datos, ventana) {
  if (!datos || datos.length === 0) return;

  // Determinar si son datos raw o agregados por hora
  const esRaw = "cpu_global" in (datos[0] || {});
  const labels = datos.map(d => {
    const ts = d.timestamp || d.hora || "";
    // Para ventanas largas, mostrar solo fecha+hora
    return ventana === "1h" ? ts.slice(11, 19) : ts.slice(5, 16).replace("T", " ");
  });
  const cpuArr   = datos.map(d => esRaw ? d.cpu_global    : d.cpu_avg);
  const memArr   = datos.map(d => esRaw ? d.mem_pct       : d.mem_avg);
  const discoArr = datos.map(d => esRaw ? d.disco_pct     : d.disco_avg);
  const redArr   = datos.map(d => esRaw
    ? (d.red_env || 0) + (d.red_recv || 0)
    : d.red_avg || 0);

  crearGraficaLinea("chart-hist-cpu", labels,
    [{ label: "CPU %",   clave: "cpu",   datos: cpuArr,   fill: true }]);
  crearGraficaLinea("chart-hist-mem", labels,
    [{ label: "RAM %",   clave: "mem",   datos: memArr,   fill: true }]);
  crearGraficaLinea("chart-hist-disco", labels,
    [{ label: "Disco %", clave: "disco", datos: discoArr, fill: false }]);
  crearGraficaLinea("chart-hist-red", labels,
    [{ label: "Red KB/s total", clave: "red", datos: redArr, fill: false }]);
}

// ══════════════════════════════════════════════════════
// TARJETAS DE MÉTRICAS (tiempo real)
// ══════════════════════════════════════════════════════

function actualizarTarjetas(m) {
  // CPU
  setVal("val-cpu-global",   m.cpu?.global ?? 0, "%");
  setVal("val-cpu-nucleos",  m.cpu?.nucleos ?? "--");
  setVal("val-cpu-freq",     m.cpu?.frecuencia_mhz ?? "--", " MHz");
  setBar("bar-cpu",          m.cpu?.global ?? 0);
  colorearBarra("bar-cpu",   m.cpu?.global ?? 0, "green");
  renderizarNucleos(m.cpu?.por_nucleo ?? []);

  // Memoria
  setVal("val-mem-pct",    m.memoria?.porcentaje ?? 0, "%");
  setVal("val-mem-usado",  m.memoria?.usado_mb   ?? 0, " MB");
  setVal("val-mem-total",  m.memoria?.total_mb   ?? 0, " MB");
  setBar("bar-mem",        m.memoria?.porcentaje ?? 0);
  colorearBarra("bar-mem", m.memoria?.porcentaje ?? 0, "blue");

  setVal("val-swap-pct",   m.memoria?.swap_pct     ?? 0, "%");
  setVal("val-swap-usado", m.memoria?.swap_usado_mb ?? 0, " MB");

  // Disco
  setVal("val-disco-pct",    m.disco?.porcentaje    ?? 0, "%");
  setVal("val-disco-lec",    m.disco?.lectura_mbs   ?? 0, " MB/s");
  setVal("val-disco-esc",    m.disco?.escritura_mbs ?? 0, " MB/s");
  setVal("val-disco-libre",  m.disco?.libre_gb      ?? 0, " GB");
  setBar("bar-disco",        m.disco?.porcentaje    ?? 0);
  colorearBarra("bar-disco", m.disco?.porcentaje    ?? 0, "orange");

  // Gauges SVG
  if (typeof setGauge === "function") {
    setGauge("gauge-cpu",   m.cpu?.global         ?? 0);
    setGauge("gauge-mem",   m.memoria?.porcentaje  ?? 0);
    setGauge("gauge-disco", m.disco?.porcentaje    ?? 0);
  }
  // Tags de estado
  if (typeof setTag === "function") {
    setTag("tag-cpu",   m.cpu?.global         ?? 0);
    setTag("tag-mem",   m.memoria?.porcentaje  ?? 0);
    setTag("tag-disco", m.disco?.porcentaje    ?? 0);
    setTag("tag-red",   0); // red no tiene umbral porcentual
  }

  // Red
  setVal("val-red-env",   m.red?.enviado_kbs  ?? 0, " KB/s");
  setVal("val-red-rec",   m.red?.recibido_kbs ?? 0, " KB/s");
  setVal("val-red-pkt-e", m.red?.paquetes_enviados  ?? 0);
  setVal("val-red-pkt-r", m.red?.paquetes_recibidos ?? 0);

  // Timestamp (ignorado en la nueva UI — no hay elemento)
  // setVal("val-timestamp", ...);

  // Procesos top
  if (typeof renderizarProcesosPanel === "function") {
    renderizarProcesosPanel(m.procesos ?? []);
  } else {
    renderizarProcesos(m.procesos ?? []);
  }
}

function setVal(id, val, sufijo = "") {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = (typeof val === "number" ? val.toLocaleString("es-ES") : val) + sufijo;
}

function setBar(id, pct) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.width = `${Math.min(100, Math.max(0, pct))}%`;
}

function colorearBarra(id, pct, colorBase = "green") {
  const el = document.getElementById(id);
  if (!el) return;
  // En la nueva UI, la barra cambia a naranja/rojo según umbral
  const color = pct >= 85 ? "red" : pct >= 60 ? "orange" : colorBase;
  el.className = "kpi-bar " + color;
}

function renderizarNucleos(nucleos) {
  const contenedor = document.getElementById("nucleos-grid");
  if (!contenedor) return;
  contenedor.innerHTML = nucleos.map((pct, i) => {
    const color = pct >= 85 ? "#f87171" : pct >= 60 ? "#fb923c" : "#22d3a0";
    return `<div style="display:flex;flex-direction:column;align-items:center;gap:3px;min-width:44px">
      <span style="font-size:.65rem;color:var(--text-muted);font-family:monospace">C${i}</span>
      <div style="width:36px;height:5px;background:var(--border);border-radius:99px;overflow:hidden">
        <div style="height:100%;width:${Math.min(pct,100)}%;background:${color};border-radius:99px;transition:width .4s"></div>
      </div>
      <span style="font-size:.7rem;font-weight:600;font-family:monospace;color:${color}">${pct}%</span>
    </div>`;
  }).join("");
}

function renderizarProcesos(procs) {
  const tbody = document.getElementById("procesos-tbody");
  if (!tbody) return;
  tbody.innerHTML = procs.map(p => `
    <tr>
      <td>${p.pid ?? "--"}</td>
      <td class="proc-name" title="${p.name ?? ""}">${p.name ?? "--"}</td>
      <td>${(p.cpu_percent ?? 0).toFixed(1)}%</td>
      <td>${(p.memory_percent ?? 0).toFixed(1)}%</td>
    </tr>`).join("");
}

// ══════════════════════════════════════════════════════
// RESUMEN ESTADÍSTICO (Web Worker)
// ══════════════════════════════════════════════════════

function actualizarResumenStats(stats) {
  // CPU
  setVal("stat-cpu-avg",  stats.cpu?.avg  ?? 0, "%");
  setVal("stat-cpu-max",  stats.cpu?.max  ?? 0, "%");
  setVal("stat-cpu-p95",  stats.cpu?.p95  ?? 0, "%");
  // Mem
  setVal("stat-mem-avg",  stats.mem?.avg  ?? 0, "%");
  setVal("stat-mem-max",  stats.mem?.max  ?? 0, "%");
  setVal("stat-mem-p95",  stats.mem?.p95  ?? 0, "%");
  // Num muestras
  setVal("stat-muestras", stats.muestras  ?? 0);
}

// ══════════════════════════════════════════════════════
// ALERTAS
// ══════════════════════════════════════════════════════

function procesarAlertasNuevas(alertas, ts) {
  alertas.forEach(a => {
    mostrarToast(`⚠️ ${a.mensaje}`, a.severidad === "critica" ? "error" : "warn");
  });
  // Refrescar lista de alertas completa
  socket?.emit("solicitar_alertas", { limite: CONFIG.alertaMaxLista });
}

function renderizarListaAlertas(alertas) {
  const lista = document.getElementById("alertas-lista");
  if (!lista) return;

  // Actualizar contadores (panel + sidebar badge)
  const criticas = alertas.filter(a => a.severidad === "critica").length;
  const warns    = alertas.length - criticas;
  if (typeof window._actualizarBadgeAlertas === "function") {
    window._actualizarBadgeAlertas(criticas, warns);
  }
  const contadorEl = document.getElementById("alertas-count");
  if (contadorEl) {
    contadorEl.textContent = alertas.length;
    contadorEl.style.display = alertas.length > 0 ? "" : "none";
  }

  if (alertas.length === 0) {
    lista.innerHTML = `<div class="empty-state">✅ Sin alertas recientes</div>`;
    return;
  }

  lista.innerHTML = alertas.map(a => `
    <div class="alerta-item ${a.severidad === "critica" ? "critica" : "warn"}">
      <div style="display:flex;justify-content:space-between;margin-bottom:3px">
        <span style="font-weight:600;font-size:.8rem">${a.metrica ?? ""}</span>
        <span class="mono muted" style="font-size:.72rem">${(a.timestamp ?? "").replace("T"," ")}</span>
      </div>
      <div style="font-size:.82rem">${a.mensaje}</div>
      <div class="muted" style="font-size:.72rem;margin-top:3px">Umbral: ${a.umbral ?? "?"}% · Valor: ${a.valor ?? "?"}%</div>
    </div>`).join("");
}

// ══════════════════════════════════════════════════════
// ESTADO DE CONEXIÓN
// ══════════════════════════════════════════════════════

function actualizarEstadoConexion(conectado) {
  const dot   = document.getElementById("ws-dot");
  const texto = document.getElementById("ws-estado");
  if (dot)   dot.className   = "ws-dot " + (conectado ? "conectado" : "desconectado");
  if (texto) texto.textContent = conectado ? "Conectado" : "Desconectado";
}

// ══════════════════════════════════════════════════════
// TOASTS (notificaciones)
// ══════════════════════════════════════════════════════

let toastTimeout = null;
function mostrarToast(msg, tipo = "info") {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent  = msg;
  el.className    = `toast show ${tipo}`;
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => { el.className = "toast"; }, 4000);
}

// ══════════════════════════════════════════════════════
// EXPORTAR CSV
// ══════════════════════════════════════════════════════

function exportarCSV() {
  const datos = estado.historico;
  if (!datos || datos.length === 0) {
    mostrarToast("No hay datos históricos cargados.", "warn");
    return;
  }
  const cabecera = Object.keys(datos[0]).join(",");
  const filas    = datos.map(d => Object.values(d).join(","));
  const csv      = [cabecera, ...filas].join("\n");
  const blob     = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url      = URL.createObjectURL(blob);
  const a        = document.createElement("a");
  a.href         = url;
  a.download     = `syswatch_${estado.ventana}_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  mostrarToast("📥 CSV exportado correctamente.", "info");
}

// ══════════════════════════════════════════════════════
// TEMA CLARO / OSCURO
// ══════════════════════════════════════════════════════

function toggleTema() {
  estado.temaOscuro = !estado.temaOscuro;
  document.body.classList.toggle("tema-claro", !estado.temaOscuro);
  const btn = document.getElementById("btn-tema");
  if (btn) btn.textContent = estado.temaOscuro ? "☀️ Claro" : "🌙 Oscuro";
}

// ══════════════════════════════════════════════════════
// SELECTOR DE VENTANA TEMPORAL
// ══════════════════════════════════════════════════════

function cambiarVentana(ventana) {
  estado.ventana = ventana;
  // Nuevo selector: pills en panel histórico
  document.querySelectorAll(".pill[data-ventana]").forEach(b => {
    b.classList.toggle("activo", b.dataset.ventana === ventana);
  });
  socket?.emit("solicitar_historico", { ventana });
}

// ══════════════════════════════════════════════════════
// INICIALIZACIÓN
// ══════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  // Worker
  iniciarWorker();

  // Gráficas en tiempo real (vacías al inicio)
  iniciarGraficasRT();

  // WebSocket
  conectarWebSocket();

  // Pills de ventana temporal (panel histórico)
  document.querySelectorAll(".pill[data-ventana]").forEach(btn => {
    btn.addEventListener("click", () => cambiarVentana(btn.dataset.ventana));
  });

  // Botón exportar CSV (topbar)
  document.getElementById("btn-export-csv")?.addEventListener("click", exportarCSV);

  // El botón de tema está en el topbar y manejado en index.html inline

  // Estado inicial de conexión
  actualizarEstadoConexion(false);

  console.log("[SysWatch] Dashboard inicializado.");
});

```
**index.html**
```html
<!DOCTYPE html>
<html lang="es" data-tema="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SysWatch — Monitor de Sistema</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
</head>
<body>

<!-- ── FONDO DECORATIVO ──────────────────────────────── -->
<div class="bg-grid"></div>
<div class="bg-glow bg-glow-1"></div>
<div class="bg-glow bg-glow-2"></div>
<div class="bg-glow bg-glow-3"></div>

<!-- ══════════════════════════════════════════════════════
     SIDEBAR
══════════════════════════════════════════════════════ -->
<aside class="sidebar" id="sidebar">
  <div class="sidebar-logo">
    <div class="logo-icon">⬡</div>
    <div>
      <div class="logo-name">SysWatch</div>
      <div class="logo-ver">v1.0</div>
    </div>
  </div>

  <nav class="sidebar-nav">
    <div class="nav-group-label">MONITORIZACIÓN</div>

    <a class="nav-item active" href="#" data-panel="panel-realtime">
      <span>▶</span> Tiempo Real
    </a>
    <a class="nav-item" href="#" data-panel="panel-historico">
      <span>⌛</span> Histórico
    </a>
    <a class="nav-item" href="#" data-panel="panel-procesos">
      <span>⚙</span> Procesos
    </a>

    <div class="nav-group-label" style="margin-top:16px">SISTEMA</div>

    <a class="nav-item" href="#" data-panel="panel-alertas">
      <span>🔔</span> Alertas
      <span class="nav-badge" id="nav-badge-alertas" style="display:none">0</span>
    </a>
    <a class="nav-item" href="#" data-panel="panel-estado">
      <span>🗄</span> Base de Datos
    </a>
  </nav>

  <div class="sidebar-footer">
    <div class="ws-pill" id="ws-pill">
      <span class="ws-dot" id="ws-dot"></span>
      <span id="ws-estado">Desconectado</span>
    </div>
  </div>
</aside>

<!-- ══════════════════════════════════════════════════════
     LAYOUT PRINCIPAL
══════════════════════════════════════════════════════ -->
<div class="layout" id="layout">

  <!-- ── TOPBAR ─────────────────────────────────── -->
  <header class="topbar">
    <button class="topbar-toggle" id="topbar-toggle" title="Colapsar sidebar">☰</button>
    <div class="topbar-breadcrumb">
      <span class="muted">SysWatch</span>
      <span class="muted"> / </span>
      <span id="breadcrumb-panel">Tiempo Real</span>
    </div>
    <div class="topbar-spacer"></div>
    <div class="topbar-clock mono" id="reloj-topbar">--:--:--</div>
    <button class="topbar-btn" id="btn-export-csv" title="Exportar CSV">↓ CSV</button>
    <button class="topbar-btn icon-only" id="btn-toggle-tema" title="Cambiar tema">◑</button>
  </header>

  <!-- ══════════════════════════════════════════════
       CONTENIDO — PANELES
  ══════════════════════════════════════════════ -->
  <main class="content">

    <!-- ─────────────────────────────────────────────
         PANEL 1 · TIEMPO REAL
    ───────────────────────────────────────────── -->
    <section class="panel active" id="panel-realtime">

      <!-- KPI Row -->
      <div class="kpi-row">

        <!-- KPI CPU -->
        <div class="kpi-card kpi-green">
          <div class="kpi-top">
            <span class="kpi-label">CPU Global</span>
            <span class="kpi-tag green" id="tag-cpu">OK</span>
          </div>
          <div class="kpi-gauge-area">
            <svg class="kpi-gauge" viewBox="0 0 120 75">
              <path class="gauge-bg" d="M15,65 A50,50 0 0,1 105,65"/>
              <path class="gauge-arc gauge-arc-green" id="gauge-cpu" d="M15,65 A50,50 0 0,1 105,65" stroke-dasharray="0 157"/>
            </svg>
            <div class="kpi-center">
              <div class="kpi-val" id="val-cpu-global">—</div>
              <div class="kpi-unit">%</div>
            </div>
          </div>
          <div class="kpi-foot">
            <span class="mono muted" id="val-cpu-nucleos">—</span> núcleos ·
            <span class="mono muted" id="val-cpu-freq">—</span>
          </div>
          <div class="kpi-bar-wrap">
            <div class="kpi-bar green" id="bar-cpu" style="width:0%"></div>
          </div>
        </div>

        <!-- KPI RAM -->
        <div class="kpi-card kpi-blue">
          <div class="kpi-top">
            <span class="kpi-label">Memoria RAM</span>
            <span class="kpi-tag green" id="tag-mem">OK</span>
          </div>
          <div class="kpi-gauge-area">
            <svg class="kpi-gauge" viewBox="0 0 120 75">
              <path class="gauge-bg" d="M15,65 A50,50 0 0,1 105,65"/>
              <path class="gauge-arc gauge-arc-blue" id="gauge-mem" d="M15,65 A50,50 0 0,1 105,65" stroke-dasharray="0 157"/>
            </svg>
            <div class="kpi-center">
              <div class="kpi-val" id="val-mem-pct">—</div>
              <div class="kpi-unit">%</div>
            </div>
          </div>
          <div class="kpi-foot">
            <span class="mono muted" id="val-mem-usado">—</span> /
            <span class="mono muted" id="val-mem-total">—</span> MB
          </div>
          <div class="kpi-bar-wrap">
            <div class="kpi-bar blue" id="bar-mem" style="width:0%"></div>
          </div>
        </div>

        <!-- KPI Disco -->
        <div class="kpi-card kpi-orange">
          <div class="kpi-top">
            <span class="kpi-label">Disco</span>
            <span class="kpi-tag green" id="tag-disco">OK</span>
          </div>
          <div class="kpi-gauge-area">
            <svg class="kpi-gauge" viewBox="0 0 120 75">
              <path class="gauge-bg" d="M15,65 A50,50 0 0,1 105,65"/>
              <path class="gauge-arc gauge-arc-orange" id="gauge-disco" d="M15,65 A50,50 0 0,1 105,65" stroke-dasharray="0 157"/>
            </svg>
            <div class="kpi-center">
              <div class="kpi-val" id="val-disco-pct">—</div>
              <div class="kpi-unit">%</div>
            </div>
          </div>
          <div class="kpi-foot">
            <span class="mono muted" id="val-disco-lec">—</span> lec ·
            <span class="mono muted" id="val-disco-esc">—</span> esc
          </div>
          <div class="kpi-bar-wrap">
            <div class="kpi-bar orange" id="bar-disco" style="width:0%"></div>
          </div>
        </div>

        <!-- KPI Red -->
        <div class="kpi-card kpi-violet">
          <div class="kpi-top">
            <span class="kpi-label">Red</span>
            <span class="kpi-tag green" id="tag-red">OK</span>
          </div>
          <div class="net-split">
            <div class="net-box">
              <div class="net-arrow up">↑</div>
              <div class="net-val mono" id="val-red-env">—</div>
              <div class="net-unit">KB/s</div>
            </div>
            <div class="net-divider"></div>
            <div class="net-box">
              <div class="net-arrow down">↓</div>
              <div class="net-val mono" id="val-red-rec">—</div>
              <div class="net-unit">KB/s</div>
            </div>
          </div>
          <div class="kpi-foot">
            Pkts ↑ <span class="mono muted" id="val-red-pkt-e">—</span> ·
            ↓ <span class="mono muted" id="val-red-pkt-r">—</span>
          </div>
        </div>

      </div><!-- /kpi-row -->

      <!-- Núcleos CPU -->
      <div class="glass-card" style="margin-bottom:16px">
        <div class="card-header">
          <span class="card-title">Núcleos CPU</span>
          <span class="card-badge"><span class="live-dot"></span> En vivo</span>
        </div>
        <div id="nucleos-grid" class="nucleos-grid">
          <span class="muted" style="font-size:0.75rem">Esperando datos…</span>
        </div>
      </div>

      <!-- Gráficas RT 2×2 -->
      <div class="charts-2x2">
        <div class="chart-card">
          <div class="card-header"><span class="card-title">CPU % · Tiempo Real</span></div>
          <div class="chart-wrap"><canvas id="chart-cpu-rt"></canvas></div>
        </div>
        <div class="chart-card">
          <div class="card-header"><span class="card-title">RAM % · Tiempo Real</span></div>
          <div class="chart-wrap"><canvas id="chart-mem-rt"></canvas></div>
        </div>
        <div class="chart-card">
          <div class="card-header"><span class="card-title">Disco I/O MB/s</span></div>
          <div class="chart-wrap"><canvas id="chart-disco-rt"></canvas></div>
        </div>
        <div class="chart-card">
          <div class="card-header"><span class="card-title">Red KB/s</span></div>
          <div class="chart-wrap"><canvas id="chart-red-rt"></canvas></div>
        </div>
      </div>

    </section><!-- /panel-realtime -->

    <!-- ─────────────────────────────────────────────
         PANEL 2 · HISTÓRICO
    ───────────────────────────────────────────── -->
    <section class="panel" id="panel-historico">

      <div class="hist-toolbar">
        <span class="card-title">Histórico de Métricas</span>
        <div class="pill-group">
          <button class="pill activo" data-ventana="1h">1h</button>
          <button class="pill" data-ventana="6h">6h</button>
          <button class="pill" data-ventana="24h">24h</button>
          <button class="pill" data-ventana="7d">7d</button>
          <button class="pill" data-ventana="30d">30d</button>
        </div>
        <span class="hist-hint muted">Calculado por Web Worker</span>
      </div>

      <!-- Stats strip -->
      <div class="stats-strip">
        <div class="stat-chip accent"><span class="sc-label">CPU Avg</span><span class="sc-val mono" id="stat-cpu-avg">—</span></div>
        <div class="stat-chip"><span class="sc-label">CPU Máx</span><span class="sc-val mono" id="stat-cpu-max">—</span></div>
        <div class="stat-chip"><span class="sc-label">CPU p95</span><span class="sc-val mono" id="stat-cpu-p95">—</span></div>
        <div class="stat-chip accent"><span class="sc-label">RAM Avg</span><span class="sc-val mono" id="stat-mem-avg">—</span></div>
        <div class="stat-chip"><span class="sc-label">RAM Máx</span><span class="sc-val mono" id="stat-mem-max">—</span></div>
        <div class="stat-chip"><span class="sc-label">RAM p95</span><span class="sc-val mono" id="stat-mem-p95">—</span></div>
        <div class="stat-chip"><span class="sc-label">Muestras</span><span class="sc-val mono" id="stat-muestras">—</span></div>
      </div>

      <!-- Gráficas históricas 2×2 -->
      <div class="charts-2x2">
        <div class="chart-card">
          <div class="card-header"><span class="card-title">CPU % histórico</span></div>
          <div class="chart-wrap"><canvas id="chart-hist-cpu"></canvas></div>
        </div>
        <div class="chart-card">
          <div class="card-header"><span class="card-title">RAM % histórico</span></div>
          <div class="chart-wrap"><canvas id="chart-hist-mem"></canvas></div>
        </div>
        <div class="chart-card">
          <div class="card-header"><span class="card-title">Disco % histórico</span></div>
          <div class="chart-wrap"><canvas id="chart-hist-disco"></canvas></div>
        </div>
        <div class="chart-card">
          <div class="card-header"><span class="card-title">Red KB/s histórico</span></div>
          <div class="chart-wrap"><canvas id="chart-hist-red"></canvas></div>
        </div>
      </div>

    </section><!-- /panel-historico -->

    <!-- ─────────────────────────────────────────────
         PANEL 3 · PROCESOS
    ───────────────────────────────────────────── -->
    <section class="panel" id="panel-procesos">
      <div class="glass-card">
        <div class="card-header">
          <span class="card-title">Top Procesos por CPU</span>
          <span class="card-badge"><span class="live-dot"></span> En vivo</span>
        </div>
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th>PID</th>
                <th>Nombre</th>
                <th>CPU %</th>
                <th>RAM %</th>
                <th>Actividad</th>
              </tr>
            </thead>
            <tbody id="procesos-tbody">
              <tr><td class="empty-cell" colspan="5">Esperando datos…</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section><!-- /panel-procesos -->

    <!-- ─────────────────────────────────────────────
         PANEL 4 · ALERTAS
    ───────────────────────────────────────────── -->
    <section class="panel" id="panel-alertas">
      <div class="glass-card">
        <div class="card-header">
          <span class="card-title">Alertas del Sistema</span>
          <span class="count-badge red" id="alertas-count" style="display:none">0</span>
        </div>
        <div id="alertas-lista" class="alertas-lista">
          <div class="empty-state">✅ Sin alertas recientes</div>
        </div>
      </div>
    </section><!-- /panel-alertas -->

    <!-- ─────────────────────────────────────────────
         PANEL 5 · BASE DE DATOS
    ───────────────────────────────────────────── -->
    <section class="panel" id="panel-estado">
      <div class="glass-card" style="max-width:680px">
        <div class="card-header">
          <span class="card-title">Estado de la Base de Datos</span>
          <button class="topbar-btn" onclick="refrescarEstado()">↻ Refrescar</button>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
          <div class="stat-mini green">
            <div class="sm-label">Registros RAW</div>
            <div class="sm-val mono" id="bd-raw">—</div>
          </div>
          <div class="stat-mini blue">
            <div class="sm-label">Registros por Hora</div>
            <div class="sm-val mono" id="bd-horas">—</div>
          </div>
          <div class="stat-mini red">
            <div class="sm-label">Alertas guardadas</div>
            <div class="sm-val mono" id="bd-alertas">—</div>
          </div>
          <div class="stat-mini violet">
            <div class="sm-label">Tamaño BD</div>
            <div class="sm-val mono" id="bd-tam">—</div>
          </div>
        </div>

        <div class="mant-desc">
          Mantenimiento: elimina registros con más de 30 días para liberar espacio.
          La base de datos está en <span class="ic mono">syswatch.db</span>.
        </div>
        <div class="mant-btns">
          <button class="action-btn danger" onclick="limpiarBD()">🗑️ Limpiar datos &gt;30 días</button>
        </div>
      </div>
    </section><!-- /panel-estado -->

  </main><!-- /content -->

  <!-- TOAST -->
  <div class="toast" id="toast"></div>

</div><!-- /layout -->

<script>
// ── Reloj topbar ──────────────────────────────────────
(function tickReloj() {
  const el = document.getElementById('reloj-topbar');
  if (el) el.textContent = new Date().toLocaleTimeString('es-ES');
  setTimeout(tickReloj, 1000);
})();

// ── Sidebar toggle ────────────────────────────────────
document.getElementById('topbar-toggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('collapsed');
  document.getElementById('layout').classList.toggle('sb-collapsed');
});

// ── Navegación de paneles ─────────────────────────────
const navItems = document.querySelectorAll('.nav-item[data-panel]');
const panels   = document.querySelectorAll('.panel');
const breadcrumb = document.getElementById('breadcrumb-panel');
const labels = {
  'panel-realtime':  'Tiempo Real',
  'panel-historico': 'Histórico',
  'panel-procesos':  'Procesos',
  'panel-alertas':   'Alertas',
  'panel-estado':    'Base de Datos'
};

navItems.forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    const target = item.dataset.panel;
    navItems.forEach(n => n.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    item.classList.add('active');
    document.getElementById(target)?.classList.add('active');
    if (breadcrumb) breadcrumb.textContent = labels[target] || target;
    if (target === 'panel-estado') refrescarEstado();
  });
});

// ── Tema toggle ───────────────────────────────────────
document.getElementById('btn-toggle-tema').addEventListener('click', () => {
  const html = document.documentElement;
  html.dataset.tema = html.dataset.tema === 'dark' ? 'light' : 'dark';
});

// ── Gauge helper ──────────────────────────────────────
function setGauge(id, pct) {
  const el = document.getElementById(id);
  if (!el) return;
  const arc = Math.min(pct / 100, 1) * 157;
  el.setAttribute('stroke-dasharray', arc.toFixed(1) + ' 157');
}

// ── Tag helper ────────────────────────────────────────
function setTag(id, pct) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = pct >= 85 ? 'CRÍTICO' : pct >= 60 ? 'ALERTA' : 'OK';
  el.className = 'kpi-tag ' + (pct >= 85 ? 'red' : pct >= 60 ? 'yellow' : 'green');
}

// ── Badge alertas sidebar ─────────────────────────────
window._actualizarBadgeAlertas = function(criticas, warns) {
  const b = document.getElementById('nav-badge-alertas');
  const ac = document.getElementById('alertas-count');
  const total = criticas + warns;
  if (b) { b.textContent = total; b.style.display = total > 0 ? '' : 'none'; }
  if (ac) { ac.textContent = total; ac.style.display = total > 0 ? '' : 'none'; }
};

// ── Procesos panel ────────────────────────────────────
function renderizarProcesosPanel(procs) {
  const tbody = document.getElementById('procesos-tbody');
  if (!tbody || !procs.length) return;
  const maxCpu = Math.max(...procs.map(p => p.cpu_percent || 0), 1);
  tbody.innerHTML = procs.map(p => {
    const bar = ((p.cpu_percent || 0) / maxCpu * 100).toFixed(0);
    const cls = p.cpu_percent > 50 ? 'red' : p.cpu_percent > 20 ? 'yellow' : 'green';
    return `<tr>
      <td class="mono muted">${p.pid ?? '--'}</td>
      <td class="proc-name">${p.name ?? '--'}</td>
      <td><span class="pct-badge ${cls}">${(p.cpu_percent ?? 0).toFixed(1)}%</span></td>
      <td class="mono muted">${(p.memory_percent ?? 0).toFixed(1)}%</td>
      <td><div class="act-bar-wrap"><div class="act-bar ${cls}" style="width:${bar}%"></div></div></td>
    </tr>`;
  }).join('');
}

// ── Estado BD ─────────────────────────────────────────
async function refrescarEstado() {
  try {
    const d = await fetch('/api/estado').then(r => r.json());
    const b = d.base_datos || {};
    document.getElementById('bd-raw').textContent     = (b.raw     ?? '—').toLocaleString('es-ES');
    document.getElementById('bd-horas').textContent   = (b.horas   ?? '—').toLocaleString('es-ES');
    document.getElementById('bd-alertas').textContent = (b.alertas ?? '—').toLocaleString('es-ES');
    document.getElementById('bd-tam').textContent     = (b['tamaño_mb'] ?? '—') + ' MB';
  } catch(e) { console.warn(e); }
}

async function limpiarBD() {
  if (!confirm('¿Eliminar datos con más de 30 días?')) return;
  try {
    const d = await fetch('/api/mantenimiento/limpiar?dias=30').then(r => r.json());
    mostrarToast('🗑️ ' + d.eliminados + ' filas eliminadas.', 'info');
    refrescarEstado();
  } catch(e) { mostrarToast('Error al limpiar BD', 'error'); }
}
</script>

<script src="app.js"></script>
</body>
</html>
```
**styles.css**
```css
/* 
   SysWatch  Professional Dark Dashboard
   Diseño: glassmorphism + Grafana-inspired
 */

/*  Variables  */
:root {
  --sidebar-w: 220px;
  --topbar-h:  52px;
  --radius:    10px;
  --radius-lg: 14px;
  --trans:     0.22s ease;
}

[data-tema="dark"] {
  --bg:        #0d0f17;
  --bg2:       #111420;
  --surface:   rgba(255,255,255,.04);
  --surface2:  rgba(255,255,255,.07);
  --border:    rgba(255,255,255,.09);
  --text:      #e2e8f0;
  --text-muted:#6b7280;
  --green:     #22d3a0;
  --blue:      #60a5fa;
  --orange:    #fb923c;
  --violet:    #a78bfa;
  --red:       #f87171;
  --yellow:    #fbbf24;
  --green-glow:rgba(34,211,160,.15);
  --blue-glow: rgba(96,165,250,.15);
  --orange-glow:rgba(251,146,60,.15);
  --violet-glow:rgba(167,139,250,.15);
}

[data-tema="light"] {
  --bg:        #f0f4f8;
  --bg2:       #e8edf3;
  --surface:   rgba(255,255,255,.7);
  --surface2:  rgba(255,255,255,.9);
  --border:    rgba(0,0,0,.1);
  --text:      #1e293b;
  --text-muted:#64748b;
  --green:     #059669;
  --blue:      #2563eb;
  --orange:    #ea580c;
  --violet:    #7c3aed;
  --red:       #dc2626;
  --yellow:    #d97706;
  --green-glow:rgba(5,150,105,.1);
  --blue-glow: rgba(37,99,235,.1);
  --orange-glow:rgba(234,88,12,.1);
  --violet-glow:rgba(124,58,237,.1);
}

/*  Reset & Base  */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  height: 100%;
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 14px;
  background: var(--bg);
  color: var(--text);
  overflow-x: hidden;
}

a { color: inherit; text-decoration: none; }
button { cursor: pointer; font-family: inherit; }

/*  Background decorativo  */
.bg-grid {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
  background-size: 40px 40px;
}

.bg-glow {
  position: fixed; z-index: 0; pointer-events: none;
  border-radius: 50%; filter: blur(80px); opacity: .6;
}
.bg-glow-1 { width: 500px; height: 500px; top: -120px; left: -120px; background: rgba(34,211,160,.06); }
.bg-glow-2 { width: 400px; height: 400px; top: 30%; right: -100px; background: rgba(96,165,250,.06); }
.bg-glow-3 { width: 350px; height: 350px; bottom: -80px; left: 35%; background: rgba(167,139,250,.05); }

/*  Sidebar  */
.sidebar {
  position: fixed; top: 0; left: 0; bottom: 0; z-index: 100;
  width: var(--sidebar-w);
  background: var(--bg2);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  transition: width var(--trans), transform var(--trans);
  overflow: hidden;
}

.sidebar.collapsed { width: 60px; }
.sidebar.collapsed .logo-name,
.sidebar.collapsed .logo-ver,
.sidebar.collapsed .nav-group-label,
.sidebar.collapsed .nav-item > span:last-child,
.sidebar.collapsed .ws-pill span:last-child { display: none; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 10px 0; }
.sidebar.collapsed .nav-item > span:first-child { font-size: 1.1rem; }

.sidebar-logo {
  display: flex; align-items: center; gap: 10px;
  padding: 18px 16px 14px;
  border-bottom: 1px solid var(--border);
}
.logo-icon { font-size: 1.6rem; color: var(--green); line-height: 1; }
.logo-name { font-weight: 700; font-size: 1rem; letter-spacing: .5px; }
.logo-ver  { font-size: .65rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }

.sidebar-nav { flex: 1; padding: 12px 8px; overflow-y: auto; }
.nav-group-label {
  font-size: .65rem; font-weight: 600; letter-spacing: 1.2px;
  color: var(--text-muted); padding: 8px 8px 4px; text-transform: uppercase;
}
.nav-item {
  display: flex; align-items: center; gap: 9px;
  padding: 9px 10px; border-radius: var(--radius);
  color: var(--text-muted); font-size: .84rem; font-weight: 500;
  transition: background var(--trans), color var(--trans);
  margin-bottom: 2px; white-space: nowrap;
}
.nav-item:hover  { background: var(--surface2); color: var(--text); }
.nav-item.active { background: rgba(34,211,160,.12); color: var(--green); }
.nav-badge {
  margin-left: auto; background: var(--red); color: #fff;
  font-size: .65rem; font-weight: 700; border-radius: 99px;
  padding: 1px 6px; min-width: 20px; text-align: center;
}

.sidebar-footer {
  padding: 12px 10px; border-top: 1px solid var(--border);
}
.ws-pill {
  display: flex; align-items: center; gap: 7px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 99px; padding: 5px 12px; font-size: .75rem;
  color: var(--text-muted);
}
.ws-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--red); flex-shrink: 0;
  transition: background var(--trans);
}
.ws-dot.conectado { background: var(--green); box-shadow: 0 0 6px var(--green); }

/*  Layout  */
.layout {
  margin-left: var(--sidebar-w);
  min-height: 100vh; display: flex; flex-direction: column;
  transition: margin-left var(--trans);
  position: relative; z-index: 1;
}
.layout.sb-collapsed { margin-left: 60px; }

/*  Topbar  */
.topbar {
  position: sticky; top: 0; z-index: 50;
  height: var(--topbar-h);
  display: flex; align-items: center; gap: 10px;
  padding: 0 20px;
  background: rgba(13,15,23,.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}
[data-tema="light"] .topbar { background: rgba(240,244,248,.85); }

.topbar-toggle {
  background: none; border: none; color: var(--text-muted);
  font-size: 1.1rem; padding: 4px 6px; border-radius: 6px;
  transition: color var(--trans), background var(--trans);
}
.topbar-toggle:hover { color: var(--text); background: var(--surface2); }

.topbar-breadcrumb { font-size: .84rem; font-weight: 500; }
.topbar-spacer { flex: 1; }

.topbar-clock {
  font-size: .8rem; color: var(--text-muted);
  letter-spacing: .5px; min-width: 60px;
}

.topbar-btn {
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text-muted); font-size: .78rem; font-weight: 500;
  padding: 5px 12px; border-radius: 6px;
  transition: background var(--trans), color var(--trans), border-color var(--trans);
}
.topbar-btn:hover { background: var(--surface2); color: var(--text); border-color: var(--green); }
.topbar-btn.icon-only { padding: 5px 10px; font-size: .9rem; }

/*  Content  */
.content {
  flex: 1; padding: 20px 24px; overflow-y: auto;
}

/*  Paneles  */
.panel { display: none; animation: fadeIn .25s ease; }
.panel.active { display: block; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

/*  KPI Row  */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 14px; margin-bottom: 16px;
}

.kpi-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 16px;
  position: relative; overflow: hidden;
  transition: transform var(--trans), box-shadow var(--trans);
}
.kpi-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0;
  height: 3px; border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}
.kpi-card:hover { transform: translateY(-2px); }

.kpi-green::before { background: var(--green); box-shadow: 0 0 12px var(--green); }
.kpi-blue::before  { background: var(--blue);  box-shadow: 0 0 12px var(--blue); }
.kpi-orange::before { background: var(--orange); box-shadow: 0 0 12px var(--orange); }
.kpi-violet::before { background: var(--violet); box-shadow: 0 0 12px var(--violet); }

.kpi-green { box-shadow: 0 4px 24px var(--green-glow); }
.kpi-blue  { box-shadow: 0 4px 24px var(--blue-glow); }
.kpi-orange { box-shadow: 0 4px 24px var(--orange-glow); }
.kpi-violet { box-shadow: 0 4px 24px var(--violet-glow); }

.kpi-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.kpi-label { font-size: .78rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: .6px; }

.kpi-tag {
  font-size: .62rem; font-weight: 700; padding: 2px 7px;
  border-radius: 99px; text-transform: uppercase; letter-spacing: .5px;
}
.kpi-tag.green  { background: rgba(34,211,160,.15); color: var(--green); }
.kpi-tag.yellow { background: rgba(251,191,36,.15);  color: var(--yellow); }
.kpi-tag.red    { background: rgba(248,113,113,.15); color: var(--red); }

/*  Gauge SVG  */
.kpi-gauge-area { position: relative; width: 100%; }
.kpi-gauge { width: 100%; max-width: 120px; display: block; margin: 0 auto; }

.gauge-bg {
  fill: none; stroke: var(--border); stroke-width: 9;
  stroke-linecap: round;
}
.gauge-arc {
  fill: none; stroke-width: 9; stroke-linecap: round;
  transition: stroke-dasharray .5s cubic-bezier(.4,0,.2,1);
}
.gauge-arc-green  { stroke: var(--green); filter: drop-shadow(0 0 4px var(--green)); }
.gauge-arc-blue   { stroke: var(--blue);  filter: drop-shadow(0 0 4px var(--blue)); }
.gauge-arc-orange { stroke: var(--orange); filter: drop-shadow(0 0 4px var(--orange)); }
.gauge-arc-yellow { stroke: var(--yellow); filter: drop-shadow(0 0 4px var(--yellow)); }
.gauge-arc-red    { stroke: var(--red);    filter: drop-shadow(0 0 4px var(--red)); }

.kpi-center {
  position: absolute; left: 50%; top: 15%; transform: translate(-50%, -50%);
  text-align: center; pointer-events: none;
}
.kpi-val  { font-size: 1.1rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; line-height: 1; }
.kpi-unit { font-size: .65rem; color: var(--text-muted); margin-top: 1px; }

.kpi-foot { font-size: .72rem; color: var(--text-muted); text-align: center; margin: 4px 0 8px; }

.kpi-bar-wrap {
  height: 4px; background: var(--surface2); border-radius: 99px; overflow: hidden;
}
.kpi-bar { height: 100%; border-radius: 99px; transition: width .5s ease; }
.kpi-bar.green  { background: var(--green); }
.kpi-bar.blue   { background: var(--blue); }
.kpi-bar.orange { background: var(--orange); }

/*  Network card  */
.net-split { display: flex; align-items: center; justify-content: center; gap: 0; margin: 12px 0 8px; }
.net-box   { flex: 1; text-align: center; }
.net-divider { width: 1px; height: 48px; background: var(--border); margin: 0 10px; }
.net-arrow { font-size: 1rem; font-weight: 700; }
.net-arrow.up   { color: var(--green); }
.net-arrow.down { color: var(--blue); }
.net-val  { font-size: 1.3rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; line-height: 1.1; }
.net-unit { font-size: .65rem; color: var(--text-muted); }

/*  Glass Cards  */
.glass-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  backdrop-filter: blur(8px);
  margin-bottom: 16px;
}

.card-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.card-title { font-size: .88rem; font-weight: 600; letter-spacing: .3px; }
.card-badge {
  display: flex; align-items: center; gap: 5px;
  font-size: .7rem; color: var(--text-muted);
}
.live-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--green);
  box-shadow: 0 0 5px var(--green);
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .3; } }

/*  Núcleos grid  */
.nucleos-grid {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 4px 0;
}

/*  Charts 22  */
.charts-2x2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}
.chart-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 14px;
}
.chart-wrap { height: 160px; }
.chart-wrap canvas { width: 100% !important; height: 100% !important; }

/*  Histórico toolbar  */
.hist-toolbar {
  display: flex; align-items: center; flex-wrap: wrap; gap: 10px;
  margin-bottom: 14px;
}
.hist-hint { font-size: .72rem; }
.pill-group { display: flex; gap: 4px; }
.pill {
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text-muted); font-size: .75rem; font-weight: 500;
  padding: 4px 12px; border-radius: 99px;
  transition: background var(--trans), color var(--trans), border-color var(--trans);
}
.pill:hover   { border-color: var(--green); color: var(--text); }
.pill.activo  { background: rgba(34,211,160,.15); border-color: var(--green); color: var(--green); }

/*  Stats strip  */
.stats-strip {
  display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;
}
.stat-chip {
  display: flex; flex-direction: column;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 14px; min-width: 90px;
}
.stat-chip.accent { border-color: rgba(34,211,160,.3); }
.sc-label { font-size: .65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .5px; }
.sc-val   { font-size: .95rem; font-weight: 600; margin-top: 2px; }

/*  Table  */
.table-scroll { overflow-x: auto; }
.data-table {
  width: 100%; border-collapse: collapse; font-size: .82rem;
}
.data-table th {
  text-align: left; padding: 8px 10px;
  font-size: .68rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: .8px; color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}
.data-table td {
  padding: 9px 10px; border-bottom: 1px solid rgba(255,255,255,.04);
  vertical-align: middle;
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--surface2); }
.empty-cell { text-align: center; color: var(--text-muted); padding: 24px !important; }
.proc-name  { font-weight: 500; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.pct-badge {
  font-size: .72rem; font-weight: 700; padding: 2px 8px; border-radius: 99px;
  font-family: 'JetBrains Mono', monospace;
}
.pct-badge.green  { background: rgba(34,211,160,.12);  color: var(--green); }
.pct-badge.yellow { background: rgba(251,191,36,.12);   color: var(--yellow); }
.pct-badge.red    { background: rgba(248,113,113,.12);  color: var(--red); }

.act-bar-wrap { height: 5px; background: var(--surface2); border-radius: 99px; min-width: 80px; }
.act-bar { height: 100%; border-radius: 99px; transition: width .4s ease; }
.act-bar.green  { background: var(--green); }
.act-bar.yellow { background: var(--yellow); }
.act-bar.red    { background: var(--red); }

/*  Alertas  */
.alertas-lista { max-height: 420px; overflow-y: auto; }
.empty-state { text-align: center; color: var(--text-muted); padding: 32px; font-size: .85rem; }
.count-badge {
  font-size: .72rem; font-weight: 700; padding: 2px 8px;
  border-radius: 99px;
}
.count-badge.red    { background: rgba(248,113,113,.15); color: var(--red); }
.count-badge.yellow { background: rgba(251,191,36,.15);  color: var(--yellow); }

/* Alert items rendered by app.js */
.alerta-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 12px; border-radius: 8px;
  border: 1px solid var(--border); margin-bottom: 6px;
  font-size: .82rem;
}
.alerta-item.critica { border-color: rgba(248,113,113,.3); background: rgba(248,113,113,.06); }
.alerta-item.warn    { border-color: rgba(251,191,36,.3);  background: rgba(251,191,36,.06); }

/*  BD Panel  */
.stat-mini {
  padding: 14px 16px; border-radius: var(--radius);
  border: 1px solid var(--border); background: var(--surface);
}
.stat-mini.green  { border-color: rgba(34,211,160,.25); }
.stat-mini.blue   { border-color: rgba(96,165,250,.25); }
.stat-mini.red    { border-color: rgba(248,113,113,.25); }
.stat-mini.violet { border-color: rgba(167,139,250,.25); }
.sm-label { font-size: .68rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .7px; margin-bottom: 4px; }
.sm-val   { font-size: 1.3rem; font-weight: 700; }
.stat-mini.green .sm-val  { color: var(--green); }
.stat-mini.blue .sm-val   { color: var(--blue); }
.stat-mini.red .sm-val    { color: var(--red); }
.stat-mini.violet .sm-val { color: var(--violet); }

.mant-desc { font-size: .82rem; color: var(--text-muted); margin-bottom: 14px; line-height: 1.5; }
.mant-btns { display: flex; gap: 8px; }
.action-btn {
  padding: 8px 18px; border-radius: 8px; font-size: .82rem; font-weight: 600;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text); transition: all var(--trans);
}
.action-btn.danger { border-color: rgba(248,113,113,.4); color: var(--red); }
.action-btn.danger:hover { background: rgba(248,113,113,.12); }

/*  Toast  */
.toast {
  position: fixed; bottom: 24px; right: 24px; z-index: 9999;
  padding: 10px 18px; border-radius: 10px;
  background: var(--surface2); border: 1px solid var(--border);
  backdrop-filter: blur(12px);
  font-size: .82rem; font-weight: 500;
  opacity: 0; pointer-events: none;
  transition: opacity .3s ease, transform .3s ease;
  transform: translateY(10px);
  max-width: 320px;
}
.toast.show { opacity: 1; transform: none; pointer-events: auto; }
.toast.success { border-color: var(--green); color: var(--green); }
.toast.error   { border-color: var(--red);   color: var(--red); }
.toast.info    { border-color: var(--blue);  color: var(--blue); }

/*  Utilities  */
.mono  { font-family: 'JetBrains Mono', monospace; }
.muted { color: var(--text-muted); }
.green  { color: var(--green); }
.blue   { color: var(--blue); }
.orange { color: var(--orange); }
.violet { color: var(--violet); }
.ic { font-family: 'JetBrains Mono', monospace; font-size: .82em; background: var(--surface2); padding: 1px 5px; border-radius: 4px; }

/*  Scrollbar  */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/*  Responsive  */
@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); }
  .sidebar.collapsed { transform: translateX(0); width: 60px; }
  .layout { margin-left: 0 !important; }
  .kpi-row { grid-template-columns: 1fr 1fr; }
  .charts-2x2 { grid-template-columns: 1fr; }
  .content { padding: 14px 12px; }
}
```
### workers
**stats_worker.js**
```js
/**
 * SysWatch - Monitor de Recursos del Servidor
 * frontend/workers/stats_worker.js
 *
 * Web Worker que ejecuta cálculos estadísticos en segundo plano
 * SIN bloquear el hilo principal de la interfaz.
 *
 * Conceptos de clase aplicados:
 *   - Web Workers (Unidad 1 - Actividad Final EVAL - igual al ejercicio de clase)
 *   - Comunicación asíncrona entre hilo UI ↔ Worker via postMessage
 */

"use strict";

/**
 * Calcula estadísticas básicas de un array de números.
 * @param {number[]} arr
 * @returns {{min:number, max:number, avg:number, p95:number, last:number}}
 */
function calcularStats(arr) {
  if (!arr || arr.length === 0) {
    return { min: 0, max: 0, avg: 0, p95: 0, last: 0 };
  }
  const sorted = [...arr].sort((a, b) => a - b);
  const n = sorted.length;
  const sum = sorted.reduce((s, v) => s + v, 0);
  const p95idx = Math.floor(n * 0.95);
  return {
    min:  +sorted[0].toFixed(2),
    max:  +sorted[n - 1].toFixed(2),
    avg:  +(sum / n).toFixed(2),
    p95:  +sorted[Math.min(p95idx, n - 1)].toFixed(2),
    last: +sorted[n - 1].toFixed(2),
  };
}

/**
 * Determina el color semáforo de un valor porcentual.
 * @param {number} pct
 * @returns {"verde"|"amarillo"|"rojo"}
 */
function semaforo(pct) {
  if (pct < 60) return "verde";
  if (pct < 85) return "amarillo";
  return "rojo";
}

/**
 * Procesa un lote de métricas históricas y calcula resúmenes.
 * @param {Object[]} datos - Array de filas históricas.
 * @returns {Object} Objeto con estadísticas por métrica.
 */
function procesarHistorico(datos) {
  const cpu    = datos.map(d => d.cpu_global   ?? d.cpu_avg  ?? 0);
  const mem    = datos.map(d => d.mem_pct      ?? d.mem_avg  ?? 0);
  const disco  = datos.map(d => d.disco_pct    ?? d.disco_avg ?? 0);
  const redEnv = datos.map(d => d.red_env      ?? 0);
  const redRec = datos.map(d => d.red_recv     ?? 0);
  const red    = cpu.map((_, i) => (redEnv[i] || 0) + (redRec[i] || 0));

  return {
    cpu:    { ...calcularStats(cpu),   semaforo: semaforo(calcularStats(cpu).avg) },
    mem:    { ...calcularStats(mem),   semaforo: semaforo(calcularStats(mem).avg) },
    disco:  { ...calcularStats(disco), semaforo: semaforo(calcularStats(disco).avg) },
    red:    calcularStats(red),
    muestras: datos.length,
  };
}

// ── Escucha mensajes del hilo principal ──────────────────────────────────

self.onmessage = function (event) {
  const { tipo, payload, id } = event.data;

  try {
    switch (tipo) {
      case "procesar_historico": {
        const resultado = procesarHistorico(payload.datos);
        self.postMessage({ tipo: "historico_procesado", id, resultado });
        break;
      }

      case "calcular_stats_array": {
        // Permite calcular stats de cualquier array arbitrario
        const resultado = calcularStats(payload.valores);
        self.postMessage({ tipo: "stats_calculadas", id, resultado });
        break;
      }

      case "ping": {
        self.postMessage({ tipo: "pong", id, ts: Date.now() });
        break;
      }

      default:
        self.postMessage({ tipo: "error", id, mensaje: `Tipo desconocido: ${tipo}` });
    }
  } catch (err) {
    self.postMessage({ tipo: "error", id, mensaje: err.message });
  }
};

```