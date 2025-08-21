import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date

# ---------- ESTILO / BRANDING ----------
PRIMARY = "#1160C7"
YELLOW  = "#FFC600"
DARK    = "#00315E"

st.set_page_config(page_title="Matriz de Seguimiento SERVQUAL - APROFAM", page_icon="✅", layout="wide")

st.markdown(
    f"""
    <style>
    .big-title {{ font-size: 1.6rem; font-weight: 800; color:{DARK}; }}
    .pill {{
        display:inline-block; padding:4px 10px; border-radius:999px;
        font-weight:600; margin-right:6px; font-size:.8rem; color:white; background:{PRIMARY};
    }}
    .stButton>button {{
        background:{PRIMARY}; color:white; border:0; border-radius:10px; padding:8px 16px;
        font-weight:700;
    }}
    .danger>button {{ background:#d7263d!important; }}
    .soft>button {{ background:{YELLOW}!important; color:#1c1c1c!important; }}
    .section-title {{ font-weight:800; color:{DARK}; margin-top:6px; }}
    </style>
""",
    unsafe_allow_html=True
)

# Extra CSS for data editor wrapping
st.markdown(
    """
    <style>
    div[data-testid="stDataFrame"] div[role="gridcell"] { 
        white-space: normal !important; 
        line-height: 1.3 !important;
    }
    div[data-testid="stDataFrame"] div[role="row"] { min-height: 46px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- LOGIN SENCILLO ----------
def login(username: str, password: str) -> bool:
    return username.strip().lower() == "admin" and password == "Aprof@n2025"

if "authed" not in st.session_state:
    st.session_state.authed = False

with st.sidebar:
    st.markdown("<div class='big-title'>SERVQUAL • APROFAM</div>", unsafe_allow_html=True)
    st.caption("Matriz de acción y seguimiento")

    if not st.session_state.authed:
        u = st.text_input("Usuario", value="", placeholder="admin")
        p = st.text_input("Contraseña", value="", type="password", placeholder="••••••••")
        if st.button("Ingresar"):
            st.session_state.authed = login(u, p)
            if not st.session_state.authed:
                st.error("Usuario o contraseña incorrectos.")
        st.stop()
    else:
        st.success("Sesión iniciada")
        if st.button("Cerrar sesión", type="primary"):
            st.session_state.clear()
            st.rerun()

# ---------- CATÁLOGOS ----------
# Subproblemas por código (catálogo ampliable)
SUBPROBLEMAS = {
    "FIA_P001": [
        "FIA_P001A - Explicación confusa",
        "FIA_P001B - Faltó información",
        "FIA_P001C - Personal desatento",
        "FIA_P001D - Lenguaje técnico",
    ],
}
ALL_SUBP_OPTIONS = sorted({opt for lst in SUBPROBLEMAS.values() for opt in lst})

CAT_RESPONSABLES = [
    "BRYSEYDA A. ZUÑIGA GOMEZ",
    "DANIEL ALEJANDRO MONTERROSO MORALES",
    "DARWIN RENE RODAS CHEGUEN",
    "EDWIN HAROLDO MAYEN ALVARADO",
    "EVELYN ROCIO RUIZ BARRIENTOS",
    "EYBI VINICIO BEDOYA AVILA",
    "HECTOR LEONARDO MEJIA SANCHEZ",
    "IVAN ALBERTO MOLINA ALVAREZ",
    "JENNIFER ANDREA JACOBO GALVEZ",
    "MARIO FERNANDO HERNANDEZ PINEDA",
    "MARITZA ELIZABETH CHANG GODINEZ DE VALLE",
    "MIRIAM YESENIA PAREDES QUINTEROS",
]

SUCURSALES = [
    "CLINICA AMATITLAN","CLINICA ANTIGUA","CLINICA BARBERENA","CLINICA CHIMALTENANGO",
    "CLINICA MALACATAN","CLINICA MAZATENANGO","CLINICA PUERTO BARRIOS","CLINICA QUICHE",
    "CLINICA RETALHULEU","CLINICA VILLA NUEVA","CLINICA ZONA 6","CLINICA ZONA 19",
    "HOSPITAL CENTRAL","HOSPITAL COATEPEQUE","HOSPITAL COBAN","HOSPITAL ESCUINTLA",
    "HOSPITAL HUEHUETENANGO","HOSPITAL JUTIAPA","HOSPITAL PETEN","HOSPITAL QUETZALTENANGO",
    "HOSPITAL SAN PEDRO","HOSPITAL ZACAPA","CLINICA ZONA 17"
]

CAT_ESTADO = ["Pendiente", "En progreso", "Completado", "Bloqueado"]
CAT_PLAZO  = ["15 días", "30 días", "45 días", "60 días"]
CAT_DIM    = ["FIABILIDAD", "CAPACIDAD DE RESPUESTA", "SEGURIDAD", "EMPATÍA", "ASPECTOS TANGIBLES", "EXPERIENCIA/EXPANSIÓN"]

# 28 preguntas (código + texto corto)
PREGUNTAS = [
    ("FIA_P001","¿El personal de recepción le explicó de forma clara y sencilla todos los pasos que debía seguir para su consulta?"),
    ("FIA_P002","¿Caja/pago fue rápido?"),
    ("FIA_P003","¿Respetaron orden y turno?"),
    ("FIA_P004","¿Doctor explicó diagnóstico claramente?"),
    ("FIA_P005","¿Fue fácil obtener su cita?"),
    ("CAP_P006","¿Atención rápida tras llegada?"),
    ("CAP_P007","¿Informaron otros servicios APROFAM?"),
    ("CAP_P008","¿Call center rápido y resolutivo?"),
    ("CAP_P009","¿Farmacia cumplió lo esperado?"),
    ("SEG_P010","¿Médico/enfermera inspiraron confianza?"),
    ("SEG_P011","¿Examen físico completo?"),
    ("SEG_P012","¿Respondió todas sus preguntas?"),
    ("SEG_P013","¿Instalaciones limpias/seguras?"),
    ("SEG_P014","¿Explicaron procedimientos claramente?"),
    ("SEG_P015","¿Explicaron medicamentos y cuidados?"),
    ("EMP_P016","¿Trato amable, respeto y paciencia?"),
    ("EMP_P017","¿Médico mostró interés real?"),
    ("EMP_P018","¿Consejos personalizados de salud?"),
    ("TAN_P019","¿Instalaciones accesibles y cómodas?"),
    ("TAN_P020","¿Recibió recordatorios claros?"),
    ("TAN_P021","¿Espera en servicios fue razonable?"),
    ("EXP_P022","¿Informaron servicios extra (vacunas, etc.)?"),
    ("EXP_P023","¿Mencionaron telemedicina/virtual?"),
    ("EXP_P024","¿Servicios para atender a su familia?"),
    ("EXP_P025","¿Encontró info confiable de APROFAM?"),
    ("EXP_P026","¿Precio del servicio fue justo?"),
    ("EXP_P027","¿APROFAM es su 1ª opción (lab/farma/img)?"),
    ("EXP_P028","¿Recomendaría APROFAM?"),
]
MAP_DIM = {
    **{k:"FIABILIDAD" for k in ["FIA_P001","FIA_P002","FIA_P003","FIA_P004","FIA_P005"]},
    **{k:"CAPACIDAD DE RESPUESTA" for k in ["CAP_P006","CAP_P007","CAP_P008","CAP_P009"]},
    **{k:"SEGURIDAD" for k in ["SEG_P010","SEG_P011","SEG_P012","SEG_P013","SEG_P014","SEG_P015"]},
    **{k:"EMPATÍA" for k in ["EMP_P016","EMP_P017","EMP_P018"]},
    **{k:"ASPECTOS TANGIBLES" for k in ["TAN_P019","TAN_P020","TAN_P021"]},
    **{k:"EXPERIENCIA/EXPANSIÓN" for k in ["EXP_P022","EXP_P023","EXP_P024","EXP_P025","EXP_P026","EXP_P027","EXP_P028"]},
}

# ---------- ESTADO INICIAL ----------
# ---------- TYPE COERCION ----------
def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    if "Fecha seguimiento" in df.columns:
        df["Fecha seguimiento"] = pd.to_datetime(df["Fecha seguimiento"], errors="coerce").dt.date
    if "% Avance" in df.columns:
        df["% Avance"] = pd.to_numeric(df["% Avance"], errors="coerce").fillna(0).astype(int)
    # Ensure object dtype for select columns
    for c in ["Código","Dimensión","Pregunta evaluada","Subproblema identificado","Causa raíz",
              "Acción correctiva","Responsable","Plazo","Estado","Sucursal"]:
        if c in df.columns:
            df[c] = df[c].astype(object)
    return df

DEFAULT_COLS = [
    "Código","Dimensión","Pregunta evaluada","Subproblema identificado","Causa raíz",
    "Acción correctiva","Fecha seguimiento","Responsable","Plazo","Estado","% Avance","Sucursal"
]
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=DEFAULT_COLS)

# Apply deferred filter overrides BEFORE widgets are created
ov = st.session_state.pop("_override_filters", None)
if ov:
    for k,v in ov.items():
        st.session_state[k] = v

# ---------- HEADER ----------
st.markdown("<span class='big-title'>PLAN DE ACCIÓN • MATRIZ DE SEGUIMIENTO</span>", unsafe_allow_html=True)
st.write(
    f"<span class='pill'>Total preguntas: 28</span>"
    f"<span class='pill' style='background:{YELLOW}; color:{DARK}'>Responsables: {len(CAT_RESPONSABLES)}</span>"
    f"<span class='pill'>Sucursales: {len(SUCURSALES)}</span>",
    unsafe_allow_html=True
)

# Extra CSS for data editor wrapping
st.markdown(
    """
    <style>
    div[data-testid="stDataFrame"] div[role="gridcell"] { 
        white-space: normal !important; 
        line-height: 1.3 !important;
    }
    div[data-testid="stDataFrame"] div[role="row"] { min-height: 46px !important; }
    </style>
    """,
    unsafe_allow_html=True
)
st.divider()

# ===========================
# 1) FILTROS DE VISUALIZACIÓN
# ===========================
st.markdown("<div class='section-title'>Filtros de visualización</div>", unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 1.2, 1.2])
opts_dim = ["Todas"]+CAT_DIM
dim_val = st.session_state.get("f_dim", "Todas")
dim_idx = opts_dim.index(dim_val) if dim_val in opts_dim else 0
with fc1:
    f_dim = st.selectbox("Dimensión", opts_dim, index=dim_idx, key="f_dim")
opts_resp = ["Todos"]+CAT_RESPONSABLES
resp_val = st.session_state.get("f_resp", "Todos")
resp_idx = opts_resp.index(resp_val) if resp_val in opts_resp else 0
with fc2:
    f_resp = st.selectbox("Responsable", opts_resp, index=resp_idx, key="f_resp")
opts_est = ["Todos"]+CAT_ESTADO
est_val = st.session_state.get("f_estado", "Todos")
est_idx = opts_est.index(est_val) if est_val in opts_est else 0
with fc3:
    f_estado = st.selectbox("Estado", opts_est, index=est_idx, key="f_estado")
with fc4:
    f_suc = st.multiselect("Sucursal", SUCURSALES, default=st.session_state.get("f_suc", []), key="f_suc")

st.divider()

# ==============================
# 2) AGREGAR FILAS POR DIMENSIÓN
# ==============================
st.markdown("<div class='section-title'>Agregar filas por dimensión</div>", unsafe_allow_html=True)
ac1, ac2, ac3, ac4, ac5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2])
with ac1:
    dim_to_add = st.selectbox("Dimensión a cargar", CAT_DIM, index=0, key="dim_to_add")
with ac2:
    resp_to_add = st.selectbox("Responsable (asignar)", [""]+CAT_RESPONSABLES, index=0, key="resp_to_add")
with ac3:
    estado_to_add = st.selectbox("Estado (asignar)", CAT_ESTADO, index=0, key="estado_to_add")
with ac4:
    avance_to_add = st.slider("% Avance (asignar)", 0, 100, 0, 5, key="avance_to_add")
with ac5:
    suc_to_add = st.selectbox("Sucursal (asignar)", SUCURSALES, index=0, key="suc_to_add")

pregs_dim = [ (c,t) for c,t in PREGUNTAS if MAP_DIM[c] == dim_to_add ]
labels_dim = [ f"{c} – {t}" for c,t in pregs_dim ]

sel_all = st.checkbox("Seleccionar TODAS las preguntas de esta dimensión", value=True)
if not sel_all:
    sel_labels = st.multiselect("Seleccionar preguntas específicas", labels_dim, default=labels_dim)
else:
    sel_labels = labels_dim

if st.button("➕ Agregar por dimensión", type="primary"):
    new_rows = []
    for opt in sel_labels:
        codigo = opt.split(" – ")[0]
        new_rows.append({
            "Código": codigo,
            "Dimensión": MAP_DIM[codigo],
            "Pregunta evaluada": opt,
            "Subproblema identificado": "",
            "Causa raíz": "",
            "Acción correctiva": "",
            "Fecha seguimiento": date.today(),
            "Responsable": resp_to_add,
            "Plazo": "30 días",
            "Estado": estado_to_add,
            "% Avance": avance_to_add,
            "Sucursal": suc_to_add,
        })
    if new_rows:
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True)
        st.session_state.df = _coerce_types(st.session_state.df)
        # Defer filter changes to next rerun to avoid StreamlitAPIException
        st.session_state["_override_filters"] = {
            "f_dim": dim_to_add,
            "f_resp": (resp_to_add if resp_to_add else "Todos"),
            "f_estado": estado_to_add,
            "f_suc": [suc_to_add],
        }
        st.success(f"Agregadas {len(new_rows)} filas de {dim_to_add}.")
        st.rerun()

st.divider()

# =====================
# 3) MATRIZ (EDITABLE)
# =====================
st.session_state.df = _coerce_types(st.session_state.df)

df_view = st.session_state.df.copy()
if f_dim != "Todas":
    df_view = df_view[df_view["Dimensión"] == f_dim]
if f_resp != "Todos":
    df_view = df_view[df_view["Responsable"] == f_resp]
if f_estado != "Todos":
    df_view = df_view[df_view["Estado"] == f_estado]
if f_suc:
    df_view = df_view[df_view["Sucursal"].isin(f_suc)]

if len(st.session_state.df) and df_view.empty:
    st.info("No hay filas que coincidan con los filtros activos. Revisa Responsable/Estado/Sucursal.")

st.write("### 🧾 Matriz (editable)")
edited = st.data_editor(
    df_view,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Código": st.column_config.SelectboxColumn(options=[c for c,_ in PREGUNTAS]),
        "Dimensión": st.column_config.SelectboxColumn(options=CAT_DIM),
        "Pregunta evaluada": st.column_config.SelectboxColumn(options=[f"{c} – {t}" for c,t in PREGUNTAS], width="large"),
        "Subproblema identificado": st.column_config.SelectboxColumn(options=(ALL_SUBP_OPTIONS if ALL_SUBP_OPTIONS else [""]), help="Opciones dependen del código (por ahora: FIA_P001). Si no aplica, puedes escribir texto libre en la celda."),
        "Responsable": st.column_config.SelectboxColumn(options=[""]+CAT_RESPONSABLES),
        "Plazo": st.column_config.TextColumn(help="Campo abierto (ej. 30 días, 2025-09-15, 6 semanas)"),
        "Estado": st.column_config.SelectboxColumn(options=CAT_ESTADO),
        "Sucursal": st.column_config.SelectboxColumn(options=SUCURSALES),
        "% Avance": st.column_config.NumberColumn(format="%.0f", min_value=0, max_value=100, step=5),
        "Fecha seguimiento": st.column_config.DateColumn(),
    },
    hide_index=True
)

if not edited.equals(df_view):
    idx_global = st.session_state.df.index[df_view.index]
    st.session_state.df.loc[idx_global, :] = edited.values


# ----- Asistente para asignar subproblema por fila -----
with st.expander("🎯 Asignar subproblema sugerido por código"):
    if st.session_state.df.empty:
        st.info("No hay filas en la matriz.")
    else:
        idx = st.selectbox("Elige la fila", options=list(st.session_state.df.index))
        cod_actual = st.session_state.df.loc[idx, "Código"] if "Código" in st.session_state.df.columns else None
        if not cod_actual or cod_actual not in SUBPROBLEMAS:
            st.warning("La fila seleccionada no tiene un código con catálogo disponible.")
        else:
            opt = st.selectbox("Opciones sugeridas", SUBPROBLEMAS[cod_actual])
            if st.button("Aplicar a la fila seleccionada"):
                st.session_state.df.loc[idx, "Subproblema identificado"] = opt
                st.success("Subproblema asignado.")
                st.rerun()


with st.expander("🗑️ Eliminar filas"):
    if len(st.session_state.df) == 0:
        st.info("No hay filas en la matriz.")
    else:
        to_delete = st.multiselect("Selecciona por índice para eliminar", options=list(st.session_state.df.index))
        if st.button("Eliminar seleccionadas", type="primary", key="del"):
            st.session_state.df.drop(index=to_delete, inplace=True)
            st.session_state.df.reset_index(drop=True, inplace=True)
            st.success("Filas eliminadas.")

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Matriz")
    return buffer.getvalue()

st.download_button(
    "⬇️ Exportar a Excel",
    data=to_excel_bytes(st.session_state.df),
    file_name="matriz_servqual_aprofam.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
