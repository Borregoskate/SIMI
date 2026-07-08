# SIMI BLUEPRINT

## Sistema Inteligente de Mercado e Investigaciones

Versión del documento: 1.0  
Release objetivo: 0.2.0  
Estado: Diseño arquitectónico inicial

---

# 1. Visión del producto

SIMI es una plataforma de inteligencia para procedimientos de contratación.

Su objetivo es transformar información dispersa de investigaciones de mercado, invitaciones, ofertas, adjudicaciones y catálogos en indicadores, diagnósticos y recomendaciones útiles para la toma de decisiones.

SIMI no debe limitarse a comparar archivos Excel.

SIMI debe evolucionar hacia una plataforma capaz de analizar el ciclo completo de contratación pública.

---

# 2. Principio rector

El negocio manda.  
El código obedece.

Toda funcionalidad nueva deberá pertenecer a un dominio de negocio claramente definido.

---

# 3. Dominios principales

## 3.1 Procedimientos

Dominio central del sistema.

Todo inicia con un procedimiento de contratación.

Ejemplos:

- Compra consolidada
- Compra emergente
- Patente
- Fuente única
- Invitación restringida
- Licitación pública
- Adjudicación directa
- Convenio marco

Campos conceptuales:

- ID_PROCEDIMIENTO
- NUMERO_PROCEDIMIENTO
- TIPO_PROCEDIMIENTO
- OBJETO_CONTRATACION
- INSTITUCION
- EJERCICIO
- ESTATUS
- FECHA_INICIO
- FECHA_FIN

---

## 3.2 Investigaciones

Representan la etapa donde se recopilan ofertas de mercado.

Una investigación pertenece a un procedimiento.

Contiene ofertas realizadas por proveedores.

---

## 3.3 Invitaciones

Representan el universo esperado de claves solicitadas.

Permiten detectar:

- Claves invitadas
- Claves ofertadas
- Claves desiertas
- Porcentaje de respuesta
- Nivel de competencia

Campos principales:

- INVESTIGACION
- CLAVE
- DESCRIPCION
- CANTIDAD REQUERIDA

---

## 3.4 Ofertas

Representan la respuesta de un proveedor.

Campos principales:

- INVESTIGACION
- RFC
- RAZON SOCIAL
- CLAVE
- DESCRIPCION
- CANTIDAD OFERTADA
- PAIS DE ORIGEN
- PRECIO UNITARIO

---

## 3.5 Claves

Dominio estratégico del sistema.

Cada clave debe poder analizarse históricamente.

El catálogo maestro de claves deberá permitir conocer:

- Vigencia
- Sustitución
- Cambio de presentación
- Cambio de concentración
- Patente
- Fuente única
- Fin de patente
- Registro sanitario
- Suspensión
- Desabasto

---

## 3.6 Proveedores

El RFC será el identificador real del proveedor.

La razón social puede variar, pero SIMI deberá unificar proveedores por RFC.

---

## 3.7 Adjudicaciones

Dominio futuro.

No debe mezclarse con ofertas.

Permitirá analizar:

- Proveedor ganador
- Precio adjudicado
- Cantidad adjudicada
- Monto adjudicado
- Diferencia contra mejor oferta
- Ahorro potencial
- Sobrecosto

---

## 3.8 Inteligencia

Dominio encargado de interpretar información.

No calcula datos brutos.

Genera:

- Diagnósticos
- Alertas
- Recomendaciones
- Conclusiones ejecutivas

---

## 3.9 Reportes

Dominio encargado de producir salidas:

- Excel
- PDF
- Dashboard
- Power BI
- API
- Reportes ejecutivos

---

# 4. Arquitectura conceptual

```text
Procedimiento
      ↓
Investigación
      ↓
Invitación
      ↓
Claves solicitadas
      ↓
Ofertas
      ↓
Claves ofertadas / desiertas
      ↓
Adjudicaciones
      ↓
Analytics
      ↓
Intelligence
      ↓
Reportes / Dashboard / IA


Este documento queda como base del Release `0.2.0`.