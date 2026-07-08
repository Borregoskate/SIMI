/*
===========================================================
SIMI
Sprint 0.5.1
Archivo: 006_create_views.sql
Descripción:
Creación de vistas base y vistas analíticas para consultas,
reportes y consumo desde Streamlit.
===========================================================
*/

------------------------------------------------------------
-- 1. Vista de claves por procedimiento
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_procedimiento_claves AS
SELECT
    pc.id_procedimiento_clave,
    pc.id_procedimiento,
    p.numero_procedimiento,
    c.id_clave,
    c.clave,
    c.descripcion,
    pc.cantidad_requerida
FROM procedimiento_claves pc
JOIN procedimientos p
    ON p.id_procedimiento = pc.id_procedimiento
JOIN claves c
    ON c.id_clave = pc.id_clave;


------------------------------------------------------------
-- 2. Vista de propuestas completas
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_propuestas AS
SELECT
    prop.id_propuesta,
    prop.id_procedimiento_clave,
    pc.id_procedimiento,
    proc.numero_procedimiento,
    c.id_clave,
    c.clave,
    c.descripcion,
    prov.id_proveedor,
    prov.rfc,
    prov.razon_social,
    prop.tipo_propuesta,
    prop.cantidad_ofertada,
    prop.id_pais_origen,
    prop.precio_unitario,
    prop.fecha_registro,
    (prop.cantidad_ofertada * prop.precio_unitario) AS monto_ofertado
FROM propuestas prop
JOIN procedimiento_claves pc
    ON pc.id_procedimiento_clave = prop.id_procedimiento_clave
JOIN procedimientos proc
    ON proc.id_procedimiento = pc.id_procedimiento
JOIN claves c
    ON c.id_clave = pc.id_clave
JOIN proveedores prov
    ON prov.id_proveedor = prop.id_proveedor;


------------------------------------------------------------
-- 3. Vista de propuesta vigente por proveedor y clave
-- Si existe SUBASTA, toma SUBASTA.
-- Si no existe, toma INICIAL.
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_propuesta_vigente_por_proveedor_clave AS
SELECT
    x.id_propuesta,
    x.id_procedimiento_clave,
    x.id_procedimiento,
    x.numero_procedimiento,
    x.id_clave,
    x.clave,
    x.descripcion,
    x.id_proveedor,
    x.rfc,
    x.razon_social,
    x.tipo_propuesta,
    x.cantidad_ofertada,
    x.id_pais_origen,
    x.precio_unitario,
    x.fecha_registro,
    x.monto_ofertado
FROM (
    SELECT
        vp.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                vp.id_procedimiento,
                vp.id_clave,
                vp.id_proveedor
            ORDER BY
                CASE
                    WHEN UPPER(vp.tipo_propuesta) = 'SUBASTA' THEN 1
                    WHEN UPPER(vp.tipo_propuesta) = 'INICIAL' THEN 2
                    ELSE 3
                END,
                vp.fecha_registro DESC,
                vp.id_propuesta DESC
        ) AS rn
    FROM vw_propuestas vp
) x
WHERE x.rn = 1;


------------------------------------------------------------
-- 4. Vista de evaluaciones técnicas
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_evaluaciones_tecnicas AS
SELECT
    e.id_evaluacion,
    e.id_procedimiento,
    proc.numero_procedimiento,
    c.id_clave,
    c.clave,
    c.descripcion,
    prov.id_proveedor,
    prov.rfc,
    prov.razon_social,
    e.resultado
FROM evaluaciones_tecnicas e
JOIN procedimientos proc
    ON proc.id_procedimiento = e.id_procedimiento
JOIN claves c
    ON c.id_clave = e.id_clave
JOIN proveedores prov
    ON prov.id_proveedor = e.id_proveedor;


------------------------------------------------------------
-- 5. Vista de propuestas con evaluación técnica
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_propuestas_con_evaluacion AS
SELECT
    pv.*,
    et.resultado AS resultado_tecnico
FROM vw_propuesta_vigente_por_proveedor_clave pv
LEFT JOIN evaluaciones_tecnicas et
    ON et.id_procedimiento = pv.id_procedimiento
   AND et.id_clave = pv.id_clave
   AND et.id_proveedor = pv.id_proveedor;


------------------------------------------------------------
-- 6. Vista de adjudicaciones actuales
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_adjudicaciones AS
SELECT
    a.id_adjudicacion,
    a.id_procedimiento,
    proc.numero_procedimiento,
    c.id_clave,
    c.clave,
    c.descripcion,
    prov.id_proveedor,
    prov.rfc,
    prov.razon_social,
    a.cantidad_adjudicada,
    a.porcentaje_adjudicado,
    a.precio_unitario_adjudicado,
    (a.cantidad_adjudicada * a.precio_unitario_adjudicado) AS monto_adjudicado_calculado
FROM adjudicaciones a
JOIN procedimientos proc
    ON proc.id_procedimiento = a.id_procedimiento
JOIN claves c
    ON c.id_clave = a.id_clave
JOIN proveedores prov
    ON prov.id_proveedor = a.id_proveedor;


------------------------------------------------------------
-- 7. Vista de adjudicaciones históricas
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_adjudicaciones_historicas AS
SELECT
    ah.id_adjudicacion_historica,
    ah.numero_procedimiento,
    c.id_clave,
    c.clave,
    c.descripcion,
    prov.id_proveedor,
    prov.rfc,
    prov.razon_social,
    ah.cantidad_adjudicada,
    ah.porcentaje_adjudicado,
    ah.precio_unitario_adjudicado,
    (ah.cantidad_adjudicada * ah.precio_unitario_adjudicado) AS monto_adjudicado_historico_calculado
FROM adjudicaciones_historicas ah
JOIN claves c
    ON c.id_clave = ah.id_clave
JOIN proveedores prov
    ON prov.id_proveedor = ah.id_proveedor;


------------------------------------------------------------
-- 8. Vista de historial de fases
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_procedimiento_fases AS
SELECT
    pf.id_procedimiento_fase,
    pf.id_procedimiento,
    proc.numero_procedimiento,
    pf.fase,
    pf.fecha
FROM procedimiento_fases pf
JOIN procedimientos proc
    ON proc.id_procedimiento = pf.id_procedimiento;


------------------------------------------------------------
-- 9. Vista de estado actual del procedimiento
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_estado_actual_procedimiento AS
SELECT
    x.id_procedimiento,
    x.numero_procedimiento,
    x.fase AS estado_actual,
    x.fecha AS fecha_estado_actual
FROM (
    SELECT
        pf.id_procedimiento,
        proc.numero_procedimiento,
        pf.fase,
        pf.fecha,
        ROW_NUMBER() OVER (
            PARTITION BY pf.id_procedimiento
            ORDER BY pf.fecha DESC, pf.id_procedimiento_fase DESC
        ) AS rn
    FROM procedimiento_fases pf
    JOIN procedimientos proc
        ON proc.id_procedimiento = pf.id_procedimiento
) x
WHERE x.rn = 1;


------------------------------------------------------------
-- 10. Vista resumen de procedimientos
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_resumen_procedimientos AS
SELECT
    proc.id_procedimiento,
    proc.numero_procedimiento,
    COUNT(DISTINCT pc.id_clave) AS total_claves,
    COUNT(DISTINCT prop.id_proveedor) AS total_proveedores,
    COUNT(prop.id_propuesta) AS total_propuestas,
    COALESCE(eap.estado_actual, 'SIN_ESTADO') AS estado_actual,
    eap.fecha_estado_actual
FROM procedimientos proc
LEFT JOIN procedimiento_claves pc
    ON pc.id_procedimiento = proc.id_procedimiento
LEFT JOIN propuestas prop
    ON prop.id_procedimiento_clave = pc.id_procedimiento_clave
LEFT JOIN vw_estado_actual_procedimiento eap
    ON eap.id_procedimiento = proc.id_procedimiento
GROUP BY
    proc.id_procedimiento,
    proc.numero_procedimiento,
    eap.estado_actual,
    eap.fecha_estado_actual;


------------------------------------------------------------
-- 11. Vista analítica: mejor precio por clave
-- Considera la propuesta vigente, sin filtrar evaluación técnica.
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_mejor_precio_por_clave AS
SELECT
    x.id_procedimiento,
    x.numero_procedimiento,
    x.id_clave,
    x.clave,
    x.descripcion,
    x.id_proveedor,
    x.rfc,
    x.razon_social,
    x.tipo_propuesta,
    x.cantidad_ofertada,
    x.precio_unitario,
    x.monto_ofertado
FROM (
    SELECT
        pv.*,
        ROW_NUMBER() OVER (
            PARTITION BY pv.id_procedimiento, pv.id_clave
            ORDER BY pv.precio_unitario ASC, pv.id_proveedor ASC
        ) AS rn
    FROM vw_propuesta_vigente_por_proveedor_clave pv
) x
WHERE x.rn = 1;


------------------------------------------------------------
-- 12. Vista analítica: mejor precio evaluado
-- Solo considera propuestas técnicamente positivas.
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_mejor_precio_evaluado AS
SELECT
    x.id_procedimiento,
    x.numero_procedimiento,
    x.id_clave,
    x.clave,
    x.descripcion,
    x.id_proveedor,
    x.rfc,
    x.razon_social,
    x.tipo_propuesta,
    x.cantidad_ofertada,
    x.precio_unitario,
    x.monto_ofertado,
    x.resultado_tecnico
FROM (
    SELECT
        pce.*,
        ROW_NUMBER() OVER (
            PARTITION BY pce.id_procedimiento, pce.id_clave
            ORDER BY pce.precio_unitario ASC, pce.id_proveedor ASC
        ) AS rn
    FROM vw_propuestas_con_evaluacion pce
    WHERE UPPER(pce.resultado_tecnico) = 'POSITIVA'
) x
WHERE x.rn = 1;


------------------------------------------------------------
-- 13. Vista analítica: comparativo histórico
-- Compara propuestas actuales contra adjudicaciones históricas.
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_comparativo_historico AS
SELECT
    pv.id_procedimiento,
    pv.numero_procedimiento,
    pv.id_clave,
    pv.clave,
    pv.descripcion,
    pv.id_proveedor,
    pv.rfc,
    pv.razon_social,
    pv.precio_unitario AS precio_actual,
    ah.numero_procedimiento AS numero_procedimiento_historico,
    ah.precio_unitario_adjudicado AS precio_historico,
    (pv.precio_unitario - ah.precio_unitario_adjudicado) AS variacion_precio,
    CASE
        WHEN ah.precio_unitario_adjudicado IS NULL
          OR ah.precio_unitario_adjudicado = 0
        THEN NULL
        ELSE ROUND(
            ((pv.precio_unitario - ah.precio_unitario_adjudicado)
            / ah.precio_unitario_adjudicado) * 100,
            2
        )
    END AS variacion_porcentual
FROM vw_propuesta_vigente_por_proveedor_clave pv
LEFT JOIN vw_adjudicaciones_historicas ah
    ON ah.id_clave = pv.id_clave
   AND ah.id_proveedor = pv.id_proveedor;


------------------------------------------------------------
-- 14. Vista analítica: proveedores por clave
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_proveedores_por_clave AS
SELECT
    pv.id_procedimiento,
    pv.numero_procedimiento,
    pv.id_clave,
    pv.clave,
    pv.descripcion,
    COUNT(DISTINCT pv.id_proveedor) AS total_proveedores,
    MIN(pv.precio_unitario) AS precio_minimo,
    MAX(pv.precio_unitario) AS precio_maximo,
    ROUND(AVG(pv.precio_unitario), 2) AS precio_promedio
FROM vw_propuesta_vigente_por_proveedor_clave pv
GROUP BY
    pv.id_procedimiento,
    pv.numero_procedimiento,
    pv.id_clave,
    pv.clave,
    pv.descripcion;


------------------------------------------------------------
-- 15. Vista futura: claves desiertas
-- Claves del procedimiento que no recibieron propuesta.
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_claves_desiertas AS
SELECT
    pc.id_procedimiento,
    pc.numero_procedimiento,
    pc.id_clave,
    pc.clave,
    pc.descripcion,
    pc.cantidad_requerida
FROM vw_procedimiento_claves pc
LEFT JOIN vw_propuesta_vigente_por_proveedor_clave pv
    ON pv.id_procedimiento = pc.id_procedimiento
   AND pv.id_clave = pc.id_clave
WHERE pv.id_propuesta IS NULL;


------------------------------------------------------------
-- 16. Vista futura: claves sin propuesta evaluada positiva
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_claves_sin_propuesta_viable AS
SELECT
    pc.id_procedimiento,
    pc.numero_procedimiento,
    pc.id_clave,
    pc.clave,
    pc.descripcion,
    pc.cantidad_requerida
FROM vw_procedimiento_claves pc
LEFT JOIN vw_mejor_precio_evaluado mpe
    ON mpe.id_procedimiento = pc.id_procedimiento
   AND mpe.id_clave = pc.id_clave
WHERE mpe.id_clave IS NULL;


------------------------------------------------------------
-- 17. Vista futura: propuestas descartadas técnicamente
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_propuestas_descartadas_tecnicamente AS
SELECT
    pce.*
FROM vw_propuestas_con_evaluacion pce
WHERE UPPER(pce.resultado_tecnico) = 'NEGATIVA';


------------------------------------------------------------
-- 18. Vista futura: media preliminar por clave
-- Considera todas las propuestas vigentes.
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_media_preliminar_por_clave AS
SELECT
    pv.id_procedimiento,
    pv.numero_procedimiento,
    pv.id_clave,
    pv.clave,
    pv.descripcion,
    COUNT(DISTINCT pv.id_proveedor) AS total_proveedores,
    ROUND(AVG(pv.precio_unitario), 2) AS media_precio_preliminar,
    MIN(pv.precio_unitario) AS precio_minimo_preliminar,
    MAX(pv.precio_unitario) AS precio_maximo_preliminar
FROM vw_propuesta_vigente_por_proveedor_clave pv
GROUP BY
    pv.id_procedimiento,
    pv.numero_procedimiento,
    pv.id_clave,
    pv.clave,
    pv.descripcion;


------------------------------------------------------------
-- 19. Vista futura: media post evaluación por clave
-- Considera solo propuestas técnicamente positivas.
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_media_post_evaluacion_por_clave AS
SELECT
    pce.id_procedimiento,
    pce.numero_procedimiento,
    pce.id_clave,
    pce.clave,
    pce.descripcion,
    COUNT(DISTINCT pce.id_proveedor) AS total_proveedores_viables,
    ROUND(AVG(pce.precio_unitario), 2) AS media_precio_post_evaluacion,
    MIN(pce.precio_unitario) AS precio_minimo_post_evaluacion,
    MAX(pce.precio_unitario) AS precio_maximo_post_evaluacion
FROM vw_propuestas_con_evaluacion pce
WHERE UPPER(pce.resultado_tecnico) = 'POSITIVA'
GROUP BY
    pce.id_procedimiento,
    pce.numero_procedimiento,
    pce.id_clave,
    pce.clave,
    pce.descripcion;


------------------------------------------------------------
-- 20. Vista futura: resumen económico por clave
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_resumen_economico_por_clave AS
SELECT
    pc.id_procedimiento,
    pc.numero_procedimiento,
    pc.id_clave,
    pc.clave,
    pc.descripcion,
    pc.cantidad_requerida,

    mp.media_precio_preliminar,
    mp.precio_minimo_preliminar,
    mp.precio_maximo_preliminar,

    mpe.media_precio_post_evaluacion,
    mpe.precio_minimo_post_evaluacion,
    mpe.precio_maximo_post_evaluacion,

    mejor.id_proveedor AS id_proveedor_mejor_precio,
    mejor.rfc AS rfc_mejor_precio,
    mejor.razon_social AS proveedor_mejor_precio,
    mejor.precio_unitario AS mejor_precio_general,

    mejor_eval.id_proveedor AS id_proveedor_mejor_precio_evaluado,
    mejor_eval.rfc AS rfc_mejor_precio_evaluado,
    mejor_eval.razon_social AS proveedor_mejor_precio_evaluado,
    mejor_eval.precio_unitario AS mejor_precio_viable

FROM vw_procedimiento_claves pc
LEFT JOIN vw_media_preliminar_por_clave mp
    ON mp.id_procedimiento = pc.id_procedimiento
   AND mp.id_clave = pc.id_clave
LEFT JOIN vw_media_post_evaluacion_por_clave mpe
    ON mpe.id_procedimiento = pc.id_procedimiento
   AND mpe.id_clave = pc.id_clave
LEFT JOIN vw_mejor_precio_por_clave mejor
    ON mejor.id_procedimiento = pc.id_procedimiento
   AND mejor.id_clave = pc.id_clave
LEFT JOIN vw_mejor_precio_evaluado mejor_eval
    ON mejor_eval.id_procedimiento = pc.id_procedimiento
   AND mejor_eval.id_clave = pc.id_clave;


------------------------------------------------------------
-- 21. Vista futura: resumen de adjudicación por clave
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_resumen_adjudicacion_por_clave AS
SELECT
    a.id_procedimiento,
    a.numero_procedimiento,
    a.id_clave,
    a.clave,
    a.descripcion,
    COUNT(DISTINCT a.id_proveedor) AS total_proveedores_adjudicados,
    SUM(a.cantidad_adjudicada) AS cantidad_total_adjudicada,
    SUM(a.monto_adjudicado_calculado) AS monto_total_adjudicado_calculado,
    MIN(a.precio_unitario_adjudicado) AS precio_minimo_adjudicado,
    MAX(a.precio_unitario_adjudicado) AS precio_maximo_adjudicado
FROM vw_adjudicaciones a
GROUP BY
    a.id_procedimiento,
    a.numero_procedimiento,
    a.id_clave,
    a.clave,
    a.descripcion;


------------------------------------------------------------
-- 22. Vista futura: comparación propuesta vs adjudicación
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_comparativo_propuesta_adjudicacion AS
SELECT
    pv.id_procedimiento,
    pv.numero_procedimiento,
    pv.id_clave,
    pv.clave,
    pv.descripcion,
    pv.id_proveedor,
    pv.rfc,
    pv.razon_social,
    pv.precio_unitario AS precio_propuesto,
    a.precio_unitario_adjudicado,
    (pv.precio_unitario - a.precio_unitario_adjudicado) AS diferencia_precio,
    CASE
        WHEN a.precio_unitario_adjudicado IS NULL
          OR a.precio_unitario_adjudicado = 0
        THEN NULL
        ELSE ROUND(
            ((pv.precio_unitario - a.precio_unitario_adjudicado)
            / a.precio_unitario_adjudicado) * 100,
            2
        )
    END AS diferencia_porcentual
FROM vw_propuesta_vigente_por_proveedor_clave pv
LEFT JOIN vw_adjudicaciones a
    ON a.id_procedimiento = pv.id_procedimiento
   AND a.id_clave = pv.id_clave
   AND a.id_proveedor = pv.id_proveedor;


------------------------------------------------------------
-- 23. Vista futura: ranking de proveedores por clave
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_ranking_proveedores_por_clave AS
SELECT
    pv.id_procedimiento,
    pv.numero_procedimiento,
    pv.id_clave,
    pv.clave,
    pv.descripcion,
    pv.id_proveedor,
    pv.rfc,
    pv.razon_social,
    pv.tipo_propuesta,
    pv.precio_unitario,
    pv.cantidad_ofertada,
    pv.monto_ofertado,
    ROW_NUMBER() OVER (
        PARTITION BY pv.id_procedimiento, pv.id_clave
        ORDER BY pv.precio_unitario ASC, pv.id_proveedor ASC
    ) AS ranking_precio
FROM vw_propuesta_vigente_por_proveedor_clave pv;


------------------------------------------------------------
-- 24. Vista futura: ranking de proveedores viables por clave
------------------------------------------------------------
CREATE OR REPLACE VIEW vw_ranking_proveedores_viables_por_clave AS
SELECT
    pce.id_procedimiento,
    pce.numero_procedimiento,
    pce.id_clave,
    pce.clave,
    pce.descripcion,
    pce.id_proveedor,
    pce.rfc,
    pce.razon_social,
    pce.tipo_propuesta,
    pce.precio_unitario,
    pce.cantidad_ofertada,
    pce.monto_ofertado,
    pce.resultado_tecnico,
    ROW_NUMBER() OVER (
        PARTITION BY pce.id_procedimiento, pce.id_clave
        ORDER BY pce.precio_unitario ASC, pce.id_proveedor ASC
    ) AS ranking_precio_viable
FROM vw_propuestas_con_evaluacion pce
WHERE UPPER(pce.resultado_tecnico) = 'POSITIVA';