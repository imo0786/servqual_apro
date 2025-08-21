# streamlit_app.py
# Matriz de seguimiento SERVQUAL – APROFAM (per-row subproblema dropdown, no auto-rellenar)

import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date

# --------- AG Grid (para dropdown por fila) ---------
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
    _AGGRID_OK = True
except Exception:
    _AGGRID_OK = False

# --------- Branding / Estilo ---------
PRIMARY = "#1160C7"
YELLOW  = "#FFC600"
DARK    = "#00315E"

st.set_page_config(page_title="Matriz SERVQUAL • APROFAM", page_icon="✅", layout="wide")

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
      .section-title {{ font-weight:800; color:{DARK}; margin-top:6px; }}
      /* Envolver texto y aumentar altura en celdas */
      div[data-testid="stDataFrame"] div[role="gridcell"] {{ white-space: normal !important; line-height: 1.3 !important; }}
      div[data-testid="stDataFrame"] div[role="row"] {{ min-height: 46px !important; }}
    </style>
    """,
    unsafe_allow_html=True
)

# --------- Login ---------
def login(user: str, pwd: str) -> bool:
    return user.strip().lower() == "admin" and pwd == "Aprof@n2025"

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

# --------- Catálogos ---------
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
CAT_PLAZO_SUG = "Ej.: 30 días, 45 días, 2025-09-15"
CAT_DIM = ["FIABILIDAD", "CAPACIDAD DE RESPUESTA", "SEGURIDAD", "EMPATÍA", "ASPECTOS TANGIBLES", "EXPERIENCIA/EXPANSIÓN"]

# --------- Preguntas (28) con código + texto completo ---------
PREGUNTAS = [
    ("FIA_P001","¿El personal de recepción le explicó de forma clara y sencilla todos los pasos que debía seguir para su consulta?"),
    ("FIA_P002","¿La atención en caja o el pago de sus servicios fue rápida?"),
    ("FIA_P003","¿Respetaron el orden de llegada y su turno para atenderle?"),
    ("FIA_P004","¿El doctor le explicó de manera clara y detallada su diagnóstico?"),
    ("FIA_P005","¿Fue fácil obtener y programar su cita?"),
    ("CAP_P006","¿Recibió atención rápidamente después de llegar al hospital/clínica?"),
    ("CAP_P007","¿El personal le informó sobre otros servicios o programas de APROFAM que podrían complementar su cuidado de salud?"),
    ("CAP_P008","¿El personal del call center atendió su llamada con rapidez y resolvió su solicitud?"),
    ("CAP_P009","¿Su experiencia en la farmacia del hospital/clínica fue la que esperaba?"),
    ("SEG_P010","¿El médico y/o enfermera le inspiraron confianza en su conocimiento y diagnóstico?"),
    ("SEG_P011","¿El médico le examinó físicamente de forma completa según su problema de salud?"),
    ("SEG_P012","¿El doctor le respondió todas sus preguntas?"),
    ("SEG_P013","¿Encontró el hospital/clínica limpio y en buenas condiciones?"),
    ("SEG_P014","¿Le explicaron de forma clara todos los procedimientos o exámenes que se debe realizar?"),
    ("SEG_P015","¿Le explicaron claramente cómo tomar sus medicamentos y qué cuidados debe tener en casa?"),
    ("EMP_P016","¿El personal le trató con amabilidad, respeto y paciencia durante su visita?"),
    ("EMP_P017","¿Sintió que el doctor realmente se interesó por resolver su problema de salud?"),
    ("EMP_P018","¿Le dieron consejos sobre cómo mejorar su salud y prevenir complicaciones?"),
    ("TAN_P019","¿Las instalaciones del hospital/clínica son cómodas y accesibles para personas con discapacidad?"),
    ("TAN_P020","¿Recibió recordatorios sobre su cita o promoción de servicios?"),
    ("TAN_P021","¿El tiempo que esperó en laboratorio, farmacia y otros servicios fue razonable?"),
    ("EXP_P022","¿Le informaron sobre otros servicios disponibles como vacunación, salud mental o nutrición?"),
    ("EXP_P023","¿Le informaron sobre opciones de asesoría virtual o telemedicina disponibles para su seguimiento médico?"),
    ("EXP_P024","¿Considera que APROFAM ofrece los servicios para atender a su familia?"),
    ("EXP_P025","¿Encontró fácilmente información confiable de APROFAM en redes sociales, página web o centros de atención?"),
    ("EXP_P026","¿Le pareció justo el precio por el servicio que recibió?"),
    ("EXP_P027","¿Nos considera como su primera opción en servicios de laboratorio, farmacia y ultrasonidos?"),
    ("EXP_P028","¿Recomendaría este hospital/clínica a sus familiares y amigos por la buena atención que recibió?"),
]

MAP_DIM = {
    **{k:"FIABILIDAD" for k in ["FIA_P001","FIA_P002","FIA_P003","FIA_P004","FIA_P005"]},
    **{k:"CAPACIDAD DE RESPUESTA" for k in ["CAP_P006","CAP_P007","CAP_P008","CAP_P009"]},
    **{k:"SEGURIDAD" for k in ["SEG_P010","SEG_P011","SEG_P012","SEG_P013","SEG_P014","SEG_P015"]},
    **{k:"EMPATÍA" for k in ["EMP_P016","EMP_P017","EMP_P018"]},
    **{k:"ASPECTOS TANGIBLES" for k in ["TAN_P019","TAN_P020","TAN_P021"]},
    **{k:"EXPERIENCIA/EXPANSIÓN" for k in ["EXP_P022","EXP_P023","EXP_P024","EXP_P025","EXP_P026","EXP_P027","EXP_P028"]},
}

# --------- Subproblemas por código ---------
SUBPROBLEMAS = {
    "FIA_P001": ["FIA_P001A - Explicación confusa","FIA_P001B - Faltó información","FIA_P001C - Personal desatento","FIA_P001D - Lenguaje técnico"],
    "FIA_P002": ["FIA_P002A - Caja muy lenta","FIA_P002B - Cola muy larga","FIA_P002C - Pocos cajeros","FIA_P002D - Sistema muy lento"],
    "FIA_P003": ["FIA_P003A - No respetaron orden","FIA_P003B - Saltaron turnos","FIA_P003C - Sin organización","FIA_P003D - Preferencias injustas"],
    "FIA_P004": ["FIA_P004A - Explicación insuficiente","FIA_P004B - Lenguaje técnico","FIA_P004C - Poco tiempo para preguntas"],
    "FIA_P005": ["FIA_P005A - Dificultad para agendar","FIA_P005B - Canales saturados","FIA_P005C - Información confusa"],

    "CAP_P006": ["CAP_P006A - Mucha espera","CAP_P006B - Sistema lento","CAP_P006C - Falta personal","CAP_P006D - Desorganización"],
    "CAP_P007": ["CAP_P007A - No mencionaron otros servicios","CAP_P007B - Información poco clara","CAP_P007C - Personal no conocía los servicios","CAP_P007D - No indagaron necesidades adicionales"],
    "CAP_P008": ["CAP_P008A - Tardaron en responder","CAP_P008B - No resolvieron la solicitud","CAP_P008C - Muchas transferencias","CAP_P008D - Contestaron sin interés"],
    "CAP_P009": ["CAP_P009A - Precios altos","CAP_P009B - Sin disponibilidad","CAP_P009C - Sin alternativas","CAP_P009D - Atención poco amable"],

    "SEG_P010": ["SEG_P010A - Dudas sobre conocimientos","SEG_P010B - Actitud apresurada","SEG_P010C - Trato impersonal","SEG_P010D - Falta de empatía"],
    "SEG_P011": ["SEG_P011A - Examen superficial","SEG_P011B - Muy rápido","SEG_P011C - Incompleto","SEG_P011D - No evaluaron"],
    "SEG_P012": ["SEG_P012A - No resolvió dudas","SEG_P012B - Lenguaje técnico","SEG_P012C - Interrumpió","SEG_P012D - No hubo tiempo"],
    "SEG_P013": ["SEG_P013A - Baños sucios","SEG_P013B - Sala de espera sucia","SEG_P013C - Desechos mal gestionados","SEG_P013D - Equipos sin desinfección"],
    "SEG_P014": ["SEG_P014A - No explicó riesgos/beneficios","SEG_P014B - No explicó los pasos","SEG_P014C - No confirmó comprensión","SEG_P014D - Falta material informativo"],
    "SEG_P015": ["SEG_P015A - No explicó dosis/horario","SEG_P015B - No explicó efectos secundarios","SEG_P015C - No dio indicaciones escritas","SEG_P015D - Falta seguimiento"],

    "EMP_P016": ["EMP_P016A - Trato brusco","EMP_P016B - Sin paciencia","EMP_P016C - Personal grosero","EMP_P016D - Me ignoraron"],
    "EMP_P017": ["EMP_P017A - Parecía desinteresado","EMP_P017B - Muy automático","EMP_P017C - No escuchó","EMP_P017D - Falta empatía"],
    "EMP_P018": ["EMP_P018A - Muy generales","EMP_P018B - No dieron","EMP_P018C - Poco útiles","EMP_P018D - No personalizados"],

    "TAN_P019": ["TAN_P019A - Sin rampas","TAN_P019B - Espacios estrechos","TAN_P019C - Barreras físicas","TAN_P019D - Diseño inadecuado"],
    "TAN_P020": ["TAN_P020A - Sin recordatorios","TAN_P020B - Información confusa","TAN_P020C - Llegó tarde","TAN_P020D - No recibí"],
    "TAN_P021": ["TAN_P021A - Mucha espera","TAN_P021B - Sistema lento","TAN_P021C - Falta personal","TAN_P021D - Desorganización"],

    "EXP_P022": ["EXP_P022A - No informaron","EXP_P022B - Servicios limitados","EXP_P022C - Personal desconocía","EXP_P022D - No preguntaron"],
    "EXP_P023": ["EXP_P023A - No informaron","EXP_P023B - Sin asesoría virtual","EXP_P023C - Solo presencial","EXP_P023D - Falta tecnología médica"],
    "EXP_P024": ["EXP_P024A - Sin programas","EXP_P024B - Servicios separados","EXP_P024C - No disponible","EXP_P024D - Falta integración"],
    "EXP_P025": ["EXP_P025A - No tienen redes","EXP_P025B - Difícil de encontrar","EXP_P025C - Información incompleta","EXP_P025D - Información desactualizada"],
    "EXP_P026": ["EXP_P026A - Muy caro","EXP_P026B - No vale","EXP_P026C - Precio elevado","EXP_P026D - Servicio regular"],
    "EXP_P027": ["EXP_P027A - Prefiere otros proveedores","EXP_P027B - No siempre","EXP_P027C - Baja oferta","EXP_P027D - Poca confianza"],
    "EXP_P028": ["EXP_P028A - Mala experiencia","EXP_P028B - Prefiere otras clínicas","EXP_P028C - No recomendaría","EXP_P028D - Problemas generales"],
}

# --------- Estado inicial ---------
DEFAULT_COLS = [
    "Código","Dimensión","Pregunta evaluada","Subproblema identificado","Causa raíz",
    "Acción correctiva","Fecha seguimiento","Responsable","Plazo","Estado","% Avance","Sucursal"
]
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=DEFAULT_COLS)

# --------- Utilidades ---------
def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    if "Fecha seguimiento" in df.columns:
        df["Fecha seguimiento"] = pd.to_datetime(df["Fecha seguimiento"], errors="coerce").dt.date
    if "% Avance" in df.columns:
        df["% Avance"] = pd.to_numeric(df["% Avance"], errors="coerce").fillna(0).astype(int)
    for c in ["Código","Dimensión","Pregunta evaluada","Subproblema identificado","Causa raíz",
              "Acción correctiva","Responsable","Plazo","Estado","Sucursal"]:
        if c in df.columns:
            df[c] = df[c].astype(object)
    return df

# Aplicar overrides antes de crear widgets
ov = st.session_state.pop("_override_filters", None)
if ov:
    for k, v in ov.items():
        st.session_state[k] = v

# --------- Encabezado ---------
st.markdown("<span class='big-title'>PLAN DE ACCIÓN • MATRIZ DE SEGUIMIENTO</span>", unsafe_allow_html=True)
st.write(
    f"<span class='pill'>Total preguntas: 28</span>"
    f"<span class='pill' style='background:{YELLOW}; color:{DARK}'>Responsables: {len(CAT_RESPONSABLES)}</span>"
    f"<span class='pill'>Sucursales: {len(SUCURSALES)}</span>",
    unsafe_allow_html=True
)
st.divider()

# =================== Filtros de visualización ===================
st.markdown("<div class='section-title'>Filtros de visualización</div>", unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 1.2, 1.2])

with fc1:
    f_dim = st.selectbox("Dimensión", ["Todas"] + CAT_DIM, index=(["Todas"] + CAT_DIM).index(st.session_state.get("f_dim","Todas")), key="f_dim")
with fc2:
    f_resp = st.selectbox("Responsable", ["Todos"] + CAT_RESPONSABLES, index=(["Todos"] + CAT_RESPONSABLES).index(st.session_state.get("f_resp","Todos")), key="f_resp")
with fc3:
    f_estado = st.selectbox("Estado", ["Todos"] + CAT_ESTADO, index=(["Todos"] + CAT_ESTADO).index(st.session_state.get("f_estado","Todos")), key="f_estado")
with fc4:
    f_suc = st.multiselect("Sucursal", SUCURSALES, default=st.session_state.get("f_suc", []), key="f_suc")

st.divider()

# =================== Agregar filas por dimensión ===================
st.markdown("<div class='section-title'>Agregar filas por dimensión</div>", unsafe_allow_html=True)
ac1, ac2, ac3, ac4, ac5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2])

with ac1:
    dim_to_add = st.selectbox("Dimensión a cargar", CAT_DIM, index=CAT_DIM.index(st.session_state.get("dim_to_add", CAT_DIM[0])), key="dim_to_add")
with ac2:
    resp_to_add = st.selectbox("Responsable (asignar)", [""] + CAT_RESPONSABLES, index=0, key="resp_to_add")
with ac3:
    estado_to_add = st.selectbox("Estado (asignar)", CAT_ESTADO, index=0, key="estado_to_add")
with ac4:
    avance_to_add = st.slider("% Avance (asignar)", 0, 100, 0, 5, key="avance_to_add")
with ac5:
    suc_to_add = st.selectbox("Sucursal (asignar)", SUCURSALES, index=0, key="suc_to_add")

labels_dim = [f"{c} – {t}" for c, t in PREGUNTAS if MAP_DIM[c] == dim_to_add]
sel_all = st.checkbox("Seleccionar TODAS las preguntas de esta dimensión", value=True)
sel_labels = labels_dim if sel_all else st.multiselect("Seleccionar preguntas específicas", labels_dim, default=labels_dim)

if st.button("➕ Agregar por dimensión", type="primary"):
    new_rows = []
    for opt in sel_labels:
        codigo = opt.split(" – ")[0]
        new_rows.append({
            "Código": codigo,
            "Dimensión": MAP_DIM[codigo],
            "Pregunta evaluada": opt,         # código + texto completo
            "Subproblema identificado": "",
            "Causa raíz": "",
            "Acción correctiva": "",
            "Fecha seguimiento": date.today(),
            "Responsable": resp_to_add,
            "Plazo": "",                      # vacío por defecto
            "Estado": estado_to_add,
            "% Avance": avance_to_add,
            "Sucursal": suc_to_add,
        })
    if new_rows:
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(new_rows)], ignore_index=True)
        st.session_state.df = _coerce_types(st.session_state.df)
        st.session_state["_override_filters"] = {"f_dim": dim_to_add,
                                                 "f_resp": (resp_to_add if resp_to_add else "Todos"),
                                                 "f_estado": estado_to_add,
                                                 "f_suc": [suc_to_add]}
        st.success(f"Agregadas {len(new_rows)} filas de {dim_to_add}.")
        st.rerun()

st.divider()

# =================== Matriz (editable) ===================
st.session_state.df = _coerce_types(st.session_state.df)
df_view = st.session_state.df.copy()
if st.session_state.get("f_dim") not in (None, "Todas"):
    df_view = df_view[df_view["Dimensión"] == st.session_state["f_dim"]]
if st.session_state.get("f_resp") not in (None, "Todos"):
    df_view = df_view[df_view["Responsable"] == st.session_state["f_resp"]]
if st.session_state.get("f_estado") not in (None, "Todos"):
    df_view = df_view[df_view["Estado"] == st.session_state["f_estado"]]
if st.session_state.get("f_suc"):
    df_view = df_view[df_view["Sucursal"].isin(st.session_state["f_suc"])]

if len(st.session_state.df) and df_view.empty:
    st.info("No hay filas que coincidan con los filtros activos. Revisa Responsable/Estado/Sucursal.")

st.write("### 🧾 Matriz (editable)")

if _AGGRID_OK:
    # ---- AG Grid con opciones por fila (Subproblema identificado) ----
    df_ag = df_view.copy().reset_index().rename(columns={"index": "___idx"})
    df_ag["subOptions"] = df_ag["Código"].apply(lambda c: [""] + SUBPROBLEMAS.get(c, []))
    if "Fecha seguimiento" in df_ag.columns:
        df_ag["Fecha seguimiento"] = pd.to_datetime(df_ag["Fecha seguimiento"], errors="coerce").dt.strftime("%Y-%m-%d")

    gob = GridOptionsBuilder.from_dataframe(df_ag, editable=True)
    gob.configure_column("Código", editable=False, width=120)
    gob.configure_column("Dimensión", editable=False, width=160)
    gob.configure_column("Pregunta evaluada", editable=False, wrapText=True, autoHeight=True, width=700)
    gob.configure_column(
        "Subproblema identificado",
        editable=True,
        cellEditor="agSelectCellEditor",
        cellEditorParams={"values": JsCode("function(params){return params.data.subOptions || []; }")},
        width=320
    )
    gob.configure_column("Causa raíz", editable=True, width=220)
    gob.configure_column("Acción correctiva", editable=True, width=220)
    gob.configure_column("Fecha seguimiento", editable=True, cellEditor="agDateStringCellEditor", width=140)
    gob.configure_column("Responsable", editable=True, cellEditor="agSelectCellEditor",
                         cellEditorParams={"values": [""] + CAT_RESPONSABLES}, width=260)
    gob.configure_column("Plazo", editable=True, headerTooltip=f"Formato sugerido: {CAT_PLAZO_SUG}", width=150)
    gob.configure_column("Estado", editable=True, cellEditor="agSelectCellEditor",
                         cellEditorParams={"values": CAT_ESTADO}, width=140)
    gob.configure_column("Sucursal", editable=True, cellEditor="agSelectCellEditor",
                         cellEditorParams={"values": SUCURSALES}, width=200)
    gob.configure_column("% Avance", type=["numericColumn"], editable=True, width=120)
    gob.configure_column("___idx", hide=True)

    grid = AgGrid(
        df_ag,
        gridOptions=gob.build(),
        update_mode=GridUpdateMode.VALUE_CHANGED,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=False,
        height=460,
        theme="alpine"
    )
    updated = grid["data"]
    if updated is not None and len(updated):
        upd = updated.copy()
        if "Fecha seguimiento" in upd.columns:
            upd["Fecha seguimiento"] = pd.to_datetime(upd["Fecha seguimiento"], errors="coerce").dt.date
        for _, row in upd.iterrows():
            gi = int(row["___idx"])
            for col in DEFAULT_COLS:
                if col in upd.columns:
                    st.session_state.df.at[gi, col] = row.get(col, st.session_state.df.at[gi, col])
        st.session_state.df = _coerce_types(st.session_state.df)
else:
    # ---- Fallback a data_editor (lista global) ----
    edited = st.data_editor(
        df_view,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Código": st.column_config.SelectboxColumn(options=[c for c, _ in PREGUNTAS]),
            "Dimensión": st.column_config.SelectboxColumn(options=CAT_DIM),
            "Pregunta evaluada": st.column_config.SelectboxColumn(options=[f"{c} – {t}" for c, t in PREGUNTAS], width="large"),
            "Subproblema identificado": st.column_config.SelectboxColumn(options=[""] + sorted({opt for lst in SUBPROBLEMAS.values() for opt in lst})),
            "Responsable": st.column_config.SelectboxColumn(options=[""] + CAT_RESPONSABLES),
            "Plazo": st.column_config.TextColumn(help=f"Formato sugerido: {CAT_PLAZO_SUG}"),
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

# --------- Exportar a Excel ---------
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
