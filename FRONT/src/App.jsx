import { useState, useRef, useEffect } from 'react'
import {
  MessageCircle, X, Send, Link as LinkIcon, Upload, ClipboardList, Search,
  AlertTriangle, CheckCircle2, XCircle, Activity, Info, TrendingUp, BookOpen,
  Home, Sparkles, Paperclip, ShieldCheck, Youtube, ExternalLink, Play,
  Volume2, Maximize2, Settings, Video, Image as ImageIcon, Music2, Radar as RadarIcon
} from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import logo from './assets/logo.svg'
import { analyzeAudio, analyzeVideo, analyzeMediaUrl } from './services/api'

// ===== Paleta (tema claro) =====
const C = {
  bg: '#F4F6FA',
  card: '#FFFFFF',
  border: '#E6E9F0',
  navy: '#101B3D',
  navySoft: '#16234E',
  navyMuted: 'rgba(16, 27, 61, 0.06)',
  orange: '#F5822B',
  orangeSoft: 'rgba(245, 130, 43, 0.1)',
  textPrimary: '#111827',
  textMuted: '#6B7280',
  textFaint: '#9CA3AF',
  green: '#16A34A',
  greenSoft: 'rgba(22, 163, 74, 0.1)',
  amber: '#D97706',
  amberSoft: 'rgba(217, 119, 6, 0.1)',
  red: '#DC2626',
  redSoft: 'rgba(220, 38, 38, 0.1)',
  gray: '#9CA3AF',
  graySoft: 'rgba(156, 163, 175, 0.12)',
}

function App() {
  const [activeView, setActiveView] = useState('home')
  const [activeTab, setActiveTab] = useState('link')
  const [chatOpen, setChatOpen] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [urlValue, setUrlValue] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [mediaFile, setMediaFile] = useState(null)
  const [mediaResult, setMediaResult] = useState(null)
  const [heroQuery, setHeroQuery] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [newsResult, setNewsResult] = useState(null)
  const [analysisError, setAnalysisError] = useState('')
  const [mediaError, setMediaError] = useState('')
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hola. Soy el asistente de AMA-LLU-IA. Puedes preguntarme sobre verificación de contenido electoral.' }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ===== Datos de ejemplo (demo, igual que el resto del front) =====
  const chartData = [
    { name: 'Verificado', value: 55, color: C.green },
    { name: 'Dudoso', value: 30, color: C.amber },
    { name: 'Falso', value: 15, color: C.red }
  ]

  const criterios = [
    { title: 'Fuente verificada', desc: 'Origen y autoría del contenido' },
    { title: 'Coherencia del contenido', desc: 'Consistencia interna y contextual' },
    { title: 'Cruce con medios oficiales', desc: 'Corroboración con fuentes institucionales' },
    { title: '% campaña de bots/réplicas/fuentes', desc: 'Patrones de propagación artificial' },
    { title: 'Viralidad vs veracidad', desc: 'Velocidad de difusión vs confirmación' }
  ]

  const rankingNoticias = [
    { titulo: 'Candidato X promete reducir impuestos en 50%', status: 'falso', viralidad: 8500 },
    { titulo: 'Nueva ley electoral aprobada por CNE', status: 'verificado', viralidad: 6200 },
    { titulo: 'Encuesta muestra empate técnico', status: 'dudoso', viralidad: 4800 },
    { titulo: 'Debate presidencial cancelado', status: 'falso', viralidad: 3900 },
    { titulo: 'Resultados preliminares disponibles', status: 'verificado', viralidad: 2100 }
  ]

  const educacion = [
    { icon: AlertTriangle, color: C.amber, bg: C.amberSoft, title: 'Información falsa', desc: 'Contenido creado deliberadamente para engañar o manipular la opinión pública.' },
    { icon: XCircle, color: C.red, bg: C.redSoft, title: 'Campañas de bots', desc: 'Propagación artificial de contenido mediante cuentas automatizadas.' },
    { icon: CheckCircle2, color: C.green, bg: C.greenSoft, title: 'Verificación', desc: 'Proceso de corroboración con fuentes oficiales y medios confiables.' }
  ]

  const authCheck = {
    verdict: 'PROBABLEMENTE AUTÉNTICO',
    confidence: 94,
    signals: [
      { ok: true, text: 'Fuente original localizada' },
      { ok: true, text: 'Voz/audio consistente con la fuente' },
      { ok: true, text: 'Sin señales relevantes de generación por IA' },
      { ok: false, text: 'Se detectó un posible corte en 01:42' }
    ]
  }

  const fuenteOriginal = {
    titulo: 'Debate de candidatos a la Alcaldía de Quito',
    medio: 'Wambra Medio Comunitario',
    plataforma: 'YouTube',
    fecha: '2023'
  }

  const transcripcion = [
    { time: '00:32', text: '"Construimos 120 centros..."', verdict: 'FALSO', detail: 'Evidencia contradice la cifra.', fuente: 'MSP' },
    { time: '01:14', text: '"El desempleo cayó..."', verdict: 'IMPRECISO', detail: '', fuente: 'INEC' },
    { time: '02:06', text: '"Somos la ciudad con mayor..."', verdict: 'ENGAÑOSO', detail: '', fuente: 'Fuente oficial' }
  ]

  const resumenDiscurso = {
    afirmaciones: 12,
    verificables: 8,
    opiniones: 4,
    distribucion: [
      { label: 'Cierto', pct: 25, color: C.green },
      { label: 'Impreciso', pct: 25, color: C.amber },
      { label: 'Engañoso', pct: 25, color: '#EAB308' },
      { label: 'Falso', pct: 12, color: C.red },
      { label: 'Inverificable', pct: 13, color: C.gray }
    ]
  }

  const verificacionesRelacionadas = [
    { ini: 'EC', nombre: 'Ecuador Chequea', verdict: 'FALSO', coincidencia: 91 },
    { ini: 'B', nombre: 'Verificador B', verdict: 'ENGAÑOSO', coincidencia: 84 },
    { ini: 'MC', nombre: 'Medio C', verdict: 'CONTEXTO', coincidencia: 76 }
  ]

  const apiBaseUrl = resolveApiBaseUrl()

  const handleAnalyze = async () => {
    if (activeTab !== 'link' && activeView !== 'home') {
      setAnalyzing(true)
      setTimeout(() => setAnalyzing(false), 2500)
      return
    }

    const targetUrl = (activeView === 'home' ? heroQuery : urlValue).trim()
    if (!targetUrl) {
      setAnalysisError('Ingresa una URL para analizar.')
      return
    }

    setAnalyzing(true)
    setAnalysisError('')
    setNewsResult(null)

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/noticias/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: targetUrl })
      })
      const data = await response.json().catch(() => null)
      if (!response.ok) {
        throw new Error(data?.detail || 'No se pudo analizar la noticia.')
      }
      setNewsResult(data)
      setActiveView('verificar')
      setActiveTab('link')
      if (activeView === 'home') setUrlValue(targetUrl)
    } catch (error) {
      setAnalysisError(error.message || 'Error conectando con el backend.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleMediaAnalyze = async () => {
    if (!mediaFile && !videoUrl.trim()) {
      setMediaError('Sube un archivo o pega un enlace de video/audio.')
      return
    }

    setAnalyzing(true)
    setMediaError('')
    setMediaResult(null)

    try {
      let result
      if (mediaFile) {
        result = mediaFile.type.startsWith('video/')
          ? await analyzeVideo(mediaFile)
          : await analyzeAudio(mediaFile)
      } else {
        result = await analyzeMediaUrl(videoUrl.trim())
      }
      setMediaResult(result)
    } catch (error) {
      setMediaError(error.message || 'Error analizando el video/audio.')
    } finally {
      setAnalyzing(false)
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

  const navItems = [
    { id: 'home', label: 'Inicio', icon: Home },
    { id: 'verificar', label: 'Verificador', icon: Search },
    { id: 'radar', label: 'Radar', icon: RadarIcon },
    { id: 'biblioteca', label: 'Biblioteca', icon: BookOpen },
    { id: 'acerca', label: 'Acerca de', icon: Info }
  ]

  const scanColor = analyzing ? C.amber : C.orange

  const getStatusColor = (status) => {
    if (status === 'verificado') return C.green
    if (status === 'dudoso') return C.amber
    return C.red
  }

  const getStatusIcon = (status) => {
    if (status === 'verificado') return CheckCircle2
    if (status === 'dudoso') return AlertTriangle
    return XCircle
  }

  const getVerdictStyle = (verdict) => {
    const v = verdict.toUpperCase()
    if (v === 'FALSO') return { color: C.red, bg: C.redSoft }
    if (v === 'IMPRECISO' || v === 'ENGAÑOSO') return { color: C.amber, bg: C.amberSoft }
    if (v === 'CIERTO' || v === 'VERIFICADO') return { color: C.green, bg: C.greenSoft }
    return { color: C.navy, bg: C.navyMuted }
  }

  const card = { backgroundColor: C.card, border: `1px solid ${C.border}` }

  const riskColor = (level) => {
    if (level === 'bajo') return C.green
    if (level === 'medio') return C.amber
    return C.red
  }

  const prettyValue = (value) => {
    if (!value) return 'Sin dato'
    return String(value).replaceAll('_', ' ')
  }

  const electoralCheckLabel = (result) => result?.information_relevance?.is_relevant ? 'Si' : 'No'

  const goToAudit = () => {
    setActiveView('verificar')
    setActiveTab('auditor')
  }

  const contrastColor = (status) => {
    if (status === 'coincide_con_fuentes') return C.green
    if (status === 'requiere_contexto') return '#EAB308'
    if (status === 'informacion_a_contrastar') return C.amber
    if (status === 'sin_respaldo_suficiente') return '#2563EB'
    return C.gray
  }

  return (
    <div className="min-h-screen px-4 py-6 md:py-8" style={{ backgroundColor: C.bg }}>
      <div className="max-w-[1280px] mx-auto">

        {/* ===== HEADER ===== */}
        <header
          className="mb-6 flex items-center justify-between gap-4 rounded-xl px-5 py-3.5 flex-wrap"
          style={card}
        >
          <div className="flex items-center gap-2.5">
            <img src={logo} alt="AMA LLU-IA" className="w-9 h-9 flex-shrink-0" />
            <div className="leading-tight">
              <div className="text-sm font-bold tracking-tight" style={{ color: C.navy }}>
                AMA LLU-<span style={{ color: C.orange }}>IA</span>
              </div>
              <div className="text-[10px] font-mono uppercase tracking-wider" style={{ color: C.textFaint }}>
                Verificamos. Informamos. Empoderamos.
              </div>
            </div>
          </div>

          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map(item => {
              const Icon = item.icon
              const isActive = activeView === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className="px-3 py-2 text-sm font-medium transition-all flex items-center gap-1.5"
                  style={{
                    color: isActive ? C.navy : C.textMuted,
                    borderBottom: isActive ? `2px solid ${C.orange}` : '2px solid transparent'
                  }}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </button>
              )
            })}
          </nav>

          <button
            onClick={() => setActiveView('verificar')}
            className="px-4 py-2.5 rounded-lg font-semibold text-sm transition-all flex items-center gap-2 flex-shrink-0"
            style={{ backgroundColor: C.orange, color: '#FFFFFF' }}
          >
            <Sparkles className="w-4 h-4" />
            Iniciar análisis
          </button>
        </header>

        {/* ===== HOME: ANALIZADOR MULTIMEDIA ===== */}
        {activeView === 'home' && (
          <div className="space-y-6">
            {/* Hero */}
            <div
              className="relative overflow-hidden rounded-2xl px-6 py-8 md:px-10 md:py-10"
              style={{ backgroundColor: C.navy }}
            >
              <div className="hidden md:flex absolute right-8 top-8 gap-3 opacity-20">
                <div className="w-14 h-14 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'rgba(255,255,255,0.15)' }}>
                  <Video className="w-7 h-7 text-white" />
                </div>
                <div className="w-14 h-14 rounded-xl flex items-center justify-center mt-6" style={{ backgroundColor: 'rgba(255,255,255,0.15)' }}>
                  <Music2 className="w-7 h-7 text-white" />
                </div>
                <div className="w-14 h-14 rounded-xl flex items-center justify-center" style={{ backgroundColor: 'rgba(255,255,255,0.15)' }}>
                  <ImageIcon className="w-7 h-7 text-white" />
                </div>
              </div>

              <div className="relative max-w-2xl">
                <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
                  ANALIZADOR MULTIMEDIA
                </h1>
                <p className="text-sm md:text-base mt-3 leading-relaxed" style={{ color: 'rgba(255,255,255,0.75)' }}>
                  Analiza videos, audios, imágenes o enlaces para detectar autenticidad, transcribir contenido y contrastar afirmaciones con fuentes verificables.
                </p>

                <div className="mt-6 flex flex-col sm:flex-row gap-2.5">
                  <div className="relative flex-1">
                    <Paperclip className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: C.textFaint }} />
                    <input
                      type="text"
                      value={heroQuery}
                      onChange={e => setHeroQuery(e.target.value)}
                      placeholder="VIDEO / AUDIO / IMAGEN / URL"
                      className="w-full pl-11 pr-4 py-3.5 rounded-full text-sm font-mono uppercase tracking-wide focus:outline-none"
                      style={{ backgroundColor: '#FFFFFF', color: C.textPrimary }}
                    />
                  </div>
                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    className="px-6 py-3.5 rounded-full font-semibold text-sm transition-all disabled:opacity-60 flex items-center justify-center gap-2 flex-shrink-0"
                    style={{ backgroundColor: C.orange, color: '#FFFFFF' }}
                  >
                    {analyzing ? <Activity className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                    {analyzing ? 'Analizando...' : 'Analizar'}
                  </button>
                </div>
              </div>
            </div>

            {/* Fila 1: Autenticidad + Fuente original */}
            <div className="grid md:grid-cols-2 gap-5">
              <div className="rounded-xl p-6" style={card}>
                <h3 className="text-xs font-bold uppercase tracking-wider mb-4" style={{ color: C.textFaint }}>
                  ¿El contenido es auténtico?
                </h3>
                <div className="flex items-center gap-2 mb-1">
                  <ShieldCheck className="w-6 h-6" style={{ color: C.green }} />
                  <span className="text-lg font-extrabold" style={{ color: C.green }}>{authCheck.verdict}</span>
                </div>
                <p className="text-sm font-mono mb-4" style={{ color: C.textMuted }}>
                  Confianza: {authCheck.confidence}%
                </p>
                <ul className="space-y-2">
                  {authCheck.signals.map((s, i) => {
                    const Icon = s.ok ? CheckCircle2 : AlertTriangle
                    return (
                      <li key={i} className="flex items-start gap-2 text-sm" style={{ color: C.textPrimary }}>
                        <Icon className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: s.ok ? C.green : C.amber }} />
                        {s.text}
                      </li>
                    )
                  })}
                </ul>
              </div>

              <div className="rounded-xl p-6" style={card}>
                <h3 className="text-xs font-bold uppercase tracking-wider mb-4" style={{ color: C.textFaint }}>
                  Fuente original
                </h3>
                <div className="flex items-start gap-3 mb-4">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.redSoft }}>
                    <Youtube className="w-5 h-5" style={{ color: C.red }} />
                  </div>
                  <p className="text-sm font-semibold leading-snug" style={{ color: C.textPrimary }}>
                    {fuenteOriginal.titulo}
                  </p>
                </div>
                <div className="space-y-1.5 text-sm mb-5">
                  <div className="flex justify-between">
                    <span style={{ color: C.textFaint }}>Medio</span>
                    <span style={{ color: C.textPrimary }}>{fuenteOriginal.medio}</span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: C.textFaint }}>Plataforma</span>
                    <span style={{ color: C.textPrimary }}>{fuenteOriginal.plataforma}</span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: C.textFaint }}>Fecha</span>
                    <span style={{ color: C.textPrimary }}>{fuenteOriginal.fecha}</span>
                  </div>
                </div>
                <button
                  className="w-full py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2"
                  style={{ backgroundColor: C.navyMuted, color: C.navy }}
                >
                  Ver fuente original
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Fila 2: Contenido + Transcripción */}
            <div className="grid md:grid-cols-2 gap-5">
              <div className="rounded-xl overflow-hidden" style={card}>
                <div className="px-6 pt-6 pb-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider" style={{ color: C.textFaint }}>Contenido</h3>
                </div>
                <div
                  className="relative mx-6 mb-6 rounded-lg overflow-hidden flex items-center justify-center"
                  style={{ aspectRatio: '16/9', background: `linear-gradient(135deg, ${C.navy}, #1F2D5C)` }}
                >
                  <button
                    className="w-12 h-12 rounded-full flex items-center justify-center"
                    style={{ backgroundColor: 'rgba(255,255,255,0.15)' }}
                    aria-label="Reproducir"
                  >
                    <Play className="w-5 h-5 text-white ml-0.5" fill="white" />
                  </button>
                  <div className="absolute bottom-0 left-0 right-0 px-3 py-2.5" style={{ background: 'linear-gradient(transparent, rgba(0,0,0,0.6))' }}>
                    <div className="h-1 rounded-full mb-2" style={{ backgroundColor: 'rgba(255,255,255,0.25)' }}>
                      <div className="h-full w-[8%] rounded-full" style={{ backgroundColor: C.orange }} />
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-white">
                      <span>00:00 / 04:15</span>
                      <div className="flex items-center gap-2">
                        <Volume2 className="w-3.5 h-3.5" />
                        <Settings className="w-3.5 h-3.5" />
                        <Maximize2 className="w-3.5 h-3.5" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-xl p-6" style={card}>
                <h3 className="text-xs font-bold uppercase tracking-wider mb-4" style={{ color: C.textFaint }}>
                  Transcripción + Verificación
                </h3>
                <div className="space-y-3">
                  {transcripcion.map((t, i) => {
                    const vs = getVerdictStyle(t.verdict)
                    return (
                      <div key={i} className="pb-3" style={{ borderBottom: i < transcripcion.length - 1 ? `1px solid ${C.border}` : 'none' }}>
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="text-xs font-mono font-semibold" style={{ color: C.textFaint }}>{t.time}</span>
                            <p className="text-sm font-medium mt-0.5" style={{ color: C.textPrimary }}>{t.text}</p>
                            {t.detail && <p className="text-xs mt-0.5" style={{ color: C.textMuted }}>{t.detail}</p>}
                          </div>
                          <span
                            className="px-2.5 py-1 rounded-full text-[10px] font-bold flex-shrink-0"
                            style={{ backgroundColor: vs.bg, color: vs.color }}
                          >
                            {t.verdict}
                          </span>
                        </div>
                        <button className="text-xs font-semibold mt-1.5 flex items-center gap-1" style={{ color: C.navy }}>
                          Fuente: {t.fuente} <ExternalLink className="w-3 h-3" />
                        </button>
                      </div>
                    )
                  })}
                </div>
                <button className="text-sm font-semibold mt-4 flex items-center gap-1" style={{ color: C.navy }}>
                  Ver más transcripción →
                </button>
              </div>
            </div>

            {/* Fila 3: Resumen + Verificaciones relacionadas */}
            <div className="grid md:grid-cols-2 gap-5">
              <div className="rounded-xl p-6" style={card}>
                <h3 className="text-xs font-bold uppercase tracking-wider mb-4" style={{ color: C.textFaint }}>
                  Resumen del discurso
                </h3>
                <div className="grid grid-cols-3 gap-3 mb-5 text-center">
                  <div>
                    <div className="text-2xl font-extrabold" style={{ color: C.textPrimary }}>{resumenDiscurso.afirmaciones}</div>
                    <div className="text-xs" style={{ color: C.textFaint }}>afirmaciones</div>
                  </div>
                  <div>
                    <div className="text-2xl font-extrabold" style={{ color: C.textPrimary }}>{resumenDiscurso.verificables}</div>
                    <div className="text-xs" style={{ color: C.textFaint }}>verificables</div>
                  </div>
                  <div>
                    <div className="text-2xl font-extrabold" style={{ color: C.textPrimary }}>{resumenDiscurso.opiniones}</div>
                    <div className="text-xs" style={{ color: C.textFaint }}>opiniones/promesas</div>
                  </div>
                </div>
                <div className="h-2.5 rounded-full overflow-hidden flex mb-3">
                  {resumenDiscurso.distribucion.map((d, i) => (
                    <div key={i} style={{ width: `${d.pct}%`, backgroundColor: d.color }} />
                  ))}
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                  {resumenDiscurso.distribucion.map((d, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-xs">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                      <span style={{ color: C.textMuted }}>{d.label}</span>
                      <span className="font-semibold" style={{ color: C.textPrimary }}>{d.pct}%</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl p-6" style={card}>
                <h3 className="text-xs font-bold uppercase tracking-wider mb-4" style={{ color: C.textFaint }}>
                  Verificaciones relacionadas
                </h3>
                <div className="space-y-2.5">
                  {verificacionesRelacionadas.map((v, i) => {
                    const vs = getVerdictStyle(v.verdict)
                    return (
                      <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg" style={{ border: `1px solid ${C.border}` }}>
                        <div
                          className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                          style={{ backgroundColor: C.navyMuted, color: C.navy }}
                        >
                          {v.ini}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold truncate" style={{ color: C.textPrimary }}>{v.nombre}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold" style={{ backgroundColor: vs.bg, color: vs.color }}>
                              {v.verdict}
                            </span>
                            <span className="text-xs" style={{ color: C.textFaint }}>Coincidencia {v.coincidencia}%</span>
                          </div>
                        </div>
                        <button className="text-xs font-semibold flex-shrink-0" style={{ color: C.navy }}>Ver →</button>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Buscador: ¿Qué dijo realmente? */}
            <div className="rounded-xl p-6 flex flex-col md:flex-row md:items-center gap-4" style={card}>
              <div className="flex items-start gap-3 flex-1">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.navyMuted }}>
                  <Search className="w-5 h-5" style={{ color: C.navy }} />
                </div>
                <div>
                  <h3 className="text-sm font-bold" style={{ color: C.textPrimary }}>¿Qué dijo realmente?</h3>
                  <p className="text-xs mt-0.5" style={{ color: C.textMuted }}>
                    Busca y encuentra lo que dijeron realmente en debates, entrevistas y planes de gobierno.
                  </p>
                </div>
              </div>
              <div className="flex gap-2 md:w-[420px] flex-shrink-0">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Buscar en debates, entrevistas..."
                  className="flex-1 px-4 py-2.5 rounded-lg text-sm focus:outline-none"
                  style={{ backgroundColor: C.bg, border: `1px solid ${C.border}`, color: C.textPrimary }}
                />
                <button
                  className="px-5 py-2.5 rounded-lg text-sm font-semibold flex-shrink-0"
                  style={{ backgroundColor: C.navy, color: '#FFFFFF' }}
                >
                  Buscar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ===== VERIFICAR VIEW ===== */}
        {activeView === 'verificar' && (
          <main className="rounded-xl overflow-hidden" style={card}>
            <nav className="flex" style={{ borderBottom: `1px solid ${C.border}` }}>
              {tabs.map(tab => {
                const Icon = tab.icon
                const isActive = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className="flex-1 px-3 py-3.5 text-xs md:text-sm font-medium transition-all duration-200 focus:outline-none"
                    style={{
                      color: isActive ? C.navy : C.textMuted,
                      borderBottom: isActive ? `2px solid ${C.orange}` : '2px solid transparent',
                      backgroundColor: isActive ? C.navyMuted : 'transparent'
                    }}
                  >
                    <Icon className="inline-block w-4 h-4 mr-1.5 -mt-0.5" />
                    {tab.label}
                  </button>
                )
              })}
            </nav>

            <div className="p-6 md:p-8">
              {/* Link Noticia */}
              {activeTab === 'link' && (
                <div className="space-y-5">
                  <div>
                    <span className="text-xs font-mono uppercase tracking-wider block mb-1" style={{ color: C.textFaint }}>
                      URL de la noticia
                    </span>
                    <p className="text-xs mb-3" style={{ color: C.textMuted }}>
                      Pega el enlace de la noticia que deseas verificar
                    </p>
                    <div className="relative">
                      <input
                        type="url"
                        value={urlValue}
                        onChange={e => setUrlValue(e.target.value)}
                        placeholder="https://ejemplo.com/noticia-electoral"
                        className="w-full px-4 py-3 pl-11 rounded-lg text-sm transition-all focus:outline-none font-mono"
                        style={{ backgroundColor: C.bg, border: `1px solid ${C.border}`, color: C.textPrimary }}
                      />
                      <LinkIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: C.textFaint }} />
                    </div>
                  </div>
                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    className="w-full px-6 py-3 rounded-lg font-semibold text-sm transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                    style={{ backgroundColor: C.orange, color: '#FFFFFF' }}
                  >
                    {analyzing ? (
                      <><Activity className="w-4 h-4 animate-spin" /> Analizando señal...</>
                    ) : (
                      <><Search className="w-4 h-4" /> Analizar noticia</>
                    )}
                  </button>

                  {analysisError && (
                    <div className="rounded-lg p-4 text-sm flex items-start gap-3" style={{ backgroundColor: C.redSoft, border: `1px solid ${C.red}`, color: C.textPrimary }}>
                      <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: C.red }} />
                      <span>{analysisError}</span>
                    </div>
                  )}

                  {newsResult && (
                    <div className="space-y-4">
                      <div className="rounded-xl p-5" style={card}>
                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 mb-4">
                          <div>
                            <p className="text-xs font-mono uppercase tracking-wider mb-1" style={{ color: C.textFaint }}>
                              Resultado del analisis
                            </p>
                            <h3 className="text-base font-bold leading-snug" style={{ color: C.textPrimary }}>
                              {newsResult.article?.title || 'Noticia analizada'}
                            </h3>
                          </div>
                          <div
                            className="px-3 py-2 rounded-lg text-xs font-mono font-bold uppercase"
                            style={{
                              color: riskColor(newsResult.risk_assessment?.level),
                              backgroundColor: `${riskColor(newsResult.risk_assessment?.level)}18`,
                              border: `1px solid ${riskColor(newsResult.risk_assessment?.level)}55`
                            }}
                          >
                            Riesgo {prettyValue(newsResult.risk_assessment?.level)}
                          </div>
                        </div>

                        <div className="mb-4">
                          <p className="text-xs font-mono uppercase tracking-wider mb-2" style={{ color: C.textFaint }}>
                            Palabras clave
                          </p>
                          <KeywordPills items={newsResult.analysis?.keywords || []} colors={C} />
                        </div>

                        <div className="grid md:grid-cols-4 gap-3">
                          {[
                            ['Fuente', prettyValue(newsResult.source_classification?.communication_type)],
                            ['Registro', prettyValue(newsResult.source_verification?.status)],
                            ['Electoral', electoralCheckLabel(newsResult)],
                            ['URL', `${prettyValue(newsResult.url_trust_assessment?.level)} (${newsResult.url_trust_assessment?.score ?? 0})`]
                          ].map(([label, value]) => (
                            <div key={label} className="rounded-lg p-3" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
                              <p className="text-[11px] font-mono uppercase mb-1" style={{ color: C.textFaint }}>{label}</p>
                              <p className="text-sm font-semibold capitalize" style={{ color: C.textPrimary }}>{value}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-4">
                        <div className="rounded-xl p-5" style={card}>
                          <h4 className="text-sm font-semibold mb-3" style={{ color: C.textPrimary }}>Publicacion</h4>
                          <div className="space-y-2 text-xs" style={{ color: C.textMuted }}>
                            <p>Plataforma: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(newsResult.editorial_metadata?.platform)}</span></p>
                            <p>Cuenta: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(newsResult.content_attribution?.shared_by_account || newsResult.content_attribution?.publisher_name)}</span></p>
                            <p>Quien publica: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(newsResult.content_attribution?.publisher_type || newsResult.editorial_metadata?.publisher_type)}</span></p>
                            <p>Fuente: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(newsResult.source_verification?.source_name)}</span></p>
                            <p>Fecha: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(newsResult.editorial_metadata?.publication_date)}</span></p>
                            {newsResult.information_relevance?.is_relevant && (
                              <p>Eje: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(newsResult.editorial_metadata?.thematic_axis)}</span></p>
                            )}
                          </div>
                        </div>

                        <div className="rounded-xl p-5" style={card}>
                          <h4 className="text-sm font-semibold mb-3" style={{ color: C.textPrimary }}>URL</h4>
                          <div className="space-y-2 text-xs" style={{ color: C.textMuted }}>
                            <p>Confiabilidad URL: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(newsResult.url_trust_assessment?.level)}</span></p>
                            <p>Estado link: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(newsResult.url_health?.status)}</span></p>
                            {newsResult.information_relevance?.is_relevant && (
                              <p>Subtemas: <span className="font-mono" style={{ color: C.navy }}>{(newsResult.information_relevance?.subtopics || []).join(', ') || 'Sin dato'}</span></p>
                            )}
                          </div>
                        </div>
                      </div>

                      {newsResult.information_relevance?.is_relevant && (
                        <div className="rounded-xl p-5" style={card}>
                          <h4 className="text-sm font-semibold mb-2" style={{ color: C.textPrimary }}>Contexto electoral</h4>
                          <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>
                            {newsResult.information_relevance?.how_it_relates || 'Sin explicacion de relevancia.'}
                          </p>
                        </div>
                      )}

                      <button
                        onClick={goToAudit}
                        className="w-full px-4 py-3 rounded-lg font-semibold text-sm transition-all flex items-center justify-center gap-2"
                        style={{ backgroundColor: C.navy, color: '#FFFFFF' }}
                      >
                        <ClipboardList className="w-4 h-4" />
                        Ir a auditoria
                      </button>

                      <div className="rounded-xl p-5" style={card}>
                        <div className="flex items-center justify-between gap-3 mb-3">
                          <h4 className="text-sm font-semibold" style={{ color: C.textPrimary }}>Noticias relacionadas</h4>
                          <span className="text-xs font-mono" style={{ color: C.textFaint }}>
                            {newsResult.cross_source_check?.related_coverage_count ?? 0} encontradas
                          </span>
                        </div>
                        {(newsResult.related_news || []).length ? (
                          <div className="space-y-2">
                            {newsResult.related_news.slice(0, 3).map((item, index) => (
                              <a
                                key={`${item.url}-${index}`}
                                href={item.url}
                                target="_blank"
                                rel="noreferrer"
                                className="block rounded-lg p-3"
                                style={{ backgroundColor: C.bg, border: `1px solid ${C.border}`, color: C.textPrimary }}
                              >
                                <p className="text-sm font-semibold leading-snug">{item.title}</p>
                                <div className="mt-2 grid sm:grid-cols-3 gap-2 text-[11px]" style={{ color: C.textMuted }}>
                                  <p>Medio: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(item.source_name || item.source)}</span></p>
                                  <p>Registro: <span className="font-mono" style={{ color: C.navy }}>{prettyValue(item.source_registry_status)}</span></p>
                                  <p>Confianza: <span className="font-mono" style={{ color: C.navy }}>{item.source_confidence_score ?? 0}/100</span></p>
                                </div>
                                <p className="text-[11px] mt-1" style={{ color: C.textMuted }}>Tipo: {prettyValue(item.source_type)}</p>
                              </a>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>
                            No hay resultados relacionados disponibles.
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Video/Audio */}
              {activeTab === 'video' && (
                <div className="space-y-5">
                  <p className="text-xs" style={{ color: C.textMuted }}>
                    Sube un archivo de video o audio para detectar si fue generado por IA
                  </p>
                  <label
                    className="rounded-lg p-8 text-center transition-all cursor-pointer"
                    style={{ border: `2px dashed ${C.border}`, backgroundColor: C.bg }}
                  >
                    <Upload className="w-10 h-10 mx-auto mb-3" style={{ color: C.textFaint }} />
                    <p className="text-sm mb-1" style={{ color: C.textPrimary }}>
                      Arrastra un archivo o haz clic para seleccionar
                    </p>
                    <p className="text-xs font-mono" style={{ color: C.textFaint }}>
                      Video o audio · máx. 50MB
                    </p>
                    <input
                      type="file"
                      accept="video/*,audio/*"
                      className="hidden"
                      onChange={event => setMediaFile(event.target.files?.[0] || null)}
                    />
                    {mediaFile && (
                      <p className="text-xs font-mono mt-3" style={{ color: C.navy }}>
                        {mediaFile.name}
                      </p>
                    )}
                  </label>

                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
                    <span className="text-xs font-mono" style={{ color: C.textFaint }}>o pega un enlace</span>
                    <div className="flex-1 h-px" style={{ backgroundColor: C.border }} />
                  </div>

                  <div className="relative">
                    <input
                      type="url"
                      value={videoUrl}
                      onChange={e => setVideoUrl(e.target.value)}
                      placeholder="https://ejemplo.com/video.mp4"
                      className="w-full px-4 py-3 pl-11 rounded-lg text-sm transition-all focus:outline-none font-mono"
                      style={{ backgroundColor: C.bg, border: `1px solid ${C.border}`, color: C.textPrimary }}
                    />
                    <LinkIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: C.textFaint }} />
                  </div>

                  <button
                    onClick={handleMediaAnalyze}
                    disabled={analyzing}
                    className="w-full px-6 py-3 rounded-lg font-semibold text-sm transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                    style={{ backgroundColor: C.orange, color: '#FFFFFF' }}
                  >
                    {analyzing ? (
                      <><Activity className="w-4 h-4 animate-spin" /> Analizando señal...</>
                    ) : (
                      <><Search className="w-4 h-4" /> Analizar si es IA</>
                    )}
                  </button>

                  {mediaError && (
                    <div className="rounded-lg p-4 text-sm flex items-start gap-3" style={{ backgroundColor: C.redSoft, border: `1px solid ${C.red}`, color: C.textPrimary }}>
                      <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: C.red }} />
                      <span>{mediaError}</span>
                    </div>
                  )}

                  {mediaResult && (
                    <div className="space-y-4">
                      <div className="rounded-xl p-5" style={card}>
                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                          <div>
                            <p className="text-xs font-mono uppercase tracking-wider mb-1" style={{ color: C.textFaint }}>
                              Resultado video/audio
                            </p>
                            <h3 className="text-base font-bold" style={{ color: C.textPrimary }}>
                              {mediaResult.analysis_type === 'video' ? 'Analisis de video' : 'Analisis de audio'}
                            </h3>
                          </div>
                          <span className="px-3 py-2 rounded-lg text-xs font-mono font-bold uppercase" style={{ color: mediaResult.is_ai_generated ? C.red : C.green, backgroundColor: mediaResult.is_ai_generated ? C.redSoft : C.greenSoft }}>
                            {mediaResult.is_ai_generated ? 'Posible IA' : 'Sin senal fuerte de IA'}
                          </span>
                        </div>
                        <div className="grid md:grid-cols-4 gap-3 mt-4">
                          {[
                            ['Confianza', `${Math.round((mediaResult.confidence || 0) * 100)}%`],
                            ['Tipo', prettyValue(mediaResult.analysis_type)],
                            ['Manipulado', mediaResult.is_manipulated ? 'Si' : 'No'],
                            ['Desinformacion', mediaResult.is_misinformation ? 'Si' : 'No']
                          ].map(([label, value]) => (
                            <div key={label} className="rounded-lg p-3" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
                              <p className="text-[11px] font-mono uppercase mb-1" style={{ color: C.textFaint }}>{label}</p>
                              <p className="text-sm font-semibold" style={{ color: C.textPrimary }}>{value}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      {mediaResult.content_analysis?.has_transcription && (
                        <div className="rounded-xl p-5" style={card}>
                          <h4 className="text-sm font-semibold mb-2" style={{ color: C.textPrimary }}>Transcripcion</h4>
                          <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>
                            {mediaResult.content_analysis.transcription?.text || 'Sin transcripcion disponible.'}
                          </p>
                        </div>
                      )}

                      {(mediaResult.content_analysis?.transcription?.segment_verifications || []).length > 0 && (
                        <div className="rounded-xl p-5" style={card}>
                          <h4 className="text-sm font-semibold mb-3" style={{ color: C.textPrimary }}>Contraste por segmento</h4>
                          <div className="space-y-3">
                            {mediaResult.content_analysis.transcription.segment_verifications.map((segment, index) => (
                              <div key={index} className="rounded-lg p-3" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
                                <div className="flex items-start justify-between gap-3">
                                  <div>
                                    <p className="text-xs font-mono mb-1" style={{ color: C.textFaint }}>
                                      {formatSeconds(segment.start)} - {formatSeconds(segment.end)}
                                    </p>
                                    <p className="text-sm" style={{ color: C.textPrimary }}>{segment.text}</p>
                                  </div>
                                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold flex-shrink-0" style={{ backgroundColor: C.navyMuted, color: C.navy }}>
                                    {segment.label}
                                  </span>
                                </div>
                                <p className="text-xs mt-2" style={{ color: C.textMuted }}>Fuente: {segment.source}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Auditor */}
              {activeTab === 'auditor' && (
                <div className="space-y-4">
                  <div className="mb-2">
                    <div className="flex items-center gap-2 mb-2">
                      <ClipboardList className="w-5 h-5" style={{ color: C.navy }} />
                      <h3 className="text-base font-semibold" style={{ color: C.textPrimary }}>Auditoria del analisis</h3>
                    </div>
                    <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>
                      Evidencia tecnica, fuente, URL, contenido faltante y puntos verificables para revision.
                    </p>
                  </div>
                  {newsResult && (
                    <div className="space-y-4">
                      <div className="rounded-xl p-5" style={card}>
                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                          <div>
                            <p className="text-xs font-mono uppercase tracking-wider mb-1" style={{ color: C.textFaint }}>
                              Caso {newsResult.id}
                            </p>
                            <h4 className="text-sm font-semibold leading-snug" style={{ color: C.textPrimary }}>
                              {newsResult.article?.title || 'Noticia analizada'}
                            </h4>
                          </div>
                          <span className="px-3 py-2 rounded-lg text-xs font-mono font-bold uppercase" style={{ color: C.amber, backgroundColor: C.amberSoft, border: `1px solid ${C.amber}` }}>
                            Prioridad {prettyValue(newsResult.audit?.priority)}
                          </span>
                        </div>
                        <p className="text-xs leading-relaxed mt-3" style={{ color: C.textMuted }}>
                          {newsResult.audit?.evidence_summary}
                        </p>
                      </div>

                      <div className="grid md:grid-cols-2 gap-4">
                        <ResultList
                          title="Evidencia para auditoria"
                          items={(newsResult.audit?.evidence_items || []).map(item => `${item.label}: ${item.value}`)}
                          empty="No hay evidencia registrada."
                          colors={C}
                        />
                        <ResultList
                          title="Afirmaciones verificables"
                          items={(newsResult.verifiable_claims || []).map(item => item.claim)}
                          empty="No se detectaron afirmaciones verificables."
                          colors={C}
                        />
                      </div>

                      <div className="rounded-xl p-5" style={card}>
                        <h4 className="text-sm font-semibold mb-1" style={{ color: C.textPrimary }}>Transcripcion + contraste</h4>
                        <p className="text-xs leading-relaxed mb-4" style={{ color: C.textMuted }}>
                          Detectamos afirmaciones verificables y las contrastamos con fuentes publicas, oficiales y cobertura periodistica disponible.
                        </p>
                        <div className="space-y-3">
                          {(newsResult.claim_contrasts || []).map((item, index) => (
                            <div key={`${item.claim}-${index}`} className="rounded-lg p-3" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
                              <div className="flex items-center gap-2 mb-2">
                                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: contrastColor(item.status) }} />
                                <span className="text-xs font-mono uppercase" style={{ color: contrastColor(item.status) }}>
                                  {item.timestamp || `Afirmacion ${index + 1}`}
                                </span>
                              </div>
                              <p className="text-sm font-semibold leading-snug mb-2" style={{ color: C.textPrimary }}>"{item.claim}"</p>
                              <p className="text-xs font-mono font-bold uppercase mb-2" style={{ color: contrastColor(item.status) }}>
                                {item.status_label}
                              </p>
                              <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>{item.explanation}</p>
                              <p className="text-xs mt-3" style={{ color: C.textFaint }}>
                                Fuentes consultadas: <span className="font-mono" style={{ color: C.navy }}>{(item.sources_consulted || []).join(' · ') || 'Sin fuentes disponibles'}</span>
                              </p>
                              {item.evidence_url && (
                                <a href={item.evidence_url} target="_blank" rel="noreferrer" className="inline-flex mt-3 text-xs font-semibold uppercase" style={{ color: C.navy }}>
                                  Ver evidencia
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-4">
                        <ResultList
                          title="Informacion faltante"
                          items={(newsResult.analysis?.information_gaps || []).map(item => `${item.missing_item}: ${item.why_it_matters}`)}
                          empty="No se detecto informacion faltante prioritaria."
                          colors={C}
                        />
                        <ResultList
                          title="Senales tecnicas de URL"
                          items={(newsResult.url_trust_assessment?.reasons || []).concat((newsResult.url_risk_signals || []).map(item => item.explanation))}
                          empty="No hay senales tecnicas registradas."
                          colors={C}
                        />
                      </div>
                    </div>
                  )}

                  {!newsResult && (
                    <div className="rounded-lg p-4 text-xs" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}`, color: C.textMuted }}>
                      Analiza primero una URL para cargar la evidencia completa de auditoria.
                    </div>
                  )}

                  <ol className="space-y-2.5">
                    {criterios.map((criterio, index) => (
                      <li
                        key={index}
                        className="flex items-start gap-3 rounded-lg p-3"
                        style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}
                      >
                        <span
                          className="font-mono text-sm font-bold flex-shrink-0 w-6 h-6 rounded flex items-center justify-center"
                          style={{ color: C.navy, backgroundColor: C.navyMuted }}
                        >
                          {index + 1}
                        </span>
                        <div>
                          <p className="text-sm font-medium" style={{ color: C.textPrimary }}>{criterio.title}</p>
                          <p className="text-xs mt-0.5" style={{ color: C.textMuted }}>{criterio.desc}</p>
                        </div>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </main>
        )}

        {/* ===== RADAR VIEW (Análisis integral + Ranking) ===== */}
        {activeView === 'radar' && (
          <div className="grid md:grid-cols-2 gap-5">
            <div className="rounded-xl p-6" style={card}>
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-semibold" style={{ color: C.textPrimary }}>Análisis Integral</h3>
                  <span className="text-xs font-mono" style={{ color: C.textFaint }}>N = 1,247</span>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>
                  Distribución de noticias analizadas según su nivel de veracidad
                </p>
              </div>
              <div className="flex flex-col items-center gap-4">
                <div className="relative w-40 h-40">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={chartData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value" stroke="none">
                        {chartData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    <span className="text-xl font-bold font-mono" style={{ color: C.textPrimary }}>100%</span>
                    <span className="text-xs font-mono" style={{ color: C.textFaint }}>total</span>
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
                            <span className="text-xs" style={{ color: C.textPrimary }}>{item.name}</span>
                            <span className="text-xs font-mono font-bold" style={{ color: item.color }}>{item.value}%</span>
                          </div>
                          <div className="h-1 rounded-full overflow-hidden" style={{ backgroundColor: C.bg }}>
                            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${item.value}%`, backgroundColor: item.color }} />
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            <div className="rounded-xl p-6" style={card}>
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5" style={{ color: C.navy }} />
                  <h3 className="text-base font-semibold" style={{ color: C.textPrimary }}>Ranking de Noticias</h3>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>
                  Noticias más virales ordenadas por número de visualizaciones y estado de verificación
                </p>
              </div>
              <div className="space-y-2">
                {rankingNoticias.map((noticia, index) => {
                  const Icon = getStatusIcon(noticia.status)
                  return (
                    <div key={index} className="rounded-lg p-3" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
                      <div className="flex items-start gap-2">
                        <span
                          className="font-mono text-xs font-bold flex-shrink-0 w-5 h-5 rounded flex items-center justify-center mt-0.5"
                          style={{ color: C.navy, backgroundColor: C.navyMuted }}
                        >
                          {index + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs leading-relaxed truncate" style={{ color: C.textPrimary }}>{noticia.titulo}</p>
                          <div className="flex items-center gap-3 mt-1">
                            <div className="flex items-center gap-1">
                              <Icon className="w-3 h-3" style={{ color: getStatusColor(noticia.status) }} />
                              <span className="text-xs font-mono capitalize" style={{ color: getStatusColor(noticia.status) }}>{noticia.status}</span>
                            </div>
                            <span className="text-xs font-mono" style={{ color: C.textFaint }}>{noticia.viralidad.toLocaleString()} vistas</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

        {/* ===== BIBLIOTECA VIEW (Educación) ===== */}
        {activeView === 'biblioteca' && (
          <div className="rounded-xl p-6" style={card}>
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <BookOpen className="w-5 h-5" style={{ color: C.navy }} />
                <h3 className="text-base font-semibold" style={{ color: C.textPrimary }}>¿Qué es desinformación?</h3>
              </div>
              <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>
                Aprende a identificar contenido falso y técnicas de manipulación en medios digitales
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-4">
              {educacion.map((e, i) => {
                const Icon = e.icon
                return (
                  <div key={i} className="rounded-lg p-4" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ backgroundColor: e.bg }}>
                      <Icon className="w-4 h-4" style={{ color: e.color }} />
                    </div>
                    <h4 className="text-sm font-semibold mb-2" style={{ color: C.textPrimary }}>{e.title}</h4>
                    <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>{e.desc}</p>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* ===== ACERCA DE VIEW ===== */}
        {activeView === 'acerca' && (
          <div className="rounded-xl p-6 md:p-8" style={card}>
            <div className="flex items-start gap-4 mb-6">
              <img src={logo} alt="AMA LLU-IA" className="w-12 h-12 flex-shrink-0" />
              <div>
                <h2 className="text-xl font-bold" style={{ color: C.textPrimary }}>AMA LLU-IA</h2>
                <p className="text-sm mt-1" style={{ color: C.textMuted }}>
                  Plataforma de verificación de contenido electoral que ayuda a distinguir entre información verificada y desinformación,
                  analizando noticias, videos y audios para detectar patrones de manipulación y campañas de bots.
                </p>
              </div>
            </div>
            <h3 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: C.textFaint }}>
              Marco de gobernanza ética
            </h3>
            <ul className="grid sm:grid-cols-2 gap-2.5 text-sm">
              {[
                'Supervisión humana: los resultados son sugerencias, no decisiones finales',
                'Transparencia: metodología documentada y abierta',
                'Neutralidad política: no favorece candidatos ni partidos',
                'Privacidad: no almacena datos personales'
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-2" style={{ color: C.textPrimary }}>
                  <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: C.green }} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Status bar */}
        <div
          className="mt-3 flex items-center justify-between px-4 py-2.5 rounded-lg text-xs font-mono"
          style={{ ...card, color: C.textMuted }}
        >
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: C.green, animation: 'pulse-dot 2s ease-in-out infinite' }} />
            <span>Conectado</span>
          </div>
          <span>AMA-LLU-IA v1.0 · MediaHack II</span>
        </div>
      </div>

      {/* Floating Chat Button */}
      <button
        onClick={() => setChatOpen(!chatOpen)}
        className="fixed bottom-5 right-5 rounded-full flex items-center justify-center transition-all z-50 shadow-lg"
        style={{ width: '52px', height: '52px', backgroundColor: chatOpen ? C.navy : C.orange, color: '#FFFFFF' }}
        aria-label={chatOpen ? 'Cerrar chat' : 'Abrir chat'}
      >
        {chatOpen ? <X className="w-5 h-5" /> : <MessageCircle className="w-5 h-5" />}
      </button>

      {/* Chat Panel */}
      {chatOpen && (
        <div
          className="fixed bottom-20 right-5 w-[calc(100vw-2.5rem)] md:w-96 h-[420px] rounded-xl flex flex-col z-50 overflow-hidden shadow-xl"
          style={card}
        >
          <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: `1px solid ${C.border}`, backgroundColor: C.navy }}>
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: C.orange, animation: 'pulse-dot 2s ease-in-out infinite' }} />
            <h3 className="font-semibold text-sm text-white">Bot — preguntas ciudadanas</h3>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className="max-w-[80%] px-3.5 py-2.5 rounded-lg text-sm leading-relaxed"
                  style={
                    msg.role === 'user'
                      ? { backgroundColor: C.orange, color: '#FFFFFF', fontWeight: 500 }
                      : { backgroundColor: C.bg, color: C.textPrimary, border: `1px solid ${C.border}` }
                  }
                >
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <div className="p-3" style={{ borderTop: `1px solid ${C.border}` }}>
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                placeholder="Escribe tu pregunta..."
                className="flex-1 px-3 py-2.5 rounded-lg text-sm focus:outline-none"
                style={{ backgroundColor: C.bg, border: `1px solid ${C.border}`, color: C.textPrimary }}
              />
              <button
                onClick={handleSendMessage}
                className="px-3 py-2.5 rounded-lg transition-all flex items-center justify-center"
                style={{ backgroundColor: C.orange, color: '#FFFFFF' }}
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

function ResultList({ title, items, empty, colors }) {
  return (
    <div className="rounded-xl p-5" style={{ backgroundColor: colors.card, border: `1px solid ${colors.border}` }}>
      <h4 className="text-sm font-semibold mb-3" style={{ color: colors.textPrimary }}>{title}</h4>
      {items.length ? (
        <ul className="space-y-2">
          {items.slice(0, 6).map((item, index) => (
            <li key={index} className="text-xs leading-relaxed flex gap-2" style={{ color: colors.textMuted }}>
              <span className="mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: colors.orange }} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-xs" style={{ color: colors.textFaint }}>{empty}</p>
      )}
    </div>
  )
}

function KeywordPills({ items, colors }) {
  const keywords = items.filter(Boolean).slice(0, 10)
  if (!keywords.length) {
    return <p className="text-xs" style={{ color: colors.textFaint }}>Sin palabras clave detectadas.</p>
  }

  return (
    <div className="flex flex-wrap gap-2">
      {keywords.map((item, index) => (
        <span
          key={`${item}-${index}`}
          className="px-2.5 py-1 rounded-full text-xs font-mono"
          style={{ color: colors.navy, backgroundColor: colors.navyMuted, border: `1px solid ${colors.border}` }}
        >
          {item}
        </span>
      ))}
    </div>
  )
}

function resolveApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_NOTICIAS_API_URL
  if (configuredUrl && !configuredUrl.includes('localhost')) return configuredUrl
  if (typeof window === 'undefined') return configuredUrl || 'http://localhost:8001'

  const { protocol, hostname } = window.location
  if (hostname.endsWith('.app.github.dev')) {
    return `${protocol}//${hostname.replace('-5173.', '-8001.')}`
  }
  if (hostname.endsWith('.devtunnels.ms')) {
    return `${protocol}//${hostname.replace('-5173.', '-8001.')}`
  }
  if (hostname.includes('5173')) {
    return `${protocol}//${hostname.replace('5173', '8001')}`
  }

  return configuredUrl || 'http://localhost:8001'
}

function formatSeconds(value) {
  const total = Math.max(0, Math.floor(Number(value) || 0))
  const minutes = String(Math.floor(total / 60)).padStart(2, '0')
  const seconds = String(total % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}

export default App
