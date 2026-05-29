-- =============================================================
-- RetailMax -- Tab 2 "Crecimiento y Expansión" -- Parte B
-- CC3088 Base de Datos 1 | Universidad del Valle de Guatemala
-- Área 7: Estrategia y Expansión Comercial
--
-- Consultas nativas para las 4 tarjetas de la Parte B (Compa 3).
-- Convención del proyecto (igual que Parte A):
--   * Ingreso neto  = dp.cantidad * dp.precio_unitario * (1 - dp.descuento/100.0)
--   * Solo pedidos con estado = 'completado'
--   * Datos disponibles: 2024-01-01 a 2026-05-14
--     -> los dos años COMPLETOS son 2024 y 2025; 2026 es parcial.
--
-- Cada bloque se pega tal cual en una tarjeta SQL nativa de Metabase.
-- =============================================================


-- =============================================================
-- 11. Categorías con mayor crecimiento interanual (YoY)
--     Compara ingresos por categoría entre los dos años completos
--     (2024 vs 2025) y ordena por % de crecimiento.
--     Visualización sugerida: gráfico de barras (crecimiento_pct).
-- =============================================================
WITH ventas_anuales AS (
    SELECT
        c.nombre                                                        AS categoria,
        EXTRACT(YEAR FROM p.fecha)::int                                 AS anio,
        SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento/100.0)) AS ingresos
    FROM pedido         p
    JOIN detalle_pedido dp ON dp.id_pedido   = p.id_pedido
    JOIN producto       pr ON pr.id_producto = dp.id_producto
    JOIN categoria      c  ON c.id_categoria = pr.id_categoria
    WHERE p.estado = 'completado'
      AND EXTRACT(YEAR FROM p.fecha) IN (2024, 2025)   -- años completos
    GROUP BY c.nombre, EXTRACT(YEAR FROM p.fecha)
),
pivote AS (
    SELECT
        categoria,
        SUM(ingresos) FILTER (WHERE anio = 2024) AS ingresos_2024,
        SUM(ingresos) FILTER (WHERE anio = 2025) AS ingresos_2025
    FROM ventas_anuales
    GROUP BY categoria
)
SELECT
    categoria,
    ROUND(COALESCE(ingresos_2024, 0), 2)                                 AS ingresos_2024,
    ROUND(COALESCE(ingresos_2025, 0), 2)                                 AS ingresos_2025,
    ROUND(COALESCE(ingresos_2025, 0) - COALESCE(ingresos_2024, 0), 2)    AS variacion_absoluta,
    ROUND(100.0 * (ingresos_2025 - ingresos_2024) / NULLIF(ingresos_2024, 0), 2) AS crecimiento_pct
FROM pivote
ORDER BY crecimiento_pct DESC NULLS LAST;


-- =============================================================
-- 12. Días promedio entre primera y segunda compra por segmento
--     Mide la velocidad de recompra: cuántos días tarda un cliente
--     en volver a comprar tras su primer pedido, por segmento.
--     Visualización sugerida: barras (dias_promedio_recompra).
-- =============================================================
WITH compras_ordenadas AS (
    SELECT
        p.id_cliente,
        p.fecha,
        ROW_NUMBER() OVER (PARTITION BY p.id_cliente
                           ORDER BY p.fecha, p.id_pedido) AS n_compra
    FROM pedido p
    WHERE p.estado = 'completado'
),
primera_segunda AS (
    SELECT
        id_cliente,
        MAX(fecha) FILTER (WHERE n_compra = 1) AS fecha_primera,
        MAX(fecha) FILTER (WHERE n_compra = 2) AS fecha_segunda
    FROM compras_ordenadas
    WHERE n_compra <= 2
    GROUP BY id_cliente
    HAVING COUNT(*) = 2          -- solo clientes que SÍ recompraron
)
SELECT
    cl.segmento,
    COUNT(*)                                            AS clientes_con_recompra,
    ROUND(AVG(ps.fecha_segunda - ps.fecha_primera), 1)  AS dias_promedio_recompra,
    MIN(ps.fecha_segunda - ps.fecha_primera)            AS dias_min,
    MAX(ps.fecha_segunda - ps.fecha_primera)            AS dias_max
FROM primera_segunda ps
JOIN cliente cl ON cl.id_cliente = ps.id_cliente
GROUP BY cl.segmento
ORDER BY dias_promedio_recompra ASC;


-- =============================================================
-- 13. Productos con alto margen pero bajo volumen de ventas  (BONUS)
--     "Joyas ocultas": rentables por unidad pero poco vendidas
--     -> candidatos a impulsar con campañas / mejor exhibición.
--     Criterio: margen >= mediana y unidades <= mediana del catálogo.
--     Visualización sugerida: tabla o dispersión (margen_pct vs unidades).
-- =============================================================
WITH ventas_producto AS (
    SELECT
        pr.id_producto,
        pr.nombre                                                       AS producto,
        c.nombre                                                        AS categoria,
        ROUND(100.0 * (pr.precio_venta - pr.precio_costo) / pr.precio_venta, 2) AS margen_pct,
        COALESCE(SUM(dp.cantidad), 0)                                   AS unidades_vendidas,
        ROUND(COALESCE(SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento/100.0)), 0), 2) AS ingresos
    FROM producto pr
    JOIN categoria c ON c.id_categoria = pr.id_categoria
    LEFT JOIN detalle_pedido dp ON dp.id_producto = pr.id_producto
    LEFT JOIN pedido p          ON p.id_pedido     = dp.id_pedido
                               AND p.estado        = 'completado'
    GROUP BY pr.id_producto, pr.nombre, c.nombre, pr.precio_costo, pr.precio_venta
),
umbrales AS (
    SELECT
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY margen_pct)         AS margen_mediana,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY unidades_vendidas)  AS volumen_mediana
    FROM ventas_producto
)
SELECT
    v.producto,
    v.categoria,
    v.margen_pct,
    v.unidades_vendidas,
    v.ingresos,
    ROUND(u.margen_mediana::numeric, 2)  AS margen_mediana_catalogo,
    ROUND(u.volumen_mediana::numeric, 1) AS volumen_mediana_catalogo
FROM ventas_producto v
CROSS JOIN umbrales u
WHERE v.margen_pct        >= u.margen_mediana
  AND v.unidades_vendidas <= u.volumen_mediana
ORDER BY v.margen_pct DESC, v.unidades_vendidas ASC;


-- =============================================================
-- 14. Efectividad de campañas por tipo y canal  (BONUS)
--     Tasa de respuesta y costo por respuesta agrupados por
--     tipo de campaña (email, redes, SMS, descuento) y canal.
--     El CTE evita multiplicar el presupuesto por cliente alcanzado.
--     Visualización sugerida: barras (tasa_respuesta_pct) o tabla.
-- =============================================================
WITH respuestas AS (
    SELECT
        ca.id_campana,
        ca.tipo,
        ca.canal,
        ca.presupuesto,
        COUNT(cc.id_cliente)                 AS alcanzados,
        COUNT(*) FILTER (WHERE cc.respondio) AS respondieron
    FROM campana ca
    LEFT JOIN campana_cliente cc ON cc.id_campana = ca.id_campana
    GROUP BY ca.id_campana, ca.tipo, ca.canal, ca.presupuesto
)
SELECT
    tipo,
    canal,
    COUNT(*)                                                AS num_campanas,
    SUM(alcanzados)                                         AS clientes_alcanzados,
    SUM(respondieron)                                       AS clientes_respondieron,
    ROUND(100.0 * SUM(respondieron) / NULLIF(SUM(alcanzados), 0), 2) AS tasa_respuesta_pct,
    ROUND(SUM(presupuesto), 2)                              AS presupuesto_total,
    ROUND(SUM(presupuesto) / NULLIF(SUM(respondieron), 0), 2) AS costo_por_respuesta
FROM respuestas
GROUP BY tipo, canal
ORDER BY tasa_respuesta_pct DESC;
