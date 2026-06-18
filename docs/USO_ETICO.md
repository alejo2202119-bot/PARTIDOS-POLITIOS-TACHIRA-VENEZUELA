# Política de Uso Ético y Legal — VPID

> Este documento define los **principios, usos permitidos y usos prohibidos** del
> Venezuela Political Intelligence Dashboard (VPID). Su aceptación es condición de uso.

## Tabla de contenidos
1. [Principio rector](#1-principio-rector)
2. [Alcance de los datos](#2-alcance-de-los-datos)
3. [Usos permitidos](#3-usos-permitidos)
4. [Usos prohibidos](#4-usos-prohibidos)
5. [Cumplimiento legal](#5-cumplimiento-legal)
6. [Verificación de fuentes y sesgos](#6-verificación-de-fuentes-y-sesgos)
7. [Transparencia y trazabilidad](#7-transparencia-y-trazabilidad)
8. [Responsabilidad del usuario](#8-responsabilidad-del-usuario)

---

## 1. Principio rector

VPID es una herramienta de **inteligencia de fuentes abiertas (OSINT)** orientada al
**análisis del discurso público y de la cobertura mediática**. Su finalidad es
**comprender** el debate público —no vigilar personas—. Toda funcionalidad debe usarse
de forma proporcional, necesaria y respetuosa de los derechos fundamentales.

## 2. Alcance de los datos

La plataforma procesa **únicamente información pública y abiertamente disponible**:

- Artículos y notas de **medios de comunicación** publicados.
- **Feeds RSS/Atom** y portales de noticias.
- **Comunicados oficiales** de organizaciones y partidos.
- Contenido accesible mediante **APIs públicas autorizadas**.

VPID **no** recopila, almacena ni infiere datos privados, mensajería privada, ubicación
física de personas, datos biométricos ni información obtenida eludiendo controles de
acceso o términos de servicio.

## 3. Usos permitidos

- **Periodismo** e investigación de medios.
- **Investigación académica** y estudios de comunicación política.
- **Observación electoral** y análisis de procesos democráticos.
- **Análisis de sociedad civil** y organizaciones de derechos humanos.
- **Monitoreo de narrativas** y desinformación con fines de verificación.

## 4. Usos prohibidos

Queda **expresamente prohibido** emplear VPID para:

- 🚫 **Vigilancia de personas privadas** o de individuos no públicos.
- 🚫 **Desanonimización** o reidentificación de personas.
- 🚫 **Rastreo de la ubicación física** o los movimientos de personas.
- 🚫 **Acoso, intimidación, hostigamiento o persecución** política o de cualquier índole.
- 🚫 Elaboración de **listas de objetivos** para represalias o discriminación.
- 🚫 **Recolección de datos personales sensibles** (salud, orientación, etc.).
- 🚫 Eludir **robots.txt**, *paywalls* o términos de servicio de terceros.
- 🚫 Cualquier finalidad que **vulnere derechos humanos** o la legislación aplicable.

> El "Monitoreo Territorial" del sistema agrega cobertura informativa por **estado y
> municipio** (volumen y tono de noticias por región). **No** rastrea la ubicación de
> personas.

## 5. Cumplimiento legal

El usuario debe cumplir toda la legislación aplicable, incluyendo —según jurisdicción—
normas de **protección de datos**, **propiedad intelectual**, **derechos de autor** de los
medios y los **términos de servicio** de las plataformas consultadas. VPID respeta
`robots.txt`/ToS mediante la configuración `ETL_RESPECT_ROBOTS_TXT`.

## 6. Verificación de fuentes y sesgos

- La tabla **`fuentes`** registra `credibilidad`, `verificada` y `sesgo` documentado.
- Los análisis deben **contrastar fuentes** de distinta credibilidad y orientación.
- Las métricas de sentimiento y alcance son **estimaciones** sujetas a error; no son
  hechos definitivos y deben interpretarse con cautela.
- Las cifras de demostración incluidas en el repositorio son **sintéticas**.

## 7. Transparencia y trazabilidad

- Toda acción sensible queda registrada en la **auditoría** (`auditoria`).
- Los informes citan el período y la naturaleza pública de las fuentes.
- Los modelos de IA empleados se identifican en cada análisis (`modelo`).

## 8. Responsabilidad del usuario

El uso de VPID se realiza bajo **exclusiva responsabilidad del usuario**. Los autores y
mantenedores del software no se responsabilizan por usos indebidos. El incumplimiento de
esta política puede acarrear responsabilidades legales para el usuario.

---

_Véase también: [README](../README.md) · [Arquitectura](ARQUITECTURA.md) · [Licencia](../LICENSE)._
