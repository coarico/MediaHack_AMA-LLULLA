import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Link as LinkIcon, Upload, ClipboardList, Search, AlertTriangle, CheckCircle2, XCircle, Activity, Info, TrendingUp, BookOpen, Shield, Home, Play } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { analyzeUrl, analyzeAudio, analyzeVideo } from './services/api'

function App() {
  const [activeView, setActiveView] = useState('home')
  const [activeTab, setActiveTab] = useState('link')
  const [chatOpen, setChatOpen] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [urlValue, setUrlValue] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [error, setError] = useState(null)
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hola. Soy el asistente de AMA-LLU-IA. Puedes preguntarme sobre verificación de contenido electoral.' }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const chatEndRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const chartData = [
    { name: 'Verificado', value: 55, color: '#00C896' },
    { name: 'Dudoso', value: 30, color: '#E8A33D' },
    { name: 'Falso', value: 15, color: '#E85D5D' }
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

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setProgress(0)
    setError(null)
    setAnalysisResult(null)

    // Simular progreso durante el análisis
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return prev
        return prev + Math.random() * 15
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
        // Usar videoUrl si no hay archivo seleccionado
        result = await analyzeUrl(videoUrl)
      } else {
        throw new Error('Por favor ingresa una URL o selecciona un archivo')
      }

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
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#00C896' }}>
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">AMA-LLU-IA</h1>
                  <p className="text-xs text-gray-600">Verificador de contenido electoral</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs px-3 py-1.5 rounded-full font-medium" style={{ backgroundColor: '#00C89620', color: '#00C896' }}>
                  v1.0
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* ===== TABS ===== */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
              style={{
                backgroundColor: activeTab === tab.id ? '#00C896' : 'transparent',
                border: activeTab === tab.id ? 'none' : '1px solid #E9ECEF'
              }}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* ===== HOME VIEW ===== */}
        {activeView === 'home' && (
          <div className="space-y-6">
            {/* Bienvenido */}
            <div
              className="rounded-xl border p-6 md:p-8"
              style={{
                backgroundColor: '#F8F9FA',
                borderColor: '#E9ECEF'
              }}
            >
              <div className="flex items-start gap-4">
                <div
                  className="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: 'rgba(0, 200, 150, 0.1)' }}
                >
                  <Shield className="w-6 h-6" style={{ color: '#00C896' }} />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-2">Bienvenido a AMA-LLU-IA</h2>
                  <p className="text-sm leading-relaxed text-gray-600">
                    Plataforma de verificación de contenido electoral que te ayuda a distinguir entre información verificada y desinformación. 
                    Analiza noticias, videos y audios para detectar patrones de manipulación y campañas de bots.
                  </p>
                  <button
                    onClick={() => setActiveView('verificar')}
                    className="mt-4 px-5 py-2.5 rounded-lg font-semibold text-sm transition-all flex items-center gap-2"
                    style={{
                      backgroundColor: '#00C896',
                      color: '#0B0E14'
                    }}
                  >
                    <Search className="w-4 h-4" />
                    Verificar contenido ahora
                  </button>
                </div>
              </div>
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
                    <span className="text-xs font-mono text-gray-600">N = 1,247</span>
                  </div>
                  <p className="text-xs leading-relaxed text-gray-600">
                    Distribución de noticias analizadas según su nivel de veracidad
                  </p>
                </div>

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
                      <span className="text-xl font-bold font-mono text-white">100%</span>
                      <span className="text-xs font-mono" style={{ color: '#7A8290' }}>total</span>
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
                              <span className="text-xs" style={{ color: '#E8ECF1' }}>{item.name}</span>
                              <span className="text-xs font-mono font-bold" style={{ color: item.color }}>{item.value}%</span>
                            </div>
                            <div className="h-1 rounded-full overflow-hidden" style={{ backgroundColor: '#0B0E14' }}>
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
              </div>

              {/* Ranking */}
              <div
                className="rounded-xl border p-6"
                style={{
                  backgroundColor: '#F8F9FA',
                  borderColor: '#E9ECEF'
                }}
              >
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-5 h-5" style={{ color: '#00C896' }} />
                    <h3 className="text-base font-semibold text-gray-900">Ranking de Noticias</h3>
                  </div>
                  <p className="text-xs leading-relaxed text-gray-600">
                    Noticias más virales ordenadas por número de visualizaciones y estado de verificación
                  </p>
                </div>

                <div className="space-y-2">
                  {rankingNoticias.map((noticia, index) => {
                    const Icon = getStatusIcon(noticia.status)
                    return (
                      <div
                        key={index}
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
                              color: '#00C896',
                              backgroundColor: 'rgba(0, 200, 150, 0.08)'
                            }}
                          >
                            {index + 1}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs leading-relaxed truncate text-gray-900">
                              {noticia.titulo}
                            </p>
                            <div className="flex items-center gap-3 mt-1">
                              <div className="flex items-center gap-1">
                                <Icon className="w-3 h-3" style={{ color: getStatusColor(noticia.status) }} />
                                <span className="text-xs font-mono capitalize" style={{ color: getStatusColor(noticia.status) }}>
                                  {noticia.status}
                                </span>
                              </div>
                              <span className="text-xs font-mono text-gray-600">
                                {noticia.vistas.toLocaleString()} vistas
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Educación */}
            <div
              className="rounded-xl border p-6"
              style={{
                backgroundColor: '#12161F',
                borderColor: '#1E2433'
              }}
            >
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="w-5 h-5" style={{ color: '#00C896' }} />
                  <h3 className="text-base font-semibold text-white">¿Qué es desinformación?</h3>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: '#7A8290' }}>
                  Aprende a identificar contenido falso y técnicas de manipulación en medios digitales
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-4">
                <div
                  className="rounded-lg p-4"
                  style={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E9ECEF'
                  }}
                >
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ backgroundColor: 'rgba(232, 163, 61, 0.1)' }}>
                    <AlertTriangle className="w-4 h-4" style={{ color: '#E8A33D' }} />
                  </div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Información falsa</h4>
                  <p className="text-xs leading-relaxed text-gray-600">
                    Contenido creado deliberadamente para engañar o manipular la opinión pública.
                  </p>
                </div>

                <div
                  className="rounded-lg p-4"
                  style={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E9ECEF'
                  }}
                >
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ backgroundColor: 'rgba(232, 93, 93, 0.1)' }}>
                    <XCircle className="w-4 h-4" style={{ color: '#E85D5D' }} />
                  </div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Campañas de bots</h4>
                  <p className="text-xs leading-relaxed text-gray-600">
                    Propagación artificial de contenido mediante cuentas automatizadas.
                  </p>
                </div>

                <div
                  className="rounded-lg p-4"
                  style={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E9ECEF'
                  }}
                >
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ backgroundColor: 'rgba(0, 200, 150, 0.1)' }}>
                    <CheckCircle2 className="w-4 h-4" style={{ color: '#00C896' }} />
                  </div>
                  <h4 className="text-sm font-semibold text-gray-600 mb-2">Verificación</h4>
                  <p className="text-xs leading-relaxed text-gray-600">
                    Proceso de contrastar información con fuentes oficiales y verificadores independientes.
                  </p>
                </div>
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
                      color: isActive ? '#00C896' : '#6B7280',
                      borderBottom: isActive ? '2px solid #00C896' : '2px solid transparent',
                      backgroundColor: isActive ? 'rgba(0, 200, 150, 0.04)' : 'transparent'
                    }}
                    onFocus={e => e.target.style.color = '#00C896'}
                    onBlur={e => e.target.style.color = isActive ? '#00C896' : '#6B7280'}
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
                          onFocus={e => e.target.style.borderColor = '#00C896'}
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
                      backgroundColor: analyzing ? '#E9ECEF' : '#00C896',
                      color: analyzing ? '#6B7280' : '#0B0E14',
                      '--tw-ring-color': '#00C896',
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
                      border: '2px dashed #2A3142',
                      backgroundColor: '#0B0E14'
                    }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = '#00C896'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = '#2A3142'}
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
                    <div className="flex-1 h-px" style={{ backgroundColor: '#1E2433' }} />
                    <span className="text-xs font-mono" style={{ color: '#7A8290' }}>o pega un enlace</span>
                    <div className="flex-1 h-px" style={{ backgroundColor: '#1E2433' }} />
                  </div>

                  <div className="relative">
                    <input
                      type="url"
                      value={videoUrl}
                      onChange={e => setVideoUrl(e.target.value)}
                      placeholder="https://ejemplo.com/video.mp4"
                      className="w-full px-4 py-3 pl-11 rounded-lg text-sm transition-all focus:outline-none font-mono"
                      style={{
                        backgroundColor: '#0B0E14',
                        border: '1px solid #1E2433',
                        color: '#E8ECF1'
                      }}
                      onFocus={e => e.target.style.borderColor = '#00C896'}
                      onBlur={e => e.target.style.borderColor = '#1E2433'}
                    />
                    <LinkIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#7A8290' }} />
                  </div>

                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    className="w-full px-6 py-3 rounded-lg font-semibold text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    style={{
                      backgroundColor: analyzing ? '#1E2433' : '#00C896',
                      color: analyzing ? '#7A8290' : '#0B0E14',
                      '--tw-ring-color': '#00C896',
                      '--tw-ring-offset-color': '#12161F'
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

                  {/* Barra de progreso */}
                  {analyzing && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-gray-600">Procesando análisis...</span>
                        <span className="text-xs font-mono text-gray-600">{Math.round(progress)}%</span>
                      </div>
                      <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: '#E9ECEF' }}>
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{
                            width: `${progress}%`,
                            backgroundColor: '#00C896'
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Resultados del análisis */}
                  {analysisResult && (() => {
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
                      'Instagram': { color: '#E1306C', bg: '#E1306C', icon: '📷', label: 'Instagram' },
                      'TikTok': { color: '#00F2EA', bg: '#000000', icon: '🎵', label: 'TikTok' },
                      'Facebook': { color: '#1877F2', bg: '#1877F2', icon: 'f', label: 'Facebook' },
                      'Twitter': { color: '#1DA1F2', bg: '#1DA1F2', icon: '𝕏', label: 'Twitter/X' },
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
                            <div className="w-1 h-5 rounded-full" style={{ backgroundColor: '#00C896' }} />
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

                      {/* ===== TRANSCRIPCIÓN + VERIFICACIÓN ===== */}
                      {analysisResult.content_analysis?.has_transcription && analysisResult.content_analysis?.transcription?.text && (
                        <div className="rounded-xl border p-5" style={{ backgroundColor: '#F8F9FA', borderColor: '#E9ECEF' }}>
                          <div className="flex items-center gap-2 mb-4">
                            <div className="w-1 h-5 rounded-full" style={{ backgroundColor: '#00C896' }} />
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
                                  <span className="text-xs font-mono font-bold flex-shrink-0 pt-0.5" style={{ color: '#00C896' }}>{timestamp}</span>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm leading-relaxed mb-1.5 text-gray-900">"{seg.text}"</p>
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <span className="text-xs px-2 py-0.5 rounded font-bold" style={{
                                        backgroundColor: color + '20', color: color, border: `1px solid ${color}40`
                                      }}>{seg.label}</span>
                                      {seg.source !== 'N/A' && <span className="text-xs text-gray-600">↔ {seg.source}</span>}
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
                                  <span className="text-xs font-mono font-bold flex-shrink-0 pt-0.5" style={{ color: '#00C896' }}>{timestamp}</span>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm leading-relaxed text-gray-900">"{segment.text?.trim()}"</p>
                                    <span className="text-xs px-2 py-0.5 rounded font-bold" style={{ backgroundColor: '#9CA3AF20', color: '#6B7280', border: '1px solid #9CA3AF40' }}>SIN_VERIFICAR</span>
                                  </div>
                                </div>
                              )
                            }) || (
                              <div className="flex gap-3 pb-3">
                                <span className="text-xs font-mono font-bold flex-shrink-0" style={{ color: '#00C896' }}>00:00</span>
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
                                    <span className="text-xs text-gray-600">📰 {fc.publisher}</span>
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

                      {/* ===== INFO TÉCNICA ===== */}
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

                      {/* ===== VIDEOS RELACIONADOS ===== */}
                      <div className="rounded-xl border p-5" style={{ backgroundColor: '#F8F9FA', borderColor: '#E9ECEF' }}>
                        <div className="flex items-center gap-2 mb-4">
                          <div className="w-1 h-5 rounded-full" style={{ backgroundColor: '#00C896' }} />
                          <h4 className="text-sm font-bold text-gray-900 tracking-wide">VIDEOS RELACIONADOS</h4>
                        </div>
                        <div className="grid md:grid-cols-3 gap-4">
                          {[
                            { title: 'Debate presidencial completo', views: '125K', verified: true },
                            { title: 'Análisis de propuestas económicas', views: '89K', verified: true },
                            { title: 'Entrevista exclusiva candidato', views: '67K', verified: false }
                          ].map((video, idx) => (
                            <div key={idx} className="rounded-lg overflow-hidden" style={{ backgroundColor: '#FFFFFF', border: '1px solid #E9ECEF' }}>
                              <div className="aspect-video flex items-center justify-center" style={{ backgroundColor: '#F8F9FA' }}>
                                <Play className="w-8 h-8 text-gray-400" />
                              </div>
                              <div className="p-3">
                                <p className="text-xs font-medium text-gray-900 mb-1 line-clamp-2">{video.title}</p>
                                <div className="flex items-center justify-between">
                                  <span className="text-xs text-gray-600">{video.views} vistas</span>
                                  {video.verified && (
                                    <span className="flex items-center gap-1 text-xs" style={{ color: '#00C896' }}>
                                      <CheckCircle2 className="w-3 h-3" /> Verificado
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
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
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <ClipboardList className="w-5 h-5" style={{ color: '#00C896' }} />
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
                          backgroundColor: '#0B0E14',
                          border: '1px solid #1E2433'
                        }}
                      >
                        <span
                          className="font-mono text-sm font-bold flex-shrink-0 w-6 h-6 rounded flex items-center justify-center"
                          style={{
                            color: '#00C896',
                            backgroundColor: 'rgba(0, 200, 150, 0.08)'
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
            backgroundColor: '#12161F',
            border: '1px solid #1E2433',
            color: '#7A8290'
          }}
        >
          <div className="flex items-center gap-2">
            <div
              className="w-1.5 h-1.5 rounded-full"
              style={{
                backgroundColor: '#00C896',
                animation: 'pulse-dot 2s ease-in-out infinite'
              }}
            />
            <span>Conectado</span>
          </div>
          <span>AMA-LLU-IA v1.0 · MediaHack II</span>
        </div>
      </div>

      {/* Floating Chat Button */}
      <button
        onClick={() => setChatOpen(!chatOpen)}
        className="fixed bottom-5 right-5 w-13 h-13 rounded-full flex items-center justify-center transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 z-50"
        style={{
          width: '52px',
          height: '52px',
          backgroundColor: chatOpen ? '#1E2433' : '#00C896',
          color: chatOpen ? '#E8ECF1' : '#0B0E14',
          '--tw-ring-color': '#00C896',
          '--tw-ring-offset-color': '#0B0E14'
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
            backgroundColor: '#12161F',
            border: '1px solid #1E2433'
          }}
        >
          <div className="px-4 py-3 flex items-center gap-2" style={{ borderBottom: '1px solid #1E2433' }}>
            <div
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor: '#00C896',
                animation: 'pulse-dot 2s ease-in-out infinite'
              }}
            />
            <h3 className="font-semibold text-sm text-white">Bot — preguntas ciudadanas</h3>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className="max-w-[80%] px-3.5 py-2.5 rounded-lg text-sm leading-relaxed"
                  style={
                    msg.role === 'user'
                      ? { backgroundColor: '#00C896', color: '#0B0E14', fontWeight: 500 }
                      : { backgroundColor: '#0B0E14', color: '#E8ECF1', border: '1px solid #1E2433' }
                  }
                >
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <div className="p-3" style={{ borderTop: '1px solid #1E2433' }}>
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={e => setInputMessage(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                placeholder="Escribe tu pregunta..."
                className="flex-1 px-3 py-2.5 rounded-lg text-sm focus:outline-none font-mono"
                style={{
                  backgroundColor: '#0B0E14',
                  border: '1px solid #1E2433',
                  color: '#E8ECF1'
                }}
                onFocus={e => e.target.style.borderColor = '#00C896'}
                onBlur={e => e.target.style.borderColor = '#1E2433'}
              />
              <button
                onClick={handleSendMessage}
                className="px-3 py-2.5 rounded-lg transition-all flex items-center justify-center"
                style={{
                  backgroundColor: '#00C896',
                  color: '#0B0E14'
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
