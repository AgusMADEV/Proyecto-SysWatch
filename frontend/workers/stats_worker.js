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
