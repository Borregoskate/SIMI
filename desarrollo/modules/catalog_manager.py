"""
==============================================================
SIMI
Sistema Inteligente de Mercado e Investigaciones

catalog_manager.py

Carga inicial y sincronización de catálogos maestros.

Autor: Jorge Saavedra
Versión: 1.0.0
==============================================================
"""

import pandas as pd
from psycopg2.extras import execute_values


class CatalogManager:

    def __init__(self, connection):
        self.connection = connection

    def _set_user_role(self, cursor, user_role: str):
        cursor.execute("SET LOCAL simi.user_role = %s;", (user_role,))

    def _normalizar_columnas(self, df):
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace("á", "a", regex=False)
            .str.replace("é", "e", regex=False)
            .str.replace("í", "i", regex=False)
            .str.replace("ó", "o", regex=False)
            .str.replace("ú", "u", regex=False)
        )
        return df

    def _obtener_columna(self, df, opciones, nombre_logico):
        for columna in opciones:
            if columna in df.columns:
                return columna

        raise ValueError(
            f"El archivo debe contener una columna equivalente a '{nombre_logico}'. "
            f"Opciones válidas: {opciones}"
        )

    def _validar_vacios(self, df, columnas):
        for columna in columnas:
            if df[columna].isna().any() or (df[columna].astype(str).str.strip() == "").any():
                raise ValueError(f"Existen valores vacíos en la columna: {columna}")

    def cargar_categorias(self, archivo: str, id_usuario: int, user_role: str = "ADMINISTRADOR"):
        df = pd.read_excel(archivo)
        df = self._normalizar_columnas(df)

        col_categoria = self._obtener_columna(
            df,
            ["nombre_categoria", "categoria", "nombre"],
            "nombre_categoria"
        )

        df["nombre_categoria"] = df[col_categoria].astype(str).str.strip()

        self._validar_vacios(df, ["nombre_categoria"])

        if df["nombre_categoria"].duplicated().any():
            duplicadas = df[df["nombre_categoria"].duplicated()]["nombre_categoria"].tolist()
            raise ValueError(f"Existen categorías duplicadas en el archivo: {duplicadas}")

        registros = [(x,) for x in df["nombre_categoria"].tolist()]

        with self.connection:
            with self.connection.cursor() as cursor:
                self._set_user_role(cursor, user_role)

                cursor.execute("SELECT COUNT(*) FROM simi.cat_categorias_clave;")
                total_inicial = cursor.fetchone()[0]

                execute_values(
                    cursor,
                    """
                    INSERT INTO simi.cat_categorias_clave (nombre_categoria)
                    VALUES %s
                    ON CONFLICT (nombre_categoria) DO NOTHING;
                    """,
                    registros,
                )

                cursor.execute("SELECT COUNT(*) FROM simi.cat_categorias_clave;")
                total_final = cursor.fetchone()[0]

                insertados = total_final - total_inicial
                actualizados = 0

                cursor.execute(
                    """
                    INSERT INTO simi.bitacora_catalogos (
                        tabla_catalogo,
                        accion,
                        modulo,
                        id_usuario,
                        registros_insertados,
                        registros_actualizados,
                        archivo_origen,
                        observaciones
                    )
                    VALUES (
                        'cat_categorias_clave',
                        'CARGA_INICIAL',
                        'CATALOG_MANAGER',
                        %s,
                        %s,
                        %s,
                        %s,
                        'Carga inicial de categorías de claves'
                    );
                    """,
                    (id_usuario, insertados, actualizados, archivo),
                )

        return {
            "success": True,
            "tabla": "cat_categorias_clave",
            "procesados": len(registros),
            "insertados": insertados,
            "actualizados": actualizados,
        }

    def cargar_claves(self, archivo: str, id_usuario: int, user_role: str = "ADMINISTRADOR"):
        df = pd.read_excel(archivo)
        df = self._normalizar_columnas(df)

        col_clave = self._obtener_columna(
            df,
            ["clave"],
            "clave"
        )

        col_descripcion = self._obtener_columna(
            df,
            ["descripcion", "desc", "nombre_descripcion"],
            "descripcion"
        )

        col_categoria = self._obtener_columna(
            df,
            ["categoria", "nombre_categoria"],
            "categoria"
        )

        df["clave"] = df[col_clave].astype(str).str.strip()
        df["descripcion"] = df[col_descripcion].astype(str).str.strip().str.upper()
        df["categoria"] = df[col_categoria].astype(str).str.strip()

        columnas_finales = ["clave", "descripcion", "categoria"]

        self._validar_vacios(df, columnas_finales)

        if df["clave"].duplicated().any():
            duplicadas = df[df["clave"].duplicated()]["clave"].tolist()
            raise ValueError(f"Existen claves duplicadas en el archivo: {duplicadas}")

        with self.connection:
            with self.connection.cursor() as cursor:
                self._set_user_role(cursor, user_role)

                cursor.execute(
                    """
                    SELECT id_categoria, nombre_categoria
                    FROM simi.cat_categorias_clave;
                    """
                )

                categorias = {
                    nombre.strip(): id_categoria
                    for id_categoria, nombre in cursor.fetchall()
                }

                categorias_no_existentes = set(df["categoria"]) - set(categorias.keys())

                if categorias_no_existentes:
                    raise ValueError(
                        f"Categorías no existentes en base de datos: {categorias_no_existentes}"
                    )

                claves_archivo = df["clave"].tolist()

                cursor.execute(
                    """
                    SELECT clave, descripcion, id_categoria
                    FROM simi.claves
                    WHERE clave = ANY(%s);
                    """,
                    (claves_archivo,)
                )

                existentes = {
                    clave: {
                        "descripcion": descripcion,
                        "id_categoria": id_categoria,
                    }
                    for clave, descripcion, id_categoria in cursor.fetchall()
                }

                conflictos = []

                for _, row in df.iterrows():
                    clave = row["clave"]
                    descripcion_archivo = row["descripcion"]
                    id_categoria_archivo = categorias[row["categoria"]]

                    if clave in existentes:
                        descripcion_db = existentes[clave]["descripcion"]
                        id_categoria_db = existentes[clave]["id_categoria"]

                        if (
                            descripcion_archivo != descripcion_db
                            or id_categoria_archivo != id_categoria_db
                        ):
                            conflictos.append({
                                "clave": clave,
                                "descripcion_db": descripcion_db,
                                "descripcion_archivo": descripcion_archivo,
                                "id_categoria_db": id_categoria_db,
                                "id_categoria_archivo": id_categoria_archivo,
                            })

                if conflictos:
                    detalle = "\n".join(
                        [
                            f"Clave {c['clave']} ya existe con datos diferentes. "
                            f"BD: [{c['descripcion_db']}, categoria {c['id_categoria_db']}]. "
                            f"Archivo: [{c['descripcion_archivo']}, categoria {c['id_categoria_archivo']}]."
                            for c in conflictos[:20]
                        ]
                    )

                    raise ValueError(
                        "Se detectaron claves existentes con descripción o categoría diferente. "
                        "La carga fue cancelada para proteger el catálogo maestro.\n"
                        + detalle
                    )

                registros_nuevos = [
                    (
                        row["clave"],
                        row["descripcion"],
                        categorias[row["categoria"]],
                    )
                    for _, row in df.iterrows()
                    if row["clave"] not in existentes
                ]

                if registros_nuevos:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO simi.claves (
                            clave,
                            descripcion,
                            id_categoria
                        )
                        VALUES %s;
                        """,
                        registros_nuevos,
                    )

                insertados = len(registros_nuevos)
                actualizados = 0
                existentes_sin_cambios = len(df) - insertados

                cursor.execute(
                    """
                    INSERT INTO simi.bitacora_catalogos (
                        tabla_catalogo,
                        accion,
                        modulo,
                        id_usuario,
                        registros_insertados,
                        registros_actualizados,
                        archivo_origen,
                        observaciones
                    )
                    VALUES (
                        'claves',
                        'SINCRONIZACION',
                        'CATALOG_MANAGER',
                        %s,
                        %s,
                        %s,
                        %s,
                        'Carga de claves: nuevas insertadas, existentes idénticas conservadas, sin actualización automática'
                    );
                    """,
                    (id_usuario, insertados, actualizados, archivo),
                )

        return {
            "success": True,
            "tabla": "claves",
            "procesados": len(df),
            "insertados": insertados,
            "actualizados": actualizados,
            "existentes_sin_cambios": existentes_sin_cambios,
        }

    def cargar_proveedores(self, archivo: str, id_usuario: int, user_role: str = "ADMINISTRADOR"):
        df = pd.read_excel(archivo)
        df = self._normalizar_columnas(df)

        col_rfc = self._obtener_columna(
            df,
            ["rfc"],
            "rfc"
        )

        col_razon_social = self._obtener_columna(
            df,
            ["razon_social", "razon social", "proveedor", "nombre_proveedor"],
            "razon_social"
        )

        df["rfc"] = df[col_rfc].astype(str).str.strip().str.upper()
        df["razon_social"] = df[col_razon_social].astype(str).str.strip().str.upper()

        rfcs_invalidos_cortos = df[df["rfc"].str.len() < 12]["rfc"].tolist()
        rfcs_invalidos_largos = df[df["rfc"].str.len() > 13]["rfc"].tolist()

        if rfcs_invalidos_cortos:
            raise ValueError(
                "Existen RFC con longitud menor a 12 caracteres. "
                f"Revise estos RFC: {rfcs_invalidos_cortos[:20]}"
            )

        if rfcs_invalidos_largos:
            raise ValueError(
                "Existen RFC con longitud mayor a 13 caracteres. "
                f"Revise estos RFC: {rfcs_invalidos_largos[:20]}"
            )


        columnas_finales = ["rfc", "razon_social"]

        self._validar_vacios(df, columnas_finales)

        if df["rfc"].duplicated().any():
            duplicados = df[df["rfc"].duplicated()]["rfc"].tolist()
            raise ValueError(f"Existen RFC duplicados en el archivo: {duplicados}")

        with self.connection:
            with self.connection.cursor() as cursor:
                self._set_user_role(cursor, user_role)

                rfcs_archivo = df["rfc"].tolist()

                cursor.execute(
                    """
                    SELECT rfc
                    FROM simi.proveedores
                    WHERE rfc = ANY(%s);
                    """,
                    (rfcs_archivo,)
                )

                rfcs_existentes = {row[0] for row in cursor.fetchall()}

                registros = [
                    (
                        row["rfc"],
                        row["razon_social"],
                    )
                    for _, row in df.iterrows()
                ]

                execute_values(
                    cursor,
                    """
                    INSERT INTO simi.proveedores (
                        rfc,
                        razon_social
                    )
                    VALUES %s
                    ON CONFLICT (rfc)
                    DO UPDATE SET
                        razon_social = EXCLUDED.razon_social;
                    """,
                    registros,
                )

                actualizados = len(rfcs_existentes)
                insertados = len(registros) - actualizados

                cursor.execute(
                    """
                    INSERT INTO simi.bitacora_catalogos (
                        tabla_catalogo,
                        accion,
                        modulo,
                        id_usuario,
                        registros_insertados,
                        registros_actualizados,
                        archivo_origen,
                        observaciones
                    )
                    VALUES (
                        'proveedores',
                        'SINCRONIZACION',
                        'CATALOG_MANAGER',
                        %s,
                        %s,
                        %s,
                        %s,
                        'Carga o sincronización de catálogo de proveedores por RFC'
                    );
                    """,
                    (id_usuario, insertados, actualizados, archivo),
                )

        return {
            "success": True,
            "tabla": "proveedores",
            "procesados": len(registros),
            "insertados": insertados,
            "actualizados": actualizados,
        }