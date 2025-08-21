
import streamlit as st
import pandas as pd

# --- Autenticación básica ---
def check_password():
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "aprofam2024":
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False
            st.error("Usuario o contraseña incorrectos")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password", on_change=password_entered)
        return False
    else:
        return True

# --- Datos de ejemplo para FIA_P003 ---
def cargar_datos():
    data = [
        {
            "Pregunta": "¿Respetaron el orden de llegada y su turno para atenderle?",
            "Código": "FIA_P003",
            "Subproblema": "No respetaron orden",
            "Causa raíz sugerida": "Falta de control en sistema de turnos",
            "Acción correctiva sugerida": "Implementar sistema digital de turnos con pantalla visible",
            "Fecha seguimiento": "",
            "Responsable": "",
            "Plazo": "",
            "Estado": "Pendiente"
        },
        {
            "Pregunta": "¿Respetaron el orden de llegada y su turno para atenderle?",
            "Código": "FIA_P003",
            "Subproblema": "Saltaron turnos",
            "Causa raíz sugerida": "Preferencias personales del personal",
            "Acción correctiva sugerida": "Supervisión activa y rotación de personal",
            "Fecha seguimiento": "",
            "Responsable": "",
            "Plazo": "",
            "Estado": "Pendiente"
        }
    ]
    return pd.DataFrame(data)

# --- Estilos personalizados ---
def aplicar_estilos():
    st.markdown("""
        <style>
        .main {
            background-color: #F9FAFC;
        }
        .block-container {
            padding-top: 2rem;
        }
        .stApp {
            background-color: #F9FAFC;
        }
        .stButton>button {
            background-color: #FFC600;
            color: black;
        }
        .stDataFrame {
            border: 1px solid #00315E;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Dashboard visual ---
def mostrar_dashboard(df):
    st.subheader("📊 Dashboard por Sucursal")
    resumen = df.groupby("Estado").size().reset_index(name="Total")
    st.bar_chart(resumen.set_index("Estado"))

# --- Aplicación principal ---
def main():
    aplicar_estilos()
    st.title("📋 Seguimiento SERVQUAL APROFAM")
    st.markdown("### Pregunta: FIA_P003 - ¿Respetaron el orden de llegada y su turno para atenderle?")

    df = cargar_datos()
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    mostrar_dashboard(edited_df)

    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Exportar a CSV", csv, "seguimiento_servqual.csv", "text/csv")

if check_password():
    main()
