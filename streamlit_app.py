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
    .metric-card {{
        border:1px solid #e9eef5; border-left:6px solid {PRIMARY};
        padding:12px 14px; border-radius:12px; background:#fff;
    }}
    .stButton>button {{
        background:{PRIMARY}; color:white; border:0; border-radius:10px; padding:8px 16px;
        font-weight:700;
    }}
    .danger>button {{ background:#d7263d!important; }}
    .soft>button {{ background:{YELLOW}!important; color:#1c1c1c!important; }}
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
    st.image("https://i.imgur.com/t3w9wxs.png", use_column_width=True)
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

CAT_ESTADO = ["Pendiente", "En progreso", "Completado", "Bloqueado"]
CAT_PLAZO  = ["15 días", "30 días", "45 días", "60 días"]
CAT_DIM    = ["FIABILIDAD", "CAPACIDAD DE RESPUESTA", "SEGURIDAD", "EMPATÍA", "ASPECTOS TANGIBLES", "EXPERIENCIA/EXPANSIÓN"]

# 28 preguntas (código + texto corto)
PREGUNTAS = [
    ("FIA_P001","¿Recepción explicó pasos de consulta?"),
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
# mapa código->dimensión (para filtrado)
MAP_DIM = {
    **{k:"FIABILIDAD" for k in ["FIA_P001","FIA_P002","FIA_P003","FIA_P004","FIA_P005"]},
    **{k:"CAPACIDAD DE RESPUESTA" for k in ["CAP_P006","CAP_P007","CAP_P008","CAP_P009"]},
    **{k:"SEGURIDAD" for k in ["SEG_P010","SEG_P011","SEG_P012","SEG_P013","SEG_P014","SEG_P015"]},
    **{k:"EMPATÍA" for k in ["EMP_P016","EMP_P017","EMP_P018"]},
    **{k:"ASPECTOS TANGIBLES" for k in ["TAN_P019","TAN_P020","TAN_P021"]},
    **{k:"EXPERIENCIA/EXPANSIÓN" for k in ["EXP_P022","EXP_P023","EXP_P024","EXP_P025","EXP_P026","EXP_P027","EXP_P028"]},
}

# ---------- ESTADO INICIAL DE LA MATRIZ ----------
DEFAULT_COLS = [
    "Código","Dimensión","Pregunta evaluada","Subproblema identificado","Causa raíz",
    "Acción correctiva","Fecha seguimiento","Responsable","Plazo","Estado","% Avance"
]
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=DEFAULT_COLS)

# ---------- CABECERA ----------
st.markdown("<span class='big-title'>PLAN DE ACCIÓN • MATRIZ DE SEGUIMIENTO</span>", unsafe_allow_html=True)
st.write(
    f"<span class='pill'>Total preguntas: 28</span>"
    f"<span class='pill' style='background:{YELLOW}; color:{DARK}'>Catálogo responsables: {len(CAT_RESPONSABLES)}</span>",
    unsafe_allow_html=True
)
st.divider()

# ---------- CONTROLES DE FILTRO ----------
c1,c2,c3,c4 = st.columns([1.2,1.2,1.2,1])
with c1:
    f_dim = st.selectbox("Filtrar por dimensión", ["Todas"]+CAT_DIM)
with c2:
    f_resp = st.selectbox("Filtrar por responsable", ["Todos"]+CAT_RESPONSABLES)
with c3:
    f_estado = st.selectbox("Filtrar por estado", ["Todos"]+CAT_ESTADO)
with c4:
    st.caption("Acciones")
    if st.button("➕ Agregar fila", use_container_width=True):
        # Fila vacía con valores por defecto
        row = {
            "Código": "",
            "Dimensión": "",
            "Pregunta evaluada": "",
            "Subproblema identificado": "",
            "Causa raíz": "",
            "Acción correctiva": "",
            "Fecha seguimiento": date.today().isoformat(),
            "Responsable": CAT_RESPONSABLES[0],
            "Plazo": CAT_PLAZO[1],
            "Estado": "Pendiente",
            "% Avance": 0,
        }
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([row])], ignore_index=True)

# ---------- SELECTORES AMIGABLES PARA NUEVAS FILAS ----------
with st.expander("📌 Insertar nueva acción (con selectores)"):
    colA,colB = st.columns([1.2,2])
    with colA:
        opt = st.selectbox("Pregunta", options=[f"{c} – {t}" for c,t in PREGUNTAS])
        codigo = opt.split(" – ")[0]
        dimension = MAP_DIM[codigo]
    with colB:
        subp = st.text_input("Subproblema identificado", "")
        causa = st.text_input("Causa raíz", "")
        accion = st.text_input("Acción correctiva", "")
    col1,col2,col3,col4 = st.columns(4)
    with col1:
        fecha = st.date_input("Fecha de seguimiento", value=date.today())
    with col2:
        resp = st.selectbox("Responsable", CAT_RESPONSABLES)
    with col3:
        plazo = st.selectbox("Plazo", CAT_PLAZO, index=1)
    with col4:
        estado = st.selectbox("Estado", CAT_ESTADO, index=0)
    avance = st.slider("% Avance", 0, 100, 0, 5)

    if st.button("Agregar a la matriz", type="primary"):
        row = {
            "Código": codigo,
            "Dimensión": dimension,
            "Pregunta evaluada": opt,
            "Subproblema identificado": subp,
            "Causa raíz": causa,
            "Acción correctiva": accion,
            "Fecha seguimiento": fecha.isoformat(),
            "Responsable": resp,
            "Plazo": plazo,
            "Estado": estado,
            "% Avance": avance,
        }
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([row])], ignore_index=True)
        st.success("Fila agregada.")

# ---------- APLICAR FILTROS A VISTA ----------
df_view = st.session_state.df.copy()
if f_dim != "Todas":
    df_view = df_view[df_view["Dimensión"] == f_dim]
if f_resp != "Todos":
    df_view = df_view[df_view["Responsable"] == f_resp]
if f_estado != "Todos":
    df_view = df_view[df_view["Estado"] == f_estado]

# ---------- TABLA EDITABLE ----------
st.write("### 🧾 Matriz (editable)")
edited = st.data_editor(
    df_view,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Código": st.column_config.SelectboxColumn(options=[c for c,_ in PREGUNTAS]),
        "Dimensión": st.column_config.SelectboxColumn(options=CAT_DIM),
        "Pregunta evaluada": st.column_config.SelectboxColumn(options=[f"{c} – {t}" for c,t in PREGUNTAS], width="large"),
        "Responsable": st.column_config.SelectboxColumn(options=CAT_RESPONSABLES),
        "Plazo": st.column_config.SelectboxColumn(options=CAT_PLAZO),
        "Estado": st.column_config.SelectboxColumn(options=CAT_ESTADO),
        "% Avance": st.column_config.NumberColumn(format="%.0f", min_value=0, max_value=100, step=5),
        "Fecha seguimiento": st.column_config.DateColumn(),
    },
    hide_index=True
)

# Sincroniza cambios de la vista con el dataframe global
# (reemplaza únicamente el subconjunto filtrado)
if not edited.equals(df_view):
    # Localiza índices globales de las filas que están en la vista
    idx_global = st.session_state.df.index[df_view.index]
    st.session_state.df.loc[idx_global, :] = edited.values

# ---------- ELIMINAR FILAS SELECCIONADAS ----------
with st.expander("🗑️ Eliminar filas"):
    if len(st.session_state.df) == 0:
        st.info("No hay filas en la matriz.")
    else:
        to_delete = st.multiselect(
            "Selecciona por índice para eliminar",
            options=list(st.session_state.df.index),
            help="Índices del dataframe completo"
        )
        if st.button("Eliminar seleccionadas", type="primary", key="del", help="Acción irreversible", kwargs={},):
            st.session_state.df.drop(index=to_delete, inplace=True)
            st.session_state.df.reset_index(drop=True, inplace=True)
            st.success("Filas eliminadas.")

# ---------- EXPORTAR A EXCEL ----------
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Matriz")
    return buffer.getvalue()

colL, colR = st.columns([1,1])
with colL:
    st.download_button(
        "⬇️ Exportar a Excel",
        data=to_excel_bytes(st.session_state.df),
        file_name="matriz_servqual_aprofam.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
with colR:
    st.caption("Consejo: guarda tu Excel como respaldo periódico de seguimiento.")
