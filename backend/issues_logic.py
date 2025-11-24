# backend/issues_logic.py
from typing import List
from sqlalchemy.orm import Session
from . import models

"""
Este archivo define el CATÁLOGO de tipos de issues que tu auditoría puede detectar.
La lógica específica de detección (reglas) la conectas luego en generate_issues_for_crawl
en función de los datos que traigas de DataForSEO + PageSpeed Insights.
"""

# -------------------------------------------------------------------
# CATÁLOGO DE ISSUE TYPES
# -------------------------------------------------------------------

DEFAULT_ISSUE_TYPES: List[dict] = [
    # ===============================================================
    # ERRORES DE RASTREO Y RESPUESTA DEL SERVIDOR
    # ===============================================================
    {
        "code": "CRAWL_ERROR_4XX",
        "name": "Errores 4xx en páginas",
        "severity": "critical",
        "category": "technical",
        "description": "La URL devuelve un código de estado HTTP 4xx (404, 403, 401, etc.).",
        "fix_template_for_impl": (
            "Verifica si la página debe existir. Si debe estar disponible, corrige el contenido para que "
            "responda con código 200. Si ya no forma parte del sitio, configura una redirección 301 hacia "
            "la página más relevante y revisa los enlaces internos apuntando a esta URL."
        ),
        "why_it_matters": (
            "Los errores 4xx afectan la experiencia de usuario, generan frustración y fragmentan la autoridad "
            "del sitio. Los bots pierden tiempo rastreando URLs que no aportan valor."
        ),
        "technical_notes": "Revisa logs, enlaces internos, sitemap.xml y canonical tags que apunten a esta URL."
    },
    {
        "code": "CRAWL_ERROR_5XX",
        "name": "Errores 5xx en servidor",
        "severity": "critical",
        "category": "technical",
        "description": "La URL devuelve un error 5xx (500, 502, 503, 504, etc.).",
        "fix_template_for_impl": (
            "Reporta al equipo de infraestructura o hosting. Revisa errores de servidor, timeouts, "
            "configuración de caché y picos de carga. Implementa monitorización para detectar estos errores "
            "antes de que afecten a muchos usuarios."
        ),
        "why_it_matters": (
            "Los errores 5xx indican problemas en el servidor. Si son frecuentes, afectan la rastreabilidad, "
            "la indexación y la confianza de los usuarios."
        ),
        "technical_notes": "Revisar logs de servidor, configuraciones de reverse proxy, PHP/Node/Python, DB, etc."
    },
    {
        "code": "REDIRECT_3XX",
        "name": "Redirecciones 301/302",
        "severity": "major",
        "category": "technical",
        "description": "La URL devuelve un código de redirección (301 o 302).",
        "fix_template_for_impl": (
            "Confirma si la redirección es necesaria. Evita redirecciones innecesarias y asegúrate de que "
            "las URLs internas apunten directamente al destino final siempre que sea posible."
        ),
        "why_it_matters": (
            "Las redirecciones son normales, pero en exceso generan retrasos en la carga y pérdida de autoridad "
            "si se encadenan o se configuran de forma incorrecta."
        ),
        "technical_notes": "Revisa cadenas de redirección y actualiza enlaces internos para apuntar a la URL final."
    },
    {
        "code": "REDIRECT_CHAIN",
        "name": "Cadenas de redirección",
        "severity": "major",
        "category": "technical",
        "description": "La URL forma parte de una cadena de múltiples redirecciones consecutivas.",
        "fix_template_for_impl": (
            "Reduce la cadena de redirecciones. Ajusta las redirecciones para que la URL inicial apunte "
            "directamente a la URL final, sin pasos intermedios innecesarios."
        ),
        "why_it_matters": (
            "Cada salto adicional añade latencia, consume presupuesto de rastreo y puede generar errores "
            "si alguno de los pasos falla."
        ),
        "technical_notes": "Identifica la secuencia completa (A→B→C…) y simplifícala a un solo salto (A→C)."
    },
    {
        "code": "REDIRECT_LOOP",
        "name": "Bucles de redirección",
        "severity": "critical",
        "category": "technical",
        "description": "Existen redirecciones circulares (bucles) que impiden acceder al contenido.",
        "fix_template_for_impl": (
            "Corrige la configuración de redirecciones para evitar que la URL A termine redirigiendo a sí misma "
            "o a una secuencia que vuelve al origen. Ajusta reglas en servidor o en CMS."
        ),
        "why_it_matters": (
            "Los bucles de redirección bloquean el acceso al contenido tanto para usuarios como para bots, "
            "impidiendo el rastreo y la indexación."
        ),
        "technical_notes": "Revisar reglas de redirección en servidor (Apache/Nginx/Cloudflare) y en el CMS."
    },
    {
        "code": "SERVER_RESPONSE_SLOW",
        "name": "Tiempo de respuesta del servidor lento",
        "severity": "major",
        "category": "performance",
        "description": "El servidor tarda demasiado en responder a la petición inicial (TTFB alto).",
        "fix_template_for_impl": (
            "Optimiza la infraestructura (caché de servidor/app, base de datos, CDN). Reduce procesos pesados "
            "en la respuesta inicial y revisa consultas lentas a la base de datos."
        ),
        "why_it_matters": (
            "Un TTFB alto afecta directamente la velocidad percibida por el usuario y los Core Web Vitals, "
            "lo que impacta rankings y conversión."
        ),
        "technical_notes": "Apóyate en herramientas de APM y logs para detectar cuellos de botella en backend."
    },
    {
        "code": "PAGE_LOAD_SLOW",
        "name": "Tiempo de carga de página excesivo",
        "severity": "major",
        "category": "performance",
        "description": "El tiempo de carga total de la página es demasiado alto.",
        "fix_template_for_impl": (
            "Optimiza imágenes, reduce tamaño de JS y CSS, usa lazy load y revisa recursos de terceros. "
            "Implementa técnicas de minificación y compresión."
        ),
        "why_it_matters": (
            "Las páginas lentas generan abandono, reducen la satisfacción del usuario y afectan el rendimiento SEO."
        ),
        "technical_notes": "Analiza waterfall de recursos con Lighthouse/DevTools para priorizar optimizaciones."
    },

    # ===============================================================
    # PROBLEMAS DE CONTENIDO Y SEO ON-PAGE
    # ===============================================================
    {
        "code": "TITLE_MISSING",
        "name": "Título de página faltante",
        "severity": "major",
        "category": "content",
        "description": "La página no tiene etiqueta <title> definida.",
        "fix_template_for_impl": (
            "Añade un título claro que describa el contenido de la página e incluya la palabra clave principal "
            "y la intención del usuario."
        ),
        "why_it_matters": (
            "El título es uno de los factores on-page más importantes para SEO y afecta directamente el CTR."
        ),
        "technical_notes": "Definir <title> en la plantilla/base del sitio o en el CMS."
    },
    {
        "code": "TITLE_DUPLICATE",
        "name": "Títulos duplicados",
        "severity": "major",
        "category": "content",
        "description": "Varias páginas comparten el mismo título.",
        "fix_template_for_impl": (
            "Reescribe títulos para que cada página tenga un título único y alineado con su contenido específico."
        ),
        "why_it_matters": (
            "Los títulos duplicados dificultan a Google entender la diferencia entre páginas y pueden diluir "
            "la relevancia de cada una."
        ),
        "technical_notes": "Usar variables dinámicas por tipo de plantilla para generar títulos únicos."
    },
    {
        "code": "TITLE_TOO_LONG",
        "name": "Títulos demasiado largos",
        "severity": "minor",
        "category": "content",
        "description": "El título supera la longitud recomendada.",
        "fix_template_for_impl": (
            "Reduce el título a aproximadamente 50-60 caracteres, manteniendo idea principal y palabra clave "
            "sin repetir palabras innecesarias."
        ),
        "why_it_matters": (
            "Los títulos muy largos se cortan en los resultados de búsqueda y pueden disminuir el CTR."
        ),
        "technical_notes": "Apuntar a unas ~580 px de ancho visual aproximado."
    },
    {
        "code": "TITLE_TOO_SHORT",
        "name": "Títulos demasiado cortos",
        "severity": "minor",
        "category": "content",
        "description": "El título es demasiado breve o poco descriptivo.",
        "fix_template_for_impl": (
            "Añade información que aclare el contexto (producto, categoría, beneficio, marca) manteniendo claridad."
        ),
        "why_it_matters": "Títulos poco descriptivos dificultan la comprensión del contenido y reducen el CTR.",
        "technical_notes": "Evita títulos genéricos como 'Inicio', 'Página 1', 'Producto'."
    },
    {
        "code": "META_DESCRIPTION_MISSING",
        "name": "Meta descripción faltante",
        "severity": "minor",
        "category": "content",
        "description": "La página no tiene meta description.",
        "fix_template_for_impl": (
            "Redacta una meta descripción de 120-155 caracteres que resuma el contenido y destaque un beneficio "
            "claro o llamada a la acción."
        ),
        "why_it_matters": (
            "Una meta descripción bien escrita aumenta el CTR en los resultados de búsqueda aunque no sea factor "
            "de ranking directo."
        ),
        "technical_notes": "Usar <meta name=\"description\" content=\"...\">."
    },
    {
        "code": "META_DESCRIPTION_DUPLICATE",
        "name": "Meta descripciones duplicadas",
        "severity": "minor",
        "category": "content",
        "description": "Varias páginas comparten exactamente la misma meta descripción.",
        "fix_template_for_impl": (
            "Personaliza la meta descripción de cada página resaltando su contenido específico y términos clave "
            "relevantes."
        ),
        "why_it_matters": (
            "Descripciones duplicadas reducen claridad para el usuario y dificultan diferenciar páginas en SERPs."
        ),
        "technical_notes": "Usar plantillas dinámicas por tipo de página si manejas grandes volúmenes."
    },
    {
        "code": "META_DESCRIPTION_TOO_LONG",
        "name": "Meta descripciones demasiado largas",
        "severity": "minor",
        "category": "content",
        "description": "La meta descripción excede la longitud recomendada.",
        "fix_template_for_impl": (
            "Recorta la meta descripción a unos 120-155 caracteres, priorizando el beneficio principal y CTA."
        ),
        "why_it_matters": "Descripciones muy largas se cortan en el snippet y pierden impacto.",
        "technical_notes": "Prioriza el mensaje y evita frases de relleno."
    },
    {
        "code": "META_DESCRIPTION_TOO_SHORT",
        "name": "Meta descripciones demasiado cortas",
        "severity": "minor",
        "category": "content",
        "description": "La meta descripción es demasiado breve o poco informativa.",
        "fix_template_for_impl": (
            "Añade contexto sobre qué encontrará el usuario, integrando beneficios y términos relevantes."
        ),
        "why_it_matters": "Descripciones muy cortas no venden el clic y reducen oportunidades de conversión.",
        "technical_notes": "Evitar descripciones de una sola palabra o frases genéricas."
    },
    {
        "code": "H1_MISSING",
        "name": "Encabezado H1 faltante",
        "severity": "major",
        "category": "content",
        "description": "La página no tiene encabezado H1.",
        "fix_template_for_impl": (
            "Añade un H1 que resuma el tema principal de la página y esté alineado con el título y la intención "
            "de búsqueda."
        ),
        "why_it_matters": "El H1 ayuda a estructurar el contenido y a los motores de búsqueda a entender el tema.",
        "technical_notes": "Asegúrate de usar un solo H1 por página en la mayoría de los casos."
    },
    {
        "code": "H1_MULTIPLE",
        "name": "Múltiples H1 en una página",
        "severity": "minor",
        "category": "content",
        "description": "La página tiene más de un H1 definido.",
        "fix_template_for_impl": (
            "Mantén un solo H1 principal. Convierte los H1 secundarios en H2 o H3 según la jerarquía de contenido."
        ),
        "why_it_matters": "Varios H1 pueden confundir la estructura y el foco temático de la página.",
        "technical_notes": "Revisar plantillas y componentes reutilizables que puedan insertar H1 adicionales."
    },
    {
        "code": "H1_DUPLICATE",
        "name": "H1 duplicados entre páginas",
        "severity": "minor",
        "category": "content",
        "description": "Varias páginas comparten exactamente el mismo H1.",
        "fix_template_for_impl": (
            "Ajusta el H1 de cada página para que refleje su contenido específico y palabras clave objetivo."
        ),
        "why_it_matters": (
            "H1 duplicados reducen la claridad temática y pueden dispersar la relevancia entre varias URLs."
        ),
        "technical_notes": "Usar patrones dinámicos que incluyan atributos únicos (ej. nombre de producto/categoría)."
    },
    {
        "code": "CONTENT_DUPLICATE",
        "name": "Contenido duplicado",
        "severity": "major",
        "category": "content",
        "description": "El contenido principal de la página es muy similar o idéntico al de otras URLs.",
        "fix_template_for_impl": (
            "Diferencia el contenido, fusiona páginas redundantes o utiliza canonical tags cuando una versión "
            "deba ser la principal."
        ),
        "why_it_matters": (
            "El contenido duplicado dificulta decidir qué versión mostrar, diluye señales de relevancia y puede "
            "afectar el rendimiento orgánico."
        ),
        "technical_notes": "Revisar patrones de contenido generado automáticamente, filtros y parámetros."
    },
    {
        "code": "CONTENT_THIN",
        "name": "Contenido delgado (thin content)",
        "severity": "major",
        "category": "content",
        "description": "La página tiene muy poco texto o no aporta contenido suficiente.",
        "fix_template_for_impl": (
            "Amplía el contenido incluyendo información útil, FAQs, detalles de producto/servicio, ejemplos y "
            "recursos que respondan mejor a la intención del usuario."
        ),
        "why_it_matters": (
            "Páginas con poco contenido aportan poco valor al usuario y suelen posicionar peor en búsquedas "
            "competitivas."
        ),
        "technical_notes": "Revisar plantillas de listados, fichas y páginas generadas masivamente."
    },
    {
        "code": "CONTENT_EMPTY",
        "name": "Páginas sin contenido",
        "severity": "critical",
        "category": "content",
        "description": "La página prácticamente no tiene contenido visible.",
        "fix_template_for_impl": (
            "Definir si esta página debe existir. Si sí, añade contenido relevante. Si no, redirecciona a la "
            "sección más cercana que sí aporte valor."
        ),
        "why_it_matters": (
            "Las páginas vacías generan mala experiencia de usuario, aumentan el rebote y pueden ser vistas como "
            "páginas de baja calidad."
        ),
        "technical_notes": "Revisar creación automática de URLs sin contenido (ej. filtros, tags, archivos vacíos)."
    },

    # ===============================================================
    # PROBLEMAS DE ESTRUCTURA DE URLs
    # ===============================================================
    {
        "code": "URL_TOO_LONG",
        "name": "URLs demasiado largas",
        "severity": "minor",
        "category": "technical",
        "description": "La URL supera una longitud recomendable.",
        "fix_template_for_impl": (
            "Simplifica la estructura de la URL eliminando niveles innecesarios, parámetros superfluos y cadenas "
            "de texto muy largas."
        ),
        "why_it_matters": (
            "URLs excesivamente largas son más difíciles de compartir, de entender y pueden truncarse en SERPs."
        ),
        "technical_notes": "En lo posible, mantener URLs limpias, legibles y cortas."
    },
    {
        "code": "URL_TOO_MANY_PARAMS",
        "name": "URLs con parámetros excesivos",
        "severity": "minor",
        "category": "technical",
        "description": "La URL contiene demasiados parámetros de consulta.",
        "fix_template_for_impl": (
            "Reduce parámetros a los estrictamente necesarios. Usa mecanismos de tracking alternativos cuando "
            "sea posible (ej. server-side tracking)."
        ),
        "why_it_matters": "Demasiados parámetros generan versiones duplicadas o casi duplicadas de la misma página.",
        "technical_notes": "Configura reglas de parámetros en Google Search Console y en tu plataforma de analítica."
    },
    {
        "code": "URL_NON_CANONICAL",
        "name": "URLs no canónicas",
        "severity": "major",
        "category": "technical",
        "description": "La URL no coincide con la versión canónica esperada.",
        "fix_template_for_impl": (
            "Define una URL canónica clara y asegúrate de que todas las variaciones (con/ sin parámetros, mayúsculas, "
            "slash final, etc.) apunten a ella mediante redirecciones 301 y canonical tags."
        ),
        "why_it_matters": (
            "Las variaciones de URL sin una canonical clara generan duplicidad y fragmentan señales de ranking."
        ),
        "technical_notes": "Revisar reglas de reescritura de URLs y canonical tags en plantillas."
    },
    {
        "code": "URL_SPECIAL_CHARS",
        "name": "URLs con caracteres especiales o no ASCII",
        "severity": "minor",
        "category": "technical",
        "description": "La URL contiene caracteres especiales, acentos o caracteres no ASCII.",
        "fix_template_for_impl": (
            "Normaliza las URLs usando sólo caracteres ASCII, sin espacios ni caracteres especiales. Usa guiones "
            "para separar palabras."
        ),
        "why_it_matters": "URLs con caracteres especiales pueden generar problemas de codificación y compartir enlaces.",
        "technical_notes": "Evitar espacios, ñ, acentos, símbolos y caracteres reservados sin codificar."
    },
    {
        "code": "URL_UPPERCASE",
        "name": "URLs con mayúsculas",
        "severity": "minor",
        "category": "technical",
        "description": "La URL contiene letras en mayúscula.",
        "fix_template_for_impl": (
            "Unifica la convención usando sólo minúsculas y redirecciona las versiones en mayúsculas hacia la "
            "versión en minúsculas."
        ),
        "why_it_matters": "La sensibilidad a mayúsculas puede generar versiones duplicadas y enlaces rotos.",
        "technical_notes": "Configurar reglas en servidor para normalizar el case de las URLs."
    },
    {
        "code": "URL_UNDERSCORES",
        "name": "URLs con guiones bajos",
        "severity": "minor",
        "category": "technical",
        "description": "La URL usa guiones bajos (_) en lugar de guiones (-).",
        "fix_template_for_impl": (
            "Reescribe las URLs para usar guiones medios (-) como separadores de palabras, si es viable sin "
            "impactar tráfico ni posicionamiento."
        ),
        "why_it_matters": "Google recomienda guiones medios como separadores. Los guiones bajos pueden dificultar la lectura.",
        "technical_notes": "Hacer cambios de estructura de URLs con redirecciones 301 bien mapeadas."
    },

    # ===============================================================
    # ENLACES INTERNOS Y EXTERNOS
    # ===============================================================
    {
        "code": "INTERNAL_BROKEN_LINK",
        "name": "Enlaces internos rotos",
        "severity": "major",
        "category": "links",
        "description": "La página contiene enlaces internos que apuntan a URLs con error.",
        "fix_template_for_impl": (
            "Actualiza o elimina los enlaces internos que apuntan a páginas que dan error. Redirige a la URL correcta "
            "o ajusta el destino."
        ),
        "why_it_matters": (
            "Los enlaces internos rotos afectan la experiencia de usuario y desperdician presupuesto de rastreo."
        ),
        "technical_notes": "Usar herramientas de crawl para listar todos los enlaces internos rotos por origen/destino."
    },
    {
        "code": "EXTERNAL_BROKEN_LINK",
        "name": "Enlaces externos rotos",
        "severity": "minor",
        "category": "links",
        "description": "La página contiene enlaces externos que apuntan a URLs con error.",
        "fix_template_for_impl": (
            "Actualiza los enlaces externos hacia fuentes activas o elimínalos si ya no son relevantes."
        ),
        "why_it_matters": "Enlaces externos rotos perjudican la experiencia de usuario y dan mala señal de mantenimiento del sitio.",
        "technical_notes": "Revisar enlaces de recursos, referencias y partners periódicamente."
    },
    {
        "code": "OUTBOUND_TO_ERROR_PAGE",
        "name": "Enlaces salientes a páginas con error",
        "severity": "minor",
        "category": "links",
        "description": "Existen enlaces salientes (internos o externos) hacia páginas que devuelven errores.",
        "fix_template_for_impl": (
            "Asegúrate de que los enlaces salientes apunten a páginas activas y relevantes. Sustituye o elimina los que apunten a errores."
        ),
        "why_it_matters": "Los usuarios que siguen estos enlaces encuentran errores y pueden abandonar el sitio.",
        "technical_notes": "Cruzar datos de crawl con códigos de estado de destino para identificar estas situaciones."
    },
    {
        "code": "ORPHAN_PAGE",
        "name": "Páginas huérfanas",
        "severity": "major",
        "category": "links",
        "description": "Páginas que no reciben enlaces internos desde otras secciones del sitio.",
        "fix_template_for_impl": (
            "Incluye enlaces internos desde secciones relevantes (menús, listados, contenidos relacionados) "
            "para conectar estas páginas con la arquitectura de información."
        ),
        "why_it_matters": (
            "Las páginas huérfanas son difíciles de descubrir para los bots y para los usuarios, por lo que suelen "
            "tener mal rendimiento orgánico."
        ),
        "technical_notes": "Cruzar URLs rastreadas con URLs del sitemap y enlaces internos para detectar orfandad."
    },
    {
        "code": "CRAWL_DEPTH_EXCESSIVE",
        "name": "Profundidad de rastreo excesiva",
        "severity": "minor",
        "category": "links",
        "description": "La página se encuentra a demasiados clics de distancia desde la home.",
        "fix_template_for_impl": (
            "Acerca esta página a la superficie mediante enlaces internos desde secciones superiores o navegación "
            "estructurada (categorías, hubs, etc.)."
        ),
        "why_it_matters": (
            "Cuanto más profunda está una página, menos probable es que reciba rastreo y enlaces internos de calidad."
        ),
        "technical_notes": "Intentar mantener páginas importantes a 3-4 clics máximo desde la home."
    },
    {
        "code": "TOO_MANY_LINKS",
        "name": "Demasiados enlaces en una página",
        "severity": "minor",
        "category": "links",
        "description": "La página contiene un número excesivo de enlaces.",
        "fix_template_for_impl": (
            "Reduce la cantidad de enlaces no esenciales, agrupa enlaces en menús desplegables o secciones, "
            "y prioriza los enlaces más relevantes."
        ),
        "why_it_matters": (
            "Un exceso de enlaces puede dispersar la atención del usuario y diluir la autoridad distribuida."
        ),
        "technical_notes": "No hay un número mágico, pero revisar páginas con cientos de enlaces para depuración."
    },

    # ===============================================================
    # ETIQUETAS CANÓNICAS
    # ===============================================================
    {
        "code": "CANONICAL_MISSING",
        "name": "Canonical tag faltante",
        "severity": "minor",
        "category": "technical",
        "description": "La página no define una etiqueta canonical.",
        "fix_template_for_impl": (
            "Define una canonical que apunte a la versión preferida de la URL, especialmente si hay parámetros "
            "o versiones alternativas."
        ),
        "why_it_matters": (
            "Sin canonical, las variaciones de URL pueden competir entre sí y fragmentar señales de SEO."
        ),
        "technical_notes": "Usar <link rel=\"canonical\" href=\"URL\" /> en el <head>."
    },
    {
        "code": "CANONICAL_INCORRECT",
        "name": "Canonical incorrecta o conflictiva",
        "severity": "major",
        "category": "technical",
        "description": "La canonical no coincide con la URL principal esperada o entra en conflicto con otras señales.",
        "fix_template_for_impl": (
            "Ajusta la canonical para que apunte a la versión realmente principal. Evita apuntar a URLs con errores "
            "o con parámetros innecesarios."
        ),
        "why_it_matters": (
            "Canonicals incorrectas pueden desindexar accidentalmente versiones importantes o consolidar señales "
            "hacia la URL menos adecuada."
        ),
        "technical_notes": "Revisar combinación de canonical, redirects, hreflang y sitemap."
    },
    {
        "code": "CANONICAL_CHAIN",
        "name": "Cadenas de canonicalización",
        "severity": "minor",
        "category": "technical",
        "description": "La canonical apunta a una URL que a su vez apunta a otra canonical.",
        "fix_template_for_impl": (
            "Haz que todas las variaciones apunten directamente a la URL final principal, sin cadenas de canonicals."
        ),
        "why_it_matters": "Las cadenas añaden complejidad innecesaria y pueden generar señales ambiguas.",
        "technical_notes": "Evita A→B→C en canonicals; usa A/B→C directamente."
    },
    {
        "code": "CANONICAL_TO_ERROR",
        "name": "Canonical apuntando a páginas con error",
        "severity": "major",
        "category": "technical",
        "description": "La canonical apunta a una URL que devuelve un código de error.",
        "fix_template_for_impl": (
            "Actualiza la canonical para que apunte a una página activa (200) que represente la versión principal."
        ),
        "why_it_matters": "Consolidar señales hacia una URL con error implica desperdiciar relevancia y tráfico potencial.",
        "technical_notes": "Cruzar canonicals con códigos de estado HTTP para detectar este caso."
    },

    # ===============================================================
    # ROBOTS Y DIRECTIVAS
    # ===============================================================
    {
        "code": "ROBOTS_BLOCKING_INDEXABLE",
        "name": "Páginas bloqueadas por robots.txt pero indexables",
        "severity": "major",
        "category": "technical",
        "description": "La página está bloqueada en robots.txt pero pensada para ser indexada.",
        "fix_template_for_impl": (
            "Si la página debe posicionar, elimina o ajusta la regla de robots.txt. Si no debe posicionar, "
            "evalúa usar noindex y permitir el rastreo si necesitas que se apliquen otras señales."
        ),
        "why_it_matters": (
            "Bloquear el rastreo impide que Google entienda el contenido y aplique señales de ranking correctamente."
        ),
        "technical_notes": "Revisar /robots.txt y reglas específicas por path."
    },
    {
        "code": "ROBOTS_CONFLICT",
        "name": "Conflictos entre robots.txt y meta robots",
        "severity": "minor",
        "category": "technical",
        "description": "Las directivas de robots.txt entran en conflicto con meta robots o x-robots-tag.",
        "fix_template_for_impl": (
            "Unifica la intención: decide si la página debe rastrearse e indexarse y ajusta robots.txt y meta robots "
            "en consecuencia."
        ),
        "why_it_matters": (
            "Mensajes contradictorios pueden generar comportamientos inesperados en el rastreo y la indexación."
        ),
        "technical_notes": "Definir una política clara por tipo de contenido (público, privado, filtrado, etc.)."
    },
    {
        "code": "NOINDEX_ON_IMPORTANT",
        "name": "Directiva noindex en páginas importantes",
        "severity": "critical",
        "category": "technical",
        "description": "Páginas que deberían posicionar tienen la directiva noindex.",
        "fix_template_for_impl": (
            "Elimina la etiqueta noindex en páginas que deban aparecer en buscadores y revisa procesos automáticos "
            "que la estén aplicando."
        ),
        "why_it_matters": "Un noindex en páginas clave bloquea completamente su visibilidad orgánica.",
        "technical_notes": "Buscar 'noindex' en plantillas, plugins y reglas de servidor."
    },
    {
        "code": "NOFOLLOW_MISUSED",
        "name": "Directivas nofollow mal implementadas",
        "severity": "minor",
        "category": "technical",
        "description": "Uso de nofollow en enlaces o páginas donde no tiene sentido estratégico.",
        "fix_template_for_impl": (
            "Evalúa si el uso de nofollow responde a una necesidad real (ej. enlaces de pago, UGC) y elimina "
            "noffollow en enlaces internos valiosos."
        ),
        "why_it_matters": "Nofollow mal aplicado puede limitar la distribución de autoridad interna.",
        "technical_notes": "Revisar rel=\"nofollow\" en plantillas y componentes."
    },
    {
        "code": "INDEXABLE_BUT_NOT_CRAWLABLE",
        "name": "Páginas indexables pero no rastreables",
        "severity": "major",
        "category": "technical",
        "description": "La página puede indexarse pero está bloqueada para el rastreo.",
        "fix_template_for_impl": (
            "Permite el rastreo de las páginas que deban ser indexadas, ajustando robots.txt o directivas de bloqueo."
        ),
        "why_it_matters": "Google puede tener dificultades para actualizar o entender el contenido si no lo rastrea.",
        "technical_notes": "Sin rastreo, muchas señales (links, contenido, structured data) no se aprovechan bien."
    },

    # ===============================================================
    # PROBLEMAS DE IMÁGENES
    # ===============================================================
    {
        "code": "IMAGE_ALT_MISSING",
        "name": "Imágenes sin atributo ALT",
        "severity": "minor",
        "category": "content",
        "description": "La imagen no tiene atributo ALT definido.",
        "fix_template_for_impl": (
            "Añade un atributo ALT descriptivo que explique el contenido de la imagen y, cuando tenga sentido, "
            "incluya términos relevantes."
        ),
        "why_it_matters": (
            "El ALT mejora la accesibilidad, la comprensión del contenido y puede ayudar en Google Imágenes."
        ),
        "technical_notes": "Revisa plantillas de cards, sliders, galerías y componentes de media."
    },
    {
        "code": "IMAGE_ALT_EMPTY",
        "name": "Imágenes con ALT vacío",
        "severity": "minor",
        "category": "content",
        "description": "La imagen tiene un atributo ALT vacío sin necesidad.",
        "fix_template_for_impl": (
            "Rellena el ALT en imágenes relevantes para el contenido. Solo deja ALT vacío cuando la imagen sea "
            "decorativa."
        ),
        "why_it_matters": "ALT vacío en imágenes clave desaprovecha oportunidades de accesibilidad y contexto.",
        "technical_notes": "Diferenciar imágenes decorativas de imágenes de contenido."
    },
    {
        "code": "IMAGE_BROKEN",
        "name": "Imágenes rotas",
        "severity": "minor",
        "category": "content",
        "description": "La imagen referenciada no se carga (error 404 u otro).",
        "fix_template_for_impl": (
            "Actualiza la ruta de la imagen o reemplázala por una disponible. Elimina referencias a imágenes "
            "que ya no existen."
        ),
        "why_it_matters": "Las imágenes rotas generan mala experiencia de usuario y hacen que la página parezca descuidada.",
        "technical_notes": "Verificar rutas relativas, permisos y despliegues de assets."
    },
    {
        "code": "IMAGE_TOO_HEAVY",
        "name": "Imágenes demasiado grandes",
        "severity": "major",
        "category": "performance",
        "description": "El tamaño de archivo de la imagen es demasiado grande para su uso.",
        "fix_template_for_impl": (
            "Comprime las imágenes, usa formatos modernos (WebP/AVIF) y ajusta dimensiones según el tamaño real "
            "en pantalla."
        ),
        "why_it_matters": "Imágenes pesadas son una de las principales causas de páginas lentas.",
        "technical_notes": "Automatizar compresión en el pipeline de medios o en el CDN."
    },

    # ===============================================================
    # HREFLANG Y MULTIIDIOMA
    # ===============================================================
    {
        "code": "HREFLANG_MISSING",
        "name": "Etiquetas hreflang faltantes",
        "severity": "minor",
        "category": "internationalization",
        "description": "La página multiidioma carece de etiquetas hreflang.",
        "fix_template_for_impl": (
            "Añade hreflang apuntando a las versiones equivalentes en otros idiomas/regiones, incluyendo x-default "
            "si aplica."
        ),
        "why_it_matters": "Hreflang ayuda a servir la versión correcta por país/idioma y reduce contenidos duplicados entre mercados.",
        "technical_notes": "Asegurar reciprocidad y consistencia entre todas las versiones."
    },
    {
        "code": "HREFLANG_INCORRECT",
        "name": "Etiquetas hreflang mal implementadas",
        "severity": "major",
        "category": "internationalization",
        "description": "Hreflang apunta a URLs erróneas o usa códigos de idioma/región incorrectos.",
        "fix_template_for_impl": (
            "Corrige los códigos de idioma (ej. es-mx, en-us) y las URLs de destino para que correspondan a la "
            "versión adecuada."
        ),
        "why_it_matters": (
            "Implementaciones incorrectas pueden causar que Google ignore el hreflang y muestre versiones equivocadas."
        ),
        "technical_notes": "Validar con herramientas de testing hreflang y revisar sitemaps alternates."
    },
    {
        "code": "HREFLANG_NO_RECIPROCITY",
        "name": "Hreflang sin reciprocidad",
        "severity": "minor",
        "category": "internationalization",
        "description": "Una versión referencia a otra con hreflang, pero no existe reciprocidad.",
        "fix_template_for_impl": (
            "Asegura que cada URL mencionada con hreflang también devuelva un enlace hreflang de vuelta a esta página."
        ),
        "why_it_matters": "La reciprocidad es requisito para que Google confíe plenamente en la configuración hreflang.",
        "technical_notes": "Validar pares de URLs entre idiomas/regiones."
    },
    {
        "code": "HREFLANG_CANONICAL_CONFLICT",
        "name": "Conflictos entre hreflang y canonical",
        "severity": "major",
        "category": "internationalization",
        "description": "La canonical no coincide con la versión indicada por hreflang.",
        "fix_template_for_impl": (
            "Alinea canonical y hreflang para que ambas señales apunten a la versión correcta de cada idioma/región."
        ),
        "why_it_matters": "Señales contradictorias pueden hacer que una versión se desindexe o pierda relevancia.",
        "technical_notes": "Revisar plantillas multiidioma y anotaciones alternates."
    },

    # ===============================================================
    # SITEMAP XML
    # ===============================================================
    {
        "code": "SITEMAP_URL_ERROR",
        "name": "URLs en sitemap con errores",
        "severity": "major",
        "category": "sitemap",
        "description": "El sitemap incluye URLs que devuelven código de error.",
        "fix_template_for_impl": (
            "Elimina del sitemap las URLs que devuelven error o corrige las URLs que deban seguir activas."
        ),
        "why_it_matters": "Un sitemap limpio mejora la confianza en las señales que envías a los buscadores.",
        "technical_notes": "Cruzar listado de sitemap con resultados de crawl."
    },
    {
        "code": "SITEMAP_URL_BLOCKED_ROBOTS",
        "name": "URLs en sitemap bloqueadas por robots.txt",
        "severity": "major",
        "category": "sitemap",
        "description": "El sitemap referencia URLs que están bloqueadas en robots.txt.",
        "fix_template_for_impl": (
            "Si la URL debe posicionar, quita el bloqueo en robots. Si no debe, elimínala del sitemap."
        ),
        "why_it_matters": "Mandar señales contradictorias (sitemap vs robots) reduce la claridad de tu estrategia SEO.",
        "technical_notes": "Revisar políticas de indexación por tipo de contenido."
    },
    {
        "code": "SITEMAP_URL_NOINDEX",
        "name": "URLs en sitemap con noindex",
        "severity": "major",
        "category": "sitemap",
        "description": "El sitemap incluye URLs marcadas con noindex.",
        "fix_template_for_impl": (
            "Si deben posicionar, elimina el noindex. Si no, elimina esas URLs del sitemap."
        ),
        "why_it_matters": "Un sitemap debería listar URLs que quieres indexar, no las que explícitamente excluyes.",
        "technical_notes": "Revisar configuraciones automáticas de sitemaps en CMS/plugins."
    },
    {
        "code": "SITEMAP_URL_MISSING",
        "name": "URLs importantes no incluidas en sitemap",
        "severity": "minor",
        "category": "sitemap",
        "description": "Hay páginas relevantes que no aparecen en el sitemap.",
        "fix_template_for_impl": (
            "Añade las URLs estratégicas al sitemap para facilitar su descubrimiento y rastreo."
        ),
        "why_it_matters": "El sitemap sirve como guía prioritaria para el rastreo de contenidos clave.",
        "technical_notes": "Verificar reglas de inclusión/exclusión del generador de sitemap."
    },
    {
        "code": "SITEMAP_TOO_LARGE",
        "name": "Sitemaps demasiado grandes",
        "severity": "minor",
        "category": "sitemap",
        "description": "El sitemap excede el tamaño o número de URLs recomendado.",
        "fix_template_for_impl": (
            "Divide el sitemap en varios archivos (por secciones, idiomas, tipos de contenido) y usa un índice de sitemaps."
        ),
        "why_it_matters": "Sitemaps más pequeños son más manejables y se procesan con mayor facilidad.",
        "technical_notes": "Seguir límites de Google (50.000 URLs o 50MB sin comprimir por sitemap)."
    },

    # ===============================================================
    # STRUCTURED DATA (SCHEMA)
    # ===============================================================
    {
        "code": "SCHEMA_SYNTAX_ERROR",
        "name": "Errores de sintaxis en structured data",
        "severity": "minor",
        "category": "structured_data",
        "description": "El marcado structured data tiene errores de sintaxis (JSON-LD, Microdata o RDFa).",
        "fix_template_for_impl": (
            "Corrige la sintaxis del JSON-LD o marcado utilizado siguiendo la documentación oficial y validadores "
            "de Google."
        ),
        "why_it_matters": "Errores de sintaxis impiden que los buscadores interpreten correctamente tu schema.",
        "technical_notes": "Validar en herramientas oficiales de testing de structured data."
    },
    {
        "code": "SCHEMA_MISSING",
        "name": "Schema markup faltante",
        "severity": "minor",
        "category": "structured_data",
        "description": "La página no incluye ningún marcado structured data.",
        "fix_template_for_impl": (
            "Añade schema apropiado al tipo de contenido (Organization, Product, Article, FAQ, etc.)"
        ),
        "why_it_matters": (
            "El structured data ayuda a enriquecer resultados y mejorar la comprensión del contenido por parte "
            "de los buscadores."
        ),
        "technical_notes": "Usar JSON-LD recomendado por Google."
    },
    {
        "code": "SCHEMA_MISSING_REQUIRED_PROPERTY",
        "name": "Propiedades requeridas ausentes en schema",
        "severity": "minor",
        "category": "structured_data",
        "description": "Faltan propiedades requeridas o recomendadas en el marcado.",
        "fix_template_for_impl": (
            "Completa las propiedades clave (name, description, image, price, etc.) según el tipo de schema."
        ),
        "why_it_matters": (
            "Sin propiedades completas, muchos rich results no se activan o se consideran ineligibles."
        ),
        "technical_notes": "Revisar documentación específica de cada tipo (Product, FAQ, HowTo, etc.)."
    },
    {
        "code": "SCHEMA_WRONG_TYPE",
        "name": "Tipos de schema incorrectos",
        "severity": "minor",
        "category": "structured_data",
        "description": "Se ha implementado un tipo de schema no adecuado al contenido real.",
        "fix_template_for_impl": (
            "Sustituye el tipo de schema por uno que represente correctamente el contenido de la página."
        ),
        "why_it_matters": "Schema no representativo puede generar inconsistencias o ignorarse por parte de Google.",
        "technical_notes": "Evitar usar tipos genéricos cuando existe un tipo específico más apropiado."
    },

    # ===============================================================
    # PAGINACIÓN
    # ===============================================================
    {
        "code": "PAGINATION_REL_NEXT_PREV_INCORRECT",
        "name": "rel=\"next\"/\"prev\" mal implementados",
        "severity": "minor",
        "category": "technical",
        "description": "Las etiquetas de paginación rel=\"next\" y rel=\"prev\" apuntan a URLs incorrectas.",
        "fix_template_for_impl": (
            "Revisa y corrige las URLs de rel=\"next\" y rel=\"prev\" para que reflejen la secuencia real de páginas."
        ),
        "why_it_matters": "Una paginación clara ayuda a entender series de contenido largo o listados extensos.",
        "technical_notes": "Aunque Google ha cambiado su soporte, sigue siendo relevante para UX y otros bots."
    },
    {
        "code": "PAGINATION_REL_NEXT_PREV_MISSING",
        "name": "Falta de etiquetas de paginación",
        "severity": "minor",
        "category": "technical",
        "description": "No se han definido rel=\"next\"/\"prev\" en listados paginados.",
        "fix_template_for_impl": (
            "Considera añadir anotaciones de paginación si la secuencia es compleja o extensa."
        ),
        "why_it_matters": "Ayuda a algunos bots y herramientas a comprender mejor la estructura de listados.",
        "technical_notes": "Revisar componentes de paginación del front."
    },
    {
        "code": "PAGINATION_PARAM_ISSUES",
        "name": "Problemas con parámetros de paginación",
        "severity": "minor",
        "category": "technical",
        "description": "Los parámetros de paginación generan situaciones de duplicidad o indexación ineficiente.",
        "fix_template_for_impl": (
            "Normaliza parámetros de paginación y combina con canonical o reglas de parámetros para evitar "
            "duplicidad masiva."
        ),
        "why_it_matters": "Paginación mal gestionada multiplica el número de URLs sin aportar valor nuevo.",
        "technical_notes": "Definir convención consistente: ?page=2, ?p=2, etc."
    },

    # ===============================================================
    # SEGURIDAD Y PROTOCOLO
    # ===============================================================
    {
        "code": "HTTP_ON_HTTPS_SITE",
        "name": "Páginas HTTP en sitios HTTPS",
        "severity": "major",
        "category": "security",
        "description": "Existen páginas accesibles por HTTP en un dominio que usa HTTPS.",
        "fix_template_for_impl": (
            "Forza redirecciones de HTTP a HTTPS en todo el sitio y actualiza enlaces internos para usar siempre HTTPS."
        ),
        "why_it_matters": "El uso de HTTP en sitios HTTPS genera alertas de seguridad y afecta la confianza.",
        "technical_notes": "Configurar HSTS y redirecciones 301 permanentes a HTTPS."
    },
    {
        "code": "MIXED_CONTENT",
        "name": "Contenido mixto (mixed content)",
        "severity": "major",
        "category": "security",
        "description": "La página carga recursos HTTP en un contexto HTTPS.",
        "fix_template_for_impl": (
            "Actualiza todos los recursos (imágenes, scripts, CSS) para que se carguen por HTTPS. Elimina referencias HTTP."
        ),
        "why_it_matters": "El mixed content rompe el candado de seguridad y puede bloquear recursos en navegadores modernos.",
        "technical_notes": "Buscar 'http://' en el código y configuraciones de CMS/plantillas."
    },
    {
        "code": "SSL_INVALID",
        "name": "Certificados SSL vencidos o inválidos",
        "severity": "critical",
        "category": "security",
        "description": "El certificado SSL del sitio está vencido, mal configurado o es inválido.",
        "fix_template_for_impl": (
            "Renueva o corrige la configuración del certificado SSL y verifica la cadena de confianza completa."
        ),
        "why_it_matters": "Errores SSL bloquean el acceso en muchos navegadores y destruyen la confianza del usuario.",
        "technical_notes": "Revisar CA, fechas de expiración y soporte en todos los subdominios relevantes."
    },
    {
        "code": "MISSING_HTTP_TO_HTTPS_REDIRECT",
        "name": "Faltan redirecciones de HTTP a HTTPS",
        "severity": "major",
        "category": "security",
        "description": "No todas las URLs HTTP redirigen automáticamente a la versión HTTPS.",
        "fix_template_for_impl": (
            "Configura redirecciones globales para que cualquier petición HTTP vaya siempre a la versión HTTPS."
        ),
        "why_it_matters": "Exponer versiones HTTP puede crear duplicidad y problemas de seguridad.",
        "technical_notes": "Configurar reglas a nivel de servidor o CDN."
    },

    # ===============================================================
    # JAVASCRIPT Y RENDERIZADO
    # ===============================================================
    {
        "code": "JS_BLOCKING_CONTENT",
        "name": "Contenido bloqueado por JavaScript",
        "severity": "major",
        "category": "javascript",
        "description": "El contenido principal depende de JS que puede no ejecutarse correctamente para los bots.",
        "fix_template_for_impl": (
            "Evalúa renderizado dinámico o pre-rendering. Asegúrate de que el contenido crítico sea accesible "
            "en HTML renderizado."
        ),
        "why_it_matters": "Si Google no ejecuta bien el JS, puede ver una página casi vacía o incompleta.",
        "technical_notes": "Usar herramientas de inspección de HTML renderizado vs HTML inicial."
    },
    {
        "code": "JS_BLOCKED_RESOURCES",
        "name": "Recursos JS/CSS bloqueados",
        "severity": "minor",
        "category": "javascript",
        "description": "Los archivos JS o CSS están bloqueados por robots o restricciones de acceso.",
        "fix_template_for_impl": (
            "Permite que los bots accedan a los recursos críticos para el renderizado si afectan al contenido "
            "visible o layout."
        ),
        "why_it_matters": "Bloquear recursos clave puede impedir que Google renderice la página como la ve el usuario.",
        "technical_notes": "Revisar robots.txt y reglas de acceso a /static/, /assets/ u otras rutas."
    },
    {
        "code": "RENDERED_HTML_DIFFERS",
        "name": "Diferencias entre HTML sin renderizar y renderizado",
        "severity": "minor",
        "category": "javascript",
        "description": "Existe una gran diferencia entre el HTML inicial y la versión renderizada.",
        "fix_template_for_impl": (
            "Minimiza la diferencia clave moviendo contenido importante al HTML inicial o asegurando un renderizado "
            "confiable para bots."
        ),
        "why_it_matters": "Lo que ve Google puede ser diferente a lo que ve el usuario, afectando la indexación adecuada.",
        "technical_notes": "Comparar versiones con herramientas de renderizado (ej. Mobile-Friendly Test, inspección de URL)."
    },

    # ===============================================================
    # OTROS ERRORES TÉCNICOS
    # ===============================================================
    {
        "code": "EMPTY_RESPONSE",
        "name": "Páginas con respuestas vacías",
        "severity": "critical",
        "category": "technical",
        "description": "El servidor responde sin contenido útil (body vacío).",
        "fix_template_for_impl": (
            "Investiga por qué la respuesta llega vacía (errores de aplicación, permisos, timeouts) y corrige la lógica."
        ),
        "why_it_matters": "Una respuesta vacía es equivalente a una página rota a nivel de experiencia y de SEO.",
        "technical_notes": "Revisar logs de aplicación y servidor para errores en la generación de vistas."
    },
    {
        "code": "CSS_JS_BLOCKED",
        "name": "Recursos CSS/JS bloqueados",
        "severity": "minor",
        "category": "technical",
        "description": "Recursos clave como estilos o scripts están bloqueados para bots.",
        "fix_template_for_impl": (
            "Permite el acceso a recursos críticos para que la página se renderice correctamente en Google."
        ),
        "why_it_matters": "Un renderizado incompleto puede perjudicar la evaluación de UX por parte de los buscadores.",
        "technical_notes": "Revisar robots.txt y configuraciones per-path."
    },
    {
        "code": "ROBOTS_TXT_INACCESSIBLE",
        "name": "robots.txt inaccesible",
        "severity": "major",
        "category": "technical",
        "description": "El archivo robots.txt no se puede acceder o devuelve error.",
        "fix_template_for_impl": (
            "Asegura que robots.txt esté disponible en /robots.txt y devuelva un código 200 con reglas claras."
        ),
        "why_it_matters": "Sin robots.txt accesible, los bots pueden asumir restricciones o comportamientos por defecto no deseados.",
        "technical_notes": "Verificar permisos, despliegues y proxies."
    },
    {
        "code": "SITEMAP_XML_INACCESSIBLE",
        "name": "sitemap.xml inaccesible",
        "severity": "minor",
        "category": "technical",
        "description": "El sitemap principal no se puede acceder o devuelve error.",
        "fix_template_for_impl": (
            "Corrige ruta, permisos o configuración del sitemap para que esté disponible y se pueda registrar en GSC."
        ),
        "why_it_matters": "Sin sitemap funcional, es más difícil guiar el rastreo hacia las secciones clave.",
        "technical_notes": "Verificar URL exacta, index de sitemaps y respuestas HTTP."
    },
    {
        "code": "CHARSET_ISSUES",
        "name": "Problemas de codificación de caracteres",
        "severity": "minor",
        "category": "technical",
        "description": "Hay problemas con la codificación (acentos rotos, símbolos extraños, etc.).",
        "fix_template_for_impl": (
            "Unifica la codificación (idealmente UTF-8) y asegúrate de que el header HTTP y el meta charset "
            "sean coherentes."
        ),
        "why_it_matters": "Errores de codificación generan mala experiencia de lectura y pueden afectar la interpretación del contenido.",
        "technical_notes": "Revisar configuración de servidor, CMS y base de datos."
    },

    # ===============================================================
    # ISSUES ESPECÍFICOS DE PAGESPEED INSIGHTS / LIGHTHOUSE
    # ===============================================================
    {
        "code": "PERF_LCP_SLOW",
        "name": "LCP (Largest Contentful Paint) lento",
        "severity": "major",
        "category": "performance",
        "description": "El LCP está por encima del umbral recomendado.",
        "fix_template_for_impl": (
            "Optimiza el elemento principal de la página (imagen héroe, bloque principal). Comprime imágenes, "
            "mejora TTFB y reduce recursos bloqueantes de renderizado."
        ),
        "why_it_matters": "LCP es un Core Web Vital clave para la percepción de velocidad y rankings.",
        "technical_notes": "Apuntar a LCP < 2500 ms en mobile."
    },
    {
        "code": "PERF_FCP_SLOW",
        "name": "FCP (First Contentful Paint) lento",
        "severity": "minor",
        "category": "performance",
        "description": "El FCP tarda demasiado en mostrar el primer contenido.",
        "fix_template_for_impl": (
            "Reduce recursos bloqueantes en el head (CSS, JS), habilita carga diferida de scripts y optimiza el servidor."
        ),
        "why_it_matters": "Un FCP lento hace que el usuario sienta que la página 'no arranca'.",
        "technical_notes": "Revisar audits de render-blocking-resources en PageSpeed."
    },
    {
        "code": "PERF_SI_SLOW",
        "name": "Speed Index alto",
        "severity": "minor",
        "category": "performance",
        "description": "El Speed Index indica que la página tarda en llenarse visualmente.",
        "fix_template_for_impl": (
            "Optimiza carga de recursos above the fold, minimiza CSS crítico y reduce JS pesado en el inicio."
        ),
        "why_it_matters": "Un Speed Index alto se correlaciona con sensación de lentitud.",
        "technical_notes": "Analizar sugerencias de Lighthouse específicas para Speed Index."
    },
    {
        "code": "PERF_TBT_HIGH",
        "name": "Total Blocking Time (TBT) alto",
        "severity": "major",
        "category": "performance",
        "description": "El tiempo en que la página permanece bloqueada por tareas JS largas es elevado.",
        "fix_template_for_impl": (
            "Divide tareas JS largas en trozos más pequeños, aplaza scripts no críticos y elimina JS no utilizado."
        ),
        "why_it_matters": "TBT alto afecta la interactividad y se relaciona con INP (Interaction to Next Paint).",
        "technical_notes": "Revisar 'main thread' en Lighthouse y DevTools."
    },
    {
        "code": "PERF_CLS_HIGH",
        "name": "CLS (Cumulative Layout Shift) alto",
        "severity": "minor",
        "category": "performance",
        "description": "La página tiene cambios bruscos de layout durante la carga.",
        "fix_template_for_impl": (
            "Reserva espacio para imágenes, anuncios y componentes dinámicos. Evita insertar elementos por encima "
            "del contenido ya cargado."
        ),
        "why_it_matters": "CLS alto genera experiencia frustrante y afecta un Core Web Vital clave.",
        "technical_notes": "Apuntar a CLS < 0.1."
    },
    {
        "code": "PERF_RENDER_BLOCKING_RESOURCES",
        "name": "Recursos que bloquean el renderizado",
        "severity": "minor",
        "category": "performance",
        "description": "CSS o JS se cargan de forma que bloquean el renderizado de la página.",
        "fix_template_for_impl": (
            "Usa técnicas como preload, media queries diferidas, carga asíncrona/defer de JS y CSS crítico inline."
        ),
        "why_it_matters": "Bloquear el renderizado retrasa la visualización del contenido inicial.",
        "technical_notes": "Revisar audit 'render-blocking-resources' en PageSpeed."
    },
    {
        "code": "PERF_UNUSED_JS",
        "name": "JavaScript no utilizado",
        "severity": "minor",
        "category": "performance",
        "description": "Se carga una cantidad significativa de JS que no se usa en la página.",
        "fix_template_for_impl": (
            "Elimina librerías JS no utilizadas, divide bundles y carga sólo lo necesario por página."
        ),
        "why_it_matters": "JS no usado incrementa peso de la página y tiempo de ejecución sin aportar valor.",
        "technical_notes": "Revisar audit 'unused-javascript' en PageSpeed."
    },
    {
        "code": "PERF_LARGE_JS_BUNDLES",
        "name": "Bundles de JS demasiado grandes",
        "severity": "major",
        "category": "performance",
        "description": "Los archivos JS principales son muy pesados.",
        "fix_template_for_impl": (
            "Aplica code splitting, tree shaking y carga diferida de módulos. Evita cargar frameworks o librerías "
            "completas si sólo se usan pequeñas partes."
        ),
        "why_it_matters": "Bundles grandes afectan TBT, FCP y LCP.",
        "technical_notes": "Analizar network waterfall y coverage en DevTools."
    },
    {
        "code": "PERF_LARGE_IMAGES",
        "name": "Imágenes sin optimizar según PageSpeed",
        "severity": "major",
        "category": "performance",
        "description": "PageSpeed detecta imágenes que podrían optimizarse más.",
        "fix_template_for_impl": (
            "Recomprime las imágenes, usa formatos modernos y dimensiona correctamente según el tamaño real mostrado."
        ),
        "why_it_matters": "Imágenes grandes son la causa más habitual de mala puntuación en performance.",
        "technical_notes": "Revisar audits 'efficient-encoded-images' o equivalentes."
    },
    {
        "code": "PERF_TEXT_NOT_COMPRESSED",
        "name": "Texto sin compresión (text-compression)",
        "severity": "minor",
        "category": "performance",
        "description": "No se está aplicando compresión (gzip/brotli) a recursos de texto.",
        "fix_template_for_impl": (
            "Activa compresión gzip o brotli en el servidor para HTML, CSS y JS."
        ),
        "why_it_matters": "Sin compresión, los recursos tardan mucho más en descargarse.",
        "technical_notes": "Configurar compresión en servidor, reverse proxy o CDN."
    },
    {
        "code": "PERF_CACHE_POLICY_ISSUES",
        "name": "Política de caché ineficiente",
        "severity": "minor",
        "category": "performance",
        "description": "Los recursos estáticos no tienen una política de caché adecuada.",
        "fix_template_for_impl": (
            "Configura headers de caché con tiempos de vida suficientemente largos y versionado de archivos "
            "para cambios futuros."
        ),
        "why_it_matters": "Una buena caché mejora significativamente la experiencia en visitas repetidas.",
        "technical_notes": "Revisar audit 'serve-static-assets-with-an-efficient-cache-policy'."
    },
]

# -------------------------------------------------------------------
# CREACIÓN / ACTUALIZACIÓN DEL CATÁLOGO EN BD
# -------------------------------------------------------------------

def ensure_issue_types(db: Session):
    """
    Crea los IssueType definidos en DEFAULT_ISSUE_TYPES si no existen aún.
    Si ya existen, no los pisa (puedes extender lógicamente si necesitas actualizaciones).
    """
    existing_by_code = {
        it.code: it
        for it in db.query(models.IssueType).all()
    }

    for it in DEFAULT_ISSUE_TYPES:
        if it["code"] in existing_by_code:
            # Si quisieras actualizar textos automáticamente, podrías hacerlo aquí.
            continue
        db.add(models.IssueType(**it))

    db.commit()


# -------------------------------------------------------------------
# HOOKS PARA LÓGICA DE GENERACIÓN DE ISSUES Y SITE HEALTH
# -------------------------------------------------------------------
# NOTA:
# Aquí puedes conectar la lógica que ya tenías (generate_issues_for_crawl, compute_site_health)
# o crear una versión nueva que aproveche este catálogo extendido.
#
# Ejemplo:
#
# def generate_issues_for_crawl(db: Session, crawl: models.Crawl):
#     urls = db.query(models.Url).filter_by(crawl_id=crawl.id).all()
#     issue_types = {it.code: it for it in db.query(models.IssueType).all()}
#     ...
#
# def compute_site_health(db: Session, crawl: models.Crawl) -> float:
#     ...
#
# Mantengo estos fuera por claridad, para que los conectes con el
# esquema real de datos y métricas que ya estás definiendo con DataForSEO + PSI.
