import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Link as LinkIcon, Upload, ClipboardList, Search, AlertTriangle, CheckCircle2, XCircle, Activity, Info, TrendingUp, BookOpen, Home, Landmark, Scale, Users, ArrowRight } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { analyzeNewsUrl, getNewsAnalysis, analyzeMediaUrl, analyzeAudio, analyzeVideo } from './services/api'
import logo from './assets/logo.jpeg'

// Paleta de marca (del logo AMA-LLU-IA)
const BRAND_ORANGE = '#F5822B'
const BRAND_NAVY = '#101B3D'
const BRAND_NAVY_SOFT = '#16234E'

function App() {
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
    { role: 'bot', text: 'Hola. Soy el asistente de AMA LLU-IA. Puedes preguntarme sobre verificación de contenido electoral.' }
  ])
  const [inputMessage, setInputMessage] = useState('')
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

  const addHistoryEntry = (entry) => {
    setHistory(prev => {
      const updated = [entry, ...prev].slice(0, 50)
      try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(updated))
      } catch {
        // localStorage no disponible (modo privado, cuota llena, etc.) - no bloquea el analisis
      }
      return updated
    })
  }

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => () => {
    if (pollingRef.current) clearInterval(pollingRef.current)
  }, [])

  const criterios = [
    { title: 'Fuente verificada', desc: 'Origen y autoría del contenido' },
    { title: 'Coherencia del contenido', desc: 'Consistencia interna y contextual' },
    { title: 'Cruce con medios oficiales', desc: 'Corroboración con fuentes institucionales' },
    { title: '% campaña de bots/réplicas/fuentes', desc: 'Patrones de propagación artificial' },
    { title: 'Viralidad vs veracidad', desc: 'Velocidad de difusión vs confirmación' }
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

  const pollNewsAnalysis = (analysisId) => {
    if (pollingRef.current) clearInterval(pollingRef.current)
    let attempts = 0
    pollingRef.current = setInterval(async () => {
      attempts += 1
      try {
        const updated = await getNewsAnalysis(analysisId)
        setAnalysisResult(adaptNewsAnalysisResult(updated))
        if (updated.status !== 'processing' || attempts >= 20) {
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
      let result
      
      if (activeTab === 'link' && urlValue) {
        const newsResponse = await analyzeNewsUrl(urlValue)
        result = adaptNewsAnalysisResult(newsResponse)
        if (newsResponse.status === 'processing') pollNewsAnalysis(newsResponse.id)
      } else if (activeTab === 'video' && selectedFile) {
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

      // Registrar en el historial real (localStorage) para Auditor y Home
      const status = (result.is_ai_generated || result.is_misinformation)
        ? 'falso'
        : (result.confidence < 0.6 ? 'dudoso' : 'verificado')
      const sourceTitle = result.metadata?.source_metadata?.title
      const title = sourceTitle || (activeTab === 'link' ? urlValue : (selectedFile?.name || videoUrl)) || 'Contenido analizado'
      addHistoryEntry({
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        type: activeTab,
        title,
        source: activeTab === 'link' ? urlValue : (videoUrl || selectedFile?.name || ''),
        status,
        confidence: typeof result.confidence === 'number' ? result.confidence : null,
        timestamp: new Date().toISOString()
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

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return
    setMessages(prev => [...prev,
      { role: 'user', text: inputMessage },
      { role: 'bot', text: 'Procesando tu consulta sobre verificación electoral. Un momento.' }
    ])
    setInputMessage('')
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
    const risk = result.risk_assessment?.level || 'sin dato'
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
    const riskColor = risk === 'bajo' ? '#00C896' : risk === 'medio' ? '#E8A33D' : '#E85D5D'
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
                <span className="text-xs px-2.5 py-1 rounded-full font-semibold" style={{ backgroundColor: riskColor + '18', color: riskColor }}>
                  Riesgo {risk}
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

  return (
    <div className="min-h-screen px-4 py-6 md:py-12" style={{ backgroundColor: '#FFFFFF' }}>
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
                      <h3 className="text-base font-semibold text-white">Historial de análisis</h3>
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
                        return (
                          <div
                            key={item.id}
                            className="rounded-lg p-3"
                            style={{ backgroundColor: '#101B3D', border: '1px solid #16234E' }}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <p className="text-sm flex-1 min-w-0 truncate" style={{ color: '#E8ECF1' }}>{item.title}</p>
                              <span className="text-xs font-mono flex-shrink-0" style={{ color: '#7A8290' }}>
                                {new Date(item.timestamp).toLocaleString('es-EC', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                              </span>
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
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  <div className="mb-4 pt-2" style={{ borderTop: '1px solid #16234E' }}>
                    <div className="flex items-center gap-2 mb-2 pt-2">
                      <ClipboardList className="w-5 h-5" style={{ color: BRAND_ORANGE }} />
                      <h3 className="text-base font-semibold text-white">Criterios de evaluación</h3>
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

      {/* Floating Chat Button */}
      <button
        onClick={() => setChatOpen(!chatOpen)}
        className="fixed bottom-5 right-5 w-13 h-13 rounded-full flex items-center justify-center transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 z-50"
        style={{
          width: '52px',
          height: '52px',
          backgroundColor: chatOpen ? BRAND_NAVY_SOFT : BRAND_ORANGE,
          color: chatOpen ? '#E8ECF1' : '#FFFFFF',
          '--tw-ring-color': BRAND_ORANGE,
          '--tw-ring-offset-color': BRAND_NAVY
        }}
        aria-label={chatOpen ? 'Cerrar chat' : 'Abrir chat'}
      >
        {chatOpen ? <X className="w-5 h-5" /> : <MessageCircle className="w-5 h-5" />}
      </button>

      {/* Chat Panel */}
      {chatOpen && (
        <div
          className="fixed bottom-20 right-5 w-[calc(100vw-2.5rem)] md:w-96 h-[420px] rounded-xl flex flex-col z-50 overflow-hidden"
          style={{
            backgroundColor: BRAND_NAVY,
            border: `1px solid ${BRAND_NAVY_SOFT}`
          }}
        >
          <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: `1px solid ${BRAND_NAVY_SOFT}` }}>
            <div
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor: BRAND_ORANGE,
                animation: 'pulse-dot 2s ease-in-out infinite'
              }}
            />
            <h3 className="font-semibold text-sm text-white">Bot - preguntas ciudadanas</h3>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className="max-w-[80%] px-3.5 py-2.5 rounded-lg text-sm leading-relaxed"
                  style={
                    msg.role === 'user'
                      ? { backgroundColor: BRAND_ORANGE, color: '#FFFFFF', fontWeight: 500 }
                      : { backgroundColor: BRAND_NAVY_SOFT, color: '#E8ECF1', border: `1px solid ${BRAND_NAVY_SOFT}` }
                  }
                >
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <div className="p-3" style={{ borderTop: `1px solid ${BRAND_NAVY_SOFT}` }}>
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                placeholder="Escribe tu pregunta..."
                className="flex-1 px-3 py-2.5 rounded-lg text-sm focus:outline-none font-mono"
                style={{
                  backgroundColor: BRAND_NAVY_SOFT,
                  border: `1px solid ${BRAND_NAVY_SOFT}`,
                  color: '#E8ECF1'
                }}
                onFocus={e => e.target.style.borderColor = BRAND_ORANGE}
                onBlur={e => e.target.style.borderColor = BRAND_NAVY_SOFT}
              />
              <button
                onClick={handleSendMessage}
                className="px-3 py-2.5 rounded-lg transition-all flex items-center justify-center"
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

