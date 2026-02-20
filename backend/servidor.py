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
