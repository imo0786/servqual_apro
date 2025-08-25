import React, { useEffect, useMemo, useState } from "react";
import * as XLSX from "xlsx";

// --- Utilidades UI simples (sin dependencias externas) ---
const IconButton = ({ title, onClick, children, className = "" }) => (
  <button
    title={title}
    onClick={onClick}
    className={
      "inline-flex items-center justify-center rounded-xl border px-2.5 py-1.5 shadow-sm hover:shadow transition text-sm " +
      className
    }
  >
    {children}
  </button>
);

const Modal = ({ open, onClose, children, title }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-[min(900px,95vw)] max-h-[90vh] overflow-auto rounded-2xl bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">{title}</h3>
          <IconButton title="Cerrar" onClick={onClose}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </IconButton>
        </div>
        {children}
      </div>
    </div>
  );
};

const Tag = ({ children, color = "slate" }) => (
  <span className={`inline-flex items-center rounded-full bg-${color}-100 px-2 py-0.5 text-xs font-medium text-${color}-800 border border-${color}-200`}>{children}</span>
);

// Corrige clases dinámicas de Tailwind en build: opción segura
const SafeTag = ({ children, tone = "slate" }) => {
  const map = {
    slate: "bg-slate-100 text-slate-800 border-slate-200",
    green: "bg-green-100 text-green-800 border-green-200",
    yellow: "bg-yellow-100 text-yellow-800 border-yellow-200",
    red: "bg-red-100 text-red-800 border-red-200",
    blue: "bg-blue-100 text-blue-800 border-blue-200",
    violet: "bg-violet-100 text-violet-800 border-violet-200",
    orange: "bg-orange-100 text-orange-800 border-orange-200",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border ${map[tone] || map.slate}`}>{children}</span>
  );
};

// --- Motor de Sugerencias de Acción Correctiva ---
const suggestionRules = [
  { key: /confus|confusa|confuso/i, action: "Estandarizar guion y checklist; capacitar en comunicación clara; validar con técnica de 'retorno de información'." },
  { key: /falt(ó|o) info|incomplet/i, action: "Diseñar lista de información mínima; agregar señalética paso a paso; supervisión de cumplimiento diario." },
  { key: /t(á|a)rd|demora|espera|cola/i, action: "Implementar gestión de colas; priorización por hora; reforzar cajas/personal en picos; monitoreo de TME en tablero." },
  { key: /sistema lento|lento/i, action: "Revisar desempeño del SI; plan de contingencia; ventanilla offline; escalamiento a TI con métricas." },
  { key: /no (informaron|explicaron|recib[ií]|atendieron|examin[oó])/i, action: "Retroalimentación 1:1; reentrenar protocolo; auditoría por muestreo; reforzar cultura de servicio." },
  { key: /muy t[eé]cnico/i, action: "Capacitar en lenguaje sencillo; plantilla de explicación; evaluar comprensión del paciente." },
  { key: /examen superficial|no examin|faltaron pruebas/i, action: "Recordar estándar de examen físico; checklist por especialidad; doble firma en casos críticos." },
  { key: /precios altos|caro|no vale/i, action: "Revisar política de precios y comunicación de valor; opciones de paquetes; transparencia de costos." },
  { key: /sin disponibilidad|sin rampas|barreras|acceso dif/i, action: "Plan de accesibilidad: rampas, señalética, rutas; calendarizar correcciones con Mantenimiento." },
  { key: /ba[nñ]os|mal olor|sucio/i, action: "Refuerzo de limpieza con rondas programadas; checklist y bitácora; responsable por turno." },
  { key: /telemedicina|virtual|tecnolog/i, action: "Mapear flujos de telemedicina; capacitar; asegurar equipos y conectividad; protocolo de consentimiento." },
  { key: /no preguntaron|no escuch[oó]|interrump/i, action: "Entrenamiento en escucha activa; prohibir interrupciones; guía de entrevista clínica." },
  { key: /preferencias injustas|saltaron turnos|orden/i, action: "Sistema de turnos visible; auditoría aleatoria; sanción por alteración de cola; educación al usuario." },
];

function suggestActionFromText(text = "") {
  for (const r of suggestionRules) if (r.key.test(text)) return r.action;
  // fallback general
  return "Analizar causa raíz (Ishikawa/5 porqués); definir acción SMART con responsable y fecha; medir impacto en 30 días.";
}

// --- Lectura de Excel ---
function parseWorkbookToRows(workbook) {
  // Intentamos localizar hojas por aproximación
  const sheets = workbook.SheetNames;
  const pickSheet = (candidates) =>
    sheets.find((s) => candidates.some((c) => s.toLowerCase().includes(c))) || sheets[0];

  const bdSheetName = pickSheet(["bd", "base", "preg", "servqual"]);
  const catRespSheetName = sheets.find((s) => /respons/i.test(s.toLowerCase()));
  const catEstadoSheetName = sheets.find((s) => /estado/i.test(s.toLowerCase()));
  const catSucSheetName = sheets.find((s) => /sucursal|clinica|sede/i.test(s.toLowerCase()));

  const bd = XLSX.utils.sheet_to_json(workbook.Sheets[bdSheetName], { defval: "" });
  const responsables = catRespSheetName
    ? XLSX.utils.sheet_to_json(workbook.Sheets[catRespSheetName], { header: 1 })
        .flat()
        .filter(Boolean)
    : [];
  const estados = catEstadoSheetName
    ? XLSX.utils.sheet_to_json(workbook.Sheets[catEstadoSheetName], { header: 1 })
        .flat()
        .filter(Boolean)
    : ["Pendiente", "En progreso", "Resuelto", "Escalado"];
  const sucursales = catSucSheetName
    ? XLSX.utils.sheet_to_json(workbook.Sheets[catSucSheetName], { header: 1 })
        .flat()
        .filter(Boolean)
    : [
        "Hospital Central",
        "Clínica Zona 10",
        "Clínica Amatitlán",
        "Clínica Mixco",
      ];

  // Normalizamos columnas esperadas en la hoja BD
  // Soportamos encabezados: codigo, pregunta, subcodigo, subpregunta...
  const rows = [];
  bd.forEach((r, idx) => {
    const codigo = r.codigo || r.CODIGO || r.Código || r["codigo pregunta"] || r["cod_p"] || r["pregunta_codigo"] || "";
    const pregunta = r.pregunta || r.PREGUNTA || r.Pregunta || r["texto_pregunta"] || "";
    const subcodigo = r.subcodigo || r.SUBCODIGO || r.Subcodigo || r["sub_p"] || r["codigo_subpregunta"] || r["subpregunta_codigo"] || r["COD_SUB"] || "";
    const subpregunta = r.subpregunta || r.SUBPREGUNTA || r.Subpregunta || r["texto_subpregunta"] || r["categoria_subpregunta"] || "";
    const responsable = r.responsable || r.RESPONSABLE || r.Responsable || "";
    const estado = r.estado || r.ESTADO || r.Estado || "Pendiente";
    const sucursal = r.sucursal || r.SUCURSAL || r.Sucursal || "";
    const activa = r.activa ?? r.ACTIVA ?? r.Activa ?? false;
    const avance = Number(r.avance ?? r.AVANCE ?? 0) || 0;
    const accion = r["accion_correctiva"] || r["acción_correctiva"] || r["accion"] || "";

    rows.push({
      id: `${idx + 1}-${codigo || pregunta}-${subcodigo || subpregunta}`,
      codigo: String(codigo || "").trim(),
      pregunta: String(pregunta || "").trim(),
      subcodigo: String(subcodigo || "").trim(),
      subpregunta: String(subpregunta || "").trim(),
      sucursal: String(sucursal || "").trim(),
      activa: Boolean(activa),
      responsable: String(responsable || "").trim(),
      accion: String(accion || "").trim(),
      avance: Math.max(0, Math.min(100, avance)),
      estado: String(estado || "Pendiente").trim(),
    });
  });

  return { rows, responsables, estados, sucursales };
}

// Muestra mínima para previsualización si el usuario aún no carga Excel
const SAMPLE = {
  responsables: [
    "Recepción - María Pérez",
    "Caja - Luis Gómez",
    "Médico - Dra. López",
    "Farmacia - Carlos Ruiz",
  ],
  estados: ["Pendiente", "En progreso", "Resuelto", "Escalado"],
  sucursales: [
    "Hospital Central",
    "Clínica Amatitlán",
    "Clínica Mixco",
  ],
  rows: [
    {
      id: "1-FIA_P001-FIA_P001A",
      codigo: "FIA_P001",
      pregunta:
        "¿El personal de recepción le explicó de forma clara y sencilla todos los pasos que debía seguir para su consulta?",
      subcodigo: "FIA_P001A",
      subpregunta: "Explicación confusa",
      sucursal: "Hospital Central",
      activa: true,
      responsable: "Recepción - María Pérez",
      accion: "",
      avance: 15,
      estado: "Pendiente",
    },
    {
      id: "2-FIA_P002-FIA_P002A",
      codigo: "FIA_P002",
      pregunta: "¿La atención en caja o el pago de sus servicios fue rápida?",
      subcodigo: "FIA_P002A",
      subpregunta: "Caja muy lenta",
      sucursal: "Clínica Amatitlán",
      activa: true,
      responsable: "Caja - Luis Gómez",
      accion: "",
      avance: 0,
      estado: "Escalado",
    },
    {
      id: "3-CAP_P006-CAP_P006A",
      codigo: "CAP_P006",
      pregunta: "¿Recibió atención rápidamente después de llegar al hospital/clínica?",
      subcodigo: "CAP_P006A",
      subpregunta: "Mucha espera",
      sucursal: "Hospital Central",
      activa: false,
      responsable: "",
      accion: "",
      avance: 0,
      estado: "Pendiente",
    },
  ],
};

function downloadJSON(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [rows, setRows] = useState([]);
  const [responsables, setResponsables] = useState([]);
  const [estados, setEstados] = useState([]);
  const [sucursales, setSucursales] = useState([]);

  // Filtros
  const [filterSucursal, setFilterSucursal] = useState("Todos");
  const [filterEstado, setFilterEstado] = useState("Todos");
  const [filterResponsable, setFilterResponsable] = useState("Todos");
  const [q, setQ] = useState("");

  // Modal
  const [openEdit, setOpenEdit] = useState(false);
  const [draft, setDraft] = useState(null);

  useEffect(() => {
    // Carga de muestra para previsualización
    setRows(SAMPLE.rows);
    setResponsables(SAMPLE.responsables);
    setEstados(SAMPLE.estados);
    setSucursales(SAMPLE.sucursales);
  }, []);

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      const okSuc = filterSucursal === "Todos" || r.sucursal === filterSucursal;
      const okEst = filterEstado === "Todos" || r.estado === filterEstado;
      const okResp = filterResponsable === "Todos" || r.responsable === filterResponsable;
      const okQ = !q
        ? true
        : [r.codigo, r.pregunta, r.subcodigo, r.subpregunta, r.sucursal, r.responsable]
            .join(" ")
            .toLowerCase()
            .includes(q.toLowerCase());
      return okSuc && okEst && okResp && okQ;
    });
  }, [rows, filterSucursal, filterEstado, filterResponsable, q]);

  const openEditRow = (row) => {
    setDraft({ ...row });
    setOpenEdit(true);
  };

  const saveDraft = () => {
    setRows((prev) => prev.map((r) => (r.id === draft.id ? { ...draft } : r)));
    setOpenEdit(false);
  };

  const removeRow = (row) => {
    if (!confirm("¿Eliminar este registro?")) return;
    setRows((prev) => prev.filter((r) => r.id !== row.id));
  };

  const handleFile = async (file) => {
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(buf);
    const { rows: rws, responsables: resps, estados: sts, sucursales: sucs } = parseWorkbookToRows(wb);

    // Autogenerar sugerencias para entradas activas sin acción
    const withSugg = rws.map((r) => ({
      ...r,
      accion: r.accion || (r.activa ? suggestActionFromText(`${r.subpregunta} ${r.pregunta}`) : ""),
    }));

    setRows(withSugg);
    setResponsables(resps.length ? resps : SAMPLE.responsables);
    setEstados(sts.length ? sts : SAMPLE.estados);
    setSucursales(sucs.length ? sucs : SAMPLE.sucursales);
  };

  const exportXLSX = () => {
    const sheet = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, sheet, "seguimiento");
    const wbout = XLSX.write(wb, { type: "array", bookType: "xlsx" });
    const blob = new Blob([wbout], { type: "application/octet-stream" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "SEGUIMIENTO_SERVQUAL.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  };

  const addBlank = () => {
    const id = crypto.randomUUID();
    const n = {
      id,
      codigo: "",
      pregunta: "",
      subcodigo: "",
      subpregunta: "",
      sucursal: sucursales[0] || "",
      activa: false,
      responsable: responsables[0] || "",
      accion: "",
      avance: 0,
      estado: estados[0] || "Pendiente",
    };
    setRows((p) => [n, ...p]);
  };

  const bulkSuggest = () => {
    setRows((prev) =>
      prev.map((r) => ({
        ...r,
        accion: r.accion || (r.activa ? suggestActionFromText(`${r.subpregunta} ${r.pregunta}`) : ""),
      }))
    );
  };

  const progressTone = (v) => (v >= 80 ? "green" : v >= 40 ? "yellow" : "red");

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-2xl bg-[#1160C7] text-white grid place-items-center font-bold">SQ</div>
            <div>
              <h1 className="text-base font-semibold leading-tight">Seguimiento SERVQUAL • APROFAM</h1>
              <p className="text-xs text-slate-500">Control de inconsistencias por sucursal, responsable y estado</p>
            </div>
          </div>

          <div className="ml-auto flex flex-wrap items-center gap-2">
            <label className="inline-flex items-center gap-2 rounded-xl border bg-white px-3 py-1.5 text-sm shadow-sm">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-slate-500"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <input type="file" accept=".xlsx,.xls" className="hidden" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
              <span>Cargar Excel</span>
            </label>
            <IconButton title="Cargar muestra" onClick={() => {
              setRows(SAMPLE.rows);
              setResponsables(SAMPLE.responsables);
              setEstados(SAMPLE.estados);
              setSucursales(SAMPLE.sucursales);
            }} className="bg-white">
              Demo
            </IconButton>
            <IconButton title="Agregar registro" onClick={addBlank} className="bg-white">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </IconButton>
            <IconButton title="Autocompletar sugerencias" onClick={bulkSuggest} className="bg-white">
              Sugerir acciones
            </IconButton>
            <IconButton title="Exportar a Excel" onClick={exportXLSX} className="bg-white">
              Exportar
            </IconButton>
            <IconButton title="Exportar JSON" onClick={() => downloadJSON("seguimiento.json", rows)} className="bg-white">
              JSON
            </IconButton>
          </div>
        </div>
      </header>

      {/* Filtros */}
      <section className="mx-auto max-w-7xl px-4 py-3">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
          <div className="col-span-2">
            <input
              className="w-full rounded-xl border bg-white px-3 py-2 text-sm shadow-sm"
              placeholder="Buscar (código, texto, subpregunta, responsable)"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <select className="rounded-xl border bg-white px-3 py-2 text-sm shadow-sm" value={filterSucursal} onChange={(e) => setFilterSucursal(e.target.value)}>
            <option>Todos</option>
            {sucursales.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select className="rounded-xl border bg-white px-3 py-2 text-sm shadow-sm" value={filterEstado} onChange={(e) => setFilterEstado(e.target.value)}>
            <option>Todos</option>
            {estados.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select className="rounded-xl border bg-white px-3 py-2 text-sm shadow-sm" value={filterResponsable} onChange={(e) => setFilterResponsable(e.target.value)}>
            <option>Todos</option>
            {responsables.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </div>
      </section>

      {/* Tabla */}
      <main className="mx-auto max-w-7xl px-4 pb-24">
        <div className="overflow-auto rounded-2xl border bg-white shadow-sm">
          <table className="min-w-[1000px] w-full border-collapse text-sm">
            <thead className="sticky top-[58px] bg-slate-100 text-slate-700">
              <tr>
                <th className="px-3 py-2 text-left">Acciones</th>
                <th className="px-3 py-2 text-left">Sucursal</th>
                <th className="px-3 py-2 text-left">Código</th>
                <th className="px-3 py-2 text-left">Pregunta</th>
                <th className="px-3 py-2 text-left">Subcód / Subpregunta</th>
                <th className="px-3 py-2 text-left">Activa</th>
                <th className="px-3 py-2 text-left">Responsable</th>
                <th className="px-3 py-2 text-left">Acción correctiva sugerida</th>
                <th className="px-3 py-2 text-left">Avance</th>
                <th className="px-3 py-2 text-left">Estado</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} className="border-t hover:bg-slate-50">
                  <td className="px-3 py-2">
                    <div className="flex gap-2">
                      <IconButton title="Modificar" onClick={() => openEditRow(r)} className="bg-white">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
                      </IconButton>
                      <IconButton title="Eliminar" onClick={() => removeRow(r)} className="bg-white">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/></svg>
                      </IconButton>
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">{r.sucursal || <SafeTag tone="orange">(sin sucursal)</SafeTag>}</td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <SafeTag tone="blue">{r.codigo || "—"}</SafeTag>
                    </div>
                  </td>
                  <td className="px-3 py-2 max-w-[300px]"><div className="line-clamp-2">{r.pregunta}</div></td>
                  <td className="px-3 py-2 max-w-[280px]">
                    <div className="flex items-center gap-2">
                      <SafeTag tone="violet">{r.subcodigo || "—"}</SafeTag>
                      <span className="line-clamp-2 text-slate-700">{r.subpregunta}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    {r.activa ? <SafeTag tone="red">Activa</SafeTag> : <SafeTag>Inactiva</SafeTag>}
                  </td>
                  <td className="px-3 py-2">{r.responsable || <span className="text-slate-400">—</span>}</td>
                  <td className="px-3 py-2"><div className="line-clamp-2 text-slate-700">{r.accion || <span className="text-slate-400">(sugerencia pendiente)</span>}</div></td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-24 rounded bg-slate-200">
                        <div className={`h-2 rounded ${r.avance >= 80 ? "bg-green-500" : r.avance >= 40 ? "bg-yellow-500" : "bg-red-500"}`} style={{ width: `${r.avance}%` }} />
                      </div>
                      <SafeTag tone={progressTone(r.avance)}>{r.avance}%</SafeTag>
                    </div>
                  </td>
                  <td className="px-3 py-2">{r.estado}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-3 py-10 text-center text-slate-500">Sin resultados con los filtros actuales.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </main>

      {/* Modal de edición */}
      <Modal open={openEdit} onClose={() => setOpenEdit(false)} title="Modificar registro">
        {draft && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-600">Sucursal</label>
              <select className="w-full rounded-xl border px-3 py-2 text-sm" value={draft.sucursal} onChange={(e) => setDraft((d) => ({ ...d, sucursal: e.target.value }))}>
                {sucursales.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-600">Estado</label>
              <select className="w-full rounded-xl border px-3 py-2 text-sm" value={draft.estado} onChange={(e) => setDraft((d) => ({ ...d, estado: e.target.value }))}>
                {estados.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-600">Responsable</label>
              <select className="w-full rounded-xl border px-3 py-2 text-sm" value={draft.responsable} onChange={(e) => setDraft((d) => ({ ...d, responsable: e.target.value }))}>
                <option value="">—</option>
                {responsables.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-600">Subpregunta activa</label>
              <div className="flex items-center gap-2">
                <input type="checkbox" checked={draft.activa} onChange={(e) => setDraft((d) => ({ ...d, activa: e.target.checked }))} />
                <SafeTag tone={draft.activa ? "red" : "slate"}>{draft.activa ? "Activa" : "Inactiva"}</SafeTag>
              </div>
            </div>

            <div className="md:col-span-2 space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-600">Acción correctiva sugerida</label>
                <button
                  className="text-xs text-blue-600 hover:underline"
                  onClick={() => setDraft((d) => ({ ...d, accion: suggestActionFromText(`${d.subpregunta} ${d.pregunta}`) }))}
                >
                  Sugerir automáticamente
                </button>
              </div>
              <textarea
                className="min-h-[110px] w-full rounded-xl border px-3 py-2 text-sm"
                value={draft.accion}
                onChange={(e) => setDraft((d) => ({ ...d, accion: e.target.value }))}
                placeholder="Describa la acción correctiva (SMART): qué, quién, cuándo, cómo se medirá."
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-600">Avance (%)</label>
              <input
                type="number"
                min={0}
                max={100}
                className="w-full rounded-xl border px-3 py-2 text-sm"
                value={draft.avance}
                onChange={(e) => setDraft((d) => ({ ...d, avance: Math.max(0, Math.min(100, Number(e.target.value) || 0)) }))}
              />
            </div>

            <div className="md:col-span-2 flex justify-end gap-2 pt-2">
              <IconButton className="bg-white" title="Cancelar" onClick={() => setOpenEdit(false)}>Cancelar</IconButton>
              <IconButton className="bg-[#1160C7] text-white" title="Guardar cambios" onClick={saveDraft}>Guardar</IconButton>
            </div>
          </div>
        )}
      </Modal>

      {/* Footer */}
      <footer className="fixed bottom-3 left-1/2 z-30 -translate-x-1/2 rounded-full border bg-white/95 px-4 py-2 text-xs text-slate-600 shadow-lg">
        Filtros activos: {filterSucursal}/{filterEstado}/{filterResponsable} • Registros: {filtered.length} de {rows.length}
      </footer>
    </div>
  );
}
