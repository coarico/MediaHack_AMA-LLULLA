import { useState, useRef, useEffect } from 'react'
import {
  MessageCircle, X, Send, Link as LinkIcon, Upload, ClipboardList, Search,
  AlertTriangle, CheckCircle2, XCircle, Activity, Info, TrendingUp, BookOpen,
  Home, Sparkles, Paperclip, ShieldCheck, Youtube, ExternalLink, Play,
  Volume2, Maximize2, Settings, Video, Image as ImageIcon, Music2, Radar as RadarIcon
} from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import logo from './assets/logo.svg'
import { analyzeUrl, analyzeAudio, analyzeVideo } from './services/api'

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
  const [progress, setProgress] = useState(0)
  const [statusMsg, setStatusMsg] = useState('')
  const [urlValue, setUrlValue] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [error, setError] = useState(null)
  const [heroQuery, setHeroQuery] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hola. Soy el asistente de AMA-LLU-IA. Puedes preguntarme sobre verificación de contenido electoral.' }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const chatEndRef = useRef(null)
  const fileInputRef = useRef(null)

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

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setProgress(0)
    setError(null)
    setAnalysisResult(null)

    const statusSteps = [
      { pct: 5, msg: 'Iniciando análisis...' },
      { pct: 10, msg: 'Descargando contenido de la plataforma...' },
      { pct: 18, msg: 'Verificando relevancia del contenido...' },
      { pct: 25, msg: 'Extrayendo audio del video...' },
      { pct: 35, msg: 'Transcribiendo audio con Whisper (modelo base)...' },
      { pct: 55, msg: 'Análisis paralelo: IA + web + fact-check...' },
      { pct: 72, msg: 'Analizando contenido con Llama 3.3 (Groq)...' },
      { pct: 82, msg: 'Generando veredicto final...' },
    ]
    let stepIdx = 0
    setStatusMsg(statusSteps[0].msg)

    const startTime = Date.now()
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 85) return prev
        const elapsed = (Date.now() - startTime) / 1000
        // Slow exponential approach: fast at start, slow at end
        // Target ~60s to reach 85%
        const target = 85 * (1 - Math.exp(-elapsed / 30))
        const next = Math.max(prev + 0.5, Math.min(target, 85))
        // Update status message based on progress
        while (stepIdx < statusSteps.length - 1 && next >= statusSteps[stepIdx + 1].pct) {
          stepIdx++
          setStatusMsg(statusSteps[stepIdx].msg)
        }
        return Math.min(next, 85)
      })
    }, 1000)

    try {
      let result
      
      if (activeTab === 'link' && urlValue) {
        result = await analyzeUrl(urlValue)
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
        result = await analyzeUrl(videoUrl)
      } else {
        throw new Error('Por favor ingresa una URL o selecciona un archivo')
      }

      setStatusMsg('Análisis completado')
      setProgress(100)
      setAnalysisResult(result)
    } catch (err) {
      setError(err.message || 'Error al procesar el análisis')
      console.error('Error al analizar:', err)
    } finally {
      clearInterval(progressInterval)
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

                  {/* Barra de progreso */}
                  {analyzing && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs" style={{ color: C.textMuted }}>{statusMsg || 'Procesando...'}</span>
                        <span className="text-xs font-mono" style={{ color: C.textMuted }}>{Math.min(Math.round(progress), 100)}%</span>
                      </div>
                      <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: C.bg }}>
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(progress, 100)}%`, backgroundColor: C.orange }}
                        />
                      </div>
                      <p className="text-xs mt-2" style={{ color: C.textFaint }}>⏱ Esto puede tardar 1-3 minutos dependiendo del video</p>
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
                  <div
                    className="rounded-lg p-8 text-center transition-all cursor-pointer"
                    style={{ border: `2px dashed ${C.border}`, backgroundColor: C.bg }}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="w-10 h-10 mx-auto mb-3" style={{ color: C.textFaint }} />
                    <p className="text-sm mb-1" style={{ color: C.textPrimary }}>
                      {selectedFile ? selectedFile.name : 'Arrastra un archivo o haz clic para seleccionar'}
                    </p>
                    <p className="text-xs font-mono" style={{ color: C.textFaint }}>
                      Video o audio · máx. 50MB
                    </p>
                    <input
                      type="file"
                      accept="video/*,audio/*"
                      className="hidden"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                    />
                  </div>

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
                    onClick={handleAnalyze}
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

                  {/* Barra de progreso */}
                  {analyzing && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs" style={{ color: C.textMuted }}>{statusMsg || 'Procesando...'}</span>
                        <span className="text-xs font-mono" style={{ color: C.textMuted }}>{Math.min(Math.round(progress), 100)}%</span>
                      </div>
                      <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: C.bg }}>
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(progress, 100)}%`, backgroundColor: C.orange }}
                        />
                      </div>
                      <p className="text-xs mt-2" style={{ color: C.textFaint }}>⏱ Esto puede tardar 1-3 minutos dependiendo del video</p>
                    </div>
                  )}
                </div>
              )}

              {/* Resultados del análisis */}
              {analysisResult && (() => {
                const sm = analysisResult.metadata?.source_metadata
                const segVs = analysisResult.content_analysis?.transcription?.segment_verifications || []
                const segs = analysisResult.content_analysis?.transcription?.segments || []
                const fcs = analysisResult.content_analysis?.fact_checking?.fact_checks || []
                const fcCount = analysisResult.content_analysis?.fact_checking?.fact_checks_found || 0
                const totalSegs = segVs.length || segs.length || 0
                const verified = segVs.filter(s => s.label === 'VERIFICADO').length
                const imprecise = segVs.filter(s => s.label === 'IMPRECISO' || s.label === 'ENGAÑOSO').length
                const falseCount = segVs.filter(s => s.label === 'FALSO').length
                const unverified = totalSegs - verified - imprecise - falseCount
                const sourceUrl = sm?.source_url || ''
                const platform = sm?.platform || ''
                const videoTitle = sm?.title || analysisResult.metadata?.filename || 'contenido analizado'
                const channel = sm?.channel || ''

                // Detectar plataforma y generar embed URL
                const platforms = {
                  youtube: {
                    match: /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/|v\/)|youtu\.be\/)([^&\n?#]+)/,
                    embed: (id) => `https://www.youtube.com/embed/${id}`,
                    icon: Youtube, color: '#FF0000', bg: C.redSoft, label: 'YouTube',
                    thumb: (id) => `https://img.youtube.com/vi/${id}/hqdefault.jpg`,
                    searchBase: 'https://www.youtube.com/results?search_query='
                  },
                  tiktok: {
                    match: /tiktok\.com\/(@[\w.-]+\/video\/|v\/)(\d+)/,
                    embed: (id) => `https://www.tiktok.com/embed/v2/${id}`,
                    icon: Music2, color: '#000000', bg: C.navyMuted, label: 'TikTok',
                    thumb: null,
                    searchBase: 'https://www.tiktok.com/search?q='
                  },
                  instagram: {
                    match: /instagram\.com\/(reel|p)\/([^/?]+)/,
                    embed: (id) => `https://www.instagram.com/p/${id}/embed`,
                    icon: ImageIcon, color: '#E1306C', bg: 'rgba(225,48,108,0.1)', label: 'Instagram',
                    thumb: null,
                    searchBase: 'https://www.instagram.com/explore/tags/'
                  },
                  facebook: {
                    match: /facebook\.com\/(?:watch\?v=|.*\/videos\/)(\d+)/,
                    embed: (id) => `https://www.facebook.com/plugins/video.php?href=https://www.facebook.com/watch?v=${id}`,
                    icon: ShieldCheck, color: '#1877F2', bg: 'rgba(24,119,242,0.1)', label: 'Facebook',
                    thumb: null,
                    searchBase: 'https://www.facebook.com/search/top?q='
                  },
                  twitter: {
                    match: /(?:twitter|x)\.com\/\w+\/status\/(\d+)/,
                    embed: (id) => `https://platform.twitter.com/embed/Tweet.html?id=${id}`,
                    icon: MessageCircle, color: '#000000', bg: C.navyMuted, label: 'X/Twitter',
                    thumb: null,
                    searchBase: 'https://twitter.com/search?q='
                  },
                  vimeo: {
                    match: /vimeo\.com\/(\d+)/,
                    embed: (id) => `https://player.vimeo.com/video/${id}`,
                    icon: Play, color: '#17AEE9', bg: 'rgba(23,174,233,0.1)', label: 'Vimeo',
                    thumb: null,
                    searchBase: 'https://vimeo.com/search?q='
                  },
                  dailymotion: {
                    match: /(?:dailymotion\.com\/video\/|dai\.ly\/)([a-zA-Z0-9]+)/,
                    embed: (id) => `https://www.dailymotion.com/embed/video/${id}`,
                    icon: Play, color: '#0066DC', bg: 'rgba(0,102,220,0.1)', label: 'Dailymotion',
                    thumb: null,
                    searchBase: 'https://www.dailymotion.com/search?q='
                  },
                  twitch: {
                    match: /(?:clips\.twitch\.tv\/|twitch\.tv\/\w+\/clip\/)([a-zA-Z0-9_-]+)/,
                    embed: (id) => `https://clips.twitch.tv/embed?clip=${id}&parent=localhost`,
                    icon: Play, color: '#9146FF', bg: 'rgba(145,70,255,0.1)', label: 'Twitch',
                    thumb: null,
                    searchBase: 'https://www.twitch.tv/search?term='
                  },
                  reddit: {
                    match: /reddit\.com\/(?:r\/\w+\/comments\/|video\/)([a-zA-Z0-9]+)/,
                    embed: (id) => `https://www.redditmedia.com/mediaembed/${id}`,
                    icon: MessageCircle, color: '#FF4500', bg: 'rgba(255,69,0,0.1)', label: 'Reddit',
                    thumb: null,
                    searchBase: 'https://www.reddit.com/search/?q='
                  },
                  bilibili: {
                    match: /(?:bilibili\.com\/video\/|b23\.tv\/)([a-zA-Z0-9]+)/,
                    embed: (id) => `https://player.bilibili.com/player.html?bvid=${id}`,
                    icon: Play, color: '#FB7299', bg: 'rgba(251,114,153,0.1)', label: 'Bilibili',
                    thumb: null,
                    searchBase: 'https://search.bilibili.com/all?keyword='
                  }
                }

                let activePlatform = null
                let embedId = null
                let embedUrl = null
                let thumbUrl = sm?.thumbnail || null

                for (const [key, p] of Object.entries(platforms)) {
                  const m = sourceUrl.match(p.match)
                  if (m) {
                    activePlatform = p
                    embedId = m[2] || m[1]
                    embedUrl = p.embed(embedId)
                    if (!thumbUrl && p.thumb) {
                      thumbUrl = p.thumb(embedId)
                    }
                    break
                  }
                }

                const PlatIcon = activePlatform ? activePlatform.icon : Play
                const platColor = activePlatform ? activePlatform.color : C.textFaint
                const platBg = activePlatform ? activePlatform.bg : C.navyMuted
                const platLabel = activePlatform ? activePlatform.label : 'Video'
                const searchBase = activePlatform ? activePlatform.searchBase : 'https://www.google.com/search?q='

                return (
                  <div className="mt-6 space-y-4">
                    {/* VIDEO + INFO LADO A LADO */}
                    <div className="rounded-xl overflow-hidden" style={card}>
                      <div className="flex flex-col md:flex-row">
                        {/* Video - izquierda */}
                        <div className="md:flex-1 md:min-w-0">
                          {embedUrl ? (
                            <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                              <iframe
                                className="absolute top-0 left-0 w-full h-full"
                                src={embedUrl}
                                title="Video player"
                                frameBorder="0"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                              />
                            </div>
                          ) : sourceUrl ? (
                            <div className="w-full" style={{ backgroundColor: '#000' }}>
                              <video controls className="w-full" style={{ maxHeight: '400px' }}>
                                <source src={sourceUrl} />
                                Tu navegador no soporta el elemento de video.
                              </video>
                            </div>
                          ) : thumbUrl ? (
                            <a href={sourceUrl || '#'} target="_blank" rel="noopener noreferrer" className="block relative w-full" style={{ paddingBottom: '56.25%', backgroundColor: '#000' }}>
                              <img src={thumbUrl} alt={videoTitle} className="absolute top-0 left-0 w-full h-full object-cover" />
                              <div className="absolute inset-0 flex items-center justify-center">
                                <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}>
                                  <Play className="w-6 h-6 text-white" />
                                </div>
                              </div>
                            </a>
                          ) : (
                            <div className="w-full flex items-center justify-center" style={{ backgroundColor: C.bg, height: '300px' }}>
                              <div className="text-center">
                                <Play className="w-10 h-10 mx-auto mb-2" style={{ color: C.textFaint }} />
                                <p className="text-sm" style={{ color: C.textMuted }}>Video analizado</p>
                              </div>
                            </div>
                          )}
                        </div>
                        {/* Descripción - derecha */}
                        {sm && (
                          <div className="md:w-80 md:flex-shrink-0 p-5 flex flex-col justify-between" style={{ borderLeft: '1px solid ' + C.border }}>
                            <div>
                              <div className="flex items-center gap-2 mb-3">
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: platBg }}>
                                  <PlatIcon className="w-4 h-4" style={{ color: platColor }} />
                                </div>
                                <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ backgroundColor: platBg, color: platColor }}>{platLabel}</span>
                              </div>
                              <p className="text-sm font-semibold mb-2" style={{ color: C.textPrimary }}>{sm.title}</p>
                              <p className="text-xs mb-3" style={{ color: C.textMuted }}>
                                <span className="font-medium" style={{ color: C.textPrimary }}>{sm.channel}</span>
                                {sm.is_verified ? (
                                  <span className="ml-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded" style={{ backgroundColor: C.greenSoft, color: C.green }}>
                                    <CheckCircle2 className="w-3 h-3" /> Verificado
                                  </span>
                                ) : (
                                  <span className="ml-2 inline-flex items-center gap-1 px-1.5 py-0.5 rounded" style={{ backgroundColor: C.amberSoft, color: C.amber }}>
                                    <AlertTriangle className="w-3 h-3" /> No verificado
                                  </span>
                                )}
                              </p>
                              <div className="space-y-1.5 text-xs" style={{ color: C.textMuted }}>
                                {sm.view_count > 0 && <div>👁 {sm.view_count.toLocaleString()} vistas</div>}
                                {sm.duration > 0 && <div>⏱ {Math.floor(sm.duration / 60)}:{String(sm.duration % 60).padStart(2, '0')}</div>}
                                {sm.upload_date && <div>📅 {sm.upload_date}</div>}
                              </div>
                            </div>
                            {sourceUrl && (
                              <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="mt-4 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all hover:opacity-80" style={{ backgroundColor: platBg, color: platColor }}>
                                <ExternalLink className="w-3.5 h-3.5" /> Ver original en {platLabel}
                              </a>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* ANÁLISIS IA (LLM) */}
                    {analysisResult.content_analysis?.llm_analysis && (() => {
                      const llm = analysisResult.content_analysis.llm_analysis
                      const verdictColors = { 'AUTÉNTICO': C.green, 'MIXTO': C.amber, 'ENGAÑOSO': '#EAB308', 'FALSO': C.red, 'NO_APLICABLE': C.gray }
                      const vColor = verdictColors[llm.veredicto] || C.gray
                      const vIcon = llm.veredicto === 'AUTÉNTICO' ? CheckCircle2 : llm.veredicto === 'FALSO' ? XCircle : llm.veredicto === 'NO_APLICABLE' ? AlertTriangle : AlertTriangle
                      const VIcon = vIcon
                      const isNotRelevant = llm.veredicto === 'NO_APLICABLE' || llm.is_relevant === false
                      return (
                        <div className="rounded-xl p-5" style={{ ...card, border: `2px solid ${vColor}40` }}>
                          <div className="flex items-center gap-2 mb-4">
                            <div className="w-1 h-5 rounded-full" style={{ backgroundColor: vColor }} />
                            <h4 className="text-sm font-bold tracking-wide" style={{ color: C.textPrimary }}>ANÁLISIS IA</h4>
                            <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: vColor + '20', color: vColor }}>
                              {llm.model_used?.includes('llama') ? 'Llama 3.3' : 'LLM'}
                            </span>
                          </div>

                          {/* Veredicto principal */}
                          <div className="rounded-lg p-4 mb-4" style={{ backgroundColor: vColor + '15', border: `1px solid ${vColor}30` }}>
                            {isNotRelevant ? (
                              <div className="text-center py-4">
                                <AlertTriangle className="w-10 h-10 mx-auto mb-3" style={{ color: C.amber }} />
                                <p className="text-base font-bold mb-2" style={{ color: C.amber }}>CONTENIDO NO APLICABLE PARA VERIFICACIÓN</p>
                                <p className="text-sm leading-relaxed mb-3" style={{ color: C.textPrimary }}>{llm.observaciones || llm.resumen}</p>
                                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ backgroundColor: C.amberSoft, color: C.amber }}>
                                  <span className="text-xs font-medium">Categoría detectada: {llm.relevance_category || llm.tema_principal || 'No relevante'}</span>
                                </div>
                                <p className="text-xs mt-3" style={{ color: C.textMuted }}>
                                  Este contenido no corresponde a noticias, política, discursos ni claims verificables.
                                  No se realizó análisis de transcripción ni búsqueda de fuentes para optimizar recursos.
                                </p>
                              </div>
                            ) : (
                              <>
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    <VIcon className="w-6 h-6" style={{ color: vColor }} />
                                    <span className="text-lg font-bold" style={{ color: vColor }}>{llm.veredicto}</span>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-2xl font-bold font-mono" style={{ color: vColor }}>{llm.confianza}%</div>
                                    <div className="text-xs" style={{ color: C.textMuted }}>Confianza</div>
                                  </div>
                                </div>
                                <p className="text-sm leading-relaxed" style={{ color: C.textPrimary }}>{llm.resumen}</p>
                              </>
                            )}
                          </div>

                          {/* Si no es relevante, no mostrar el resto del análisis */}
                          {!isNotRelevant && (
                            <>

                          {/* Tema y contexto */}
                          <div className="grid md:grid-cols-2 gap-3 mb-4">
                            {llm.tema_principal && (
                              <div className="rounded-lg p-3" style={{ backgroundColor: C.bg }}>
                                <p className="text-xs font-semibold mb-1" style={{ color: C.textMuted }}>TEMA PRINCIPAL</p>
                                <p className="text-sm" style={{ color: C.textPrimary }}>{llm.tema_principal}</p>
                              </div>
                            )}
                            {llm.contexto_politico && (
                              <div className="rounded-lg p-3" style={{ backgroundColor: C.bg }}>
                                <p className="text-xs font-semibold mb-1" style={{ color: C.textMuted }}>CONTEXTO POLÍTICO</p>
                                <p className="text-sm" style={{ color: C.textPrimary }}>{llm.contexto_politico}</p>
                              </div>
                            )}
                          </div>

                          {/* Afirmaciones clave del LLM */}
                          {llm.afirmaciones_clave?.length > 0 && (
                            <div className="mb-4">
                              <p className="text-xs font-semibold mb-2" style={{ color: C.textMuted }}>AFIRMACIONES DETECTADAS POR IA</p>
                              <div className="space-y-2">
                                {llm.afirmaciones_clave.map((claim, idx) => (
                                  <div key={idx} className="flex items-start gap-2 rounded-lg p-2.5" style={{ backgroundColor: C.bg }}>
                                    <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold" style={{ backgroundColor: vColor + '20', color: vColor }}>{idx + 1}</div>
                                    <p className="text-xs leading-relaxed" style={{ color: C.textPrimary }}>{claim}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Observaciones */}
                          {llm.observaciones && (
                            <div className="rounded-lg p-3" style={{ backgroundColor: C.bg }}>
                              <p className="text-xs font-semibold mb-1" style={{ color: C.textMuted }}>OBSERVACIONES</p>
                              <p className="text-xs leading-relaxed" style={{ color: C.textPrimary }}>{llm.observaciones}</p>
                            </div>
                          )}

                          {/* Fuentes en las que se basó el análisis */}
                          {(() => {
                            const wc = analysisResult.content_analysis?.web_context || {}
                            const articles = wc.articles || []
                            const cr = wc.cross_reference || {}
                            const matchingArticles = cr.matching_articles || []
                            const hasSources = articles.length > 0
                            const hasMatches = matchingArticles.length > 0
                            return (
                              <div className="mt-4">
                                {/* Badge de coincidencia - consistente con fuentes reales */}
                                {llm.coincide_con_fuentes !== undefined && (
                                  <div className="mb-3">
                                    {hasSources && hasMatches ? (
                                      <span className="text-xs flex items-center gap-1 px-2 py-1 rounded" style={{ backgroundColor: C.greenSoft, color: C.green }}>
                                        <CheckCircle2 className="w-3 h-3" /> La IA confirma coincidencia con {matchingArticles.length} fuente(s) encontrada(s)
                                      </span>
                                    ) : hasSources ? (
                                      <span className="text-xs flex items-center gap-1 px-2 py-1 rounded" style={{ backgroundColor: C.amberSoft, color: C.amber }}>
                                        <AlertTriangle className="w-3 h-3" /> Se encontraron {articles.length} fuente(s) pero la IA no encuentra coincidencia clara
                                      </span>
                                    ) : (
                                      <span className="text-xs flex items-center gap-1 px-2 py-1 rounded" style={{ backgroundColor: C.amberSoft, color: C.amber }}>
                                        <AlertTriangle className="w-3 h-3" /> No se encontraron fuentes web para verificar el contenido
                                      </span>
                                    )}
                                  </div>
                                )}

                                {/* Fuentes reales encontradas */}
                                {articles.length > 0 ? (
                                  <div>
                                    <p className="text-xs font-semibold mb-2" style={{ color: C.textMuted }}>FUENTES CONSULTADAS PARA EL ANÁLISIS ({articles.length})</p>
                                    <div className="space-y-2">
                                      {articles.slice(0, 8).map((article, idx) => {
                                        const isReliable = matchingArticles.some(m => m.url === article.url && m.is_reliable)
                                        return (
                                          <a key={idx} href={article.url} target="_blank" rel="noopener noreferrer" className="block rounded-lg p-3 transition-all hover:shadow-md" style={{ backgroundColor: isReliable ? C.greenSoft : C.bg, border: `1px solid ${isReliable ? C.green + '30' : C.border}`, textDecoration: 'none' }}>
                                            <div className="flex items-start gap-2">
                                              <span className="font-mono text-xs flex-shrink-0" style={{ color: C.textFaint }}>{idx + 1}</span>
                                              <div className="flex-1 min-w-0">
                                                <p className="text-xs font-medium mb-1 line-clamp-2" style={{ color: C.textPrimary }}>{article.title}</p>
                                                <div className="flex items-center gap-2 flex-wrap">
                                                  <span className="text-xs" style={{ color: C.textMuted }}>📰 {article.source}</span>
                                                  {article.date && <span className="text-xs" style={{ color: C.textFaint }}>{article.date}</span>}
                                                  {isReliable && (
                                                    <span className="text-xs px-1.5 py-0.5 rounded font-medium flex items-center gap-0.5" style={{ backgroundColor: C.greenSoft, color: C.green }}>
                                                      <CheckCircle2 className="w-2.5 h-2.5" /> Confiable
                                                    </span>
                                                  )}
                                                  <ExternalLink className="w-3 h-3 ml-auto" style={{ color: C.textFaint }} />
                                                </div>
                                                {article.snippet && (
                                                  <p className="text-xs mt-1 line-clamp-2" style={{ color: C.textMuted }}>{article.snippet}</p>
                                                )}
                                              </div>
                                            </div>
                                          </a>
                                        )
                                      })}
                                    </div>
                                  </div>
                                ) : (
                                  <div className="rounded-lg p-3" style={{ backgroundColor: C.bg }}>
                                    <p className="text-xs" style={{ color: C.textMuted }}>No se encontraron fuentes web relacionadas para este contenido. El análisis se basó únicamente en la transcripción y conocimiento del modelo.</p>
                                  </div>
                                )}
                              </div>
                            )
                          })()
                          }
                            </>
                          )}
                        </div>
                      )
                    })()}

                    {/* RESUMEN DEL ANÁLISIS */}
                    <div className="rounded-xl p-5" style={card}>
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-1 h-5 rounded-full" style={{ backgroundColor: C.orange }} />
                        <h4 className="text-sm font-bold tracking-wide" style={{ color: C.textPrimary }}>RESUMEN DEL ANÁLISIS</h4>
                      </div>
                      {/* Info del análisis */}
                      <div className="grid grid-cols-3 gap-3 mb-4">
                        <div className="rounded-lg p-3 text-center" style={{ backgroundColor: C.bg }}>
                          <div className="text-xl font-bold font-mono" style={{ color: C.textPrimary }}>{analysisResult.analysis_type || 'N/A'}</div>
                          <div className="text-xs mt-1" style={{ color: C.textMuted }}>Tipo de análisis</div>
                        </div>
                        <div className="rounded-lg p-3 text-center" style={{ backgroundColor: C.bg }}>
                          <div className="text-xl font-bold font-mono" style={{ color: C.textPrimary }}>{analysisResult.content_analysis?.transcription?.language || 'N/A'}</div>
                          <div className="text-xs mt-1" style={{ color: C.textMuted }}>Idioma detectado</div>
                        </div>
                        <div className="rounded-lg p-3 text-center" style={{ backgroundColor: C.bg }}>
                          <div className="text-xl font-bold font-mono" style={{ color: C.textPrimary }}>{fcCount}</div>
                          <div className="text-xs mt-1" style={{ color: C.textMuted }}>Fact-checks encontrados</div>
                        </div>
                      </div>
                      {/* Claims extraídos */}
                      {analysisResult.content_analysis?.extracted_claims?.length > 0 && (
                        <div className="mb-4">
                          <p className="text-xs font-semibold mb-2" style={{ color: C.textMuted }}>AFIRMACIONES CLAVE DETECTADAS</p>
                          <div className="space-y-2">
                            {analysisResult.content_analysis.extracted_claims.slice(0, 5).map((claim, idx) => (
                              <div key={idx} className="flex items-start gap-2 rounded-lg p-2.5" style={{ backgroundColor: C.bg }}>
                                <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold" style={{ backgroundColor: C.orange + '20', color: C.orange }}>{idx + 1}</div>
                                <p className="text-xs leading-relaxed" style={{ color: C.textPrimary }}>{claim}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {/* Transcripción resumida */}
                      {analysisResult.content_analysis?.has_transcription && analysisResult.content_analysis?.transcription?.text && (
                        <div>
                          <p className="text-xs font-semibold mb-2" style={{ color: C.textMuted }}>TRANSCRIPCIÓN COMPLETA</p>
                          <div className="rounded-lg p-3 max-h-32 overflow-y-auto" style={{ backgroundColor: C.bg }}>
                            <p className="text-xs leading-relaxed" style={{ color: C.textPrimary }}>{analysisResult.content_analysis.transcription.text}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* VERIFICACIONES RELACIONADAS */}
                    {fcCount > 0 && (
                      <div className="rounded-xl p-5" style={card}>
                        <div className="flex items-center gap-2 mb-4">
                          <div className="w-1 h-5 rounded-full" style={{ backgroundColor: '#3B82F6' }} />
                          <h4 className="text-sm font-bold tracking-wide" style={{ color: C.textPrimary }}>VERIFICACIONES RELACIONADAS</h4>
                          <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(59,130,246,0.1)', color: '#3B82F6' }}>{fcCount} encontradas</span>
                        </div>
                        <div className="space-y-3">
                          {fcs.slice(0, 4).map((fc, idx) => {
                            const ratingLower = (fc.rating || '').toLowerCase()
                            const isFalse = ratingLower.includes('false') || ratingLower.includes('falso')
                            const isTrue = ratingLower.includes('true') || ratingLower.includes('verdadero')
                            const ratingColor = isFalse ? C.red : isTrue ? C.green : C.amber
                            return (
                              <div key={idx} className="rounded-lg p-3" style={{ backgroundColor: C.bg }}>
                                <p className="text-sm font-medium mb-2" style={{ color: C.textPrimary }}>{fc.title}</p>
                                <div className="flex items-center gap-3 flex-wrap">
                                  <span className="text-xs" style={{ color: C.textMuted }}>📰 {fc.publisher}</span>
                                  <span className="text-xs px-2 py-0.5 rounded font-semibold" style={{ backgroundColor: ratingColor + '20', color: ratingColor }}>{fc.rating}</span>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}

                    {/* DETECCIÓN DE IA / DEEPFAKE */}
                    {(() => {
                      const isAI = analysisResult.is_ai_generated
                      const isManipulated = analysisResult.is_manipulated
                      const confidence = analysisResult.confidence
                      // If content is authentic, invert: 25% AI risk = 75% authenticity confidence
                      const aiScore = isAI ? Math.round(confidence * 100) : Math.round((1 - confidence) * 100)
                      const aiColor = isAI ? C.red : isManipulated ? C.amber : C.green
                      const aiIcon = isAI ? XCircle : isManipulated ? AlertTriangle : CheckCircle2
                      const AiIcon = aiIcon
                      const aiLabel = isAI ? 'CONTENIDO GENERADO POR IA' : isManipulated ? 'CONTENIDO MANIPULADO' : 'CONTENIDO AUTÉNTICO'
                      const aiDesc = isAI
                        ? `Este ${analysisResult.analysis_type === 'video' ? 'video' : 'audio'} presenta patrones consistentes con generación artificial (deepfake). Confianza: ${aiScore}%`
                        : isManipulated
                        ? `Se detectaron anomalías que sugieren manipulación o edición sospechosa. Confianza: ${aiScore}%`
                        : `No se detectaron indicios de generación artificial ni manipulación. El contenido parece genuino.`
                      const vd = analysisResult.video_details
                      const ad = analysisResult.audio_details
                      return (
                        <div className="rounded-xl p-5" style={{ ...card, border: `2px solid ${aiColor}40` }}>
                          <div className="flex items-center gap-2 mb-4">
                            <div className="w-1 h-5 rounded-full" style={{ backgroundColor: aiColor }} />
                            <h4 className="text-sm font-bold tracking-wide" style={{ color: C.textPrimary }}>DETECCIÓN DE IA</h4>
                            <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: aiColor + '20', color: aiColor }}>
                              {analysisResult.analysis_type === 'video' ? 'Video' : 'Audio'}
                            </span>
                          </div>

                          {/* Veredicto IA */}
                          <div className="rounded-lg p-4 mb-4" style={{ backgroundColor: aiColor + '15', border: `1px solid ${aiColor}30` }}>
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <AiIcon className="w-6 h-6" style={{ color: aiColor }} />
                                <span className="text-base font-bold" style={{ color: aiColor }}>{aiLabel}</span>
                              </div>
                              <div className="text-right">
                                <div className="text-2xl font-bold font-mono" style={{ color: aiColor }}>{aiScore}%</div>
                                <div className="text-xs" style={{ color: C.textMuted }}>Confianza</div>
                              </div>
                            </div>
                            <p className="text-sm leading-relaxed" style={{ color: C.textPrimary }}>{aiDesc}</p>
                          </div>

                          {/* Métricas técnicas */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                            {vd && (
                              <>
                                <div className="rounded-lg p-2.5 text-center" style={{ backgroundColor: C.bg }}>
                                  <div className="text-lg font-bold font-mono" style={{ color: vd.facial_consistency !== null ? (vd.facial_consistency > 0.7 ? C.green : C.amber) : C.textFaint }}>
                                    {vd.facial_consistency !== null ? `${Math.round(vd.facial_consistency * 100)}%` : 'N/A'}
                                  </div>
                                  <div className="text-xs" style={{ color: C.textMuted }}>Consistencia facial</div>
                                </div>
                                <div className="rounded-lg p-2.5 text-center" style={{ backgroundColor: C.bg }}>
                                  <div className="text-lg font-bold font-mono" style={{ color: vd.frame_artifacts !== null ? (vd.frame_artifacts < 0.3 ? C.green : C.amber) : C.textFaint }}>
                                    {vd.frame_artifacts !== null ? `${Math.round(vd.frame_artifacts * 100)}%` : 'N/A'}
                                  </div>
                                  <div className="text-xs" style={{ color: C.textMuted }}>Artefactos frame</div>
                                </div>
                                <div className="rounded-lg p-2.5 text-center" style={{ backgroundColor: C.bg }}>
                                  <div className="text-lg font-bold font-mono" style={{ color: vd.compression_anomalies !== null ? (vd.compression_anomalies < 0.3 ? C.green : C.amber) : C.textFaint }}>
                                    {vd.compression_anomalies !== null ? `${Math.round(vd.compression_anomalies * 100)}%` : 'N/A'}
                                  </div>
                                  <div className="text-xs" style={{ color: C.textMuted }}>Anomalías compresión</div>
                                </div>
                              </>
                            )}
                            {ad && (
                              <>
                                <div className="rounded-lg p-2.5 text-center" style={{ backgroundColor: C.bg }}>
                                  <div className="text-lg font-bold font-mono" style={{ color: ad.spectral_score < 0.3 ? C.green : C.amber }}>
                                    {Math.round(ad.spectral_score * 100)}%
                                  </div>
                                  <div className="text-xs" style={{ color: C.textMuted }}>Análisis espectral</div>
                                </div>
                                <div className="rounded-lg p-2.5 text-center" style={{ backgroundColor: C.bg }}>
                                  <div className="text-lg font-bold font-mono" style={{ color: ad.pitch_consistency > 0.7 ? C.green : C.amber }}>
                                    {Math.round(ad.pitch_consistency * 100)}%
                                  </div>
                                  <div className="text-xs" style={{ color: C.textMuted }}>Consistencia pitch</div>
                                </div>
                                <div className="rounded-lg p-2.5 text-center" style={{ backgroundColor: C.bg }}>
                                  <div className="text-lg font-bold font-mono" style={{ color: ad.noise_detection < 0.3 ? C.green : C.amber }}>
                                    {Math.round(ad.noise_detection * 100)}%
                                  </div>
                                  <div className="text-xs" style={{ color: C.textMuted }}>Ruido artificial</div>
                                </div>
                                {ad.ml_score !== null && (
                                  <div className="rounded-lg p-2.5 text-center" style={{ backgroundColor: C.bg }}>
                                    <div className="text-lg font-bold font-mono" style={{ color: ad.ml_score < 0.3 ? C.green : C.red }}>
                                      {Math.round(ad.ml_score * 100)}%
                                    </div>
                                    <div className="text-xs" style={{ color: C.textMuted }}>Score ML deepfake</div>
                                  </div>
                                )}
                              </>
                            )}
                          </div>

                          {/* Artefactos detectados */}
                          {(vd?.artifacts?.length > 0 || ad?.artifacts?.length > 0) && (
                            <div className="mt-3 space-y-1.5">
                              <p className="text-xs font-semibold" style={{ color: C.textMuted }}>ARTEFACTOS DETECTADOS</p>
                              {(vd?.artifacts || []).concat(ad?.artifacts || []).map((art, idx) => (
                                <div key={idx} className="flex items-start gap-2 rounded-lg p-2" style={{ backgroundColor: C.bg }}>
                                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" style={{ color: C.amber }} />
                                  <div>
                                    <p className="text-xs font-medium" style={{ color: C.textPrimary }}>{art.type}</p>
                                    <p className="text-xs" style={{ color: C.textMuted }}>{art.description}</p>
                                  </div>
                                  <span className="text-xs font-mono ml-auto" style={{ color: C.amber }}>{Math.round(art.confidence * 100)}%</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )
                    })()}

                    {/* INFO TÉCNICA */}
                    <div className="rounded-xl p-4" style={card}>
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-1 h-5 rounded-full" style={{ backgroundColor: C.gray }} />
                        <h4 className="text-xs font-bold tracking-wide" style={{ color: C.textPrimary }}>INFO TÉCNICA</h4>
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-xs">
                        <div className="rounded-lg p-2.5" style={{ backgroundColor: C.bg }}>
                          <p style={{ color: C.textMuted }}>Formato</p>
                          <p className="font-mono font-bold mt-1" style={{ color: C.textPrimary }}>{analysisResult.metadata?.format || 'N/A'}</p>
                        </div>
                        <div className="rounded-lg p-2.5" style={{ backgroundColor: C.bg }}>
                          <p style={{ color: C.textMuted }}>Duración</p>
                          <p className="font-mono font-bold mt-1" style={{ color: C.textPrimary }}>{analysisResult.metadata?.duration ? `${analysisResult.metadata.duration.toFixed(1)}s` : 'N/A'}</p>
                        </div>
                        <div className="rounded-lg p-2.5" style={{ backgroundColor: C.bg }}>
                          <p style={{ color: C.textMuted }}>Procesado</p>
                          <p className="font-mono font-bold mt-1" style={{ color: C.textPrimary }}>{analysisResult.processing_time?.toFixed(2) || 'N/A'}s</p>
                        </div>
                      </div>
                    </div>

                    {/* VIDEOS RELACIONADOS */}
                    <div className="rounded-xl p-5" style={card}>
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-1 h-5 rounded-full" style={{ backgroundColor: C.orange }} />
                        <h4 className="text-sm font-bold tracking-wide" style={{ color: C.textPrimary }}>VIDEOS RELACIONADOS</h4>
                      </div>
                      <div className="grid md:grid-cols-3 gap-4">
                        {(() => {
                          const webArticles = analysisResult.content_analysis?.web_context?.articles || []
                          const llmTopic = analysisResult.content_analysis?.llm_analysis?.tema_principal || ''
                          const llmContext = analysisResult.content_analysis?.llm_analysis?.contexto_politico || ''
                          // For uploads: use LLM topic + context for better related videos
                          const searchTopic = llmTopic ? `${llmTopic} ${llmContext}`.trim() : videoTitle
                          const relatedVideos = [
                            { title: llmTopic ? `${llmTopic} - análisis` : `${videoTitle} - análisis`, url: `${searchBase}${encodeURIComponent(searchTopic + ' análisis')}`, thumb: webArticles[0]?.image || thumbUrl, source: webArticles[0]?.source || platLabel },
                            { title: channel ? `Más de ${channel}` : (llmTopic ? `Más sobre ${llmTopic}` : 'Videos del mismo tema'), url: `${searchBase}${encodeURIComponent(channel || searchTopic)}`, thumb: webArticles[1]?.image || null, source: webArticles[1]?.source || platLabel },
                            { title: 'Verificación de hechos', url: `${searchBase}${encodeURIComponent(searchTopic + ' verificación fact check')}`, thumb: webArticles[2]?.image || null, source: webArticles[2]?.source || platLabel }
                          ]
                          return relatedVideos.map((video, idx) => (
                          <a key={idx} href={video.url} target="_blank" rel="noopener noreferrer" className="rounded-lg overflow-hidden block transition-all hover:shadow-md" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
                            <div className="aspect-video flex items-center justify-center relative" style={{ backgroundColor: C.navyMuted }}>
                              {video.thumb ? (
                                <img src={video.thumb} alt={video.title} className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }} />
                              ) : null}
                              <div className="w-full h-full items-center justify-center" style={{ display: video.thumb ? 'none' : 'flex' }}>
                                <Play className="w-8 h-8" style={{ color: C.textFaint }} />
                              </div>
                              <div className="absolute bottom-2 right-2 w-7 h-7 rounded-full flex items-center justify-center" style={{ backgroundColor: platBg }}>
                                <PlatIcon className="w-4 h-4" style={{ color: platColor }} />
                              </div>
                            </div>
                            <div className="p-3">
                              <p className="text-xs font-medium mb-1 line-clamp-2" style={{ color: C.textPrimary }}>{video.title}</p>
                              <div className="flex items-center justify-between">
                                <span className="text-xs" style={{ color: C.textMuted }}>📰 {video.source}</span>
                                <ExternalLink className="w-3 h-3" style={{ color: C.textFaint }} />
                              </div>
                            </div>
                          </a>
                          ))
                        })()}
                      </div>
                    </div>
                  </div>
                )
              })()}

              {/* Error */}
              {error && (
                <div className="mt-4 rounded-lg border p-4" style={{ backgroundColor: C.redSoft, borderColor: C.red }}>
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: C.red }} />
                    <p className="text-xs" style={{ color: C.red }}>{error}</p>
                  </div>
                </div>
              )}

              {/* Auditor */}
              {activeTab === 'auditor' && (
                <div className="space-y-4">
                  <div className="mb-2">
                    <div className="flex items-center gap-2 mb-2">
                      <ClipboardList className="w-5 h-5" style={{ color: C.navy }} />
                      <h3 className="text-base font-semibold" style={{ color: C.textPrimary }}>Criterios de evaluación</h3>
                    </div>
                    <p className="text-xs leading-relaxed" style={{ color: C.textMuted }}>
                      Estos son los 5 criterios que utilizamos para verificar la autenticidad del contenido electoral
                    </p>
                  </div>
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

export default App
