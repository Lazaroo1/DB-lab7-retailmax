#!/usr/bin/env python3
# =============================================================
# Crea las 4 tarjetas de Tab 2 - Parte B en Metabase vía API REST
# y las agrega al Tab 2 del dashboard, SIN editar el dump a mano.
#
# Solo usa la librería estándar de Python 3. Metabase en :3000.
# Uso:  python3 consultas/crear_tarjetas_metabase.py
# Idempotente: si una tarjeta con el mismo nombre ya existe, la
# reutiliza; no duplica tarjetas ya presentes en el Tab 2.
# =============================================================
import json
import sys
import urllib.request

MB = "http://localhost:3000"
EMAIL = "calificar@uvg.edu.gt"
PASS = "secret123+"
DB_NAME = "RetailMax DB"
DASH_NAME = "Estrategia y Expansión Comercial"
TAB_MATCH = "crecimiento"  # subcadena (minúsculas) que identifica el Tab 2

SESSION = None


def api(method, path, payload=None):
    url = MB + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if SESSION:
        req.add_header("X-Metabase-Session", SESSION)
    with urllib.request.urlopen(req) as r:
        body = r.read().decode()
        return json.loads(body) if body else None


CARDS = [
    {
        "name": "11. Categorías con mayor crecimiento interanual",
        "display": "bar",
        "query": """WITH ventas_anuales AS (
    SELECT c.nombre AS categoria, EXTRACT(YEAR FROM p.fecha)::int AS anio,
           SUM(dp.cantidad * dp.precio_unitario * (1 - dp.descuento/100.0)) AS ingresos
    FROM pedido p
    JOIN detalle_pedido dp ON dp.id_pedido = p.id_pedido
    JOIN producto pr ON pr.id_producto = dp.id_producto
    JOIN categoria c ON c.id_categoria = pr.id_categoria
    WHERE p.estado = 'completado' AND EXTRACT(YEAR FROM p.fecha) IN (2024, 2025)
    GROUP BY c.nombre, EXTRACT(YEAR FROM p.fecha)
),
pivote AS (
    SELECT categoria,
           SUM(ingresos) FILTER (WHERE anio = 2024) AS ingresos_2024,
           SUM(ingresos) FILTER (WHERE anio = 2025) AS ingresos_2025
    FROM ventas_anuales GROUP BY categoria
)
SELECT categoria,
       ROUND(COALESCE(ingresos_2024,0),2) AS ingresos_2024,
       ROUND(COALESCE(ingresos_2025,0),2) AS ingresos_2025,
       ROUND(COALESCE(ingresos_2025,0)-COALESCE(ingresos_2024,0),2) AS variacion_absoluta,
       ROUND(100.0*(ingresos_2025-ingresos_2024)/NULLIF(ingresos_2024,0),2) AS crecimiento_pct
FROM pivote ORDER BY crecimiento_pct DESC NULLS LAST;""",
        "viz": {"graph.dimensions": ["categoria"], "graph.metrics": ["crecimiento_pct"]},
    },
    {
        "name": "12. Días promedio entre 1ª y 2ª compra por segmento",
        "display": "bar",
        "query": """WITH compras_ordenadas AS (
    SELECT p.id_cliente, p.fecha,
           ROW_NUMBER() OVER (PARTITION BY p.id_cliente ORDER BY p.fecha, p.id_pedido) AS n_compra
    FROM pedido p WHERE p.estado = 'completado'
),
primera_segunda AS (
    SELECT id_cliente,
           MAX(fecha) FILTER (WHERE n_compra = 1) AS fecha_primera,
           MAX(fecha) FILTER (WHERE n_compra = 2) AS fecha_segunda
    FROM compras_ordenadas WHERE n_compra <= 2
    GROUP BY id_cliente HAVING COUNT(*) = 2
)
SELECT cl.segmento,
       COUNT(*) AS clientes_con_recompra,
       ROUND(AVG(ps.fecha_segunda - ps.fecha_primera),1) AS dias_promedio_recompra,
       MIN(ps.fecha_segunda - ps.fecha_primera) AS dias_min,
       MAX(ps.fecha_segunda - ps.fecha_primera) AS dias_max
FROM primera_segunda ps
JOIN cliente cl ON cl.id_cliente = ps.id_cliente
GROUP BY cl.segmento ORDER BY dias_promedio_recompra ASC;""",
        "viz": {"graph.dimensions": ["segmento"], "graph.metrics": ["dias_promedio_recompra"]},
    },
    {
        "name": "13. Productos alto margen / bajo volumen",
        "display": "table",
        "query": """WITH ventas_producto AS (
    SELECT pr.id_producto, pr.nombre AS producto, c.nombre AS categoria,
           ROUND(100.0*(pr.precio_venta-pr.precio_costo)/pr.precio_venta,2) AS margen_pct,
           COALESCE(SUM(dp.cantidad),0) AS unidades_vendidas,
           ROUND(COALESCE(SUM(dp.cantidad*dp.precio_unitario*(1-dp.descuento/100.0)),0),2) AS ingresos
    FROM producto pr
    JOIN categoria c ON c.id_categoria = pr.id_categoria
    LEFT JOIN detalle_pedido dp ON dp.id_producto = pr.id_producto
    LEFT JOIN pedido p ON p.id_pedido = dp.id_pedido AND p.estado = 'completado'
    GROUP BY pr.id_producto, pr.nombre, c.nombre, pr.precio_costo, pr.precio_venta
),
umbrales AS (
    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY margen_pct) AS margen_mediana,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY unidades_vendidas) AS volumen_mediana
    FROM ventas_producto
)
SELECT v.producto, v.categoria, v.margen_pct, v.unidades_vendidas, v.ingresos,
       ROUND(u.margen_mediana::numeric,2) AS margen_mediana_catalogo,
       ROUND(u.volumen_mediana::numeric,1) AS volumen_mediana_catalogo
FROM ventas_producto v CROSS JOIN umbrales u
WHERE v.margen_pct >= u.margen_mediana AND v.unidades_vendidas <= u.volumen_mediana
ORDER BY v.margen_pct DESC, v.unidades_vendidas ASC;""",
        "viz": {},
    },
    {
        "name": "14. Efectividad de campañas por tipo y canal",
        "display": "bar",
        "query": """WITH respuestas AS (
    SELECT ca.id_campana, ca.tipo, ca.canal, ca.presupuesto,
           COUNT(cc.id_cliente) AS alcanzados,
           COUNT(*) FILTER (WHERE cc.respondio) AS respondieron
    FROM campana ca
    LEFT JOIN campana_cliente cc ON cc.id_campana = ca.id_campana
    GROUP BY ca.id_campana, ca.tipo, ca.canal, ca.presupuesto
)
SELECT tipo, canal,
       COUNT(*) AS num_campanas,
       SUM(alcanzados) AS clientes_alcanzados,
       SUM(respondieron) AS clientes_respondieron,
       ROUND(100.0*SUM(respondieron)/NULLIF(SUM(alcanzados),0),2) AS tasa_respuesta_pct,
       ROUND(SUM(presupuesto),2) AS presupuesto_total,
       ROUND(SUM(presupuesto)/NULLIF(SUM(respondieron),0),2) AS costo_por_respuesta
FROM respuestas GROUP BY tipo, canal ORDER BY tasa_respuesta_pct DESC;""",
        "viz": {"graph.dimensions": ["tipo", "canal"], "graph.metrics": ["tasa_respuesta_pct"]},
    },
]


def main():
    global SESSION
    print("==> Login...")
    SESSION = api("POST", "/api/session", {"username": EMAIL, "password": PASS})["id"]

    dbs = api("GET", "/api/database")
    dbs = dbs.get("data", dbs) if isinstance(dbs, dict) else dbs
    db_id = next(d["id"] for d in dbs if d["name"] == DB_NAME)
    print(f"    DB_ID={db_id}")

    dash_list = api("GET", "/api/dashboard")
    dash_id = next(d["id"] for d in dash_list if d["name"] == DASH_NAME)
    dash = api("GET", f"/api/dashboard/{dash_id}")
    collection_id = dash.get("collection_id")
    tab_id = next(t["id"] for t in dash.get("tabs", []) if TAB_MATCH in t["name"].lower())
    print(f"    DASH_ID={dash_id}  TAB_ID={tab_id}  COLLECTION_ID={collection_id}")

    existing_cards = {c["name"]: c["id"] for c in api("GET", "/api/card")}
    card_ids = []
    for spec in CARDS:
        if spec["name"] in existing_cards:
            cid = existing_cards[spec["name"]]
            print(f"==> Reutilizando tarjeta '{spec['name']}' (id={cid})")
        else:
            print(f"==> Creando tarjeta '{spec['name']}'...")
            payload = {
                "name": spec["name"],
                "display": spec["display"],
                "visualization_settings": spec["viz"],
                "dataset_query": {
                    "type": "native",
                    "native": {"query": spec["query"], "template-tags": {}},
                    "database": db_id,
                },
                "collection_id": collection_id,
            }
            cid = api("POST", "/api/card", payload)["id"]
            print(f"    card_id={cid}")
        card_ids.append(cid)

    # tarjetas ya presentes en este tab (para no re-insertar)
    present = {dc.get("card_id") for dc in dash["dashcards"]
               if dc.get("dashboard_tab_id") == tab_id}
    to_add = [(spec, cid) for spec, cid in zip(CARDS, card_ids) if cid not in present]
    if not to_add:
        print("==> Las 4 tarjetas ya están en el Tab 2. Nada que insertar.")
        return

    start_row = max((dc["row"] + dc["size_y"] for dc in dash["dashcards"]
                     if dc.get("dashboard_tab_id") == tab_id), default=0)
    print(f"==> Insertando {len(to_add)} tarjeta(s) a partir de row={start_row}")

    # layout relativo a start_row (cuadrícula de 24 columnas):
    # fila 1: #11 y #12 lado a lado | fila 2: #13 tabla ancha | fila 3: #14
    # (row_off, col, size_x, size_y) -- una entrada por tarjeta, en orden
    layout = [(0, 0, 12, 6), (0, 12, 12, 6), (6, 0, 24, 7), (13, 0, 12, 6)]
    keep = ["id", "card_id", "dashboard_tab_id", "row", "col", "size_x", "size_y",
            "parameter_mappings", "visualization_settings", "series"]
    dashcards = [{k: dc.get(k) for k in keep} for dc in dash["dashcards"]]

    for i, (spec, cid) in enumerate(to_add):
        row_off, col, sx, sy = layout[i % len(layout)]
        dashcards.append({
            "id": -(i + 1), "card_id": cid, "dashboard_tab_id": tab_id,
            "row": start_row + row_off, "col": col,
            "size_x": sx, "size_y": sy,
            "parameter_mappings": [], "visualization_settings": {}, "series": [],
        })
    api("PUT", f"/api/dashboard/{dash_id}", {"dashcards": dashcards, "tabs": dash["tabs"]})
    print(f"==> Listo. {len(to_add)} tarjeta(s) agregada(s) al Tab 2.")
    print(f"==> Ver: {MB}/dashboard/{dash_id}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"ERROR HTTP {e.code}: {e.read().decode()[:500]}", file=sys.stderr)
        sys.exit(1)
