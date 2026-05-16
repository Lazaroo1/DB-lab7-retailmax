# Lab 7 - Visualización de Datos | RetailMax
**CC3088 - Bases de Datos 1 | Universidad del Valle de Guatemala**  
**Área 7: Estrategia y Expansión Comercial**

---

## Integrantes
- Lázaro Daniel Díaz Bojórquez - 24713
- Carlos André Lopez Salazar - 24531
- David Eduardo López Arriaza - 24730

---

## Requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo

---

## Cómo levantar el ambiente

```bash
git clone https://github.com/Lazaroo1/DB-lab7-retailmax.git
cd DB-lab7-retailmax
docker compose up -d
```

Esperar ~3 minutos mientras Metabase inicializa. Luego correr:

```bash
docker exec retailmax_postgres psql -U retailmax_user -d metabase_db -c "UPDATE setting SET value = 'true' WHERE key = 'setup-token';"
docker restart retailmax_metabase
```

Esperar 1 minuto más y abrir **http://localhost:3000**

### Credenciales de Metabase
| Campo | Valor |
|-------|-------|
| Email | `calificar@uvg.edu.gt` |
| Contraseña | `secret123+` |

---

## Estructura del repositorio

```
DB-lab7-retailmax/
├── docker-compose.yml             # Ambiente completo PostgreSQL + Metabase
├── init/
│   ├── 00_create_metabase_db.sql  # Crea la DB interna de Metabase
│   ├── 01_DDL.sql                 # Esquema de RetailMax
│   ├── 02_DATA.sql                # Datos de prueba
│   ├── 03_metabase_dump.sql       # Dump del dashboard construido
│   └── 04_restore_metabase.sh     # Script que restaura el dump en metabase_db
├── informe.pdf                    # Documentación de los 12 indicadores
└── README.md
```

---

## Video de presentación
[Enlace al video](#) *(pendiente)*

---

## Dashboard

El dashboard **Estrategia y Expansión Comercial** está organizado en 2 tabs:

- **Tab 1 - Desempeño Global:** indicadores de ingresos por mes, top tiendas, canales de venta, márgenes por categoría, estados de pedidos y ticket promedio por segmento de cliente.
- **Tab 2 - Crecimiento y Expansión:** análisis regional, crecimiento de clientes, rendimiento de tiendas, evolución interanual de ventas, categorías con mayor crecimiento y comportamiento de recompra.