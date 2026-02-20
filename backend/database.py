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
