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
