import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Link as LinkIcon, Upload, ClipboardList, Search, AlertTriangle, CheckCircle2, XCircle, Activity, Info, TrendingUp, BookOpen, Home, Landmark, Scale, Users, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { analyzeNewsUrl, getNewsAnalysis, askKuybot, analyzeMediaUrl, analyzeAudio, analyzeVideo } from './services/api'
import logo from './assets/logo.jpeg'
import kuybotMascot from './assets/KUYBOT.png'

// Paleta de marca (del logo AMA-LLU-IA)
const BRAND_ORANGE = '#F5822B'
const BRAND_NAVY = '#101B3D'
const BRAND_NAVY_SOFT = '#16234E'

// ===== Terminos y Condiciones =====
// TERMS_VERSION debe incrementarse cada vez que cambie el texto legal,
// para que el modal se vuelva a mostrar a usuarios que ya habian aceptado una version anterior.
const TERMS_VERSION = '2026-08-15'
const TERMS_STORAGE_KEY = 'ama_llu_ia_terms_accepted_version'

const TERMS_META = [
  'Última actualización: 15 de agosto de 2026',
  'Aplicativo: AMALLU-IA',
  'Proyecto: MediaHack — OpenLab'
]

const TERMS_INTRO = [
  'Bienvenido/a a AMALLU-IA, una herramienta desarrollada en el marco del proyecto MediaHack de OpenLab, orientada a apoyar el análisis, contraste y comprensión de información difundida en medios digitales y en entornos de internet.',
  'Al acceder, utilizar o navegar por AMALLU-IA, el usuario declara haber leído, comprendido y aceptado los presentes Términos y Condiciones de Uso. Si no está de acuerdo con ellos, deberá abstenerse de utilizar el servicio.'
]

const TERMS_SECTIONS = [
  {
    title: '1. Descripción del servicio',
    blocks: [
      { type: 'p', text: 'AMALLU-IA es una solución tecnológica diseñada para ayudar a los usuarios a evaluar información mediante herramientas de análisis automatizado, procesamiento de lenguaje natural, inteligencia artificial y consulta de fuentes disponibles en internet.' },
      { type: 'p', text: 'Entre sus funciones pueden incluirse, de manera no exhaustiva:' },
      { type: 'ul', items: [
        'Análisis de contenido informativo.',
        'Contraste de información entre fuentes.',
        'Identificación de posibles inconsistencias, señales de desinformación o contenido cuestionable.',
        'Generación de resúmenes y contexto relacionado.',
        'Búsqueda de información asociada.',
        'Interacción mediante un asistente conversacional basado en inteligencia artificial.'
      ] },
      { type: 'p', text: 'El servicio tiene un carácter de apoyo a la comprensión informativa y no sustituye el criterio humano ni la valoración crítica del usuario.' }
    ]
  },
  {
    title: '2. Naturaleza de los resultados',
    blocks: [
      { type: 'p', text: 'Los resultados, análisis, recomendaciones, resúmenes, indicadores o respuestas generadas por AMALLU-IA tienen un carácter informativo, orientativo y de apoyo al análisis.' },
      { type: 'p', text: 'No deben entenderse como:' },
      { type: 'ul', items: [
        'Verificación definitiva de verdad o falsedad.',
        'Certificación de la autenticidad de una fuente.',
        'Garantía de exactitud absoluta.',
        'Sustituto del juicio crítico, la investigación periodística o la verificación documental.'
      ] },
      { type: 'p', text: 'Los resultados pueden verse afectados por:' },
      { type: 'ul', items: [
        'Limitaciones de las fuentes consultadas.',
        'Calidad, disponibilidad o actualización de la información.',
        'Error, sesgo o ambigüedad del contenido original.',
        'Faltantes de contexto o información incompleta.',
        'Restricciones técnicas del sistema.',
        'Limitaciones de los modelos de inteligencia artificial.',
        'Cambios posteriores en una noticia, publicación o fuente.'
      ] },
      { type: 'p', text: 'Por ello, el usuario debe verificar la información con fuentes primarias, confiables y actualizadas antes de asumirla como verdadera o actuar en consecuencia.' }
    ]
  },
  {
    title: '3. Inteligencia artificial y limitaciones',
    blocks: [
      { type: 'p', text: 'AMALLU-IA utiliza tecnologías de inteligencia artificial para procesar, interpretar y responder sobre información disponible en fuentes públicas y/o aportadas por el usuario.' },
      { type: 'p', text: 'Estas tecnologías pueden producir:' },
      { type: 'ul', items: [
        'Respuestas incompletas.',
        'Interpretaciones erróneas.',
        'Información desactualizada.',
        'Hallazgos no verificables.',
        'Errores de contexto o de análisis.'
      ] },
      { type: 'p', text: 'El usuario reconoce y acepta que la inteligencia artificial no es infalible y puede presentar sesgos, limitaciones técnicas o errores de razonamiento.' },
      { type: 'p', text: 'AMALLU-IA se esfuerza por mejorar la calidad de sus resultados mediante contraste de fuentes, análisis contextual y mecanismos de apoyo, pero no garantiza la exactitud absoluta ni la corrección de todos los resultados generados.' }
    ]
  },
  {
    title: '4. Fuentes de información y contenido externo',
    blocks: [
      { type: 'p', text: 'AMALLU-IA puede consultar, procesar, analizar o referenciar contenido proveniente de fuentes externas, incluyendo medios digitales, páginas web, APIs de terceros, documentos públicos o materiales disponibles en internet.' },
      { type: 'p', text: 'La presencia o mención de una fuente en la plataforma no implica que AMALLU-IA garantice, avale, respalde o certifique la totalidad de su contenido ni la veracidad de cada información que la fuente publique.' },
      { type: 'p', text: 'Las fuentes externas mantienen sus propios derechos, políticas de uso, condiciones de servicio y responsabilidades. AMALLU-IA no controla necesariamente el contenido, la actualización, la veracidad o la disponibilidad de dichas fuentes.' }
    ]
  },
  {
    title: '5. Uso responsable del servicio',
    blocks: [
      { type: 'p', text: 'El usuario se compromete a utilizar AMALLU-IA de manera responsable, ética y conforme a la legislación aplicable.' },
      { type: 'p', text: 'Queda prohibido utilizar el servicio para:' },
      { type: 'ul', items: [
        'Difundir, generar o apoyar deliberadamente información falsa o engañosa.',
        'Manipular resultados con fines de daño, odio, persecución o desinformación.',
        'Amenazar, acosar, difamar, injuriar o vulnerar derechos de terceros.',
        'Realizar actividades ilegales o contrarias a la normativa vigente.',
        'Obtener acceso no autorizado a sistemas, APIs, datos o servicios.',
        'Intentar vulnerar la seguridad, integridad o funcionamiento del aplicativo.',
        'Usar los resultados como única base para decisiones con consecuencias relevantes o de impacto significativo.',
        'Interferir con el rendimiento, estabilidad o disponibilidad del sistema.'
      ] },
      { type: 'p', text: 'AMALLU-IA puede restringir, suspender o cancelar el acceso de un usuario si detecta uso indebido, ilegal o incompatible con estos términos.' }
    ]
  },
  {
    title: '6. Contenido proporcionado por el usuario',
    blocks: [
      { type: 'p', text: 'El usuario puede introducir textos, enlaces, archivos, capturas, imágenes, videos u otros contenidos para su análisis.' },
      { type: 'p', text: 'Al hacerlo, el usuario declara que:' },
      { type: 'ul', items: [
        'Tiene derecho a aportar dicho contenido.',
        'Su uso para fines de análisis no infringe derechos de terceros.',
        'No comparte información privada o sensible sin la debida autorización.',
        'No utiliza el sistema para violar la privacidad de otras personas ni la normativa vigente.'
      ] },
      { type: 'p', text: 'El usuario es responsable del contenido que ingresa al sistema, así como de las consecuencias derivadas de su uso.' },
      { type: 'p', text: 'AMALLU-IA no será responsable por el contenido suministrado directamente por el usuario ni por los efectos que dicho contenido pueda generar en terceros.' }
    ]
  },
  {
    title: '7. Protección de datos y privacidad',
    blocks: [
      { type: 'p', text: 'AMALLU-IA reconoce la importancia de la protección de datos personales y la confidencialidad de la información tratada mediante la plataforma.' },
      { type: 'p', text: 'El servicio deberá operar conforme a la normativa aplicable en materia de protección de datos personales, así como a las políticas internas del proyecto.' },
      { type: 'p', text: 'Se recomienda al usuario:' },
      { type: 'ul', items: [
        'No ingresar información personal sensible innecesaria.',
        'No compartir datos de terceros sin consentimiento.',
        'No utilizar el sistema para procesar información confidencial de forma irresponsable.'
      ] },
      { type: 'p', text: 'Cuando corresponda, el proyecto podrá informar al usuario sobre la finalidad del tratamiento de datos, plazos, almacenamiento, uso interno y mecanismos disponibles para ejercer derechos previstos por la normativa aplicable.' }
    ]
  },
  {
    title: '8. Seguridad y disponibilidad',
    blocks: [
      { type: 'p', text: 'AMALLU-IA implementa medidas técnicas y operativas razonables para proteger la integridad, confidencialidad y disponibilidad del servicio. Sin embargo, ningún sistema conectado a internet puede garantizar una seguridad absoluta.' },
      { type: 'p', text: 'El equipo del proyecto no puede asegurar que el sistema esté libre de fallos, interrupciones, accesos no autorizados o errores técnicos.' },
      { type: 'p', text: 'Por ello, el sistema puede experimentar:' },
      { type: 'ul', items: [
        'Interrupciones temporales.',
        'Cambios de funcionamiento.',
        'Errores o inconsistencias.',
        'Despliegues de mejoras o correcciones.',
        'Fallas de servicios externos o dependencias de terceros.',
        'Problemas de conectividad o infraestructura.'
      ] },
      { type: 'p', text: 'AMALLU-IA puede modificar, suspender o retirar funcionalidades sin previo aviso, especialmente en fases de desarrollo, prueba o demostración.' }
    ]
  },
  {
    title: '9. Prototipo y naturaleza del proyecto',
    blocks: [
      { type: 'p', text: 'AMALLU-IA es un proyecto desarrollado dentro del marco del hackatón MediaHack de OpenLab y puede encontrarse en fase de prototipo, validación o mejora continua.' },
      { type: 'p', text: 'Por tanto, el servicio puede estar sujeto a cambios, experimentación, evolución técnica y ajustes funcionales.' },
      { type: 'p', text: 'La disponibilidad de una funcionalidad en una etapa concreta no garantiza que permanezca activa de manera indefinida ni que se mantenga en su versión actual.' }
    ]
  },
  {
    title: '10. Servicios de terceros y APIs',
    blocks: [
      { type: 'p', text: 'AMALLU-IA puede depender de herramientas, plataformas, APIs o servicios de terceros para funcionalidades de análisis, búsqueda, almacenamiento, autentificación, procesamiento de contenido o generación de respuestas.' },
      { type: 'p', text: 'El uso de dichos servicios está sujeto a sus propios términos, condiciones, políticas y restricciones, que el usuario acepta de manera indirecta al utilizar AMALLU-IA.' },
      { type: 'p', text: 'El proyecto no garantiza la continuidad, disponibilidad ni rendimiento de herramientas externas, ni asume responsabilidad por fallas, interrupciones o decisiones tomadas por terceros.' }
    ]
  },
  {
    title: '11. Propiedad intelectual',
    blocks: [
      { type: 'p', text: 'AMALLU-IA, su código, estructura, diseño, interfaz, marca, nombre, componentes desarrollados por el proyecto y su contenido original pertenecen a sus correspondientes titulares, conforme a la normativa aplicable.' },
      { type: 'p', text: 'Los contenidos generados por terceros, incluidos textos, imágenes, videos, publicaciones, noticias, materiales periodísticos y demás fuentes citadas o consultadas, son propiedad de sus autores o titulares de derechos respectivos.' },
      { type: 'p', text: 'AMALLU-IA no reclama propiedad sobre contenidos ajenos simplemente por referenciarlos, analizarlos o incluirlos en la plataforma, salvo que exista una expresión legal específica a favor del proyecto.' },
      { type: 'p', text: 'El usuario no deberá reproducir, distribuir, reutilizar ni explotar el contenido o la interfaz del servicio sin la autorización correspondiente.' }
    ]
  },
  {
    title: '12. Limitación de responsabilidad',
    blocks: [
      { type: 'p', text: 'En la máxima medida permitida por la ley, AMALLU-IA y sus desarrolladores, colaboradores o instituciones asociadas no serán responsables por:' },
      { type: 'ul', items: [
        'Daños directos, indirectos, incidentales, consecuentes o punitivos derivados del uso del servicio.',
        'Decisiones tomadas por el usuario sobre la base exclusiva de los resultados del sistema.',
        'Pérdidas, perjuicios o consecuencias provocadas por información inexacta, incompleta o engañosa.',
        'Fallas, errores, interrupciones o indisponibilidad del servicio.',
        'Uso indebido del sistema por terceros.',
        'Impactos derivados de contenidos o servicios de terceros.'
      ] },
      { type: 'p', text: 'El usuario reconoce que el uso del servicio es bajo su responsabilidad exclusiva y que debe aplicar criterio propio, verificaciones adicionales y juicio profesional cuando corresponda.' }
    ]
  },
  {
    title: '13. Exclusión de responsabilidad en decisiones de alto impacto',
    blocks: [
      { type: 'p', text: 'Los resultados generados por AMALLU-IA no deben utilizarse como única base para decisiones de alto impacto o consecuencias relevantes, tales como:' },
      { type: 'ul', items: [
        'Decisiones legales.',
        'Decisiones médicas.',
        'Decisiones financieras.',
        'Evaluaciones de empleo o contratación.',
        'Decisiones políticas o institucionales.',
        'Acciones de reputación o sanción.',
        'Cualquier decisión con efectos sustanciales para terceros.'
      ] },
      { type: 'p', text: 'El sistema es una herramienta de apoyo y no reemplaza la investigación humana, la valoración de expertos ni la verificación documental.' }
    ]
  },
  {
    title: '14. Modificaciones de los Términos',
    blocks: [
      { type: 'p', text: 'AMALLU-IA puede modificar estos Términos y Condiciones en cualquier momento para reflejar:' },
      { type: 'ul', items: [
        'Cambios funcionales del servicio.',
        'Ajustes técnicos o legales.',
        'Actualizaciones de políticas de privacidad o seguridad.',
        'Cambios en servicios de terceros.',
        'Mejora del funcionamiento del proyecto.'
      ] },
      { type: 'p', text: 'La versión vigente será la publicada dentro del aplicativo o en la plataforma donde se ofrezca el servicio. El uso continuado del servicio después de cambios implica la aceptación de los nuevos términos.' }
    ]
  },
  {
    title: '15. Terminación del acceso',
    blocks: [
      { type: 'p', text: 'AMALLU-IA puede, a su criterio, suspender o cancelar el acceso del usuario cuando se detecten:' },
      { type: 'ul', items: [
        'Incumplimiento de estos Términos.',
        'Uso indebido o malicioso del servicio.',
        'Violación de la normativa aplicable.',
        'Riesgo para la integridad, seguridad o continuidad del proyecto.'
      ] },
      { type: 'p', text: 'El usuario podrá dejar de usar el servicio en cualquier momento.' }
    ]
  },
  {
    title: '16. Ley aplicable y jurisdicción',
    blocks: [
      { type: 'p', text: 'Estos Términos y Condiciones se rigen por la legislación aplicable en Ecuador, sin perjuicio de la normativa internacional o sectorial que pueda resultar aplicable en función del uso o de la ubicación del usuario y del proyecto.' },
      { type: 'p', text: 'En caso de disputa, las partes podrán intentar una solución amistosa antes de recurrir a mecanismos jurisdiccionales.' }
    ]
  },
  {
    title: '17. Aceptación',
    blocks: [
      { type: 'p', text: 'Al aceptar estos Términos y Condiciones, al continuar utilizando AMALLU-IA o al acceder a sus funcionalidades, el usuario declara haber leído, entendido y aceptado todas las disposiciones aquí establecidas.' },
      { type: 'p', text: 'Si el usuario no acepta estos términos, debe abstenerse de utilizar el servicio.' }
    ]
  },
  {
    title: '18. Contacto',
    blocks: [
      { type: 'p', text: 'Para consultas, sugerencias, reportes o comentarios sobre el uso del servicio, el usuario puede contactarse con el equipo del proyecto a través de los canales habilitados por MediaHack — OpenLab.' }
    ]
  }
]

const TERMS_CLOSING = []

function App() {
  const [termsAccepted, setTermsAccepted] = useState(() => {
    try {
      return localStorage.getItem(TERMS_STORAGE_KEY) === TERMS_VERSION
    } catch {
      return false
    }
  })
  const [termsExpanded, setTermsExpanded] = useState(false)
  const [termsChecked, setTermsChecked] = useState(false)

  const handleAcceptTerms = () => {
    try {
      localStorage.setItem(TERMS_STORAGE_KEY, TERMS_VERSION)
    } catch {
      // localStorage no disponible (modo privado, cuota llena, etc.) - se volvera a pedir la proxima vez
    }
    setTermsAccepted(true)
  }

  const [activeView, setActiveView] = useState('home')
  const [activeTab, setActiveTab] = useState('link')
  const [chatOpen, setChatOpen] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [urlValue, setUrlValue] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [error, setError] = useState(null)
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hola. Soy Kuybot, tu asistente de investigación periodística. Analiza una noticia y puedo ayudarte a contrastarla con contexto y fuentes.' }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [kuybotBusy, setKuybotBusy] = useState(false)
  const chatEndRef = useRef(null)
  const fileInputRef = useRef(null)
  const pollingRef = useRef(null)

  const HISTORY_KEY = 'ama_llu_ia_history'
  const [history, setHistory] = useState(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(HISTORY_KEY))
      return Array.isArray(stored) ? stored : []
    } catch {
      return []
    }
  })

  const persistHistory = (list) => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(list))
    } catch {
      try {
        // Sin espacio para el detalle completo: guardamos solo el resumen de cada analisis
        const lightweight = list.map(({ detail, ...rest }) => rest)
        localStorage.setItem(HISTORY_KEY, JSON.stringify(lightweight))
      } catch {
        // localStorage no disponible (modo privado, cuota llena, etc.) - no bloquea el analisis
      }
    }
  }

  const addHistoryEntry = (entry) => {
    setHistory(prev => {
      const updated = [entry, ...prev].slice(0, 50)
      persistHistory(updated)
      return updated
    })
  }

  // Actualiza en su lugar una entrada ya guardada (usado cuando el analisis de una
  // noticia sigue en 'processing' y luego termina con el valor final real).
  const updateHistoryEntry = (id, patch) => {
    setHistory(prev => {
      const updated = prev.map(h => (h.id === id ? { ...h, ...patch } : h))
      persistHistory(updated)
      return updated
    })
  }

  const [expandedHistoryIds, setExpandedHistoryIds] = useState(() => new Set())
  const toggleHistoryExpanded = (id) => {
    setExpandedHistoryIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  // Abre a Kuybot con una pregunta ya enfocada en el analisis guardado en Auditoria.
  const handleAskKuybot = (item) => {
    setInputMessage(`Cuéntame más sobre el análisis de: "${item.title}"`)
    setChatOpen(true)
  }

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => () => {
    if (pollingRef.current) clearInterval(pollingRef.current)
  }, [])

  const criterios = [
    { title: 'Verificación de la fuente', desc: 'Coincidencia con medios Radar, registro interno o redes de verificación (IFCN)' },
    { title: 'Confiabilidad técnica del URL', desc: 'HTTPS, redirecciones y accesibilidad del dominio' },
    { title: 'Calidad y estructura del contenido', desc: 'Autoría, fecha, fuentes citadas y coherencia del texto' },
    { title: 'Señales de manipulación y sesgo', desc: 'Clickbait, sesgo editorial y señales de manipulación detectadas' },
    { title: 'Cruce con cobertura relacionada', desc: 'Fuentes independientes y medios Radar que cubren la misma noticia' }
  ]

  // Estadisticas reales derivadas del historial (nada de datos ficticios)
  const totalAnalyzed = history.length
  const statusCounts = { verificado: 0, dudoso: 0, falso: 0 }
  history.forEach(h => { if (statusCounts[h.status] !== undefined) statusCounts[h.status]++ })
  const chartData = totalAnalyzed > 0 ? [
    { name: 'Verificado', value: Math.round((statusCounts.verificado / totalAnalyzed) * 100), color: '#00C896' },
    { name: 'Dudoso', value: Math.round((statusCounts.dudoso / totalAnalyzed) * 100), color: '#E8A33D' },
    { name: 'Falso', value: Math.round((statusCounts.falso / totalAnalyzed) * 100), color: '#E85D5D' }
  ] : []
  const recentHistory = history.slice(0, 5)

  const kuybotSuggestions = [
    '¿Esta información ha sido verificada?',
    '¿Qué fuentes respaldan esta noticia?',
    '¿Qué fuentes contradicen esta información?',
    '¿Qué dicen las fuentes oficiales?',
    '¿Existen verificaciones relacionadas?',
    '¿Qué ocurrió realmente?'
  ]

  const adaptNewsAnalysisResult = (result) => {
    const score = (result.news_reliability_assessment?.score ?? result.analysis?.credibility?.score ?? 0) / 100
    const related = result.related_news || []
    const sourceName = result.source_verification?.source_name || result.content_attribution?.publisher_name || result.article?.source_domain
    return {
      module: 'noticias',
      raw_news: result,
      is_ai_generated: false,
      is_misinformation: result.risk_assessment?.level === 'alto' || result.risk_assessment?.level === 'critico',
      confidence: Math.max(0, Math.min(1, score)),
      processing_time: null,
      metadata: {
        format: 'URL noticia',
        duration: null,
        source_metadata: {
          title: result.article?.title || result.analysis?.topic || 'Noticia analizada',
          channel: sourceName || 'Sin fuente',
          platform: result.editorial_metadata?.platform || 'sitio_web',
          source_url: result.source_input?.final_url || result.source_input?.original_url,
          upload_date: result.editorial_metadata?.publication_date,
          is_verified: ['radar_media', 'registered_media', 'ifcn_verified'].includes(result.source_verification?.status),
          view_count: 0,
          duration: 0,
        }
      },
      content_analysis: {
        has_transcription: false,
        transcription: {
          text: result.analysis?.summary || '',
          segments: [],
          segment_verifications: [],
        },
        fact_checking: {
          fact_checks_found: related.length,
          fact_checks: related.map(item => ({
            title: item.title,
            publisher: item.source_name || item.source || 'Fuente',
            rating: item.source_registry_status || 'relacionada',
          })),
        },
      },
    }
  }

  const truncateText = (text, max = 500) => {
    if (!text) return ''
    return text.length > max ? `${text.slice(0, max)}…` : text
  }

  // Extrae del resultado completo del Back solo lo necesario para mostrar el
  // detalle del analisis en Auditoria, evitando guardar textos muy largos (articulo completo, etc.)
  const buildNewsHistoryDetail = (raw) => ({
    kind: 'news',
    reliability: raw.news_reliability_assessment || null,
    sourceVerification: raw.source_verification || null,
    sourceClassification: raw.source_classification ? {
      communication_type: raw.source_classification.communication_type,
      is_radar_media: raw.source_classification.is_radar_media,
      explanation: raw.source_classification.explanation
    } : null,
    urlTrust: raw.url_trust_assessment || null,
    contentClassification: raw.url_content_classification ? {
      content_kind: raw.url_content_classification.content_kind,
      is_news: raw.url_content_classification.is_news
    } : null,
    informationRelevance: raw.information_relevance ? {
      domain: raw.information_relevance.domain,
      is_relevant: raw.information_relevance.is_relevant,
      how_it_relates: truncateText(raw.information_relevance.how_it_relates, 200)
    } : null,
    llmExecution: raw.llm_execution ? {
      provider: raw.llm_execution.provider,
      status: raw.llm_execution.status
    } : null,
    contentQuality: raw.content_quality || null,
    analysis: raw.analysis ? {
      summary: truncateText(raw.analysis.summary, 500),
      topic: raw.analysis.topic,
      category: raw.analysis.category,
      sentiment: raw.analysis.sentiment,
      bias_analysis: raw.analysis.bias_analysis,
      clickbait: raw.analysis.clickbait,
      credibility: raw.analysis.credibility,
      manipulation_signals: raw.analysis.manipulation_signals || [],
      recommendation: raw.analysis.recommendation,
      main_claims: (raw.analysis.main_claims || []).slice(0, 6),
      missing_context: raw.analysis.missing_context || []
    } : null,
    crossSource: raw.cross_source_check || null,
    genderImpact: raw.gender_impact_assessment ? {
      status_label: raw.gender_impact_assessment.status_label,
      score: raw.gender_impact_assessment.score,
      explanation: raw.gender_impact_assessment.explanation,
      signals: (raw.gender_impact_assessment.signals || []).map(s => ({ label: s.label, severity: s.severity }))
    } : null,
    relatedNews: (raw.related_news || []).slice(0, 6).map(r => ({
      title: r.title,
      url: r.url,
      source_name: r.source_name || r.source,
      relation_label: r.relation_label
    })),
    claimContrasts: (raw.claim_contrasts || []).slice(0, 6).map(c => ({
      claim: truncateText(c.claim, 200),
      status_label: c.status_label,
      explanation: truncateText(c.explanation, 200),
      sources_consulted: (c.sources_consulted || []).slice(0, 3),
      evidence_url: c.evidence_url || null
    })),
    informationGaps: (raw.analysis?.information_gaps || []).slice(0, 5).map(g => ({
      missing_item: g.missing_item,
      why_it_matters: truncateText(g.why_it_matters, 200),
      suggested_verification: truncateText(g.suggested_verification, 200),
      priority: g.priority
    })),
    audit: raw.audit ? {
      priority: raw.audit.priority,
      evidence_summary: raw.audit.evidence_summary,
      evidence_items: (raw.audit.evidence_items || []).slice(0, 14).map(e => ({
        type: e.type,
        label: e.label,
        value: truncateText(e.value, 160),
        severity: e.severity
      })),
      reviewRecommendations: (
        (raw.audit.presentation_blocks || []).find(b => b.title === 'Recomendaciones para revisar')?.items || []
      ).slice(0, 6)
    } : null,
    article: raw.article ? {
      title: raw.article.title,
      author: raw.article.author,
      published_at: raw.article.published_at,
      source_domain: raw.article.source_domain
    } : null
  })

  const buildMediaHistoryDetail = (raw) => ({
    kind: 'media',
    is_ai_generated: raw.is_ai_generated,
    is_manipulated: raw.is_manipulated,
    is_misinformation: raw.is_misinformation,
    confidence: raw.confidence,
    analysis_type: raw.analysis_type,
    audioDetails: raw.audio_details || null,
    videoDetails: raw.video_details || null,
    metadata: raw.metadata || null,
    processingTime: raw.processing_time,
    contentAnalysis: raw.content_analysis ? {
      fakeNews: raw.content_analysis.fake_news || null,
      factChecking: raw.content_analysis.fact_checking ? {
        fact_checks_found: raw.content_analysis.fact_checking.fact_checks_found,
        fact_checks: (raw.content_analysis.fact_checking.fact_checks || []).slice(0, 5)
      } : null,
      extractedClaims: (raw.content_analysis.extracted_claims || []).slice(0, 6),
      llmAnalysis: raw.content_analysis.llm_analysis || null,
      transcriptionExcerpt: truncateText(raw.content_analysis.transcription?.text, 500)
    } : null
  })

  // Arma los campos guardables del historial a partir de un resultado ya adaptado.
  // `pending` marca que el analisis de noticia todavia sigue procesandose en el Back
  // y que el porcentaje/detalle mostrado es provisional (se reemplaza al terminar).
  const buildHistoryPayload = (type, sourceValue, result, pending = false) => {
    const status = (result.is_ai_generated || result.is_misinformation)
      ? 'falso'
      : (result.confidence < 0.6 ? 'dudoso' : 'verificado')
    const sourceTitle = result.metadata?.source_metadata?.title
    const title = sourceTitle || (type === 'link' ? sourceValue : (selectedFile?.name || videoUrl)) || 'Contenido analizado'
    const detail = type === 'link'
      ? buildNewsHistoryDetail(result.raw_news || {})
      : buildMediaHistoryDetail(result || {})
    return {
      type,
      title,
      source: type === 'link' ? sourceValue : (videoUrl || selectedFile?.name || ''),
      status,
      confidence: typeof result.confidence === 'number' ? result.confidence : null,
      detail,
      pending
    }
  }

  const pollNewsAnalysis = (analysisId, sourceUrl, historyEntryId) => {
    if (pollingRef.current) clearInterval(pollingRef.current)
    let attempts = 0
    pollingRef.current = setInterval(async () => {
      attempts += 1
      try {
        const updated = await getNewsAnalysis(analysisId)
        const adapted = adaptNewsAnalysisResult(updated)
        setAnalysisResult(adapted)
        const stillProcessing = updated.status === 'processing'
        if (!stillProcessing && historyEntryId) {
          // El analisis ya termino en el Back: reemplazamos el valor provisional
          // guardado al enviar la noticia por el resultado final real.
          updateHistoryEntry(historyEntryId, buildHistoryPayload('link', sourceUrl, adapted, false))
        }
        if (!stillProcessing || attempts >= 20) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
      } catch {
        if (attempts >= 3) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
      }
    }, 2500)
  }

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setError(null)
    setAnalysisResult(null)
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }

    try {
      if (activeTab === 'link' && urlValue) {
        const newsResponse = await analyzeNewsUrl(urlValue)
        const result = adaptNewsAnalysisResult(newsResponse)
        setAnalysisResult(result)

        // Se guarda de inmediato para que aparezca en Auditoria apenas se envia la
        // noticia; si el Back todavia la esta procesando, se marca como "pending" y
        // se actualiza en su lugar con el valor final cuando termine el analisis.
        const pending = newsResponse.status === 'processing'
        const historyEntryId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
        addHistoryEntry({
          id: historyEntryId,
          timestamp: new Date().toISOString(),
          ...buildHistoryPayload('link', urlValue, result, pending)
        })
        if (pending) pollNewsAnalysis(newsResponse.id, urlValue, historyEntryId)
        return
      }

      let result
      if (activeTab === 'video' && selectedFile) {
        const fileType = selectedFile.type
        if (fileType.startsWith('audio/')) {
          result = await analyzeAudio(selectedFile)
        } else if (fileType.startsWith('video/')) {
          result = await analyzeVideo(selectedFile)
        } else {
          throw new Error('Tipo de archivo no soportado. Usa archivos de audio o video.')
        }
      } else if (activeTab === 'video' && videoUrl) {
        // Usar videoUrl si no hay archivo seleccionado
        result = await analyzeMediaUrl(videoUrl)
      } else {
        throw new Error('Por favor ingresa una URL o selecciona un archivo')
      }

      setAnalysisResult(result)
      addHistoryEntry({
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        timestamp: new Date().toISOString(),
        ...buildHistoryPayload(activeTab, videoUrl || selectedFile?.name, result, false)
      })
    } catch (err) {
      setError(err.message || 'Error al procesar el análisis')
      console.error('Error al analizar:', err)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
    }
  }

  const currentNewsPayload = analysisResult?.raw_news || null
  const currentNewsContext = currentNewsPayload ? {
    title: currentNewsPayload.article?.title || currentNewsPayload.analysis?.topic || 'Noticia analizada',
    summary: currentNewsPayload.analysis?.summary || currentNewsPayload.article?.description || 'Sin resumen disponible.',
    platform: currentNewsPayload.editorial_metadata?.platform || 'sitio web',
    publisher: currentNewsPayload.content_attribution?.publisher_name || currentNewsPayload.source_verification?.source_name || currentNewsPayload.article?.source_domain || 'Sin fuente',
    publicationDate: currentNewsPayload.editorial_metadata?.publication_date || currentNewsPayload.article?.published_at || 'Sin fecha detectada',
    relatedSources: (currentNewsPayload.related_news || []).slice(0, 4).map(item => ({
      name: item.source_name || item.source || 'Fuente relacionada',
      url: item.url
    })).filter(item => item.url)
  } : null

  const handleSendMessage = async () => {
    const trimmed = inputMessage.trim()
    if (!trimmed || kuybotBusy) return

    const chatHistory = messages.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'assistant',
      content: msg.text || '',
      text: msg.text || '',
      sources: Array.isArray(msg.sources) ? msg.sources : [],
      created_at: new Date().toISOString()
    }))

    setMessages(prev => [...prev, { role: 'user', text: trimmed, sources: [] }])
    setInputMessage('')
    setKuybotBusy(true)

    try {
      const response = await askKuybot({
        question: trimmed,
        news: currentNewsPayload,
        history: chatHistory,
      })

      setMessages(prev => [...prev, {
        role: 'bot',
        text: response?.answer || 'No recibí una respuesta útil de Kuybot.',
        sources: Array.isArray(response?.sources) ? response.sources.filter(Boolean) : []
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: `No pude completar la consulta. ${err?.message || 'Revisa la conexión con el backend de Noticias.'}`,
        sources: []
      }])
    } finally {
      setKuybotBusy(false)
    }
  }

  const tabs = [
    { id: 'link', label: 'Link Noticia', icon: LinkIcon },
    { id: 'video', label: 'Video/Audio', icon: Upload },
    { id: 'auditor', label: 'Auditor', icon: ClipboardList }
  ]

  const scanColor = analyzing ? '#E8A33D' : '#00C896'

  const getStatusColor = (status) => {
    if (status === 'verificado') return '#00C896'
    if (status === 'dudoso') return '#E8A33D'
    return '#E85D5D'
  }

  const getStatusIcon = (status) => {
    if (status === 'verificado') return CheckCircle2
    if (status === 'dudoso') return AlertTriangle
    return XCircle
  }

  const NewsResultPanel = ({ result }) => {
    if (!result) return null

    const score = result.news_reliability_assessment?.score ?? result.analysis?.credibility?.score ?? 0
    const article = result.article || {}
    const editorial = result.editorial_metadata || {}
    const source = result.source_verification || {}
    const urlCheck = result.url_verification || {}
    const gender = result.gender_impact_assessment || {}
    const related = result.related_news || []
    const keywords = result.analysis?.keywords || article.keywords || []
    const reviewBlock = (result.audit?.presentation_blocks || []).find(block => block.title === 'Recomendaciones para revisar')
    const summary = result.analysis?.summary || article.description || 'Sin resumen disponible.'
    const isElectoral = Boolean(result.electoral_relevance?.is_electoral || result.analysis?.is_electoral)
    const safeScore = Math.max(0, Math.min(100, Number(score) || 0))
    const confidenceData = [
      { name: 'Confiabilidad', value: safeScore, color: safeScore >= 80 ? '#00C896' : safeScore >= 60 ? '#E8A33D' : '#E85D5D' },
      { name: 'Pendiente', value: Math.max(0, 100 - safeScore), color: '#E9ECEF' },
    ]
    const sourceLabel = source.source_name || editorial.publisher_name || article.source_domain || 'Sin fuente'
    const publisherType = editorial.publisher_type || source.source_type || 'sin clasificar'
    const contentType = result.content_classification?.type || urlCheck.content_type || 'sin dato'
    const genderState = gender.status || gender.level || 'sin dato'
    const llm = result.llm_execution || {}
    const llmStatus = llm.status === 'used' ? 'LLM usado' : llm.status === 'fallback' ? 'Fallback local' : 'IA no usada'
    const humanContentType = contentType === 'noticia' ? 'Noticia' : contentType === 'social_post' ? 'Publicacion social' : 'Contenido por revisar'
    const humanPublisherType = publisherType === 'medio_comunicacion' ? 'Medio de comunicacion' : publisherType === 'usuario_cuenta_personal' ? 'Cuenta personal' : publisherType.replaceAll('_', ' ')
    const humanSourceStatus = source.status === 'radar_media' ? 'Medio en radar' : source.status === 'registered_media' ? 'Medio registrado' : source.status === 'ifcn_verified' ? 'Verificador IFCN' : 'Fuente sin registro'
    const humanGenderState = genderState === 'sin_senales_relevantes' ? 'Sin senales relevantes' : genderState === 'senales_para_revision' ? 'Senales para revision' : genderState === 'alerta_impacto_genero' ? 'Alerta de impacto de genero' : 'Sin dato'
    const rawPublicationDate = editorial.publication_date || article.published_at
    const dateLabel = rawPublicationDate
      ? new Intl.DateTimeFormat('es-EC', {
          dateStyle: 'medium',
          timeStyle: 'short',
          timeZone: 'America/Guayaquil',
        }).format(new Date(rawPublicationDate))
      : 'Fecha de la noticia no detectada'
    const isUpdatingRelated = result.status === 'processing'
    const confidenceCaption = isUpdatingRelated
      ? 'Actualizando con cobertura relacionada'
      : related.length > 0
        ? 'Calculada con fuente, URL y contraste'
        : 'Calculada con fuente y contenido disponible'
    const renderActionItem = (item) => {
      if (typeof item === 'string') {
        return { title: item, detail: null, reason: null, priority: null }
      }
      if (!item || typeof item !== 'object') {
        return { title: String(item), detail: null, reason: null, priority: null }
      }
      return {
        title: item.title || item.missing_item || item.label || 'Informacion por revisar',
        detail: item.action || item.suggested_verification || item.description || item.value || item.recommendation || null,
        reason: item.reason || item.why_it_matters || null,
        priority: item.priority || item.severity || null,
      }
    }
    const actionItems = Array.isArray(reviewBlock?.items) ? reviewBlock.items : []

    return (
      <div className="mt-6 rounded-xl border overflow-hidden" style={{ backgroundColor: '#FFFFFF', borderColor: '#E9ECEF' }}>
        <div className="grid lg:grid-cols-[1.55fr_0.45fr]">
          <section className="p-5 md:p-6 space-y-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs px-2.5 py-1 rounded-full font-semibold" style={{ backgroundColor: '#F5822B18', color: BRAND_ORANGE }}>
                  {humanContentType}
                </span>
                <span className="text-xs px-2.5 py-1 rounded-full font-semibold" style={{ backgroundColor: isElectoral ? '#00C89618' : '#E9ECEF', color: isElectoral ? '#008F6A' : '#6B7280' }}>
                  {isElectoral ? 'Electoral' : 'No electoral'}
                </span>
                {isUpdatingRelated && (
                  <span className="text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1" style={{ backgroundColor: '#3B82F618', color: '#2563EB' }}>
                    <Activity className="w-3 h-3 animate-spin" />
                    Consultando relacionadas
                  </span>
                )}
              </div>
              <h3 className="text-xl md:text-2xl font-bold leading-tight" style={{ color: BRAND_NAVY }}>
                {article.title || result.analysis?.topic || 'Resultado del analisis'}
              </h3>
              <p className="text-sm leading-relaxed text-gray-700">{summary}</p>
            </div>

            <div className="grid md:grid-cols-3 gap-3 rounded-lg p-3" style={{ backgroundColor: '#F8F9FA' }}>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-gray-500">Fuente</p>
                <p className="text-sm font-semibold text-gray-900 mt-1">{sourceLabel}</p>
                <p className="text-xs text-gray-600">{humanPublisherType}</p>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-gray-500">Fecha de la noticia</p>
                <p className="text-sm font-semibold text-gray-900 mt-1">{dateLabel}</p>
                <p className="text-xs text-gray-600">{editorial.platform === 'sitio_web' ? 'Sitio web' : editorial.platform || 'Sitio web'}</p>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-gray-500">Registro</p>
                <p className="text-sm font-semibold text-gray-900 mt-1">{humanSourceStatus}</p>
                <p className="text-xs text-gray-600">{urlCheck.final_domain || article.source_domain || 'Dominio no detectado'}</p>
              </div>
            </div>

            {keywords.length > 0 && (
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-gray-500 mb-2">Palabras clave</p>
                <div className="flex flex-wrap gap-2">
                  {keywords.slice(0, 12).map((keyword, idx) => (
                    <span key={`${keyword}-${idx}`} className="text-xs px-2.5 py-1 rounded-full" style={{ backgroundColor: '#F8F9FA', color: '#374151', border: '1px solid #E9ECEF' }}>
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-lg p-4" style={{ backgroundColor: '#F8F9FA' }}>
              <div className="flex items-center gap-2 mb-3">
                <Info className="w-4 h-4" style={{ color: BRAND_ORANGE }} />
                <h4 className="text-sm font-bold text-gray-900">Recomendaciones para revisar</h4>
              </div>
              {actionItems.length > 0 ? (
                <ul className="space-y-2">
                  {actionItems.map((item, idx) => {
                    const formatted = renderActionItem(item)
                    return (
                      <li key={idx} className="flex gap-2 text-sm text-gray-700">
                        <span className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: BRAND_ORANGE }} />
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-gray-900">{formatted.title}</span>
                            {formatted.priority && (
                              <span className="text-[11px] px-1.5 py-0.5 rounded uppercase tracking-wide" style={{ backgroundColor: '#F5822B18', color: BRAND_ORANGE }}>
                                Prioridad {formatted.priority}
                              </span>
                            )}
                          </div>
                          {formatted.detail && <p className="mt-1 text-gray-700">{formatted.detail}</p>}
                          {formatted.reason && <p className="mt-1 text-xs text-gray-500">{formatted.reason}</p>}
                        </div>
                      </li>
                    )
                  })}
                </ul>
              ) : (
                <p className="text-sm text-gray-700">No se detectaron recomendaciones especificas para esta noticia con la informacion disponible.</p>
              )}
            </div>

            <div>
              <div className="flex items-center justify-between gap-3 mb-3">
                <h4 className="text-sm font-bold text-gray-900">Noticias relacionadas</h4>
                <span className="text-xs px-2 py-1 rounded-full" style={{ backgroundColor: '#16234E10', color: BRAND_NAVY }}>
                  {isUpdatingRelated ? 'Consultando base de datos' : `${related.length} encontradas`}
                </span>
              </div>
              {isUpdatingRelated && (
                <div className="rounded-lg border p-3 mb-3 flex items-start gap-2" style={{ backgroundColor: '#EFF6FF', borderColor: '#BFDBFE' }}>
                  <Activity className="w-4 h-4 animate-spin mt-0.5 flex-shrink-0" style={{ color: '#2563EB' }} />
                  <p className="text-xs leading-relaxed" style={{ color: '#1D4ED8' }}>
                    Consultando en la base de datos y contrastando fuentes relacionadas. La confiabilidad puede actualizarse cuando aparezcan coincidencias relevantes.
                  </p>
                </div>
              )}
              {related.length > 0 ? (
                <div className="space-y-2">
                  {related.slice(0, 5).map((item, idx) => (
                    <a
                      key={`${item.url || item.title}-${idx}`}
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="block rounded-lg border p-3 transition-colors hover:bg-gray-50"
                      style={{ borderColor: '#E9ECEF' }}
                    >
                      <p className="text-sm font-semibold text-gray-900">{item.title}</p>
                      <div className="mt-1 flex flex-wrap gap-2 text-xs text-gray-600">
                        <span>{item.source_name || item.source || 'Fuente'}</span>
                        {item.relation_score != null && (
                          <span>Relacion {item.relation_score}%</span>
                        )}
                        {(item.source_veracity_score ?? item.source_confidence_score ?? item.confidence) != null && (
                          <span>Medio {item.source_veracity_score ?? item.source_confidence_score ?? item.confidence}%</span>
                        )}
                        <span>{item.source_type === 'medio_radar' ? 'Medio en radar' : item.source_type === 'medio_no_radar' ? 'Medio registrado' : item.source_category || 'Otra fuente'}</span>
                      </div>
                      {item.relation_label && (
                        <p className="mt-2 text-xs text-gray-500">Relacion con la noticia principal: {item.relation_label}.</p>
                      )}
                    </a>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-600">No se encontraron coberturas relacionadas para este contexto.</p>
              )}
            </div>

            <button
              type="button"
              onClick={() => setActiveTab('auditor')}
              className="w-full px-4 py-3 rounded-lg font-semibold text-sm flex items-center justify-center gap-2"
              style={{ backgroundColor: BRAND_NAVY, color: '#FFFFFF' }}
            >
              Ir a auditoria
              <ArrowRight className="w-4 h-4" />
            </button>
          </section>

          <aside className="p-5 md:p-6 border-t lg:border-t-0 lg:border-l space-y-5" style={{ borderColor: '#E9ECEF', backgroundColor: '#F8F9FA' }}>
            <div className="h-44 relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={confidenceData} dataKey="value" innerRadius={48} outerRadius={68} startAngle={90} endAngle={450}>
                    {confidenceData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <div className="text-3xl font-bold font-mono" style={{ color: safeScore >= 80 ? '#00C896' : safeScore >= 60 ? '#E8A33D' : '#E85D5D' }}>{safeScore}%</div>
                <div className="text-xs text-gray-500">Confiabilidad</div>
              </div>
            </div>
            <p className="text-xs leading-relaxed text-center text-gray-600 -mt-2">{confidenceCaption}</p>

            <div className="space-y-3">
              <div className="rounded-lg bg-white border p-3" style={{ borderColor: '#E9ECEF' }}>
                <p className="text-xs text-gray-500">Fuente</p>
                <p className="text-sm font-semibold text-gray-900">{humanSourceStatus}</p>
              </div>
              <div className="rounded-lg bg-white border p-3" style={{ borderColor: '#E9ECEF' }}>
                <p className="text-xs text-gray-500">Impacto de genero</p>
                <p className="text-sm font-semibold text-gray-900">{humanGenderState}</p>
                {Array.isArray(gender.signals) && gender.signals.length > 0 && (
                  <p className="text-xs text-gray-600 mt-1">{gender.signals.slice(0, 3).join(', ')}</p>
                )}
              </div>
              <div className="rounded-lg bg-white border p-3" style={{ borderColor: '#E9ECEF' }}>
                <p className="text-xs text-gray-500">Analisis IA</p>
                <p className="text-sm font-semibold text-gray-900">{llm.status === 'used' ? 'Analisis aplicado' : llmStatus}</p>
                <p className="text-xs text-gray-600 mt-1">Las recomendaciones de revision estan en el panel principal.</p>
              </div>
            </div>
          </aside>
        </div>
      </div>
    )
  }

  const detailCardStyle = { backgroundColor: '#0B1430', border: '1px solid #1C2A52' }
  const detailLabelStyle = { color: '#E8ECF1' }
  const detailMutedStyle = { color: '#7A8290' }

  const CONTENT_KIND_LABELS = {
    noticia: 'Noticia',
    publicacion_red_social: 'Publicación social',
    video_audio: 'Video / audio',
    otro: 'Otro contenido',
    indeterminado: 'Contenido por revisar'
  }

  const renderNewsHistoryDetail = (d) => {
    const score = d.reliability?.score ?? null
    const donutColor = score == null ? '#7A8290' : score >= 80 ? '#00C896' : score >= 60 ? '#E8A33D' : '#E85D5D'
    const donutData = score == null ? [] : [
      { name: 'Confiabilidad', value: score, color: donutColor },
      { name: 'Pendiente', value: Math.max(0, 100 - score), color: '#1C2A52' }
    ]
    const contentKindLabel = CONTENT_KIND_LABELS[d.contentClassification?.content_kind] || 'Contenido por revisar'
    const domain = d.informationRelevance?.domain
    const domainLabel = domain === 'electoral' ? 'Electoral' : domain === 'no_electoral' ? 'No electoral' : 'Relevancia indeterminada'
    const domainColor = domain === 'electoral' ? '#00C896' : '#7A8290'
    const llmStatus = d.llmExecution?.status
    const llmLabel = llmStatus === 'used' ? 'Análisis IA aplicado' : llmStatus === 'fallback' ? 'Fallback local' : llmStatus === 'failed' ? 'IA con error' : llmStatus === 'disabled' ? 'IA no usada' : 'Sin dato'

    return (
    <div className="mt-3 pt-3 space-y-2" style={{ borderTop: '1px solid #1C2A52' }}>
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs px-2.5 py-1 rounded-full font-semibold" style={{ backgroundColor: BRAND_ORANGE + '22', color: BRAND_ORANGE }}>
          {contentKindLabel}
        </span>
        <span className="text-xs px-2.5 py-1 rounded-full font-semibold" style={{ backgroundColor: domainColor + '22', color: domainColor }}>
          {domainLabel}
        </span>
      </div>

      {d.reliability && (
        <div className="rounded-lg p-4" style={detailCardStyle}>
          <div className="flex items-center gap-4">
            <div className="w-24 h-24 relative flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={donutData} dataKey="value" innerRadius={30} outerRadius={44} startAngle={90} endAngle={450}>
                    {donutData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-lg font-bold font-mono" style={{ color: donutColor }}>{score}%</span>
              </div>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold" style={detailLabelStyle}>Confiabilidad</span>
                <span className="text-xs font-mono capitalize" style={{ color: donutColor }}>{d.reliability.level}</span>
              </div>
              <p className="text-xs mt-1 leading-relaxed" style={detailMutedStyle}>{d.reliability.explanation}</p>
            </div>
          </div>
          {d.reliability.factors?.length > 0 && (
            <div className="mt-3 pt-3" style={{ borderTop: '1px solid #1C2A52' }}>
              <span className="text-xs font-semibold" style={detailLabelStyle}>¿Por qué este porcentaje?</span>
              <ul className="mt-1.5 space-y-0.5">
                {d.reliability.factors.map((f, i) => (
                  <li key={i} className="text-xs" style={detailMutedStyle}>· {f}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs" style={detailMutedStyle}>Fuente</span>
          <p className="text-sm font-semibold mt-0.5 truncate" style={detailLabelStyle}>{d.sourceVerification?.source_name || d.article?.source_domain || 'Sin fuente'}</p>
        </div>
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs" style={detailMutedStyle}>Impacto de género</span>
          <p className="text-sm font-semibold mt-0.5 truncate" style={detailLabelStyle}>{d.genderImpact?.status_label || 'Sin señales relevantes'}</p>
        </div>
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs" style={detailMutedStyle}>Análisis IA</span>
          <p className="text-sm font-semibold mt-0.5 truncate" style={detailLabelStyle}>{llmLabel}</p>
        </div>
      </div>

      {d.sourceVerification && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Fuente</span>
          <p className="text-xs mt-1" style={detailMutedStyle}>
            Estado: <span style={detailLabelStyle}>{d.sourceVerification.status}</span>
            {d.sourceVerification.source_name && <> · {d.sourceVerification.source_name}</>}
          </p>
          {d.sourceVerification.recommendation && (
            <p className="text-xs mt-1 leading-relaxed" style={detailMutedStyle}>{d.sourceVerification.recommendation}</p>
          )}
        </div>
      )}

      {d.contentQuality && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold" style={detailLabelStyle}>Calidad del contenido</span>
            <span className="text-xs font-mono font-bold" style={{ color: BRAND_ORANGE }}>{d.contentQuality.quality_score}/100</span>
          </div>
          <p className="text-xs" style={detailMutedStyle}>
            Autor: {d.contentQuality.has_author ? 'Sí' : 'No'} · Fecha: {d.contentQuality.has_date ? 'Sí' : 'No'} · Fuentes citadas: {d.contentQuality.has_sources ? 'Sí' : 'No'}
          </p>
        </div>
      )}

      {d.analysis && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Análisis del contenido</span>
          {d.analysis.summary && <p className="text-xs mt-1 leading-relaxed" style={detailMutedStyle}>{d.analysis.summary}</p>}
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 text-xs" style={detailMutedStyle}>
            {d.analysis.bias_analysis && <span>Sesgo: <span style={detailLabelStyle}>{d.analysis.bias_analysis.score}/100</span></span>}
            {d.analysis.clickbait && <span>Clickbait: <span style={detailLabelStyle}>{d.analysis.clickbait.score}/100</span></span>}
            {d.analysis.credibility && <span>Credibilidad: <span style={detailLabelStyle}>{d.analysis.credibility.score}/100 ({d.analysis.credibility.risk_level})</span></span>}
          </div>
          {d.analysis.manipulation_signals?.length > 0 && (
            <p className="text-xs mt-1.5" style={{ color: '#E8A33D' }}>Señales de manipulación: {d.analysis.manipulation_signals.join(', ')}</p>
          )}
          {d.analysis.recommendation && (
            <p className="text-xs mt-1.5 leading-relaxed" style={detailMutedStyle}><span style={detailLabelStyle}>Recomendación:</span> {d.analysis.recommendation}</p>
          )}
        </div>
      )}

      {d.crossSource && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Cruce con cobertura relacionada</span>
          <p className="text-xs mt-1" style={detailMutedStyle}>
            Fuentes independientes: {d.crossSource.independent_sources_count} · Cobertura Radar: {d.crossSource.radar_media_coverage_count} · Estado: {d.crossSource.coverage_status}
          </p>
        </div>
      )}

      {d.genderImpact && d.genderImpact.signals?.length > 0 && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Impacto de género</span>
          <p className="text-xs mt-1" style={detailMutedStyle}>{d.genderImpact.status_label}</p>
        </div>
      )}

      {d.relatedNews?.length > 0 && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Noticias relacionadas</span>
          <ul className="mt-1.5 space-y-1">
            {d.relatedNews.map((r, i) => (
              <li key={i} className="text-xs" style={detailMutedStyle}>· {r.title}{r.source_name ? ` (${r.source_name})` : ''}</li>
            ))}
          </ul>
        </div>
      )}

      {d.claimContrasts?.length > 0 && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Afirmaciones contrastadas con fuentes</span>
          <ul className="mt-1.5 space-y-2">
            {d.claimContrasts.map((c, i) => (
              <li key={i} className="text-xs" style={detailMutedStyle}>
                <span style={detailLabelStyle}>{c.status_label}:</span> {c.claim}
                {c.sources_consulted?.length > 0 && (
                  <div className="mt-0.5">Fuentes consultadas: {c.sources_consulted.join(', ')}</div>
                )}
                {c.evidence_url && (
                  <a href={c.evidence_url} target="_blank" rel="noreferrer" className="mt-0.5 inline-block underline" style={{ color: BRAND_ORANGE }}>
                    Ver evidencia
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {d.informationGaps?.length > 0 && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Vacíos de información y contexto faltante</span>
          <ul className="mt-1.5 space-y-2">
            {d.informationGaps.map((g, i) => (
              <li key={i} className="text-xs" style={detailMutedStyle}>
                <span style={detailLabelStyle}>{g.missing_item}</span>
                {g.priority && (
                  <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wide" style={{ backgroundColor: BRAND_ORANGE + '22', color: BRAND_ORANGE }}>
                    Prioridad {g.priority}
                  </span>
                )}
                {g.why_it_matters && <div className="mt-0.5">{g.why_it_matters}</div>}
                {g.suggested_verification && <div className="mt-0.5">Sugerencia: {g.suggested_verification}</div>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {d.audit?.reviewRecommendations?.length > 0 && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Recomendaciones para revisar</span>
          <ul className="mt-1.5 space-y-1">
            {d.audit.reviewRecommendations.map((item, i) => (
              <li key={i} className="text-xs" style={detailMutedStyle}>· {typeof item === 'string' ? item : (item.title || item.missing_item || item.label || JSON.stringify(item))}</li>
            ))}
          </ul>
        </div>
      )}

      {d.audit && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold" style={detailLabelStyle}>Evidencia de auditoría</span>
            {d.audit.priority && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wide font-semibold"
                style={{
                  backgroundColor: (d.audit.priority === 'alta' || d.audit.priority === 'critica' ? '#E85D5D' : d.audit.priority === 'media' ? '#E8A33D' : '#00C896') + '22',
                  color: d.audit.priority === 'alta' || d.audit.priority === 'critica' ? '#E85D5D' : d.audit.priority === 'media' ? '#E8A33D' : '#00C896'
                }}
              >
                Prioridad {d.audit.priority}
              </span>
            )}
          </div>
          {d.audit.evidence_summary && (
            <p className="text-xs leading-relaxed mb-2" style={detailMutedStyle}>{d.audit.evidence_summary}</p>
          )}
          {d.audit.evidence_items?.length > 0 && (
            <ul className="space-y-1">
              {d.audit.evidence_items.map((e, i) => {
                const severityColor = e.severity === 'alta' ? '#E85D5D' : e.severity === 'media' ? '#E8A33D' : '#00C896'
                return (
                  <li key={i} className="text-xs flex items-start gap-1.5" style={detailMutedStyle}>
                    <span className="w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0" style={{ backgroundColor: severityColor }} />
                    <span><span style={detailLabelStyle}>{e.label}:</span> {e.value}</span>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      )}
    </div>
    )
  }

  const renderMediaHistoryDetail = (d) => (
    <div className="mt-3 pt-3 space-y-2" style={{ borderTop: '1px solid #1C2A52' }}>
      <div className="rounded-lg p-3" style={detailCardStyle}>
        <span className="text-xs font-semibold" style={detailLabelStyle}>Resultado del análisis</span>
        <p className="text-xs mt-1" style={detailMutedStyle}>
          Generado por IA: {d.is_ai_generated ? 'Sí' : 'No'} · Manipulado: {d.is_manipulated ? 'Sí' : 'No'} · Desinformación: {d.is_misinformation ? 'Sí' : 'No'}
        </p>
      </div>

      {d.contentAnalysis?.llmAnalysis && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold" style={detailLabelStyle}>Veredicto de IA (contexto y evidencia)</span>
            {d.contentAnalysis.llmAnalysis.veredicto && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wide font-semibold"
                style={{
                  backgroundColor: (d.contentAnalysis.llmAnalysis.veredicto === 'AUTÉNTICO' ? '#00C896' : d.contentAnalysis.llmAnalysis.veredicto === 'MIXTO' ? '#E8A33D' : '#E85D5D') + '22',
                  color: d.contentAnalysis.llmAnalysis.veredicto === 'AUTÉNTICO' ? '#00C896' : d.contentAnalysis.llmAnalysis.veredicto === 'MIXTO' ? '#E8A33D' : '#E85D5D'
                }}
              >
                {d.contentAnalysis.llmAnalysis.veredicto}{d.contentAnalysis.llmAnalysis.confianza != null ? ` · ${d.contentAnalysis.llmAnalysis.confianza}%` : ''}
              </span>
            )}
          </div>
          {d.contentAnalysis.llmAnalysis.resumen && (
            <p className="text-xs leading-relaxed mb-1.5" style={detailMutedStyle}>{d.contentAnalysis.llmAnalysis.resumen}</p>
          )}
          {d.contentAnalysis.llmAnalysis.contexto_politico && (
            <p className="text-xs mb-1"><span style={detailLabelStyle}>Contexto:</span> <span style={detailMutedStyle}>{d.contentAnalysis.llmAnalysis.contexto_politico}</span></p>
          )}
          {d.contentAnalysis.llmAnalysis.coincide_con_fuentes != null && (
            <p className="text-xs mb-1" style={detailMutedStyle}>Coincide con fuentes consultadas: {d.contentAnalysis.llmAnalysis.coincide_con_fuentes ? 'Sí' : 'No'}</p>
          )}
          {d.contentAnalysis.llmAnalysis.indicios_ia && (
            <p className="text-xs mb-1" style={detailMutedStyle}>Indicios de generación por IA: {d.contentAnalysis.llmAnalysis.indicios_ia}</p>
          )}
          {d.contentAnalysis.llmAnalysis.observaciones && (
            <p className="text-xs" style={detailMutedStyle}>Observaciones: {d.contentAnalysis.llmAnalysis.observaciones}</p>
          )}
          {d.contentAnalysis.llmAnalysis.afirmaciones_clave?.length > 0 && (
            <div className="mt-2 pt-2" style={{ borderTop: '1px solid #1C2A52' }}>
              <span className="text-xs font-semibold" style={detailLabelStyle}>Afirmaciones clave contrastadas</span>
              <ul className="mt-1 space-y-0.5">
                {d.contentAnalysis.llmAnalysis.afirmaciones_clave.map((c, i) => (
                  <li key={i} className="text-xs" style={detailMutedStyle}>· {c}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {d.contentAnalysis?.extractedClaims?.length > 0 && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Afirmaciones extraídas</span>
          <ul className="mt-1.5 space-y-0.5">
            {d.contentAnalysis.extractedClaims.map((c, i) => (
              <li key={i} className="text-xs" style={detailMutedStyle}>· {c}</li>
            ))}
          </ul>
        </div>
      )}

      {(d.audioDetails || d.videoDetails) && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Señales técnicas</span>
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5 text-xs" style={detailMutedStyle}>
            {d.audioDetails?.spectral_score != null && <span>Espectral: {(d.audioDetails.spectral_score * 100).toFixed(0)}%</span>}
            {d.audioDetails?.pitch_consistency != null && <span>Consistencia de tono: {(d.audioDetails.pitch_consistency * 100).toFixed(0)}%</span>}
            {d.audioDetails?.ml_score != null && <span>Score ML: {(d.audioDetails.ml_score * 100).toFixed(0)}%</span>}
            {d.videoDetails?.facial_consistency != null && <span>Consistencia facial: {(d.videoDetails.facial_consistency * 100).toFixed(0)}%</span>}
            {d.videoDetails?.frame_artifacts != null && <span>Artefactos de fotograma: {(d.videoDetails.frame_artifacts * 100).toFixed(0)}%</span>}
          </div>
        </div>
      )}

      {d.contentAnalysis?.fakeNews && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Clasificación de contenido</span>
          <p className="text-xs mt-1" style={detailMutedStyle}>
            {d.contentAnalysis.fakeNews.label || (d.contentAnalysis.fakeNews.is_fake_news ? 'Posible desinformación' : 'Sin indicios de desinformación')} · {(d.contentAnalysis.fakeNews.confidence * 100).toFixed(0)}% confianza
          </p>
          {d.contentAnalysis.fakeNews.details && (
            <p className="text-xs mt-1 leading-relaxed" style={detailMutedStyle}>{d.contentAnalysis.fakeNews.details}</p>
          )}
        </div>
      )}

      {d.contentAnalysis?.transcriptionExcerpt && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Transcripción</span>
          <p className="text-xs mt-1 leading-relaxed" style={detailMutedStyle}>{d.contentAnalysis.transcriptionExcerpt}</p>
        </div>
      )}

      {d.contentAnalysis?.factChecking?.fact_checks?.length > 0 && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Verificaciones encontradas</span>
          <ul className="mt-1.5 space-y-1">
            {d.contentAnalysis.factChecking.fact_checks.map((f, i) => (
              <li key={i} className="text-xs" style={detailMutedStyle}>· {f.title || f.claim_text || 'Verificación'}{f.publisher ? ` (${f.publisher})` : ''}</li>
            ))}
          </ul>
        </div>
      )}

      {d.metadata && (
        <div className="rounded-lg p-3" style={detailCardStyle}>
          <span className="text-xs font-semibold" style={detailLabelStyle}>Info técnica</span>
          <p className="text-xs mt-1" style={detailMutedStyle}>
            Formato: {d.metadata.format || 'N/A'} · Duración: {d.metadata.duration ? `${d.metadata.duration.toFixed(1)}s` : 'N/A'} · Procesado en {d.processingTime ? `${d.processingTime.toFixed(2)}s` : 'N/A'}
          </p>
        </div>
      )}
    </div>
  )

  const renderHistoryDetail = (item) => {
    if (!item.detail) {
      return (
        <div className="mt-3 pt-3" style={{ borderTop: '1px solid #1C2A52' }}>
          <p className="text-xs" style={detailMutedStyle}>No hay detalle disponible para este análisis (se guardó antes de esta actualización).</p>
        </div>
      )
    }
    return item.detail.kind === 'media' ? renderMediaHistoryDetail(item.detail) : renderNewsHistoryDetail(item.detail)
  }

  return (
    <div className="min-h-screen px-4 py-6 md:py-12" style={{ backgroundColor: '#FFFFFF' }}>
      {/* ===== MODAL TERMINOS Y CONDICIONES (bloqueante hasta aceptar) ===== */}
      {!termsAccepted && (
        <div
          className="fixed inset-0 z-[200] flex items-center justify-center p-4"
          style={{ backgroundColor: 'rgba(16,27,61,0.65)' }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="terms-modal-title"
        >
          <div
            className="w-full max-w-xl rounded-xl shadow-2xl flex flex-col overflow-hidden"
            style={{ backgroundColor: '#FFFFFF', maxHeight: '90vh' }}
          >
            {/* Header */}
            <div className="flex items-center gap-3 px-6 py-4 border-b flex-shrink-0" style={{ borderColor: '#E9ECEF' }}>
              <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: BRAND_ORANGE + '1A' }}>
                <Scale className="w-5 h-5" style={{ color: BRAND_ORANGE }} />
              </div>
              <div>
                <h2 id="terms-modal-title" className="text-base font-bold" style={{ color: BRAND_NAVY }}>Términos y Condiciones de Uso</h2>
                <p className="text-xs text-gray-500">Debes leerlos y aceptarlos para continuar</p>
              </div>
            </div>

            {/* Body */}
            <div className="px-6 py-4">
              <div className="relative">
                <div
                  className="overflow-y-auto pr-1"
                  style={{ maxHeight: termsExpanded ? '50vh' : '190px' }}
                >
                  {TERMS_META.map((line, i) => (
                    <p key={i} className="text-xs text-gray-500">{line}</p>
                  ))}
                  <div className="my-3 border-t" style={{ borderColor: '#E9ECEF' }} />
                  {TERMS_INTRO.map((t, i) => (
                    <p key={i} className="text-sm text-gray-700 mb-3 leading-relaxed">{t}</p>
                  ))}
                  {TERMS_SECTIONS.map((sec, i) => (
                    <div key={i} className="mb-4">
                      <h4 className="text-sm font-bold mb-1.5" style={{ color: BRAND_NAVY }}>{sec.title}</h4>
                      {sec.blocks.map((b, j) => (
                        b.type === 'ul' ? (
                          <ul key={j} className="list-disc pl-5 mb-2 space-y-1">
                            {b.items.map((it, k) => (
                              <li key={k} className="text-sm text-gray-700 leading-relaxed">{it}</li>
                            ))}
                          </ul>
                        ) : (
                          <p key={j} className="text-sm text-gray-700 mb-2 leading-relaxed">{b.text}</p>
                        )
                      ))}
                    </div>
                  ))}
                  {TERMS_CLOSING.length > 0 && (
                    <div className="mt-2 pt-4 border-t text-center" style={{ borderColor: '#E9ECEF' }}>
                      {TERMS_CLOSING.map((t, i) => (
                        <p key={i} className={i === 0 ? 'text-sm font-bold' : 'text-xs text-gray-500'} style={i === 0 ? { color: BRAND_NAVY } : undefined}>{t}</p>
                      ))}
                    </div>
                  )}
                </div>
                {!termsExpanded && (
                  <div
                    className="absolute bottom-0 left-0 right-0 h-14 pointer-events-none"
                    style={{ background: 'linear-gradient(to bottom, rgba(255,255,255,0), #FFFFFF)' }}
                  />
                )}
              </div>
              {!termsExpanded && (
                <button
                  type="button"
                  onClick={() => setTermsExpanded(true)}
                  className="mt-2 text-sm font-semibold text-left"
                  style={{ color: BRAND_ORANGE }}
                >
                  Leer más ↓
                </button>
              )}
            </div>

            {/* Footer */}
            <div className="border-t px-6 py-4 flex-shrink-0" style={{ borderColor: '#E9ECEF', backgroundColor: '#F8F9FA' }}>
              <label className={`flex items-start gap-2.5 ${termsExpanded ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}`}>
                <input
                  type="checkbox"
                  checked={termsChecked}
                  disabled={!termsExpanded}
                  onChange={(e) => setTermsChecked(e.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded flex-shrink-0"
                  style={{ accentColor: BRAND_ORANGE }}
                />
                <span className="text-sm text-gray-700">
                  He leído y acepto los <strong>Términos y Condiciones de Uso</strong> de AMALLU-IA.
                </span>
              </label>
              {!termsExpanded && (
                <p className="text-xs mt-1.5 ml-[26px]" style={{ color: BRAND_ORANGE }}>
                  Despliega "Leer más" para leer el documento completo antes de aceptar.
                </p>
              )}
              <button
                type="button"
                onClick={handleAcceptTerms}
                disabled={!termsChecked}
                className="mt-3 w-full py-2.5 rounded-lg text-sm font-semibold transition-all"
                style={{
                  backgroundColor: termsChecked ? BRAND_ORANGE : '#E9ECEF',
                  color: termsChecked ? '#FFFFFF' : '#9CA3AF',
                  cursor: termsChecked ? 'pointer' : 'not-allowed'
                }}
              >
                Aceptar y continuar
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-[1200px] mx-auto">
        {/* ===== HEADER ===== */}
        <header className="mb-6">
          <div
            className="rounded-xl border px-6 py-4"
            style={{
              backgroundColor: '#F8F9FA',
              borderColor: '#E9ECEF'
            }}
          >
            <div className="flex items-center justify-between">
              <button
                onClick={() => setActiveView('home')}
                className="flex items-center gap-3 text-left focus:outline-none"
                aria-label="Ir al inicio"
              >
                <img src={logo} alt="AMA LLU-IA" className="w-10 h-10 rounded-lg flex-shrink-0 object-cover" />
                <div>
                  <h1 className="text-xl font-bold tracking-tight" style={{ color: BRAND_NAVY }}>
                    AMA LLU-<span style={{ color: BRAND_ORANGE }}>IA</span>
                  </h1>
                  <p className="text-xs font-medium text-gray-600">Verificamos. Informamos. Empoderamos.</p>
                </div>
              </button>
              <div className="flex items-center gap-2">
                {activeView === 'verificar' && (
                  <button
                    onClick={() => setActiveView('home')}
                    className="text-xs px-3 py-1.5 rounded-full font-medium flex items-center gap-1.5 transition-all hover:bg-gray-100"
                    style={{ border: '1px solid #E9ECEF', color: '#6B7280' }}
                  >
                    <Home className="w-3.5 h-3.5" />
                    Inicio
                  </button>
                )}
                <span className="text-xs px-3 py-1.5 rounded-full font-medium" style={{ backgroundColor: BRAND_ORANGE + '20', color: BRAND_ORANGE }}>
                  v1.0
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* ===== TABS (acceso rapido desde Home; en "verificar" ya esta la barra de tabs del panel) ===== */}
        {activeView === 'home' && (
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id); setActiveView('verificar') }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
                style={{
                  backgroundColor: activeTab === tab.id ? BRAND_ORANGE : 'transparent',
                  border: activeTab === tab.id ? 'none' : '1px solid #E9ECEF'
                }}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        )}

        {/* ===== HOME VIEW ===== */}
        {activeView === 'home' && (
          <div className="space-y-6">
            {/* Bienvenido / Hero */}
            <div
              className="relative overflow-hidden rounded-xl border p-6 md:p-10"
              style={{
                backgroundColor: '#F8F9FA',
                borderColor: '#E9ECEF'
              }}
            >
              <Landmark
                className="hidden md:block absolute -right-6 -bottom-8 w-56 h-56 pointer-events-none"
                style={{ color: BRAND_NAVY, opacity: 0.06 }}
              />
              <div className="relative flex items-start gap-4 max-w-2xl">
                <img src={logo} alt="AMA LLU-IA" className="w-12 h-12 rounded-lg flex-shrink-0 object-cover" />
                <div>
                  <span
                    className="inline-block text-xs font-semibold px-2.5 py-1 rounded-full mb-3"
                    style={{ backgroundColor: BRAND_ORANGE + '1A', color: BRAND_ORANGE }}
                  >
                    Verificación de contenido electoral
                  </span>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Bienvenido a AMA LLU-<span style={{ color: BRAND_ORANGE }}>IA</span>
                  </h2>
                  <p className="text-sm leading-relaxed text-gray-600">
                    En época de elecciones, la información circula más rápido de lo que se puede verificar.
                    Esta herramienta analiza noticias, videos y audios para ayudarte a identificar señales de
                    manipulación o desinformación electoral - pero no decide por ti: te da elementos objetivos
                    para que <strong>tú corrobores y decidas</strong> qué creer y qué compartir.
                  </p>
                  <button
                    onClick={() => setActiveView('verificar')}
                    className="mt-5 px-5 py-2.5 rounded-lg font-semibold text-sm transition-all flex items-center gap-2"
                    style={{
                      backgroundColor: BRAND_ORANGE,
                      color: '#FFFFFF'
                    }}
                  >
                    <Search className="w-4 h-4" />
                    Verificar contenido ahora
                  </button>

                  <div className="flex flex-wrap gap-2 mt-5">
                    {['Contexto electoral Ecuador', 'IA + criterio humano', 'Fuentes oficiales'].map((badge) => (
                      <span
                        key={badge}
                        className="text-xs px-3 py-1 rounded-full font-medium text-gray-600"
                        style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}
                      >
                        {badge}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* ¿Qué es la desinformación? */}
            <div
              className="rounded-xl border p-6"
              style={{
                backgroundColor: '#F8F9FA',
                borderColor: '#E9ECEF'
              }}
            >
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="w-5 h-5" style={{ color: BRAND_ORANGE }} />
                  <h3 className="text-base font-semibold text-gray-900">¿Qué es la desinformación?</h3>
                </div>
                <p className="text-xs leading-relaxed text-gray-600">
                  Durante los procesos electorales circula mucho contenido y no todo es confiable. Reconocer estas
                  formas de manipulación es el primer paso para protegerte de ellas.
                </p>
              </div>

              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  {
                    icon: AlertTriangle,
                    color: '#E8A33D',
                    title: 'Información falsa',
                    desc: 'Contenido creado deliberadamente para engañar, muchas veces disfrazado de noticia real.'
                  },
                  {
                    icon: Activity,
                    color: '#3B82F6',
                    title: 'Audio/video manipulado',
                    desc: 'Grabaciones editadas o generadas con IA (deepfakes) para tergiversar una declaración.'
                  },
                  {
                    icon: XCircle,
                    color: '#E85D5D',
                    title: 'Campañas de bots',
                    desc: 'Cuentas automatizadas que amplifican un mensaje para simular apoyo o rechazo masivo.'
                  },
                  {
                    icon: CheckCircle2,
                    color: '#00C896',
                    title: 'Verificación',
                    desc: 'Contrastar la información con fuentes oficiales y verificadores independientes antes de creer o compartir.'
                  }
                ].map((item) => (
                  <div
                    key={item.title}
                    className="rounded-lg p-4"
                    style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                      style={{ backgroundColor: item.color + '1A' }}
                    >
                      <item.icon className="w-4 h-4" style={{ color: item.color }} />
                    </div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">{item.title}</h4>
                    <p className="text-xs leading-relaxed text-gray-600">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* ¿Cómo te ayuda cada sección? */}
            <div
              className="rounded-xl border p-6"
              style={{
                backgroundColor: '#F8F9FA',
                borderColor: '#E9ECEF'
              }}
            >
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Search className="w-5 h-5" style={{ color: BRAND_ORANGE }} />
                  <h3 className="text-base font-semibold text-gray-900">
                    ¿Cómo te ayuda AMA LLU-<span style={{ color: BRAND_ORANGE }}>IA</span>?
                  </h3>
                </div>
                <p className="text-xs leading-relaxed text-gray-600">
                  Cuatro herramientas, un mismo objetivo: darte elementos para decidir con criterio propio.
                </p>
              </div>

              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  {
                    icon: LinkIcon,
                    title: 'Link Noticia',
                    desc: 'Pega el enlace de una noticia y analizamos su contenido, fuente y coherencia con la información oficial.',
                    action: () => { setActiveTab('link'); setActiveView('verificar') }
                  },
                  {
                    icon: Upload,
                    title: 'Video / Audio',
                    desc: 'Sube o enlaza un video o audio. Transcribimos lo dicho y verificamos las afirmaciones segmento por segmento.',
                    action: () => { setActiveTab('video'); setActiveView('verificar') }
                  },
                  {
                    icon: ClipboardList,
                    title: 'Auditor',
                    desc: 'Respaldo de todos los links y noticias ya analizados, con sus resultados y criterios aplicados.',
                    action: () => { setActiveTab('auditor'); setActiveView('verificar') }
                  },
                  {
                    icon: MessageCircle,
                    title: 'Bot',
                    desc: 'Resuelve dudas puntuales sobre verificación electoral conversando directamente con el asistente.',
                    action: () => setChatOpen(true)
                  }
                ].map((item) => (
                  <button
                    key={item.title}
                    onClick={item.action}
                    className="text-left rounded-lg p-4 transition-all hover:-translate-y-0.5 group"
                    style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                      style={{ backgroundColor: BRAND_ORANGE + '1A' }}
                    >
                      <item.icon className="w-4 h-4" style={{ color: BRAND_ORANGE }} />
                    </div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">{item.title}</h4>
                    <p className="text-xs leading-relaxed text-gray-600 mb-3">{item.desc}</p>
                    <span className="text-xs font-medium flex items-center gap-1" style={{ color: BRAND_ORANGE }}>
                      Ir a {item.title}
                      <ArrowRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Rúbrica de clasificación */}
            <div
              className="rounded-xl border p-6"
              style={{
                backgroundColor: '#F8F9FA',
                borderColor: '#E9ECEF'
              }}
            >
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Scale className="w-5 h-5" style={{ color: BRAND_ORANGE }} />
                  <h3 className="text-base font-semibold text-gray-900">Rúbrica de clasificación</h3>
                </div>
                <p className="text-xs leading-relaxed text-gray-600">
                  Así evalúan los modelos el contenido que analizas. Cada criterio suma evidencia, no un veredicto.
                </p>
              </div>

              <div
                className="flex items-start gap-3 rounded-lg p-4 mb-4"
                style={{ backgroundColor: 'rgba(59, 130, 246, 0.06)', border: '1px solid rgba(59, 130, 246, 0.2)' }}
              >
                <Info className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#3B82F6' }} />
                <p className="text-xs leading-relaxed text-gray-700">
                  Estos criterios son una <strong>guía de apoyo y prevención</strong>, no una afirmación de verdad ni
                  una sentencia definitiva sobre el contenido. La herramienta señala patrones que suelen asociarse a
                  la desinformación; <strong>es la persona usuaria quien debe corroborar la información con fuentes
                  oficiales y tomar la decisión final.</strong>
                </p>
              </div>

              <ol className="grid sm:grid-cols-2 gap-3">
                {criterios.map((criterio, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-3 rounded-lg p-3"
                    style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}
                  >
                    <span
                      className="font-mono text-sm font-bold flex-shrink-0 w-6 h-6 rounded flex items-center justify-center"
                      style={{ color: BRAND_ORANGE, backgroundColor: BRAND_ORANGE + '14' }}
                    >
                      {index + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{criterio.title}</p>
                      <p className="text-xs mt-0.5 text-gray-600">{criterio.desc}</p>
                    </div>
                  </li>
                ))}
              </ol>

              <div className="flex items-start gap-3 mt-4 pt-4" style={{ borderTop: '1px solid #E9ECEF' }}>
                <Users className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#7A8290' }} />
                <p className="text-xs leading-relaxed text-gray-600">
                  La decisión de creer, dudar o compartir un contenido siempre es tuya. AMA LLU-IA solo facilita el
                  trabajo de verificación.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <TrendingUp className="w-4 h-4" style={{ color: BRAND_ORANGE }} />
              <h3 className="text-sm font-bold text-gray-900 tracking-wide">LO QUE YA SE HA VERIFICADO</h3>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Análisis Integral */}
              <div
                className="rounded-xl border p-6"
                style={{
                  backgroundColor: '#F8F9FA',
                  borderColor: '#E9ECEF'
                }}
              >
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-base font-semibold text-gray-900">Análisis Integral</h3>
                    <span className="text-xs font-mono text-gray-600">N = {totalAnalyzed}</span>
                  </div>
                  <p className="text-xs leading-relaxed text-gray-600">
                    Distribución real de lo que has analizado en este navegador, según su nivel de veracidad
                  </p>
                </div>

                {totalAnalyzed === 0 ? (
                  <div className="rounded-lg p-6 text-center" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}>
                    <TrendingUp className="w-7 h-7 mx-auto mb-2 text-gray-400" />
                    <p className="text-xs text-gray-500">
                      Aún no hay análisis. Verifica tu primer contenido para ver estadísticas reales aquí.
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-4">
                    <div className="relative w-40 h-40">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={45}
                            outerRadius={70}
                            paddingAngle={3}
                            dataKey="value"
                            stroke="none"
                          >
                            {chartData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                        <span className="text-xl font-bold font-mono text-gray-900">{totalAnalyzed}</span>
                        <span className="text-xs font-mono text-gray-500">total</span>
                      </div>
                    </div>

                    <div className="w-full space-y-2">
                      {chartData.map((item, index) => {
                        const Icon = getStatusIcon(item.name.toLowerCase())
                        return (
                          <div key={index} className="flex items-center gap-2">
                            <Icon className="w-3.5 h-3.5 flex-shrink-0" style={{ color: item.color }} />
                            <div className="flex-1">
                              <div className="flex items-baseline justify-between mb-0.5">
                                <span className="text-xs text-gray-700">{item.name}</span>
                                <span className="text-xs font-mono font-bold" style={{ color: item.color }}>{item.value}%</span>
                              </div>
                              <div className="h-1 rounded-full overflow-hidden" style={{ backgroundColor: '#E9ECEF' }}>
                                <div
                                  className="h-full rounded-full transition-all duration-700"
                                  style={{
                                    width: `${item.value}%`,
                                    backgroundColor: item.color
                                  }}
                                />
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Tendencias actuales */}
              <div
                className="rounded-xl border p-6"
                style={{
                  backgroundColor: '#F8F9FA',
                  borderColor: '#E9ECEF'
                }}
              >
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-5 h-5" style={{ color: BRAND_ORANGE }} />
                    <h3 className="text-base font-semibold text-gray-900">Tendencias actuales</h3>
                  </div>
                  <p className="text-xs leading-relaxed text-gray-600">
                    Tus análisis más recientes, del más nuevo al más antiguo
                  </p>
                </div>

                {recentHistory.length === 0 ? (
                  <div className="rounded-lg p-6 text-center" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}>
                    <Search className="w-7 h-7 mx-auto mb-2 text-gray-400" />
                    <p className="text-xs text-gray-500">
                      Todavía no hay contenido analizado. Usa "Verificar contenido ahora" para empezar.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {recentHistory.map((item, index) => {
                      const Icon = getStatusIcon(item.status)
                      return (
                        <div
                          key={item.id}
                          className="rounded-lg p-3 transition-all hover:bg-opacity-80"
                          style={{
                            backgroundColor: '#FFFFFF',
                            border: '1px solid #E9ECEF'
                          }}
                        >
                          <div className="flex items-start gap-2">
                            <span
                              className="font-mono text-xs font-bold flex-shrink-0 w-5 h-5 rounded flex items-center justify-center mt-0.5"
                              style={{
                                color: BRAND_ORANGE,
                                backgroundColor: BRAND_ORANGE + '14'
                              }}
                            >
                              {index + 1}
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs leading-relaxed truncate text-gray-900">
                                {item.title}
                              </p>
                              <div className="flex items-center gap-3 mt-1">
                                <div className="flex items-center gap-1">
                                  <Icon className="w-3 h-3" style={{ color: getStatusColor(item.status) }} />
                                  <span className="text-xs font-mono capitalize" style={{ color: getStatusColor(item.status) }}>
                                    {item.status}
                                  </span>
                                </div>
                                <span className="text-xs font-mono text-gray-600">
                                  {item.type === 'link' ? 'Noticia' : 'Video/Audio'}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                    <button
                      onClick={() => { setActiveTab('auditor'); setActiveView('verificar') }}
                      className="w-full text-center text-xs font-medium py-2 mt-1"
                      style={{ color: BRAND_ORANGE }}
                    >
                      Ver historial completo en Auditor
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ===== VERIFICAR VIEW ===== */}
        {activeView === 'verificar' && (
          <main
            className="rounded-xl border overflow-hidden"
            style={{
              backgroundColor: '#F8F9FA',
              borderColor: '#E9ECEF'
            }}
          >
            {/* Tabs */}
            <nav className="flex" style={{ borderBottom: '1px solid #E9ECEF' }}>
              {tabs.map(tab => {
                const Icon = tab.icon
                const isActive = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className="flex-1 px-3 py-3.5 text-xs md:text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-inset"
                    style={{
                      color: isActive ? BRAND_ORANGE : '#6B7280',
                      borderBottom: isActive ? `2px solid ${BRAND_ORANGE}` : '2px solid transparent',
                      backgroundColor: isActive ? BRAND_ORANGE + '0A' : 'transparent'
                    }}
                    onFocus={e => e.target.style.color = BRAND_ORANGE}
                    onBlur={e => e.target.style.color = isActive ? BRAND_ORANGE : '#6B7280'}
                  >
                    <Icon className="inline-block w-4 h-4 mr-1.5 -mt-0.5" />
                    {tab.label}
                  </button>
                )
              })}
            </nav>

            {/* Tab Content */}
            <div className="p-6 md:p-8">
              {/* Link Noticia */}
              {activeTab === 'link' && (
                <div className="space-y-5">
                  <div>
                    <label className="block mb-2">
                      <div className="mb-3">
                        <span className="text-xs font-mono uppercase tracking-wider block mb-1 text-gray-600">
                          URL de la noticia
                        </span>
                        <p className="text-xs text-gray-600">
                          Pega el enlace de la noticia que deseas verificar
                        </p>
                      </div>
                      <div className="relative">
                        <input
                          type="url"
                          value={urlValue}
                          onChange={e => setUrlValue(e.target.value)}
                          placeholder="https://ejemplo.com/noticia-electoral"
                          className="w-full px-4 py-3 pl-11 rounded-lg text-sm transition-all focus:outline-none font-mono"
                          style={{
                            backgroundColor: '#FFFFFF',
                            border: '1px solid #E9ECEF',
                            color: '#111827'
                          }}
                          onFocus={e => e.target.style.borderColor = BRAND_ORANGE}
                          onBlur={e => e.target.style.borderColor = '#E9ECEF'}
                        />
                        <LinkIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      </div>
                    </label>
                  </div>
                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    className="w-full px-6 py-3 rounded-lg font-semibold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    style={{
                      backgroundColor: analyzing ? '#E9ECEF' : BRAND_ORANGE,
                      color: analyzing ? '#6B7280' : '#FFFFFF',
                      '--tw-ring-color': BRAND_ORANGE,
                      '--tw-ring-offset-color': '#FFFFFF'
                    }}
                  >
                    {analyzing ? (
                      <>
                        <Activity className="w-4 h-4 animate-spin" />
                        Analizando señal...
                      </>
                    ) : (
                      <>
                        <Search className="w-4 h-4" />
                        Analizar noticia
                      </>
                    )}
                  </button>
                  {analysisResult?.module === 'noticias' && (
                    <NewsResultPanel result={analysisResult.raw_news} />
                  )}
                  {error && (
                    <div className="mt-4 rounded-lg border p-4" style={{ backgroundColor: '#FEF2F2', borderColor: '#E85D5D' }}>
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#E85D5D' }} />
                        <p className="text-xs" style={{ color: '#E85D5D' }}>{error}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Video/Audio */}
              {activeTab === 'video' && (
                <div className="space-y-5">
                  <div className="mb-3">
                    <p className="text-xs" style={{ color: '#7A8290' }}>
                      Sube un archivo de video o audio para detectar si fue generado por IA
                    </p>
                  </div>
                  <div
                    className="rounded-lg p-8 text-center transition-all cursor-pointer"
                    style={{
                      border: '2px dashed #16234E',
                      backgroundColor: '#101B3D'
                    }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = BRAND_ORANGE}
                    onMouseLeave={e => e.currentTarget.style.borderColor = '#16234E'}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="w-10 h-10 mx-auto mb-3" style={{ color: '#7A8290' }} />
                    <p className="text-sm mb-1" style={{ color: '#E8ECF1' }}>
                      {selectedFile ? selectedFile.name : 'Arrastra un archivo o haz clic para seleccionar'}
                    </p>
                    <p className="text-xs font-mono" style={{ color: '#7A8290' }}>
                      {selectedFile ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : 'Video o audio · máx. 50MB'}
                    </p>
                    <input 
                      ref={fileInputRef}
                      type="file" 
                      accept="video/*,audio/*" 
                      className="hidden" 
                      onChange={handleFileChange}
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-px" style={{ backgroundColor: '#16234E' }} />
                    <span className="text-xs font-mono" style={{ color: '#7A8290' }}>o pega un enlace</span>
                    <div className="flex-1 h-px" style={{ backgroundColor: '#16234E' }} />
                  </div>

                  <div className="relative">
                    <input
                      type="url"
                      value={videoUrl}
                      onChange={e => setVideoUrl(e.target.value)}
                      placeholder="https://ejemplo.com/video.mp4"
                      className="w-full px-4 py-3 pl-11 rounded-lg text-sm transition-all focus:outline-none font-mono"
                      style={{
                        backgroundColor: '#101B3D',
                        border: '1px solid #16234E',
                        color: '#E8ECF1'
                      }}
                      onFocus={e => e.target.style.borderColor = BRAND_ORANGE}
                      onBlur={e => e.target.style.borderColor = '#16234E'}
                    />
                    <LinkIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#7A8290' }} />
                  </div>

                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    className="w-full px-6 py-3 rounded-lg font-semibold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    style={{
                      backgroundColor: analyzing ? '#16234E' : BRAND_ORANGE,
                      color: analyzing ? '#7A8290' : '#FFFFFF',
                      '--tw-ring-color': BRAND_ORANGE,
                      '--tw-ring-offset-color': '#101B3D'
                    }}
                  >
                    {analyzing ? (
                      <>
                        <Activity className="w-4 h-4 animate-spin" />
                        Analizando señal...
                      </>
                    ) : (
                      <>
                        <Search className="w-4 h-4" />
                        Analizar si es IA
                      </>
                    )}
                  </button>

                  {/* Resultados del análisis */}
                  {analysisResult && analysisResult.module !== 'noticias' && (() => {
                    const sm = analysisResult.metadata?.source_metadata
                    const segVs = analysisResult.content_analysis?.transcription?.segment_verifications || []
                    const segs = analysisResult.content_analysis?.transcription?.segments || []
                    const fcs = analysisResult.content_analysis?.fact_checking?.fact_checks || []
                    const fcCount = analysisResult.content_analysis?.fact_checking?.fact_checks_found || 0

                    // Stats for speech summary
                    const totalSegs = segVs.length || segs.length || 0
                    const verified = segVs.filter(s => s.label === 'VERIFICADO').length
                    const falseCount = segVs.filter(s => s.label === 'FALSO').length
                    const imprecise = segVs.filter(s => s.label === 'IMPRECISO' || s.label === 'ENGAÑOSO').length
                    const unverified = segVs.filter(s => s.label === 'SIN_VERIFICAR' || s.label === 'DISPUTADO').length

                    // Platform config
                    const platformConfig = {
                      'YouTube': { color: '#FF0000', bg: '#FF0000', icon: '▶', label: 'YouTube' },
                      'Instagram': { color: '#E1306C', bg: '#E1306C', icon: 'IG', label: 'Instagram' },
                      'TikTok': { color: '#00F2EA', bg: '#000000', icon: 'TT', label: 'TikTok' },
                      'Facebook': { color: '#1877F2', bg: '#1877F2', icon: 'f', label: 'Facebook' },
                      'Twitter': { color: '#1DA1F2', bg: '#1DA1F2', icon: 'X', label: 'Twitter/X' },
                      'Generic': { color: '#7A8290', bg: '#7A8290', icon: '▶', label: sm?.platform || 'Video' },
                    }
                    const pc = platformConfig[sm?.platform] || platformConfig['Generic']

                    // Extract YouTube video ID for embed
                    const ytMatch = sm?.source_url?.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n]+)/)
                    const ytId = ytMatch ? ytMatch[1] : null

                    return (
                    <div className="mt-6 space-y-4">
                      {/* ===== VIDEO PLAYER + FUENTE ORIGINAL ===== */}
                      <div className="rounded-xl border overflow-hidden" style={{ backgroundColor: '#FFFFFF', borderColor: '#E9ECEF' }}>
                        {/* Video player - full-width */}
                        {ytId ? (
                          <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                            <iframe
                              className="absolute top-0 left-0 w-full h-full"
                              src={`https://www.youtube.com/embed/${ytId}`}
                              title="Video player"
                              frameBorder="0"
                              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                              allowFullScreen
                            />
                          </div>
                        ) : (
                          <div className="w-full flex items-center justify-center" style={{ backgroundColor: '#F8F9FA', height: '400px' }}>
                            <div className="text-center">
                              <div className="w-20 h-20 rounded-xl mx-auto flex items-center justify-center mb-3" style={{ backgroundColor: pc.bg }}>
                                <span className="text-3xl">{pc.icon}</span>
                              </div>
                              <p className="text-sm text-gray-600">Video analizado</p>
                            </div>
                          </div>
                        )}

                        {/* Source info */}
                        {sm && (
                          <div className="p-5">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: pc.bg }}>
                                <span className="text-white font-bold text-sm">{pc.icon}</span>
                              </div>
                              <span className="text-xs px-2 py-0.5 rounded font-medium" style={{ backgroundColor: pc.bg + '20', color: pc.color }}>
                                {pc.label}
                              </span>
                              {sm.is_verified ? (
                                <span className="flex items-center gap-1 text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: '#00C89620', color: '#00C896' }}>
                                  <CheckCircle2 className="w-3 h-3" /> Verificado
                                </span>
                              ) : (
                                <span className="flex items-center gap-1 text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: '#E8A33D20', color: '#E8A33D' }}>
                                  <AlertTriangle className="w-3 h-3" /> No verificado
                                </span>
                              )}
                            </div>
                            <p className="text-sm font-semibold text-gray-900 mb-2">{sm.title}</p>
                            <div className="flex items-center gap-3 text-xs flex-wrap text-gray-600">
                              <span className="font-medium text-gray-900">{sm.channel}</span>
                              {sm.view_count > 0 && <span>· {sm.view_count.toLocaleString()} vistas</span>}
                              {sm.upload_date && <span>· {sm.upload_date}</span>}
                              {sm.duration > 0 && <span>· {Math.floor(sm.duration / 60)}:{String(sm.duration % 60).padStart(2, '0')}</span>}
                            </div>
                            {!sm.is_verified && (
                              <div className="mt-3 rounded-lg p-2.5 flex items-start gap-2" style={{ backgroundColor: '#E8A33D10' }}>
                                <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" style={{ color: '#E8A33D' }} />
                                <p className="text-xs" style={{ color: '#E8A33D' }}>
                                  Canal no verificado oficialmente. Verifica antes de compartir.
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      {/* ===== BANNER DE VEREDICTO ===== */}
                      <div className="rounded-xl border-2 p-4" style={{
                        backgroundColor: analysisResult.is_ai_generated ? '#FEF2F2' : '#F0FDF4',
                        borderColor: analysisResult.is_ai_generated ? '#E85D5D' : '#00C896'
                      }}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {analysisResult.is_ai_generated ? (
                              <XCircle className="w-7 h-7" style={{ color: '#E85D5D' }} />
                            ) : (
                              <CheckCircle2 className="w-7 h-7" style={{ color: '#00C896' }} />
                            )}
                            <div>
                              <h4 className="text-base font-bold text-gray-900">
                                {analysisResult.is_ai_generated ? 'Contenido Sospechoso' : 'Contenido Auténtico'}
                              </h4>
                              <p className="text-xs text-gray-600">
                                Procesado en {analysisResult.processing_time?.toFixed(1) || 'N/A'}s
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold font-mono" style={{ color: analysisResult.is_ai_generated ? '#E85D5D' : '#00C896' }}>
                              {(analysisResult.confidence * 100).toFixed(0)}%
                            </div>
                            <div className="text-xs text-gray-600">Fiabilidad</div>
                          </div>
                        </div>
                        <div className="mt-2 h-2 rounded-full overflow-hidden" style={{ backgroundColor: '#E9ECEF' }}>
                          <div className="h-full rounded-full transition-all duration-1000" style={{
                            width: `${analysisResult.confidence * 100}%`,
                            backgroundColor: analysisResult.is_ai_generated ? '#E85D5D' : '#00C896'
                          }} />
                        </div>
                      </div>

                      {/* ===== RESUMEN DEL DISCURSO ===== */}
                      {totalSegs > 0 && (
                        <div className="rounded-xl border p-5" style={{ backgroundColor: '#F8F9FA', borderColor: '#E9ECEF' }}>
                          <div className="flex items-center gap-2 mb-4">
                            <div className="w-1 h-5 rounded-full" style={{ backgroundColor: BRAND_ORANGE }} />
                            <h4 className="text-sm font-bold text-gray-900 tracking-wide">RESUMEN DEL DISCURSO</h4>
                          </div>

                          {/* Stats grid */}
                          <div className="grid grid-cols-4 gap-3 mb-4">
                            <div className="rounded-lg p-3 text-center" style={{ backgroundColor: '#FFFFFF' }}>
                              <div className="text-xl font-bold font-mono text-gray-900">{totalSegs}</div>
                              <div className="text-xs mt-1 text-gray-600">Afirmaciones</div>
                            </div>
                            <div className="rounded-lg p-3 text-center" style={{ backgroundColor: '#00C89610' }}>
                              <div className="text-xl font-bold font-mono" style={{ color: '#00C896' }}>{verified}</div>
                              <div className="text-xs mt-1" style={{ color: '#00C896' }}>Verificadas</div>
                            </div>
                            <div className="rounded-lg p-3 text-center" style={{ backgroundColor: '#E8A33D10' }}>
                              <div className="text-xl font-bold font-mono" style={{ color: '#E8A33D' }}>{imprecise}</div>
                              <div className="text-xs mt-1" style={{ color: '#E8A33D' }}>Imprecisas</div>
                            </div>
                            <div className="rounded-lg p-3 text-center" style={{ backgroundColor: '#E85D5D10' }}>
                              <div className="text-xl font-bold font-mono" style={{ color: '#E85D5D' }}>{falseCount}</div>
                              <div className="text-xs mt-1" style={{ color: '#E85D5D' }}>Falsas</div>
                            </div>
                          </div>

                          {/* Stacked bar */}
                          <div className="h-3 rounded-full overflow-hidden flex" style={{ backgroundColor: '#E9ECEF' }}>
                            {verified > 0 && <div style={{ width: `${(verified / totalSegs) * 100}%`, backgroundColor: '#00C896' }} />}
                            {imprecise > 0 && <div style={{ width: `${(imprecise / totalSegs) * 100}%`, backgroundColor: '#E8A33D' }} />}
                            {falseCount > 0 && <div style={{ width: `${(falseCount / totalSegs) * 100}%`, backgroundColor: '#E85D5D' }} />}
                            {unverified > 0 && <div style={{ width: `${(unverified / totalSegs) * 100}%`, backgroundColor: '#9CA3AF' }} />}
                          </div>

                          {/* Legend */}
                          <div className="flex items-center gap-4 mt-3 flex-wrap">
                            <span className="flex items-center gap-1.5 text-xs text-gray-600">
                              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#00C896' }} /> Verificadas
                            </span>
                            <span className="flex items-center gap-1.5 text-xs text-gray-600">
                              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#E8A33D' }} /> Imprecisas
                            </span>
                            <span className="flex items-center gap-1.5 text-xs text-gray-600">
                              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#E85D5D' }} /> Falsas
                            </span>
                            <span className="flex items-center gap-1.5 text-xs text-gray-600">
                              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#9CA3AF' }} /> Sin verificar
                            </span>
                          </div>
                        </div>
                      )}

                      {/* ===== TRANSCRIPCION + VERIFICACION ===== */}
                      {analysisResult.content_analysis?.has_transcription && analysisResult.content_analysis?.transcription?.text && (
                        <div className="rounded-xl border p-5" style={{ backgroundColor: '#F8F9FA', borderColor: '#E9ECEF' }}>
                          <div className="flex items-center gap-2 mb-4">
                            <div className="w-1 h-5 rounded-full" style={{ backgroundColor: BRAND_ORANGE }} />
                            <h4 className="text-sm font-bold text-gray-900 tracking-wide">TRANSCRIPCIÓN + VERIFICACIÓN</h4>
                          </div>
                          <div className="space-y-3">
                            {segVs.length > 0 ? segVs.slice(0, 6).map((seg, idx) => {
                              const minutes = Math.floor(seg.start / 60)
                              const seconds = Math.floor(seg.start % 60)
                              const timestamp = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
                              const labelColors = {
                                'FALSO': '#E85D5D',
                                'IMPRECISO': '#E8A33D',
                                'ENGAÑOSO': '#E8A33D',
                                'VERIFICADO': '#00C896',
                                'DISPUTADO': '#3B82F6',
                                'SIN_VERIFICAR': '#7A8290'
                              }
                              const color = labelColors[seg.label] || '#7A8290'
                              return (
                                <div key={idx} className="flex gap-3 pb-3" style={{ borderBottom: idx < 5 ? '1px solid #E9ECEF' : 'none' }}>
                                  <span className="text-xs font-mono font-bold flex-shrink-0 pt-0.5" style={{ color: BRAND_ORANGE }}>{timestamp}</span>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm leading-relaxed mb-1.5 text-gray-900">"{seg.text}"</p>
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span className="text-xs px-2 py-0.5 rounded font-bold" style={{
                                        backgroundColor: color + '20', color: color, border: `1px solid ${color}40`
                                      }}>{seg.label}</span>
                                      {seg.source !== 'N/A' && <span className="text-xs text-gray-600">Fuente: {seg.source}</span>}
                                      {seg.fact_checks_found > 0 && <span className="text-xs text-gray-600">({seg.fact_checks_found} verif.)</span>}
                                    </div>
                                  </div>
                                </div>
                              )
                            }) : segs.slice(0, 6).map((segment, idx) => {
                              const minutes = Math.floor(segment.start / 60)
                              const seconds = Math.floor(segment.start % 60)
                              const timestamp = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
                              return (
                                <div key={idx} className="flex gap-3 pb-3" style={{ borderBottom: idx < 5 ? '1px solid #E9ECEF' : 'none' }}>
                                  <span className="text-xs font-mono font-bold flex-shrink-0 pt-0.5" style={{ color: BRAND_ORANGE }}>{timestamp}</span>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm leading-relaxed text-gray-900">"{segment.text?.trim()}"</p>
                                    <span className="text-xs px-2 py-0.5 rounded font-bold" style={{ backgroundColor: '#9CA3AF20', color: '#6B7280', border: '1px solid #9CA3AF40' }}>SIN_VERIFICAR</span>
                                  </div>
                                </div>
                              )
                            }) || (
                              <div className="flex gap-3 pb-3">
                                <span className="text-xs font-mono font-bold flex-shrink-0" style={{ color: BRAND_ORANGE }}>00:00</span>
                                <p className="text-sm leading-relaxed text-gray-900">{analysisResult.content_analysis.transcription.text}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* ===== VERIFICACIONES RELACIONADAS ===== */}
                      {fcCount > 0 && (
                        <div className="rounded-xl border p-5" style={{ backgroundColor: '#F8F9FA', borderColor: '#E9ECEF' }}>
                          <div className="flex items-center gap-2 mb-4">
                            <div className="w-1 h-5 rounded-full" style={{ backgroundColor: '#3B82F6' }} />
                            <h4 className="text-sm font-bold text-gray-900 tracking-wide">VERIFICACIONES RELACIONADAS</h4>
                            <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: '#3B82F620', color: '#3B82F6' }}>{fcCount} encontradas</span>
                          </div>
                          <div className="space-y-3">
                            {fcs.slice(0, 4).map((fc, idx) => {
                              const ratingLower = (fc.rating || '').toLowerCase()
                              const isFalse = ratingLower.includes('false') || ratingLower.includes('falso')
                              const isTrue = ratingLower.includes('true') || ratingLower.includes('verdadero')
                              const ratingColor = isFalse ? '#E85D5D' : isTrue ? '#00C896' : '#E8A33D'
                              return (
                                <div key={idx} className="rounded-lg p-3" style={{ backgroundColor: '#FFFFFF' }}>
                                  <p className="text-sm font-medium mb-2 text-gray-900">{fc.title}</p>
                                  <div className="flex items-center gap-3 flex-wrap">
                                    <span className="text-xs text-gray-600">{fc.publisher}</span>
                                    <span className="text-xs px-2 py-0.5 rounded font-semibold" style={{ backgroundColor: ratingColor + '20', color: ratingColor }}>
                                      {fc.rating}
                                    </span>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )}

                      {/* ===== INFO TECNICA ===== */}
                      <div className="rounded-xl border p-4" style={{ backgroundColor: '#F8F9FA', borderColor: '#E9ECEF' }}>
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-1 h-5 rounded-full" style={{ backgroundColor: '#9CA3AF' }} />
                          <h4 className="text-xs font-bold text-gray-900 tracking-wide">INFO TÉCNICA</h4>
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-xs">
                          <div className="rounded-lg p-2.5" style={{ backgroundColor: '#FFFFFF' }}>
                            <p className="text-gray-600">Formato</p>
                            <p className="font-mono font-bold text-gray-900 mt-1">{analysisResult.metadata?.format || 'N/A'}</p>
                          </div>
                          <div className="rounded-lg p-2.5" style={{ backgroundColor: '#FFFFFF' }}>
                            <p className="text-gray-600">Duración</p>
                            <p className="font-mono font-bold text-gray-900 mt-1">{analysisResult.metadata?.duration ? `${analysisResult.metadata.duration.toFixed(1)}s` : 'N/A'}</p>
                          </div>
                          <div className="rounded-lg p-2.5" style={{ backgroundColor: '#FFFFFF' }}>
                            <p className="text-gray-600">Procesado</p>
                            <p className="font-mono font-bold text-gray-900 mt-1">{analysisResult.processing_time?.toFixed(2) || 'N/A'}s</p>
                          </div>
                        </div>
                      </div>
                    </div>
                    )
                  })()}

                  {/* Error */}
                  {error && (
                    <div className="mt-4 rounded-lg border p-4" style={{ backgroundColor: '#FEF2F2', borderColor: '#E85D5D' }}>
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#E85D5D' }} />
                        <p className="text-xs" style={{ color: '#E85D5D' }}>{error}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Auditor */}
              {activeTab === 'auditor' && (
                <div className="space-y-4">
                  {/* Historial real de analisis (guardado en este navegador) */}
                  <div className="mb-2">
                    <div className="flex items-center gap-2 mb-2">
                      <ClipboardList className="w-5 h-5" style={{ color: BRAND_ORANGE }} />
                      <h3 className="text-base font-semibold text-gray-900">Historial de análisis</h3>
                    </div>
                    <p className="text-xs leading-relaxed" style={{ color: '#7A8290' }}>
                      Registro de los links, noticias, videos y audios que ya analizaste en este navegador
                    </p>
                  </div>

                  {history.length === 0 ? (
                    <div className="rounded-lg p-6 text-center" style={{ backgroundColor: '#101B3D', border: '1px solid #16234E' }}>
                      <ClipboardList className="w-7 h-7 mx-auto mb-2" style={{ color: '#7A8290' }} />
                      <p className="text-xs" style={{ color: '#7A8290' }}>
                        Todavía no has analizado ningún contenido. Los resultados aparecerán aquí automáticamente
                        cada vez que uses Link Noticia o Video/Audio.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2 mb-2">
                      {history.map((item) => {
                        const Icon = getStatusIcon(item.status)
                        const isExpanded = expandedHistoryIds.has(item.id)
                        return (
                          <div
                            key={item.id}
                            className="rounded-lg p-3"
                            style={{ backgroundColor: '#101B3D', border: '1px solid #16234E' }}
                          >
                            <button
                              type="button"
                              onClick={() => toggleHistoryExpanded(item.id)}
                              className="w-full text-left"
                              aria-expanded={isExpanded}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <p className="text-sm flex-1 min-w-0 truncate" style={{ color: '#E8ECF1' }}>{item.title}</p>
                                <div className="flex items-center gap-2 flex-shrink-0">
                                  <span className="text-xs font-mono" style={{ color: '#7A8290' }}>
                                    {new Date(item.timestamp).toLocaleString('es-EC', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                                  </span>
                                  {isExpanded ? (
                                    <ChevronUp className="w-3.5 h-3.5" style={{ color: '#7A8290' }} />
                                  ) : (
                                    <ChevronDown className="w-3.5 h-3.5" style={{ color: '#7A8290' }} />
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-2 mt-1.5">
                                <Icon className="w-3 h-3" style={{ color: getStatusColor(item.status) }} />
                                <span className="text-xs font-mono capitalize" style={{ color: getStatusColor(item.status) }}>
                                  {item.status}
                                </span>
                                <span className="text-xs font-mono" style={{ color: '#7A8290' }}>
                                  · {item.type === 'link' ? 'Noticia' : 'Video/Audio'}
                                </span>
                                {item.confidence !== null && (
                                  <span className="text-xs font-mono" style={{ color: '#7A8290' }}>
                                    · {(item.confidence * 100).toFixed(0)}% confianza
                                  </span>
                                )}
                                {item.pending && (
                                  <span className="text-xs font-mono flex items-center gap-1" style={{ color: BRAND_ORANGE }}>
                                    ·
                                    <span
                                      className="w-1.5 h-1.5 rounded-full inline-block"
                                      style={{ backgroundColor: BRAND_ORANGE, animation: 'pulse-dot 2s ease-in-out infinite' }}
                                    />
                                    Actualizando…
                                  </span>
                                )}
                              </div>
                            </button>
                            {isExpanded && (
                              <>
                                {renderHistoryDetail(item)}
                                <button
                                  type="button"
                                  onClick={() => handleAskKuybot(item)}
                                  className="mt-2 w-full flex items-center justify-center gap-2 text-xs font-semibold py-2 rounded-lg"
                                  style={{ backgroundColor: BRAND_ORANGE + '18', color: BRAND_ORANGE }}
                                >
                                  <MessageCircle className="w-3.5 h-3.5" />
                                  Preguntar a Kuybot sobre esto
                                </button>
                              </>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}

                  <div className="mb-4 pt-2" style={{ borderTop: '1px solid #16234E' }}>
                    <div className="flex items-center gap-2 mb-2 pt-2">
                      <ClipboardList className="w-5 h-5" style={{ color: BRAND_ORANGE }} />
                      <h3 className="text-base font-semibold text-gray-900">Criterios de evaluación</h3>
                    </div>
                    <p className="text-xs leading-relaxed" style={{ color: '#7A8290' }}>
                      Estos son los 5 criterios que utilizamos para verificar la autenticidad del contenido electoral
                    </p>
                  </div>
                  <ol className="space-y-2.5">
                    {criterios.map((criterio, index) => (
                      <li
                        key={index}
                        className="flex items-start gap-3 rounded-lg p-3 transition-all"
                        style={{
                          backgroundColor: '#101B3D',
                          border: '1px solid #16234E'
                        }}
                      >
                        <span
                          className="font-mono text-sm font-bold flex-shrink-0 w-6 h-6 rounded flex items-center justify-center"
                          style={{
                            color: BRAND_ORANGE,
                            backgroundColor: BRAND_ORANGE + '14'
                          }}
                        >
                          {index + 1}
                        </span>
                        <div>
                          <p className="text-sm font-medium" style={{ color: '#E8ECF1' }}>{criterio.title}</p>
                          <p className="text-xs mt-0.5" style={{ color: '#7A8290' }}>{criterio.desc}</p>
                        </div>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </main>
        )}

        {/* Status bar */}
        <div
          className="mt-3 flex items-center justify-between px-4 py-2.5 rounded-lg text-xs font-mono"
          style={{
            backgroundColor: BRAND_NAVY,
            border: `1px solid ${BRAND_NAVY_SOFT}`,
            color: '#7A8290'
          }}
        >
          <div className="flex items-center gap-2">
            <div
              className="w-1.5 h-1.5 rounded-full"
              style={{
                backgroundColor: BRAND_ORANGE,
                animation: 'pulse-dot 2s ease-in-out infinite'
              }}
            />
            <span>Conectado</span>
          </div>
          <span>AMA LLU-IA v1.0 · MediaHack II</span>
        </div>
      </div>

      {/* Floating Kuybot Button */}
      <div className="fixed bottom-5 right-5 flex flex-col items-center z-50">
        {!chatOpen && (
          <div
            className="relative mb-2 px-3 py-2 rounded-2xl text-[10px] font-semibold shadow-lg"
            style={{ backgroundColor: '#FFFFFF', color: BRAND_NAVY, border: '1px solid #E9ECEF' }}
          >
            <span className="block leading-snug text-center">Soy Kuybot</span>
            <span className="block leading-snug text-center text-gray-500">Analicemos esta noticia</span>
            <span className="absolute left-1/2 -bottom-1.5 w-3 h-3 bg-white border-b border-r border-slate-200 transform -translate-x-1/2 rotate-45" />
          </div>
        )}
        <button
          onClick={() => setChatOpen(!chatOpen)}
          className="rounded-full flex items-center justify-center transition-all overflow-visible"
          style={{ width: '118px', height: '118px', background: 'transparent', border: 'none' }}
          aria-label={chatOpen ? 'Cerrar Kuybot' : 'Abrir Kuybot'}
        >
          {chatOpen ? (
            <div
              className="w-[74px] h-[74px] rounded-full flex items-center justify-center"
              style={{ backgroundColor: BRAND_ORANGE, color: '#FFFFFF', boxShadow: '0 22px 42px rgba(245,130,43,0.35)' }}
            >
              <X className="w-7 h-7" />
            </div>
          ) : (
            <img src={kuybotMascot} alt="Kuybot" className="w-full h-full object-contain drop-shadow-[0_18px_30px_rgba(15,23,42,0.25)]" />
          )}
        </button>
      </div>

      {/* Chat Panel */}
      {chatOpen && (
        <div
          className="fixed bottom-24 right-5 w-[calc(100vw-1.5rem)] md:w-[420px] h-[520px] rounded-2xl flex flex-col z-50 overflow-hidden shadow-2xl"
          style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}
        >
          <div className="px-4 py-3.5 flex items-center justify-between gap-3" style={{ background: `linear-gradient(135deg, ${BRAND_NAVY}, ${BRAND_NAVY_SOFT})` }}>
            <div className="flex items-center gap-2.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: BRAND_ORANGE, animation: 'pulse-dot 2s ease-in-out infinite' }} />
              <div>
                <h3 className="font-bold text-sm text-white">KUYBOT</h3>
                <p className="text-[10px] uppercase tracking-[0.18em] text-white/70">Asistente de investigación</p>
              </div>
            </div>
            <button
              onClick={() => setChatOpen(false)}
              className="rounded-full w-7 h-7 flex items-center justify-center"
              style={{ backgroundColor: 'rgba(255,255,255,0.10)', color: '#FFFFFF' }}
              aria-label="Cerrar Kuybot"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3.5 space-y-3.5" style={{ backgroundColor: '#F7F9FC' }}>
            {currentNewsContext ? (
              <div className="rounded-xl p-3.5" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}>
                <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-gray-400">Noticia en análisis</span>
                <p className="text-sm font-bold leading-snug mt-2" style={{ color: BRAND_NAVY }}>{currentNewsContext.title}</p>
                <p className="text-[11px] leading-relaxed mt-2 text-gray-600">
                  {currentNewsContext.summary.slice(0, 180)}{currentNewsContext.summary.length > 180 ? '...' : ''}
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-[10px] text-gray-600">
                  <div className="rounded-lg p-2 bg-gray-50">
                    <span className="block font-mono uppercase mb-1 text-gray-400">Plataforma</span>
                    {currentNewsContext.platform}
                  </div>
                  <div className="rounded-lg p-2 bg-gray-50">
                    <span className="block font-mono uppercase mb-1 text-gray-400">Publicador</span>
                    {currentNewsContext.publisher}
                  </div>
                  <div className="rounded-lg p-2 bg-gray-50 col-span-2">
                    <span className="block font-mono uppercase mb-1 text-gray-400">Fecha</span>
                    {currentNewsContext.publicationDate}
                  </div>
                </div>
                {currentNewsContext.relatedSources.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {currentNewsContext.relatedSources.map((item, idx) => (
                      <a
                        key={`${item.name}-${idx}`}
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-2 py-1 rounded-full text-[10px] font-medium"
                        style={{ backgroundColor: '#101B3D10', color: BRAND_NAVY }}
                      >
                        {item.name}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-xl p-3.5" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}>
                <p className="text-sm font-semibold" style={{ color: BRAND_NAVY }}>Sin noticia activa</p>
                <p className="text-[11px] mt-1 text-gray-600">Analiza una URL para que Kuybot cargue automáticamente el contexto periodístico.</p>
              </div>
            )}

            <div className="rounded-xl p-2.5" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}>
              <p className="text-[10px] font-mono uppercase tracking-[0.18em] mb-2 text-gray-400">Preguntas rápidas</p>
              <div className="flex flex-wrap gap-2">
                {kuybotSuggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInputMessage(suggestion)}
                    className="px-2.5 py-1.5 rounded-full text-[10px] font-medium text-left"
                    style={{ backgroundColor: '#F5822B18', color: BRAND_NAVY, border: '1px solid #F5822B24' }}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>

            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className="max-w-[82%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm whitespace-pre-line"
                  style={
                    msg.role === 'user'
                      ? { backgroundColor: BRAND_ORANGE, color: '#FFFFFF', fontWeight: 600 }
                      : { backgroundColor: '#FFFFFF', color: BRAND_NAVY, border: '1px solid #E9ECEF' }
                  }
                >
                  {msg.text}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-100">
                      <div className="text-[10px] font-mono uppercase tracking-[0.18em] mb-2 text-gray-400">Bibliografía</div>
                      <div className="space-y-1.5">
                        {msg.sources.slice(0, 6).map((source, sourceIdx) => {
                          let hostname = source
                          try {
                            hostname = new URL(source).hostname.replace('www.', '')
                          } catch {
                            hostname = source
                          }
                          return (
                            <a
                              key={`${source}-${sourceIdx}`}
                              href={source}
                              target="_blank"
                              rel="noreferrer"
                              className="block text-[10px] leading-relaxed break-all underline-offset-2"
                              style={{ color: BRAND_NAVY }}
                            >
                              <span className="font-semibold">{hostname}</span>
                            </a>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {kuybotBusy && (
              <div className="flex justify-start">
                <div className="max-w-[82%] px-3 py-2.5 rounded-2xl text-sm" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}>
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <Activity className="w-3.5 h-3.5 animate-spin" />
                    Kuybot está revisando el contexto...
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="p-3" style={{ borderTop: '1px solid #E9ECEF', backgroundColor: '#FFFFFF' }}>
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                placeholder="Investiga esta noticia conmigo..."
                className="flex-1 px-3 py-2.5 rounded-xl text-sm focus:outline-none"
                style={{ backgroundColor: '#F7F9FC', border: '1px solid #E9ECEF', color: BRAND_NAVY }}
                disabled={kuybotBusy}
              />
              <button
                onClick={handleSendMessage}
                disabled={kuybotBusy || !inputMessage.trim()}
                className="px-3 py-2.5 rounded-xl transition-all flex items-center justify-center disabled:opacity-50"
                style={{
                  backgroundColor: BRAND_ORANGE,
                  color: '#FFFFFF'
                }}
                aria-label="Enviar mensaje"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App

