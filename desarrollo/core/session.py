"""
==============================================================
SIMI

session.py

Control de sesión de usuario.
==============================================================
"""

import streamlit as st


def inicializar_sesion():
    if "usuario_autenticado" not in st.session_state:
        st.session_state.usuario_autenticado = False

    if "usuario" not in st.session_state:
        st.session_state.usuario = None

    if "rol" not in st.session_state:
        st.session_state.rol = None

    if "id_usuario" not in st.session_state:
        st.session_state.id_usuario = None


def cerrar_sesion():
    st.session_state.usuario_autenticado = False
    st.session_state.usuario = None
    st.session_state.rol = None
    st.session_state.id_usuario = None