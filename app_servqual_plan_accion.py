"""
Plan de Acción • SERVQUAL (modo dual)

Este archivo funciona en dos modos:
1) **Modo Streamlit** (UI completa): si el paquete `streamlit` está disponible, se
   renderiza la interfaz como app web para crear/editar/exportar la matriz.
2) **Modo librería** (sin Streamlit): si NO hay `streamlit`, el módulo se puede
   importar sin errores. En este modo quedan accesibles las funciones de
   manipulación de datos (carga, guardado, alta por dimensión, etc.), lo que
   permite correr pruebas o usar el código desde otros scripts.

Además, se usa almacenamiento en **CSV** para evitar dependencias extra (por

Ej. `pyarrow`) que requiere Parquet.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import pandas as pd

# -------------------------------------------------------------
# Detectar si Streamlit está disponible (modo dual)
# -------------------------------------------------------------
try:  # pragma: no cover - la detección no es parte de la lógica de negocio
    import streamlit as st  # type: ignore
    _HAS_ST = True
except Exception:  # ImportError o similar -> modo librería
    st = None  # type: ignore
    _HAS_ST = False

# -------------------------------------------------------------
# CONSTANTES / CATÁLOGOS (comparten UI y librería)
# -------------------------------------------------------------
DIMENSIONES = [
    ("FIA", "FIABILIDAD"),
    ("CAP", "CAPACIDAD DE RESPUESTA"),
    ("SEG", "SEGURIDAD"),
    ("EMP", "EMPATÍA"),
    ("TAN", "ASPECTOS TANGIBLES"),
    ("EXP", "EXPERIENCIA / EXPANSIÓN"),
]

ESTADOS = ["Pendiente", "En progreso", "Completado", "Bloqueado"]

RESPONSABLES = [
    "BRYSEYDA A. ZUÑIGA GOMEZ",
    "DANIEL ALEJANDRO MONTERR0SO MORALES",
    "DARWIN RENE RODAS CHEGUEN",
    "IVAN ALBERTO MOLINA ALVAREZ",
]

SUCURSALES = [
    "CLINICA AMATITLAN",
    "CLINICA ANTIGUA",
    "CLINICA MAZATENANGO",
]

# Mapa: código -> (dimensión, texto de la pregunta)
PREGUNTAS: dict[str, tuple[str, str]] = {
    # FIABILIDAD (5)
    "FIA_P001": (
        "FIABILIDAD",
        "¿El personal de recepción le explicó de forma clara y sencilla todos los pasos que debía seguir para su consulta?",
    ),
    "FIA_P002": ("FIABILIDAD", "¿La atención en caja o el pago de sus servicios fue rápida?"),
    "FIA_P003": ("FIABILIDAD", "¿Respetaron el orden de llegada y su turno para atenderle?"),
    "FIA_P004": ("FIABILIDAD", "¿El doctor le explicó de manera clara y detallada su diagnóstico?"),
    "FIA_P005": ("FIABILIDAD", "¿Fue fácil obtener su cita?"),
    # CAPACIDAD DE RESPUESTA (4)
    "CAP_P006": (
        "CAPACIDAD DE RESPUESTA",
        "¿Recibió atención rápidamente después de llegar al hospital/clínica?",
    ),
    "CAP_P007": (
        "CAPACIDAD DE RESPUESTA",
        "¿El personal le informó sobre otros servicios o programas de APROFAM que podrían complementar su cuidado de salud?",
    ),
    "CAP_P008": (
        "CAPACIDAD DE RESPUESTA",
        "¿El personal del call center atendió su llamada con rapidez y resolvió su solicitud?",
    ),
    "CAP_P009": (
        "CAPACIDAD DE RESPUESTA",
        "¿Su experiencia en la farmacia del hospital/clínica fue la que esperaba?",
    ),
    # SEGURIDAD (6)
    "SEG_P010": (
        "SEGURIDAD",
        "¿El médico y la enfermera le inspiraron confianza en la atención?",
    ),
    "SEG_P011": (
        "SEGURIDAD",
        "¿El médico le examinó físicamente de forma completa según su problema de salud?",
    ),
    "SEG_P012": ("SEGURIDAD", "¿El doctor le respondió todas sus preguntas?"),
    "SEG_P013": (
        "SEGURIDAD",
        "¿Encontró el hospital/clínica limpia y en buenas condiciones?",
    ),
    "SEG_P014": (
        "SEGURIDAD",
        "¿Le explicaron de forma clara todos los procedimientos o exámenes que se debe realizar?",
    ),
    "SEG_P015": (
        "SEGURIDAD",
        "¿Le explicaron claramente cómo tomar sus medicamentos y qué cuidados debe tener en casa?",
    ),
    # EMPATÍA (3)
    "EMP_P016": (
        "EMPATÍA",
        "¿Todo el personal le trató con amabilidad, respeto y paciencia durante su visita?",
    ),
    "EMP_P017": (
        "EMPATÍA",
        "¿Sintió que el doctor realmente se interesó por resolver su problema de salud?",
    ),
    "EMP_P018": (
        "EMPATÍA",
        "¿Le dieron consejos sobre cómo mejorar su salud y prevenir complicaciones?",
    ),
    # TANGIBLES (3)
    "TAN_P019": (
        "ASPECTOS TANGIBLES",
        "¿Las instalaciones del hospital/clínica son cómodas y accesibles para personas con discapacidad?",
    ),
    "TAN_P020": (
        "ASPECTOS TANGIBLES",
        "¿Recibió recordatorios sobre su cita o promoción de servicios?",
    ),
    "TAN_P021": (
        "ASPECTOS TANGIBLES",
        "¿El tiempo que esperó en laboratorio, farmacia y otros servicios fue razonable?",
    ),
    # EXPERIENCIA/EXPANSIÓN (7)
    "EXP_P022": (
        "EXPERIENCIA / EXPANSIÓN",
        "¿Le informaron sobre otros servicios disponibles como vacunación, salud mental o nutrición?",
    ),
    "EXP_P023": (
        "EXPERIENCIA / EXPANSIÓN",
        "¿Le informaron sobre opciones de asesoría virtual o telemedicina disponibles para su seguimiento médico?",
    ),
    "EXP_P024": (
        "EXPERIENCIA / EXPANSIÓN",
        "¿Considera que APROFAM ofrece los servicios para atender su familia?",
    ),
    "EXP_P025": (
        "EXPERIENCIA / EXPANSIÓN",
        "¿Encontró fácilmente información confiable de APROFAM en redes sociales, página web o centros de atención?",
    ),
    "EXP_P026": (
        "EXPERIENCIA / EXPANSIÓN",
        "¿Le pareció justo el precio por el servicio que recibió?",
    ),
    "EXP_P027": (
        "EXPERIENCIA / EXPANSIÓN",
        "¿Nos considera como su primera opción en servicios de laboratorio, farmacia y ultrasonidos?",
    ),
    "EXP_P028": (
        "EXPERIENCIA / EXPANSIÓN",
        "¿Recomendaría este hospital/clínica a sus familiares y amigos por la buena atención que recibió?",
    ),
}

# Subopciones por pregunta (exactamente como en el documento)
SUBOPCIONES: dict[str, list[str]] = {
    # FIABILIDAD
    "FIA_P001": [
        "FIA_P001A - Explicación confusa",
        "FIA_P001B - Faltó información",
        "FIA_P001C - Personal desatento",
        "FIA_P001D - Lenguaje técnico",
    ],
    "FIA_P002": [
        "FIA_P002A - Caja muy lenta",
        "FIA_P002B - Cola muy larga",
        "FIA_P002C - Pocos cajeros",
        "FIA_P002D - Sistema muy lento",
    ],
    "FIA_P003": [
        "FIA_P003A - No respetaron orden",
        "FIA_P003B - Saltaron turnos",
        "FIA_P003C - Sin organización",
        "FIA_P003D - Preferencias injustas",
    ],
    "FIA_P004": [
        "FIA_P004A - Explicación rápida",
        "FIA_P004B - Muy técnico",
        "FIA_P004C - Faltó detalle",
        "FIA_P004D - No entendí",
    ],
    "FIA_P005": [
        "FIA_P005A - Sin disponibilidad",
        "FIA_P005B - Proceso complicado",
        "FIA_P005C - Mucha espera",
        "FIA_P005D - Sistema deficiente",
    ],
    # CAPACIDAD DE RESPUESTA
    "CAP_P006": [
        "CAP_P006A - Mucha espera",
        "CAP_P006B - Sistema lento",
        "CAP_P006C - Falta personal",
        "CAP_P006D - Desorganización",
    ],
    "CAP_P007": [
        "CAP_P007A - No informaron",
        "CAP_P007B - Info incompleta",
        "CAP_P007C - Personal desconocía",
        "CAP_P007D - No indagaron",
    ],
    "CAP_P008": [
        "CAP_P008A - Tardaron en responder",
        "CAP_P008B - No resolvieron mi solicitud",
        "CAP_P008C - Me transfirieron muchas veces",
        "CAP_P008D - Contestaron sin interés",
    ],
    "CAP_P009": [
        "CAP_P009A - Precios altos",
        "CAP_P009B - Sin disponibilidad",
        "CAP_P009C - Sin alternativas",
        "CAP_P009D - Me presionaron",
    ],
    # SEGURIDAD
    "SEG_P010": [
        "SEG_P010A - Parecían inexpertos",
        "SEG_P010B - Dudaron mucho",
        "SEG_P010C - Respuestas contradictorias",
        "SEG_P010D - Falta seguridad",
    ],
    "SEG_P011": [
        "SEG_P011A - Examen superficial",
        "SEG_P011B - Muy rápido",
        "SEG_P011C - Faltaron pruebas",
        "SEG_P011D - No examinó",
    ],
    "SEG_P012": [
        "SEG_P012A - Mucha prisa",
        "SEG_P012B - No preguntó",
        "SEG_P012C - Consulta corta",
        "SEG_P012D - Me interrumpió",
    ],
    "SEG_P013": [
        "SEG_P013A - Áreas sucias",
        "SEG_P013B - Baños descuidados",
        "SEG_P013C - Equipo sucio",
        "SEG_P013D - Mal olor",
    ],
    "SEG_P014": [
        "SEG_P014A - No explicaron",
        "SEG_P014B - Muy técnico",
        "SEG_P014C - Exp rápida",
        "SEG_P014D - Quedé confuso",
    ],
    "SEG_P015": [
        "SEG_P015A - Explicación confusa",
        "SEG_P015B - Muy rápido",
        "SEG_P015C - Faltó información",
        "SEG_P015D - No explicaron",
    ],
    # EMPATÍA
    "EMP_P016": [
        "EMP_P016A - Trato brusco",
        "EMP_P016B - Sin paciencia",
        "EMP_P016C - Personal grosero",
        "EMP_P016D - Me ignoraron",
    ],
    "EMP_P017": [
        "EMP_P017A - Desinteresado",
        "EMP_P017B - Muy automático",
        "EMP_P017C - No escuchó",
        "EMP_P017D - Falta empatía",
    ],
    "EMP_P018": [
        "EMP_P018A - Consejos genéricos",
        "EMP_P018B - No dieron",
        "EMP_P018C - Muy básicos",
        "EMP_P018D - No personalizados",
    ],
    # TANGIBLES
    "TAN_P019": [
        "TAN_P019A - Sin rampas",
        "TAN_P019B - Espacios estrechos",
        "TAN_P019C - Barreras físicas",
        "TAN_P019D - Mal diseño",
    ],
    "TAN_P020": [
        "TAN_P020A - Sin recordatorios",
        "TAN_P020B - Info confusa",
        "TAN_P020C - Llegó tarde",
        "TAN_P020D - No recibí",
    ],
    "TAN_P021": [
        "TAN_P021A - Mucha espera",
        "TAN_P021B - Sistema lento",
        "TAN_P021C - Falta personal",
        "TAN_P021D - Desorganización",
    ],
    # EXP / EXPANSIÓN
    "EXP_P022": [
        "EXP_P022A - No informaron",
        "EXP_P022B - Servicios limitados",
        "EXP_P022C - Personal desconocía",
        "EXP_P022D - No preguntaron",
    ],
    "EXP_P023": [
        "EXP_P023A - No conocían telemedicina",
        "EXP_P023B - Sin asesoría virtual",
        "EXP_P023C - Solo presencial",
        "EXP_P023D - Falta tecnología",
    ],
    "EXP_P024": [
        "EXP_P024A - Sin programas",
        "EXP_P024B - Servicios separados",
        "EXP_P024C - No disponible",
        "EXP_P024D - Falta integración",
    ],
    "EXP_P025": [
        "EXP_P025A - No tienen redes",
        "EXP_P025B - Difícil de encontrar",
        "EXP_P025C - Información incompleta",
        "EXP_P025D - Información desactualizada",
    ],
    "EXP_P026": [
        "EXP_P026A - Muy caro",
        "EXP_P026B - No vale",
        "EXP_P026C - Precio elevado",
        "EXP_P026D - Servicio regular",
    ],
    "EXP_P027": [
        "EXP_P027A - Mejor otros",
        "EXP_P027B - No siempre",
        "EXP_P027C - Baja oferta",
        "EXP_P027D - Poca confianza",
    ],
    "EXP_P028": [
        "EXP_P028A - Mala experiencia",
        "EXP_P028B - Mejor otras",
        "EXP_P028C - No recomendaría",
        "EXP_P028D - Problemas generales",
    ],
}

COLS = [
    "Código",
    "Dimensión",
    "Pregunta evaluada",
    "Subproblema identificado",
    "Causa raíz",
    "Acción correctiva",
    "Fecha seguimiento",
    "Responsable",
    "Plazo",
    "Estado",
    "% Avance",
    "Sucursal",
]

DATAFILE = Path("plan_accion_servqual.csv")

# -------------------------------------------------------------
# STORAGE helpers (compatibles con pruebas sin Streamlit)
# -------------------------------------------------------------
def load_data() -> pd.DataFrame:
    """Carga el CSV si existe, sino devuelve un DataFrame vacío con columnas.

    No requiere Streamlit.
    """
    if DATAFILE.exists():
        try:
            return pd.read_csv(DATAFILE)
        except Exception:
            # Si el archivo está corrupto o vacío, devolvemos estructura base
            return pd.DataFrame(columns=COLS)
    return pd.DataFrame(columns=COLS)


def save_data(df: pd.DataFrame) -> None:
    df.to_csv(DATAFILE, index=False)


# -------------------------------------------------------------
# LÓGICA DE NEGOCIO (reusable por UI y por tests)
# -------------------------------------------------------------

def preguntas_por_dimension(nombre_dimension: str) -> list[str]:
    """Devuelve los códigos de pregunta asociados a una dimensión (nombre largo).
    Ej.: "FIABILIDAD" -> ["FIA_P001", ...]
    """
    return [code for code, (dim, _) in PREGUNTAS.items() if dim == nombre_dimension]


def construir_filas_dimension(
    dimension: str,
    responsable: str,
    estado: str,
    sucursal: str,
    fecha: date | None = None,
) -> pd.DataFrame:
    """Construye un DataFrame con las filas de una dimensión y metadatos dados.

    No guarda en disco; solo genera las filas.
    """
    if fecha is None:
        fecha = date.today()

    rows = []
    for code in preguntas_por_dimension(dimension):
        _, texto = PREGUNTAS[code]
        rows.append(
            {
                "Código": code,
                "Dimensión": dimension,
                "Pregunta evaluada": texto,
                "Subproblema identificado": "",
                "Causa raíz": "",
                "Acción correctiva": "",
                "Fecha seguimiento": str(fecha),
                "Responsable": responsable,
                "Plazo": "",
                "Estado": estado,
                "% Avance": 0,
                "Sucursal": sucursal,
            }
        )
    return pd.DataFrame(rows, columns=COLS)


def upsert_por_dimension(
    base: pd.DataFrame,
    dimension: str,
    responsable: str,
    estado: str,
    sucursal: str,
    fecha: date | None = None,
) -> pd.DataFrame:
    """Agrega filas de *dimension* evitando duplicados por (Código, Sucursal).

    Devuelve el DataFrame actualizado (no guarda en disco).
    """
    nuevos = construir_filas_dimension(dimension, responsable, estado, sucursal, fecha)
    if base.empty:
        return nuevos.copy()

    # Duplicado si ya existe el par (Código, Sucursal)
    clave = ["Código", "Sucursal"]
    merged = nuevos.merge(base[clave], on=clave, how="left", indicator=True)
    to_add = nuevos[merged["_merge"] == "left_only"][COLS]
    if to_add.empty:
        return base.copy()
    return pd.concat([base, to_add], ignore_index=True)


# -------------------------------------------------------------
# UI STREAMLIT (solo si _HAS_ST es True)
# -------------------------------------------------------------

def _header_actions_ui():
    left, mid, right = st.columns([1, 2, 1])
    with left:
        if st.button("➕ Nuevo / Editar fila", use_container_width=True, key="open_modal"):
            st.session_state["modal_open"] = True
    with mid:
        df = st.session_state.df
        st.download_button(
            "⬇️ Exportar a Excel",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"PlanAccion_SERVQUAL_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with right:
        if st.button("🗑️ Eliminar seleccionadas", use_container_width=True):
            sel = st.session_state.get("selected_rows", [])
            if sel:
                st.session_state.df = st.session_state.df.drop(index=sel).reset_index(drop=True)
                save_data(st.session_state.df)
                st.toast(f"Se eliminaron {len(sel)} fila(s)")
            else:
                st.toast("Primero selecciona fila(s) en la tabla", icon="❗")


def _modal_editor_ui():
    if not st.session_state.get("modal_open"):
        return
    with st.modal("Editar / Crear fila", key="m1"):
        df = st.session_state.df
        st.write("Completa los campos obligatorios (⭐)")
        # Selector de fila opcional
        idx_sel = st.selectbox("Fila existente (opcional):", options=["<Nueva>"] + list(range(len(df))), index=0)

        if idx_sel == "<Nueva>":
            codigo = st.selectbox("⭐ Código", options=list(PREGUNTAS.keys()))
        else:
            codigo = st.selectbox(
                "⭐ Código",
                options=list(PREGUNTAS.keys()),
                index=list(PREGUNTAS.keys()).index(df.loc[idx_sel, "Código"]),
            )

        dim, texto = PREGUNTAS[codigo]
        st.caption(f"**Dimensión detectada:** {dim}")
        st.text_area("⭐ Pregunta evaluada (completa)", value=texto, key="edit_pregunta", height=80)

        sub = st.selectbox(
            "⭐ Subproblema identificado (se muestra según código)",
            options=[""] + SUBOPCIONES.get(codigo, []),
        )
        colA, colB = st.columns(2)
        with colA:
            causa = st.text_input("Causa raíz")
            accion = st.text_input("Acción correctiva")
            fecha = st.date_input("Fecha seguimiento", value=date.today())
        with colB:
            responsable = st.selectbox("⭐ Responsable", options=RESPONSABLES)
            plazo = st.text_input("Plazo (ej. 30 días)")
            estado = st.selectbox("⭐ Estado", options=ESTADOS)
            avance = st.slider("% Avance", 0, 100, 0)
        sucursal = st.selectbox("⭐ Sucursal", options=SUCURSALES)

        if st.button("💾 Guardar", type="primary"):
            new_row = {
                "Código": codigo,
                "Dimensión": dim,
                "Pregunta evaluada": st.session_state.edit_pregunta,
                "Subproblema identificado": sub,
                "Causa raíz": causa,
                "Acción correctiva": accion,
                "Fecha seguimiento": str(fecha),
                "Responsable": responsable,
                "Plazo": plazo,
                "Estado": estado,
                "% Avance": avance,
                "Sucursal": sucursal,
            }
            if idx_sel == "<Nueva>":
                st.session_state.df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            else:
                for k, v in new_row.items():
                    st.session_state.df.loc[idx_sel, k] = v
            save_data(st.session_state.df)
            st.session_state.modal_open = False
            st.rerun()


def run_streamlit_app():  # pragma: no cover - UI
    st.set_page_config(page_title="Plan de Acción • SERVQUAL", layout="wide")

    if "df" not in st.session_state:
        st.session_state.df = load_data()
    if "selected_rows" not in st.session_state:
        st.session_state.selected_rows = []

    st.title("PLAN DE ACCIÓN • MATRIZ DE SEGUIMIENTO")

    # Filtros de visualización
    with st.expander("Filtros de visualización", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            f_dim = st.selectbox("Dimensión", options=["Todas"] + [d for _, d in DIMENSIONES])
        with c2:
            f_resp = st.selectbox("Responsable", options=["Todos"] + RESPONSABLES)
        with c3:
            f_est = st.selectbox("Estado", options=["Todos"] + ESTADOS)
        with c4:
            f_suc = st.selectbox("Sucursal", options=["Todas"] + SUCURSALES)

    # Agregar por dimensión (carga masiva y guardado automático)
    with st.expander("Agregar filas por dimensión", expanded=True):
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1:
            dim_to_add = st.selectbox("Dimensión a cargar", options=[d for _, d in DIMENSIONES])
        with c2:
            resp_asignar = st.selectbox("Responsable (asignar)", options=RESPONSABLES)
        with c3:
            estado_asignar = st.selectbox("Estado (asignar)", options=ESTADOS, index=0)
        with c4:
            suc_asignar = st.selectbox("Sucursal (asignar)", options=SUCURSALES)
        colx, _ = st.columns([1, 3])
        with colx:
            st.checkbox("Seleccionar TODAS las preguntas de esta dimensión", value=True, key="_all_q")
            if st.button("➕ Agregar por dimensión", type="primary"):
                base = st.session_state.df
                updated = upsert_por_dimension(base, dim_to_add, resp_asignar, estado_asignar, suc_asignar)
                if len(updated) == len(base):
                    st.info("Nada que agregar (posibles duplicados por Código+Sucursal).")
                else:
                    st.session_state.df = updated
                    save_data(st.session_state.df)
                    st.success(f"Agregadas {len(updated) - len(base)} fila(s) de {dim_to_add}. Se guardó automáticamente.")

    # Acciones superiores (modal, exportar, eliminar)
    _header_actions_ui()
    _modal_editor_ui()

    # Aplicar filtros a una vista
    view = st.session_state.df.copy()
    if f_dim != "Todas":
        view = view[view["Dimensión"] == f_dim]
    if f_resp != "Todos":
        view = view[view["Responsable"] == f_resp]
    if f_est != "Todos":
        view = view[view["Estado"] == f_est]
    if f_suc != "Todas":
        view = view[view["Sucursal"] == f_suc]

    st.subheader("Matriz (editable)")
    st.caption(
        "Selecciona filas con la casilla del lado izquierdo para eliminarlas con el botón de arriba. Para editar una fila, usa ‘Nuevo / Editar fila’. El guardado es automático al agregar o guardar en el modal."
    )

    if view.empty:
        st.info("No hay filas que coincidan con los filtros.")
    else:
        # Añadimos una columna de selección temporal
        view = view.reset_index(names="_idx")
        sel = st.data_editor(
            view,
            column_config={
                "_idx": st.column_config.NumberColumn("Sel", help="Marca la fila para eliminar", disabled=True),
            },
            disabled=[c for c in view.columns if c != "_idx"],
            hide_index=True,
            use_container_width=True,
            height=min(560, 100 + 30 * len(view)),
        )
        st.session_state.selected_rows = sel["_idx"].tolist() if "_idx" in sel else []


# -------------------------------------------------------------
# Punto de entrada (solo lanza UI si Streamlit está disponible)
# -------------------------------------------------------------
if _HAS_ST:  # pragma: no cover - la UI no se somete a pruebas unitarias
    run_streamlit_app()

# =============================================================
# Pequeño set de pruebas sanitarias (usables sin Streamlit)
# =============================================================
if __name__ == "__main__":  # pragma: no cover
    # "Smoke tests" rápidos en modo librería
    df0 = load_data()
    df1 = upsert_por_dimension(df0, "FIABILIDAD", RESPONSABLES[0], ESTADOS[0], SUCURSALES[0])
    assert isinstance(df1, pd.DataFrame)
    assert set(COLS).issubset(set(df1.columns))
    # No debe duplicar si llamo de nuevo con los mismos parámetros
    df2 = upsert_por_dimension(df1, "FIABILIDAD", RESPONSABLES[0], ESTADOS[0], SUCURSALES[0])
    assert len(df2) == len(df1)
    print("✓ Pruebas básicas superadas (modo librería).")
