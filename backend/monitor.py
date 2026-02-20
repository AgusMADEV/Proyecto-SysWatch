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
