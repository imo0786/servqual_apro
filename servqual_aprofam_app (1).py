
import streamlit as st
import pandas as pd

# --- Authentication ---
def login():
    st.title("SERVQUAL APROFAM - Seguimiento de Acciones Correctivas")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if username == "admin" and password == "aprofam2024":
            st.session_state["authenticated"] = True
        else:
            st.error("Credenciales incorrectas")

# --- Initial Data for FIA_P003 ---
def get_initial_data():
    data = [
        {
            "Subproblema": "No respetaron orden",
            "Causa raíz sugerida": "Falta de control en sistema de turnos",
            "Acción correctiva sugerida": "Implementar sistema digital de turnos con pantalla visible",
            "Fecha de seguimiento": "",
            "Responsable": "",
            "Plazo": "",
            "Estado": "Pendiente"
        },
        {
            "Subproblema": "Saltaron turnos",
            "Causa raíz sugerida": "Preferencias personales del personal",
            "Acción correctiva sugerida": "Supervisión activa y rotación de personal",
            "Fecha de seguimiento": "",
            "Responsable": "",
            "Plazo": "",
            "Estado": "Pendiente"
        },
        {
            "Subproblema": "Sin organización",
            "Causa raíz sugerida": "Ausencia de protocolos claros",
            "Acción correctiva sugerida": "Crear protocolo de atención por orden de llegada",
            "Fecha de seguimiento": "",
            "Responsable": "",
            "Plazo": "",
            "Estado": "Pendiente"
        },
        {
            "Subproblema": "Preferencias injustas",
            "Causa raíz sugerida": "Falta de transparencia",
            "Acción correctiva sugerida": "Publicar criterios de atención en áreas visibles",
            "Fecha de seguimiento": "",
            "Responsable": "",
            "Plazo": "",
            "Estado": "Pendiente"
        }
    ]
    return pd.DataFrame(data)

# --- Main App ---
def main():
    st.title("Seguimiento de Acciones Correctivas - FIA_P003")
    st.markdown("**Pregunta:** ¿Respetaron el orden de llegada y su turno para atenderle?")
    df = st.session_state.get("data", get_initial_data())
    edited_df = st.dataframe(df, use_container_width=True)
    st.session_state["data"] = df

    # Export to CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Exportar a CSV", data=csv, file_name="seguimiento_FIA_P003.csv", mime="text/csv")

# --- App Execution ---
if "authenticated" not in st.session_state:
    login()
elif st.session_state["authenticated"]:
    main()
