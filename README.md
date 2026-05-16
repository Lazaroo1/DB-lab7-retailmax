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

Esperar ~3 minutos mientras Metabase inicializa. Luego abrir:

**http://localhost:3000**

### Credenciales de Metabase
| Campo | Valor |
|-------|-------|
| Email | `calificar@uvg.edu.gt` |
| Contraseña | `secret123+` |

> **Nota:** La primera vez que se levanta el ambiente, completar el wizard de setup con las credenciales de arriba. La base de datos ya viene precargada con DDL y datos.

### Conexión a la base de datos (wizard)
| Campo | Valor |
|-------|-------|
| Engine | PostgreSQL |
| Host | `postgres` |
| Port | `5432` |
| Database | `retailmax` |
| Username | `retailmax_user` |
| Password | `retailmax_pass` |

---

## Estructura del repositorio

```
DB-lab7-retailmax/
├── docker-compose.yml       # Ambiente completo PostgreSQL + Metabase
├── init/
│   ├── 00_create_metabase_db.sql  # Crea la DB interna de Metabase
│   ├── 01_DDL.sql                 # Esquema de RetailMax
│   └── 02_DATA.sql                # Datos de prueba
├── metabase-data/           # Volumen persistido con el dashboard
├── informe.pdf              # Documentación de los 12 indicadores
└── README.md
```

---

## Video de presentación
[Enlace al video](#) *(pendiente)*

---

## Dashboard

El dashboard está organizado en 2 tabs:

- **Tab 1 - Desempeño Global:** indicadores de ingresos, canales, márgenes y comportamiento de clientes.
- **Tab 2 - Crecimiento y Expansión:** análisis regional, tendencias temporales y oportunidades de mercado.