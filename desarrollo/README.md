# 📊 SIMI

# Sistema Inteligente de Mercado e Investigaciones

---

## Descripción

SIMI (Sistema Inteligente de Mercado e Investigaciones) es una plataforma desarrollada para el análisis, comparación y explotación de información proveniente de investigaciones de mercado.

Su objetivo es centralizar múltiples investigaciones realizadas a lo largo del tiempo, permitiendo identificar tendencias de precios, comportamiento de proveedores, evolución de claves, oportunidades de ahorro y, en versiones futuras, realizar análisis de adjudicaciones e inteligencia comercial mediante IA.

---

# Características principales

Actualmente SIMI permite:

- Carga simultánea de múltiples investigaciones.
- Consolidación automática de información.
- Unificación de proveedores mediante RFC.
- Análisis histórico por clave.
- Análisis histórico por proveedor.
- Comparativos de precios.
- Estadísticas generales.
- Exportación de resultados a Excel.
- Arquitectura modular preparada para crecimiento.

---

# Arquitectura

```text
Investigaciones Excel
        │
        ▼
 excel_service.py
        │
        ▼
helpers.py
        │
        ▼
analytics_service.py
        │
        ▼
Modules
│
├── Resumen
├── Claves
├── Proveedores
└── Exportación
```

---

# Tecnologías utilizadas

- Python 3
- Streamlit
- Pandas
- Plotly
- OpenPyXL

---

# Estructura del proyecto

```text
SIMI/

app.py

config.py

requirements.txt

README.md

CHANGELOG.md

ROADMAP.md

docs/

modules/

services/

utils/

assets/

tests/
```

---

# Estado del proyecto

Versión actual

**0.1.0**

Estado

🟢 En desarrollo activo

---

# Próximas funcionalidades

- Dashboard Ejecutivo
- KPIs Avanzados
- Comparativos históricos
- Integración de adjudicaciones
- Indicadores de ahorro
- Inteligencia Artificial
- Reportes ejecutivos automáticos
- Exportación PDF
- Power BI Connector

---

# Autor

**Jorge Eduardo Saavedra Millán**

Desarrollado con apoyo de OpenAI.

---

# Licencia

Proyecto privado.

Todos los derechos reservados.