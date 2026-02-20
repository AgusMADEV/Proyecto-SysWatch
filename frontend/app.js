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
