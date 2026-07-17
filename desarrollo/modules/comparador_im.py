"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

comparador_im.py

Módulo Streamlit del Comparador de Investigaciones de Mercado.

Responsabilidades:
- Recibir temporalmente una nueva IM en formato Excel.
- Mostrar una vista previa del archivo.
- Ejecutar ComparadorIMService.
- Mostrar incidencias, indicadores, tablas y gráficas.
- Permitir descargar un reporte temporal en Excel.

Este módulo:
- No ejecuta SQL.
- No abre conexiones.
- No calcula reglas analíticas.
- No persiste el archivo ni los resultados.
- Mantiene el análisis únicamente en session_state.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

from io import BytesIO
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from services.comparador_im_service import (
    ComparadorIMService,
)


SESSION_ARCHIVO = "comparador_im_archivo"
SESSION_RESULTADO = "comparador_im_resultado"
SESSION_NOMBRE_ARCHIVO = "comparador_im_nombre_archivo"

COLUMNAS_ESPERADAS = [
    "RFC",
    "RAZON SOCIAL",
    "CLAVE",
    "DESCRIPCION",
    "CANTIDAD OFERTADA",
    "PAIS DE ORIGEN",
    "PRECIO UNITARIO",
]


# ==========================================================
# FORMATO Y CONVERSIÓN
# ==========================================================

def _valor_entero(valor):
    try:
        return int(valor or 0)
    except (TypeError, ValueError, OverflowError):
        return 0


def _formatear_decimal(valor, decimales=2):
    if valor is None:
        return "Sin información"

    try:
        numero = Decimal(str(valor))
    except (TypeError, ValueError):
        return "Sin información"

    return f"{numero:,.{decimales}f}"


def _formatear_moneda(valor):
    if valor is None:
        return "Sin información"

    return f"${_formatear_decimal(valor)}"


def _formatear_porcentaje(valor):
    if valor is None:
        return "Sin información"

    return f"{_formatear_decimal(valor)}%"


def _normalizar_dataframe(registros):
    if not registros:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            dict(registro)
            for registro in registros
        ]
    )


def _convertir_decimales_dataframe(df):
    """
    Convierte Decimal a float únicamente para visualización.
    """
    if df.empty:
        return df

    resultado = df.copy()

    for columna in resultado.columns:
        resultado[columna] = resultado[columna].map(
            lambda valor: (
                float(valor)
                if isinstance(valor, Decimal)
                else valor
            )
        )

    return resultado


def _leer_archivo_excel(archivo):
    """
    Lee la primera hoja del Excel sin persistir el archivo.
    """
    if archivo is None:
        return pd.DataFrame()

    return pd.read_excel(
        archivo,
        sheet_name=0,
        dtype=object,
    )


def _limpiar_dataframe_entrada(df):
    """
    Elimina filas completamente vacías y columnas sin nombre útil.
    """
    if df.empty:
        return df

    resultado = df.dropna(how="all").copy()

    columnas_validas = [
        columna
        for columna in resultado.columns
        if not str(columna).startswith("Unnamed:")
    ]

    return resultado[columnas_validas]


# ==========================================================
# ESTADO DE SESIÓN
# ==========================================================

def _inicializar_estado():
    st.session_state.setdefault(SESSION_ARCHIVO, None)
    st.session_state.setdefault(SESSION_RESULTADO, None)
    st.session_state.setdefault(SESSION_NOMBRE_ARCHIVO, None)


def _limpiar_analisis():
    st.session_state[SESSION_ARCHIVO] = None
    st.session_state[SESSION_RESULTADO] = None
    st.session_state[SESSION_NOMBRE_ARCHIVO] = None


# ==========================================================
# ENCABEZADO Y CARGA
# ==========================================================

def _mostrar_encabezado():
    st.header("Comparador de Investigaciones de Mercado")
    st.caption(
        "Compara una nueva Investigación de Mercado contra "
        "propuestas iniciales, subastas y adjudicaciones "
        "operativas e históricas."
    )
    st.info(
        "El archivo y los resultados se procesan temporalmente "
        "durante esta sesión. No se guardan en la base de datos."
    )


def _mostrar_estructura_esperada():
    with st.expander("Estructura esperada del archivo"):
        st.write(
            "La primera hoja del archivo debe contener estas columnas:"
        )
        st.code(" | ".join(COLUMNAS_ESPERADAS))
        st.caption(
            "También se aceptan los aliases CANTIDAD, PRECIO y "
            "PAIS ORIGEN."
        )


def _mostrar_carga_archivo():
    archivo = st.file_uploader(
        "Selecciona la Investigación de Mercado",
        type=["xlsx", "xls"],
        key="comparador_im_uploader",
        help=(
            "El archivo se procesa en memoria y no se almacena "
            "en SIMI."
        ),
    )

    if archivo is None:
        return None

    try:
        df = _limpiar_dataframe_entrada(
            _leer_archivo_excel(archivo)
        )
    except Exception as error:
        st.error("No fue posible leer el archivo seleccionado.")
        st.exception(error)
        return None

    if df.empty:
        st.warning(
            "El archivo no contiene filas con información en "
            "la primera hoja."
        )
        return None

    st.session_state[SESSION_ARCHIVO] = df
    st.session_state[SESSION_NOMBRE_ARCHIVO] = archivo.name

    st.success(
        f"Archivo leído correctamente: {archivo.name} "
        f"({_valor_entero(len(df))} filas)."
    )

    with st.expander("Vista previa de la IM", expanded=True):
        st.dataframe(
            df.head(50),
            width="stretch",
            hide_index=True,
        )

        if len(df) > 50:
            st.caption(
                "La vista previa muestra las primeras 50 filas."
            )

    return df


# ==========================================================
# EJECUCIÓN DEL ANÁLISIS
# ==========================================================

def _mostrar_acciones(df):
    columna_1, columna_2 = st.columns([3, 1])

    ejecutar = columna_1.button(
        "Comparar Investigación de Mercado",
        type="primary",
        width="stretch",
        disabled=df is None or df.empty,
    )

    limpiar = columna_2.button(
        "Limpiar",
        width="stretch",
    )

    if limpiar:
        _limpiar_analisis()
        st.rerun()

    return ejecutar


def _ejecutar_comparacion(df):
    service = ComparadorIMService()

    try:
        with st.spinner(
            "Comparando la investigación contra la información "
            "acumulada de SIMI..."
        ):
            resultado = service.comparar_investigacion(df)
    except ValueError as error:
        st.warning(str(error))
        return None
    except Exception as error:
        st.error(
            "No fue posible completar la comparación de la IM."
        )
        st.exception(error)
        return None

    st.session_state[SESSION_RESULTADO] = resultado
    return resultado


# ==========================================================
# INDICADORES
# ==========================================================

def _mostrar_indicadores(resumen):
    st.subheader("Resumen general")

    fila_1 = st.columns(5)
    fila_1[0].metric(
        "Filas recibidas",
        _valor_entero(
            resumen.get("total_filas_recibidas")
        ),
    )
    fila_1[1].metric(
        "Filas válidas",
        _valor_entero(
            resumen.get("total_filas_validas")
        ),
    )
    fila_1[2].metric(
        "Filas inválidas",
        _valor_entero(
            resumen.get("total_filas_invalidas")
        ),
    )
    fila_1[3].metric(
        "Claves encontradas",
        _valor_entero(
            resumen.get("claves_encontradas")
        ),
    )
    fila_1[4].metric(
        "Claves no encontradas",
        _valor_entero(
            resumen.get("claves_no_encontradas")
        ),
    )

    fila_2 = st.columns(5)
    fila_2[0].metric(
        "Claves con referencia",
        _valor_entero(
            resumen.get("claves_con_referencia")
        ),
    )
    fila_2[1].metric(
        "Sin referencia",
        _valor_entero(
            resumen.get("claves_sin_referencia")
        ),
    )
    fila_2[2].metric(
        "Cotizaciones competitivas",
        _valor_entero(
            resumen.get("cotizaciones_competitivas")
        ),
    )
    fila_2[3].metric(
        "Cotizaciones elevadas",
        _valor_entero(
            resumen.get("cotizaciones_elevadas")
        ),
    )
    fila_2[4].metric(
        "Claves con riesgo alto",
        _valor_entero(
            resumen.get("claves_riesgo_alto")
        ),
    )


# ==========================================================
# INCIDENCIAS
# ==========================================================

def _mostrar_incidencias(resultado):
    incidencias = resultado.get("incidencias", {}) or {}
    filas_invalidas = incidencias.get(
        "filas_invalidas",
        [],
    )
    claves_no_encontradas = incidencias.get(
        "claves_no_encontradas",
        [],
    )

    if not filas_invalidas and not claves_no_encontradas:
        st.success(
            "No se detectaron incidencias estructurales ni claves "
            "fuera del catálogo."
        )
        return

    if filas_invalidas:
        st.warning(
            f"Se detectaron {len(filas_invalidas)} filas inválidas."
        )

        registros = []

        for incidencia in filas_invalidas:
            registro = incidencia.get("registro") or {}

            registros.append(
                {
                    "Fila": incidencia.get("numero_fila"),
                    "RFC": registro.get("rfc"),
                    "Razón social": registro.get(
                        "razon_social"
                    ),
                    "Clave": registro.get("clave"),
                    "Errores": " | ".join(
                        incidencia.get("errores", [])
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(registros),
            width="stretch",
            hide_index=True,
        )

    if claves_no_encontradas:
        st.warning(
            f"Se detectaron {len(claves_no_encontradas)} "
            "cotizaciones con claves inexistentes."
        )

        st.dataframe(
            pd.DataFrame(claves_no_encontradas).rename(
                columns={
                    "numero_fila": "Fila",
                    "clave": "Clave",
                    "rfc": "RFC",
                    "razon_social": "Razón social",
                    "error": "Incidencia",
                }
            ),
            width="stretch",
            hide_index=True,
        )


# ==========================================================
# TABLAS
# ==========================================================

def _mostrar_tabla_resumen_claves(registros):
    df = _normalizar_dataframe(registros)

    if df.empty:
        st.info("No existen claves analizadas para mostrar.")
        return

    columnas = {
        "clave": "Clave",
        "descripcion": "Descripción",
        "categoria": "Categoría",
        "precio_referencia": "Precio referencia",
        "fuente_referencia": "Fuente",
        "nivel_confianza": "Confianza",
        "tendencia": "Tendencia",
        "total_cotizaciones_im": "Cotizaciones IM",
        "precio_minimo_im": "Precio mínimo IM",
        "precio_maximo_im": "Precio máximo IM",
        "cotizaciones_competitivas": "Competitivas",
        "cotizaciones_en_mercado": "En mercado",
        "cotizaciones_elevadas": "Elevadas",
        "cotizaciones_muy_elevadas": "Muy elevadas",
        "riesgo_clave": "Riesgo",
    }

    disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    st.dataframe(
        _convertir_decimales_dataframe(
            df[disponibles].rename(columns=columnas)
        ),
        width="stretch",
        hide_index=True,
    )


def _mostrar_tabla_cotizaciones(registros):
    df = _normalizar_dataframe(registros)

    if df.empty:
        st.info("No existen cotizaciones analizadas.")
        return

    columnas = {
        "numero_fila": "Fila",
        "clave": "Clave",
        "razon_social": "Proveedor",
        "rfc": "RFC",
        "cantidad": "Cantidad",
        "precio_im": "Precio IM",
        "precio_referencia": "Precio referencia",
        "fuente_referencia": "Fuente",
        "diferencia_unitaria": "Diferencia unitaria",
        "variacion_porcentual": "Variación (%)",
        "clasificacion_desviacion": "Clasificación",
        "nivel_confianza": "Confianza",
        "impacto_estimado": "Impacto estimado",
        "nivel_riesgo": "Riesgo",
    }

    disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    st.dataframe(
        _convertir_decimales_dataframe(
            df[disponibles].rename(columns=columnas)
        ),
        width="stretch",
        hide_index=True,
    )


def _mostrar_tabla_estadisticas(registros):
    df = _normalizar_dataframe(registros)

    if df.empty:
        st.info(
            "No existen estadísticas de mercado para mostrar."
        )
        return

    columnas = {
        "clave": "Clave",
        "fuente": "Fuente",
        "total_observaciones": "Observaciones",
        "precio_minimo": "Mínimo",
        "precio_maximo": "Máximo",
        "precio_promedio": "Promedio",
        "precio_mediana": "Mediana",
        "desviacion_estandar": "Desviación estándar",
        "percentil_25": "P25",
        "percentil_75": "P75",
        "rango_intercuartil": "IQR",
    }

    disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    st.dataframe(
        _convertir_decimales_dataframe(
            df[disponibles].rename(columns=columnas)
        ),
        width="stretch",
        hide_index=True,
    )


def _mostrar_tabla_recomendaciones(registros):
    df = _normalizar_dataframe(registros)

    if df.empty:
        st.info("No existen recomendaciones para mostrar.")
        return

    columnas = {
        "clave": "Clave",
        "numero_fila": "Fila",
        "razon_social": "Proveedor",
        "rfc": "RFC",
        "nivel": "Nivel",
        "titulo": "Recomendación",
        "mensaje": "Detalle",
    }

    disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    st.dataframe(
        df[disponibles].rename(columns=columnas),
        width="stretch",
        hide_index=True,
    )


# ==========================================================
# GRÁFICAS
# ==========================================================

def _mostrar_grafica_clasificaciones(registros):
    df = _normalizar_dataframe(registros)

    if df.empty or "clasificacion" not in df.columns:
        st.info(
            "No existen clasificaciones para generar la gráfica."
        )
        return

    resumen = (
        df.groupby("clasificacion", dropna=False)
        .size()
        .reset_index(name="total")
    )

    figura = px.bar(
        resumen,
        x="clasificacion",
        y="total",
        title="Clasificación de cotizaciones",
        labels={
            "clasificacion": "Clasificación",
            "total": "Cotizaciones",
        },
    )

    st.plotly_chart(figura, width="stretch")


def _mostrar_grafica_riesgo(registros):
    df = _normalizar_dataframe(registros)

    if df.empty or "nivel_riesgo" not in df.columns:
        st.info("No existe información de riesgo por clave.")
        return

    resumen = (
        df.groupby("nivel_riesgo", dropna=False)
        .size()
        .reset_index(name="total_claves")
    )

    figura = px.pie(
        resumen,
        names="nivel_riesgo",
        values="total_claves",
        title="Distribución del riesgo por clave",
        hole=0.45,
    )

    st.plotly_chart(figura, width="stretch")


def _mostrar_grafica_distribucion(registros):
    df = _normalizar_dataframe(registros)

    if df.empty:
        st.info(
            "No existen precios de mercado para mostrar "
            "la distribución."
        )
        return

    columnas = {"clave", "fuente", "precio"}

    if not columnas.issubset(df.columns):
        st.info(
            "La información disponible no permite construir "
            "la distribución."
        )
        return

    df["precio"] = pd.to_numeric(
        df["precio"],
        errors="coerce",
    )
    df = df.dropna(subset=["precio"])

    if df.empty:
        st.info("No existen precios numéricos disponibles.")
        return

    claves = sorted(df["clave"].dropna().unique())
    clave = st.selectbox(
        "Clave para distribución",
        options=claves,
        key="comparador_im_clave_distribucion",
    )

    filtrado = df[df["clave"] == clave]

    figura = px.box(
        filtrado,
        x="fuente",
        y="precio",
        points="all",
        title=f"Distribución de precios — {clave}",
        labels={
            "fuente": "Fuente",
            "precio": "Precio unitario",
        },
    )

    st.plotly_chart(figura, width="stretch")


def _mostrar_grafica_evolucion(registros, cotizaciones):
    df = _normalizar_dataframe(registros)
    df_im = _normalizar_dataframe(cotizaciones)

    if df.empty:
        st.info(
            "No existe una serie histórica suficiente para mostrar "
            "la evolución."
        )
        return

    columnas = {
        "clave",
        "ejercicio",
        "numero_procedimiento",
        "precio_mediana",
    }

    if not columnas.issubset(df.columns):
        st.info(
            "La información temporal disponible es insuficiente."
        )
        return

    claves = sorted(df["clave"].dropna().unique())
    clave = st.selectbox(
        "Clave para evolución",
        options=claves,
        key="comparador_im_clave_evolucion",
    )

    filtrado = df[df["clave"] == clave].copy()
    filtrado["precio_mediana"] = pd.to_numeric(
        filtrado["precio_mediana"],
        errors="coerce",
    )
    filtrado = filtrado.dropna(
        subset=["precio_mediana"]
    )

    filtrado["periodo"] = filtrado.apply(
        lambda fila: (
            f"{fila.get('ejercicio') or 'S/A'} — "
            f"{fila.get('numero_procedimiento') or 'Sin procedimiento'}"
        ),
        axis=1,
    )

    figura = px.line(
        filtrado,
        x="periodo",
        y="precio_mediana",
        markers=True,
        title=f"Evolución de precios adjudicados — {clave}",
        labels={
            "periodo": "Periodo",
            "precio_mediana": "Precio mediano",
        },
    )

    if (
        not df_im.empty
        and {"clave", "precio_im"}.issubset(df_im.columns)
    ):
        precios_im = df_im[
            df_im["clave"] == clave
        ]["precio_im"]

        precios_im = pd.to_numeric(
            precios_im,
            errors="coerce",
        ).dropna()

        if not precios_im.empty:
            figura.add_hline(
                y=float(precios_im.min()),
                line_dash="dash",
                annotation_text="Mejor precio IM",
            )

    st.plotly_chart(figura, width="stretch")


# ==========================================================
# DETALLE POR CLAVE
# ==========================================================

def _mostrar_detalle_clave(analisis_claves):
    if not analisis_claves:
        st.info("No existen claves para mostrar en detalle.")
        return

    mapa = {
        (
            f"{registro.get('clave')} — "
            f"{registro.get('descripcion') or 'Sin descripción'}"
        ): registro
        for registro in analisis_claves
    }

    etiqueta = st.selectbox(
        "Selecciona una clave",
        options=list(mapa.keys()),
        key="comparador_im_detalle_clave",
    )

    analisis = mapa[etiqueta]
    referencia = analisis.get("referencia", {}) or {}
    objetivo = analisis.get("precio_objetivo", {}) or {}
    tendencia = analisis.get("tendencia", {}) or {}
    resumen = analisis.get("resumen", {}) or {}

    fila_1 = st.columns(5)
    fila_1[0].metric(
        "Referencia",
        _formatear_moneda(
            referencia.get("precio_referencia")
        ),
    )
    fila_1[1].metric(
        "Fuente",
        referencia.get("fuente_referencia")
        or "Sin referencia",
    )
    fila_1[2].metric(
        "Precio objetivo",
        _formatear_moneda(
            objetivo.get("precio_objetivo")
        ),
    )
    fila_1[3].metric(
        "Tendencia",
        tendencia.get("tendencia")
        or "Sin información",
    )
    fila_1[4].metric(
        "Riesgo",
        resumen.get("riesgo_clave")
        or "INDETERMINADO",
    )

    if objetivo.get("rango_disponible"):
        st.info(
            "Rango objetivo sugerido: "
            f"{_formatear_moneda(objetivo.get('rango_objetivo_minimo'))} "
            "a "
            f"{_formatear_moneda(objetivo.get('rango_objetivo_maximo'))}."
        )

    cotizaciones = analisis.get("cotizaciones", [])

    _mostrar_tabla_cotizaciones(cotizaciones)


# ==========================================================
# EXPORTACIÓN TEMPORAL
# ==========================================================

def _generar_excel_resultados(resultado):
    """
    Genera un archivo en memoria. No lo guarda en disco ni BD.
    """
    salida = BytesIO()
    tablas = resultado.get("tablas", {}) or {}
    incidencias = resultado.get("incidencias", {}) or {}

    with pd.ExcelWriter(
        salida,
        engine="openpyxl",
    ) as writer:
        hojas = {
            "Resumen claves": tablas.get(
                "resumen_claves",
                [],
            ),
            "Cotizaciones": tablas.get(
                "comparacion_cotizaciones",
                [],
            ),
            "Estadisticas": tablas.get(
                "estadisticas_mercado",
                [],
            ),
            "Recomendaciones": tablas.get(
                "recomendaciones",
                [],
            ),
            "Filas invalidas": incidencias.get(
                "filas_invalidas",
                [],
            ),
            "Claves no encontradas": incidencias.get(
                "claves_no_encontradas",
                [],
            ),
        }

        for nombre, registros in hojas.items():
            df = _convertir_decimales_dataframe(
                _normalizar_dataframe(registros)
            )

            if df.empty:
                df = pd.DataFrame(
                    [{"Información": "Sin registros"}]
                )

            df.to_excel(
                writer,
                sheet_name=nombre[:31],
                index=False,
            )

    salida.seek(0)
    return salida.getvalue()


def _mostrar_descarga(resultado):
    nombre_original = (
        st.session_state.get(SESSION_NOMBRE_ARCHIVO)
        or "investigacion_mercado"
    )
    nombre_base = nombre_original.rsplit(".", 1)[0]
    nombre_salida = (
        f"{nombre_base}_comparacion_simi.xlsx"
    )

    st.download_button(
        "Descargar reporte temporal",
        data=_generar_excel_resultados(resultado),
        file_name=nombre_salida,
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        width="stretch",
    )


# ==========================================================
# CONTENIDO FINAL
# ==========================================================

def _mostrar_resultado(resultado):
    resumen = resultado.get("resumen", {}) or {}
    tablas = resultado.get("tablas", {}) or {}
    graficas = resultado.get("graficas", {}) or {}

    st.divider()
    _mostrar_indicadores(resumen)

    st.divider()
    with st.expander("Incidencias detectadas", expanded=False):
        _mostrar_incidencias(resultado)

    st.divider()
    st.subheader("Visualización analítica")

    columna_1, columna_2 = st.columns(2)

    with columna_1:
        _mostrar_grafica_clasificaciones(
            graficas.get(
                "clasificacion_cotizaciones",
                [],
            )
        )

    with columna_2:
        _mostrar_grafica_riesgo(
            graficas.get("riesgo_por_clave", [])
        )

    columna_3, columna_4 = st.columns(2)

    with columna_3:
        _mostrar_grafica_distribucion(
            graficas.get(
                "distribucion_precios",
                [],
            )
        )

    with columna_4:
        _mostrar_grafica_evolucion(
            graficas.get(
                "evolucion_precios",
                [],
            ),
            tablas.get(
                "comparacion_cotizaciones",
                [],
            ),
        )

    st.divider()
    st.subheader("Detalle de resultados")

    pestañas = st.tabs(
        [
            "Resumen por clave",
            "Cotizaciones",
            "Estadísticas",
            "Recomendaciones",
            "Detalle de clave",
        ]
    )

    with pestañas[0]:
        _mostrar_tabla_resumen_claves(
            tablas.get("resumen_claves", [])
        )

    with pestañas[1]:
        _mostrar_tabla_cotizaciones(
            tablas.get(
                "comparacion_cotizaciones",
                [],
            )
        )

    with pestañas[2]:
        _mostrar_tabla_estadisticas(
            tablas.get(
                "estadisticas_mercado",
                [],
            )
        )

    with pestañas[3]:
        _mostrar_tabla_recomendaciones(
            tablas.get("recomendaciones", [])
        )

    with pestañas[4]:
        _mostrar_detalle_clave(
            resultado.get("claves", [])
        )

    st.divider()
    _mostrar_descarga(resultado)


# ==========================================================
# CONTROLADOR PRINCIPAL
# ==========================================================

def mostrar_comparador_im():
    """
    Renderiza el Comparador de Investigaciones de Mercado.
    """
    _inicializar_estado()
    _mostrar_encabezado()
    _mostrar_estructura_esperada()

    df = _mostrar_carga_archivo()

    if df is None:
        df = st.session_state.get(SESSION_ARCHIVO)

    ejecutar = _mostrar_acciones(df)

    if ejecutar:
        resultado = _ejecutar_comparacion(df)
    else:
        resultado = st.session_state.get(SESSION_RESULTADO)

    if resultado:
        _mostrar_resultado(resultado)