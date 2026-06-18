# Manual de Usuario — Venezuela Political Intelligence Dashboard (VPID)

> **¿Qué es VPID?** Una plataforma de **inteligencia de fuentes abiertas (OSINT)** que
> monitorea y analiza **información pública** (medios, RSS, comunicados oficiales y APIs
> públicas autorizadas) sobre actores, partidos, medios, tendencias y narrativas
> políticas de Venezuela. Está pensada para usos legítimos: periodismo, investigación
> académica, observación electoral y análisis de sociedad civil.
>
> **Uso responsable:** esta herramienta **no** debe emplearse para vigilancia de
> personas privadas ni persecución política. Consulte la
> [Política de Uso Ético y Legal](USO_ETICO.md).

Este manual está dirigido a usuarios **no técnicos**. Explica cómo iniciar sesión,
recorrer cada uno de los 12 módulos, usar los filtros y el buscador, interpretar los
gráficos y mapas, gestionar alertas y generar informes.

## Tabla de contenidos

1. [Primeros pasos: inicio de sesión y roles](#1-primeros-pasos-inicio-de-sesión-y-roles)
2. [La pantalla principal](#2-la-pantalla-principal)
3. [Recorrido por los 12 módulos](#3-recorrido-por-los-12-módulos)
4. [El módulo de administración: Fuentes](#4-el-módulo-de-administración-fuentes)
5. [Filtros avanzados](#5-filtros-avanzados)
6. [Buscador inteligente (⌘K)](#6-buscador-inteligente-k)
7. [Modo oscuro y claro](#7-modo-oscuro-y-claro)
8. [Cómo leer las tarjetas KPI](#8-cómo-leer-las-tarjetas-kpi)
9. [Cómo interpretar los gráficos](#9-cómo-interpretar-los-gráficos)
10. [El mapa territorial](#10-el-mapa-territorial)
11. [Gestión de alertas](#11-gestión-de-alertas)
12. [Informes ejecutivos en PDF](#12-informes-ejecutivos-en-pdf)
13. [Preguntas frecuentes (FAQ)](#13-preguntas-frecuentes-faq)
14. [Glosario](#14-glosario)
15. [Documentos relacionados](#15-documentos-relacionados)

---

## 1. Primeros pasos: inicio de sesión y roles

Al abrir la plataforma verá una pantalla de **acceso**. Introduzca su correo y
contraseña y pulse **Iniciar sesión**.

> En modo de demostración, cualquier credencial inicia sesión (la plataforma siempre
> es explorable). En un entorno real, su administrador le entregará sus credenciales.

Lo que puede hacer depende de su **rol**. VPID tiene cuatro roles, de menor a mayor
nivel de acceso:

| Rol | Qué puede hacer |
|-----|-----------------|
| **lector** | Solo lectura del dashboard y de los módulos; **descargar informes PDF**. |
| **editor** | Lo anterior + **gestionar las fuentes** y entidades. |
| **analista** | Lo anterior + **generar informes** y **reconocer alertas**. |
| **admin** | Acceso total: configuración, fuentes, usuarios y auditoría. |

Los roles son **jerárquicos**: un rol superior incluye los permisos de los inferiores.

---

## 2. La pantalla principal

La interfaz tiene tres zonas:

- **Barra lateral (izquierda):** el menú de navegación, agrupado en *Inteligencia*,
  *Análisis*, *Territorio* y *Operaciones*. Al pie indica el estado del ETL y la hora
  del próximo ciclo (05:00 VET).
- **Barra superior:** el **buscador** (⌘K), el **selector de período** (24 h / 7 / 30
  / 90 días), el icono de **alertas** (con contador), el botón de **tema** (claro/
  oscuro) y su **menú de usuario** (Configuración, Fuentes, Cerrar sesión).
- **Área central:** el contenido del módulo seleccionado. Debajo, una barra de filtros
  y un pie con el recordatorio de uso responsable.

En la esquina puede aparecer una insignia de **modo de conexión**: `live` (conectado al
servidor) o `demo` (datos de demostración).

---

## 3. Recorrido por los 12 módulos

### 1. Dashboard Ejecutivo

Panorama consolidado del día. Muestra **cinco tarjetas KPI** (Artículos del período,
Menciones, Alcance estimado, Sentimiento global y Alertas abiertas), un gráfico de
**evolución de la cobertura** por tema, la **distribución de sentimiento**, los
**actores más mencionados**, las **narrativas predominantes**, los **temas emergentes**
y una tira de **alertas recientes**. Desde aquí puede pulsar **Informe PDF** para ir a
la generación de informes y **Actualizar** para recargar.

### 2. Monitoreo de Noticias

Listado de **artículos clasificados** procedentes de fuentes públicas. Cada fila
muestra el titular y el actor asociado, la fuente y su tipo, el tema (con color), el
estado (geográfico), el sentimiento, la relevancia, el alcance estimado y cuándo se
publicó. Dispone de un **buscador de titulares** y filtros por **tema, estado,
sentimiento y relevancia**.

### 3. Análisis de Tendencias

Evolución temporal de las menciones. Incluye el **volumen por tema (30 días)**, la
lista de **temas emergentes** (con su % de crecimiento), un gráfico de **crecimiento
por tema** y el **patrón semanal de actividad**.

### 4. Detección de Narrativas

Agrupaciones temáticas y de encuadre detectadas en la cobertura pública. Cada
**narrativa** se presenta como una tarjeta con su etiqueta (Emergente o Activa), su
variación, sus **palabras clave**, una minigráfica de evolución, el número de artículos,
el alcance y el sentimiento. Arriba se indica cuántas narrativas son emergentes.

### 5. Análisis de Sentimiento (IA)

Tono de la cobertura mediática, estimado mediante **IA o léxico**. Muestra un
**índice de sentimiento** (escala 0 negativo – 100 positivo), la **distribución**
(positivo/neutral/negativo), un **resumen** con porcentajes y la **evolución del
sentimiento por tema**.

### 6. Ranking de Actores Públicos

Figuras públicas ordenadas por **volumen de menciones** en información pública. La
tabla incluye posición, actor y cargo, organización, menciones, una **minigráfica de
tendencia**, el sentimiento y el alcance. A la derecha, un **perfil comparativo** de
los tres primeros.

### 7. Monitoreo Territorial

Distribución geográfica de la cobertura por **estado**. Combina un **mapa de cobertura**
(Leaflet), un **ranking por estado** (artículos y sentimiento) y un gráfico de
**volumen por estado**.

### 8. Mapas Interactivos

Vista a pantalla completa del **mapa geoespacial** de la actividad informativa. Permite
acercar, alejar y desplazarse para explorar la concentración de cobertura por zonas.

### 9. Alertas Tempranas

Detección automática de **picos**, **narrativas emergentes** y **anomalías**. Cada
alerta muestra su severidad, su estado, la fecha/hora, el título y la descripción.
Quienes tengan rol **analista** o superior pueden **Reconocer** una alerta.

### 10. Comparativos Históricos

Contraste de **períodos** y **correlaciones** entre temas. Incluye la comparación de
volumen (período actual vs. anterior), una **matriz de correlación** de temas y las
**series superpuestas**. Puede elegir el rango (esta semana vs. anterior, mes,
trimestre).

### 11. Centro de Inteligencia Digital

Visión **integrada** de fuentes, señales y correlaciones. Muestra KPIs de fuentes
(monitoreadas, activas, cobertura diaria, alcance acumulado), las **fuentes más
activas**, un **mapa de términos**, las **correlaciones entre temas** y la
**distribución por tipo de fuente**.

### 12. Informes Ejecutivos (PDF)

Generación y archivo de informes. La plataforma **genera automáticamente un Informe
Ejecutivo en PDF cada día a las 06:00 (VET)**, con portada institucional, KPIs,
tendencias, actores, narrativas, análisis territorial, alertas y conclusiones/
recomendaciones por IA. Puede **generar uno ahora** o **descargar** los archivados.

> **PDF es el único formato de exportación.** No hay exportación a Excel, CSV ni Word.

---

## 4. El módulo de administración: Fuentes

Además de los 12 módulos analíticos, existe el módulo **Fuentes** (disponible desde el
menú de usuario y la sección *Operaciones*). Sirve para **administrar los medios,
portales y fuentes abiertas verificables** de las que la plataforma obtiene
información.

Muestra KPIs (total de fuentes, activas, verificadas y credibilidad media) y una tabla
con: nombre, tipo, alcance, **credibilidad**, si está **verificada**, su **estado**
(activa/pausada), artículos en 30 días y última lectura. Crear, editar o eliminar
fuentes requiere rol **editor** (eliminar requiere **admin**).

---

## 5. Filtros avanzados

Los filtros le permiten acotar lo que ve. Según el módulo, encontrará:

| Filtro | Para qué sirve |
|--------|----------------|
| **Fecha / período** | Selector superior: últimas 24 h, 7, 30 o 90 días. |
| **Estado** | Estado de Venezuela (p. ej. Táchira, Zulia…). |
| **Municipio** | Municipio dentro de un estado (p. ej. San Cristóbal). |
| **Organización** | Partido, medio o institución pública. |
| **Actor** | Figura pública concreta. |
| **Medio / fuente** | Medio o portal de origen. |
| **Tema** | Categoría temática (Elecciones, Economía, DDHH…). |
| **Relevancia** | Importancia estimada: crítica, alta, media o baja. |
| **Sentimiento** | Tono: positivo, neutral o negativo. |

Los filtros se combinan: por ejemplo, en **Monitoreo de Noticias** puede ver artículos
de *tema = Elecciones*, *estado = Táchira* y *sentimiento = negativo*. Para quitar un
filtro, vuelva a la opción "Todos".

---

## 6. Buscador inteligente (⌘K)

El **buscador** de la barra superior encuentra rápidamente **actores, narrativas,
medios y temas**. Pulse en el campo (o use el atajo **⌘K** / **Ctrl K**) y empiece a
escribir; aparecerán resultados clasificados por tipo. Al elegir uno, la plataforma le
lleva al módulo correspondiente.

---

## 7. Modo oscuro y claro

VPID arranca en **modo oscuro**. Use el botón con icono de luna/sol en la barra
superior (o **Configuración → Apariencia → Alternar**) para cambiar entre **oscuro** y
**claro**. Su preferencia se recuerda para la próxima visita.

---

## 8. Cómo leer las tarjetas KPI

Las **tarjetas KPI** resumen los indicadores clave. Cada tarjeta muestra:

- Un **valor** grande (p. ej. número de artículos o menciones).
- Una **variación** respecto al período anterior (una flecha verde hacia arriba indica
  aumento; roja hacia abajo, descenso; gris, sin cambio). El número entre paréntesis es
  el porcentaje de cambio.
- Una pequeña **línea de tendencia** (*sparkline*) que muestra la evolución reciente.

Indicadores típicos: **Artículos** (ítems públicos procesados), **Menciones**
(referencias a actores), **Alcance estimado** (audiencia aproximada),
**Sentimiento global** (tono medio entre −1 y +1) y **Alertas abiertas**.

---

## 9. Cómo interpretar los gráficos

| Gráfico | Cómo leerlo |
|---------|-------------|
| **Evolución / series** (líneas/áreas) | El eje horizontal es el tiempo; el vertical, el volumen de menciones por tema. Útil para ver subidas o caídas. |
| **Distribución de sentimiento** (dona) | Proporción de cobertura positiva, neutral y negativa. |
| **Índice de sentimiento** (medidor) | Escala 0 (muy negativo) a 100 (muy positivo); 50 es neutro. |
| **Actores / volumen** (barras) | Comparación directa entre actores, temas o estados. |
| **Crecimiento / temas emergentes** | Porcentaje de aumento reciente; barras más largas = más tracción. |
| **Matriz de correlación** (mapa de calor) | Qué temas tienden a aparecer juntos; valores altos = relación más fuerte. |
| **Perfil comparativo** (radar) | Comparación multidimensional de varios actores. |

> Las cifras de demostración son **sintéticas** (ilustrativas), no mediciones reales.

---

## 10. El mapa territorial

El **mapa** (en *Monitoreo Territorial* y *Mapas Interactivos*) ubica la actividad
informativa por estado. Cada marcador representa un estado; su tamaño o intensidad
refleja el **volumen de cobertura**. Puede:

- **Acercar/alejar** con la rueda del ratón o los botones +/−.
- **Desplazarse** arrastrando el mapa.
- **Pulsar un marcador** para ver el detalle del estado (artículos y sentimiento).

El ranking lateral acompaña al mapa con las cifras por estado.

---

## 11. Gestión de alertas

Las **alertas tempranas** se generan automáticamente cuando el sistema detecta
patrones inusuales (picos de menciones, caídas de sentimiento, narrativas emergentes o
concentración territorial). Para gestionarlas:

1. Pulse el icono de **campana** en la barra superior para abrir el panel lateral, o
   entre al módulo **Alertas Tempranas**.
2. Revise cada alerta: **severidad** (info, baja, media, alta, crítica), **estado**
   (abierta, en revisión, reconocida, cerrada), título y descripción.
3. Si su rol es **analista** o superior, pulse **Reconocer** para marcar que la alerta
   ha sido atendida.

El contador junto a la campana indica cuántas alertas hay activas.

---

## 12. Informes ejecutivos en PDF

El **Informe Ejecutivo** es el entregable formal de VPID. Contiene portada
institucional, fecha, resumen ejecutivo, KPIs, tendencias del día, actores más
mencionados, narrativas predominantes, análisis territorial, alertas, un gráfico de
evolución y conclusiones/recomendaciones.

- **Automático:** se genera **cada día a las 06:00 (VET)**, después del ciclo de datos
  de las 05:00.
- **Bajo demanda:** en el módulo **Informes Ejecutivos**, pulse **Generar informe
  diario** (requiere rol analista o superior).
- **Descarga:** pulse **Descargar PDF** en cualquier informe archivado.

> **Recuerde:** PDF es la **única** forma de exportar información de la plataforma. No
> existe exportación a Excel, CSV ni Word. El PDF incluye una huella de integridad
> (SHA-256) para verificar que no ha sido alterado.

---

## 13. Preguntas frecuentes (FAQ)

**¿De dónde salen los datos?**
Exclusivamente de **información pública**: medios publicados, feeds RSS, comunicados
oficiales y APIs públicas autorizadas. No se recopilan datos privados.

**¿Las cifras son reales?**
En un despliegue conectado, reflejan la cobertura pública procesada. En el modo de
demostración, las cifras son **sintéticas** y solo sirven para ilustrar la interfaz.

**¿Puedo exportar a Excel o CSV?**
No. La **única** exportación es el **PDF** del Informe Ejecutivo, por diseño.

**¿Por qué no puedo generar un informe o reconocer una alerta?**
Esas acciones requieren rol **analista** o superior. Consulte con su administrador.

**¿Cada cuánto se actualizan los datos?**
El sistema ejecuta su ciclo diario a las **05:00 (VET)** y genera el informe a las
**06:00 (VET)**.

**¿Qué significa que una narrativa es "emergente"?**
Que ha mostrado un crecimiento reciente notable; conviene vigilarla.

**¿Cómo cambio entre modo claro y oscuro?**
Con el botón de tema en la barra superior o desde Configuración → Apariencia.

**¿Qué es la insignia `demo` / `live`?**
Indica si la plataforma está conectada al servidor (`live`) o mostrando datos de
demostración (`demo`).

---

## 14. Glosario

| Término | Definición |
|---------|------------|
| **OSINT** | Inteligencia de fuentes abiertas: análisis de información **pública** y accesible (no datos privados). |
| **Narrativa** | Conjunto de artículos que comparten un mismo encuadre o tema, agrupados automáticamente. |
| **Narrativa emergente** | Narrativa con crecimiento reciente significativo. |
| **Sentimiento** | Tono de la cobertura: positivo, neutral, negativo (o mixto). Se expresa con un *score* de −1 a +1. |
| **Score de sentimiento** | Valor numérico del tono: −1 muy negativo, 0 neutro, +1 muy positivo. |
| **Relevancia** | Importancia estimada de un artículo: baja, media, alta o crítica. |
| **Alcance estimado** | Aproximación de la audiencia potencial (proxy de visitas/seguidores). |
| **Mención** | Referencia a un actor u organización dentro de un artículo. |
| **Actor** | Figura pública (persona, partido, institución, medio…). |
| **Fuente** | Medio, portal, feed RSS o canal oficial del que proviene la información. |
| **Credibilidad** | Puntuación (0–100) asociada a una fuente. |
| **KPI** | Indicador clave de rendimiento (p. ej. total de artículos, sentimiento global). |
| **Alerta temprana** | Aviso automático ante un patrón inusual (pico, caída de sentimiento, etc.). |
| **ETL** | Proceso automático que ingiere, limpia, clasifica, analiza y agrega la información. |
| **VET** | Hora de Venezuela (America/Caracas). |
| **PDF** | Único formato de exportación de la plataforma. |

---

## 15. Documentos relacionados

- [ARQUITECTURA.md](ARQUITECTURA.md) — visión general del sistema.
- [MANUAL_TECNICO.md](MANUAL_TECNICO.md) — instalación, configuración y extensión.
- [API.md](API.md) — referencia de la API REST.
- [DESPLIEGUE.md](DESPLIEGUE.md) — despliegue local y producción.
- [USO_ETICO.md](USO_ETICO.md) — política de uso ético y legal.
