import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Link as LinkIcon, Upload, ClipboardList, Search, AlertTriangle, CheckCircle2, XCircle, Activity, Info, TrendingUp, BookOpen, Shield, Home } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'
import { analyzeUrl, analyzeAudio, analyzeVideo } from './services/api'

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
    setError(null)
    setAnalysisResult(null)

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
          throw new Error('Tipo de archivo no soportado')
        }
      } else {
        throw new Error('Por favor ingresa una URL o selecciona un archivo')
      }

      setAnalysisResult(result)
    } catch (err) {
      setError(err.message)
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

  return (
    <div className="min-h-screen px-4 py-6 md:py-12" style={{ backgroundColor: '#0B0E14' }}>
      <div className="max-w-[1200px] mx-auto">
        {/* ===== HEADER ===== */}
        <header className="mb-6">
          <div
            className="relative overflow-hidden rounded-xl border px-6 py-5"
            style={{
              backgroundColor: '#12161F',
              borderColor: '#1E2433'
            }}
          >
            {/* Scan line */}
            <div className="absolute top-0 left-0 right-0 h-[3px] overflow-hidden" style={{ backgroundColor: '#0B0E14' }}>
              <div
                className="absolute top-0 h-full w-1/3"
                style={{
                  background: `linear-gradient(90deg, transparent, ${scanColor}, transparent)`,
                  animation: 'scanline 2.5s linear infinite'
                }}
              />
            </div>

            {/* Mini waveform bars */}
            <div className="absolute top-3 right-4 flex items-end gap-[2px] h-4">
              {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map(i => (
                <div
                  key={i}
                  className="w-[2px] rounded-sm"
                  style={{
                    backgroundColor: scanColor,
                    opacity: 0.4 + (i % 3) * 0.2,
                    height: `${4 + (i % 4) * 3}px`,
                    animation: `wave ${1 + (i % 3) * 0.3}s ease-in-out infinite`,
                    animationDelay: `${i * 0.08}s`
                  }}
                />
              ))}
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{
                      backgroundColor: scanColor,
                      animation: 'pulse-dot 2s ease-in-out infinite'
                    }}
                  />
                  <span className="text-xs font-mono uppercase tracking-widest" style={{ color: scanColor }}>
                    {analyzing ? 'Analizando' : 'Sistema activo'}
                  </span>
                </div>
                <h1 className="text-2xl md:text-[28px] font-bold tracking-tight text-white leading-tight">
                  AMA-LLU-IA
                </h1>
                <p className="text-sm mt-1 font-mono" style={{ color: '#7A8290' }}>
                  Viralidad vs Veracidad
                </p>
              </div>

              {/* Navigation */}
              <nav className="hidden md:flex gap-2">
                <button
                  onClick={() => setActiveView('home')}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                  style={{
                    backgroundColor: activeView === 'home' ? 'rgba(0, 200, 150, 0.1)' : 'transparent',
                    color: activeView === 'home' ? '#00C896' : '#7A8290',
                    border: activeView === 'home' ? '1px solid #00C896' : '1px solid transparent'
                  }}
                >
                  <Home className="inline-block w-4 h-4 mr-1.5 -mt-0.5" />
                  Inicio
                </button>
                <button
                  onClick={() => setActiveView('verificar')}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                  style={{
                    backgroundColor: activeView === 'verificar' ? 'rgba(0, 200, 150, 0.1)' : 'transparent',
                    color: activeView === 'verificar' ? '#00C896' : '#7A8290',
                    border: activeView === 'verificar' ? '1px solid #00C896' : '1px solid transparent'
                  }}
                >
                  <Search className="inline-block w-4 h-4 mr-1.5 -mt-0.5" />
                  Verificar
                </button>
              </nav>
            </div>
          </div>
        </header>

        {/* ===== HOME VIEW ===== */}
        {activeView === 'home' && (
          <div className="space-y-6">
            {/* Bienvenido */}
            <div
              className="rounded-xl border p-6 md:p-8"
              style={{
                backgroundColor: '#12161F',
                borderColor: '#1E2433'
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
                  <h2 className="text-xl font-bold text-white mb-2">Bienvenido a AMA-LLU-IA</h2>
                  <p className="text-sm leading-relaxed" style={{ color: '#7A8290' }}>
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
                  backgroundColor: '#12161F',
                  borderColor: '#1E2433'
                }}
              >
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-base font-semibold text-white">Análisis Integral</h3>
                    <span className="text-xs font-mono" style={{ color: '#7A8290' }}>N = 1,247</span>
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: '#7A8290' }}>
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
                  backgroundColor: '#12161F',
                  borderColor: '#1E2433'
                }}
              >
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-5 h-5" style={{ color: '#00C896' }} />
                    <h3 className="text-base font-semibold text-white">Ranking de Noticias</h3>
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: '#7A8290' }}>
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
                          backgroundColor: '#0B0E14',
                          border: '1px solid #1E2433'
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
                            <p className="text-xs leading-relaxed truncate" style={{ color: '#E8ECF1' }}>
                              {noticia.titulo}
                            </p>
                            <div className="flex items-center gap-3 mt-1">
                              <div className="flex items-center gap-1">
                                <Icon className="w-3 h-3" style={{ color: getStatusColor(noticia.status) }} />
                                <span className="text-xs font-mono capitalize" style={{ color: getStatusColor(noticia.status) }}>
                                  {noticia.status}
                                </span>
                              </div>
                              <span className="text-xs font-mono" style={{ color: '#7A8290' }}>
                                {noticia.viralidad.toLocaleString()} vistas
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
                    backgroundColor: '#0B0E14',
                    border: '1px solid #1E2433'
                  }}
                >
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ backgroundColor: 'rgba(232, 163, 61, 0.1)' }}>
                    <AlertTriangle className="w-4 h-4" style={{ color: '#E8A33D' }} />
                  </div>
                  <h4 className="text-sm font-semibold text-white mb-2">Información falsa</h4>
                  <p className="text-xs leading-relaxed" style={{ color: '#7A8290' }}>
                    Contenido creado deliberadamente para engañar o manipular la opinión pública.
                  </p>
                </div>

                <div
                  className="rounded-lg p-4"
                  style={{
                    backgroundColor: '#0B0E14',
                    border: '1px solid #1E2433'
                  }}
                >
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ backgroundColor: 'rgba(232, 93, 93, 0.1)' }}>
                    <XCircle className="w-4 h-4" style={{ color: '#E85D5D' }} />
                  </div>
                  <h4 className="text-sm font-semibold text-white mb-2">Campañas de bots</h4>
                  <p className="text-xs leading-relaxed" style={{ color: '#7A8290' }}>
                    Propagación artificial de contenido mediante cuentas automatizadas.
                  </p>
                </div>

                <div
                  className="rounded-lg p-4"
                  style={{
                    backgroundColor: '#0B0E14',
                    border: '1px solid #1E2433'
                  }}
                >
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ backgroundColor: 'rgba(0, 200, 150, 0.1)' }}>
                    <CheckCircle2 className="w-4 h-4" style={{ color: '#00C896' }} />
                  </div>
                  <h4 className="text-sm font-semibold text-white mb-2">Verificación</h4>
                  <p className="text-xs leading-relaxed" style={{ color: '#7A8290' }}>
                    Proceso de corroboración con fuentes oficiales y medios confiables.
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
              backgroundColor: '#12161F',
              borderColor: '#1E2433'
            }}
          >
            {/* Tabs */}
            <nav className="flex" style={{ borderBottom: '1px solid #1E2433' }}>
              {tabs.map(tab => {
                const Icon = tab.icon
                const isActive = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className="flex-1 px-3 py-3.5 text-xs md:text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-inset"
                    style={{
                      color: isActive ? '#00C896' : '#7A8290',
                      borderBottom: isActive ? '2px solid #00C896' : '2px solid transparent',
                      backgroundColor: isActive ? 'rgba(0, 200, 150, 0.04)' : 'transparent'
                    }}
                    onFocus={e => e.target.style.color = '#00C896'}
                    onBlur={e => e.target.style.color = isActive ? '#00C896' : '#7A8290'}
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
                        <span className="text-xs font-mono uppercase tracking-wider block mb-1" style={{ color: '#7A8290' }}>
                          URL de la noticia
                        </span>
                        <p className="text-xs" style={{ color: '#7A8290' }}>
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
                            backgroundColor: '#0B0E14',
                            border: '1px solid #1E2433',
                            color: '#E8ECF1'
                          }}
                          onFocus={e => e.target.style.borderColor = '#00C896'}
                          onBlur={e => e.target.style.borderColor = '#1E2433'}
                        />
                        <LinkIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#7A8290' }} />
                      </div>
                    </label>
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

                  {/* Resultados del análisis */}
                  {analysisResult && (
                    <div className="mt-6 space-y-4">
                      <div className="rounded-lg border p-4" style={{ backgroundColor: '#12161F', borderColor: '#1E2433' }}>
                        <h4 className="text-sm font-semibold text-white mb-3">Resultados del Análisis</h4>
                        
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-xs" style={{ color: '#7A8290' }}>¿Es IA generada?</span>
                            <span className={`text-sm font-bold ${analysisResult.is_ai_generated ? 'text-red-500' : 'text-green-500'}`}>
                              {analysisResult.is_ai_generated ? 'SÍ' : 'NO'}
                            </span>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-xs" style={{ color: '#7A8290' }}>Confianza</span>
                            <span className="text-sm font-mono font-bold" style={{ color: '#00C896' }}>
                              {(analysisResult.confidence * 100).toFixed(1)}%
                            </span>
                          </div>

                          {analysisResult.content_analysis?.transcription && (
                            <div className="mt-4 pt-4" style={{ borderTop: '1px solid #1E2433' }}>
                              <h5 className="text-xs font-semibold text-white mb-2">Transcripción</h5>
                              <p className="text-xs leading-relaxed" style={{ color: '#E8ECF1' }}>
                                {analysisResult.content_analysis.transcription.text}
                              </p>
                            </div>
                          )}

                          {analysisResult.content_analysis?.fake_news && (
                            <div className="mt-3">
                              <div className="flex items-center justify-between">
                                <span className="text-xs" style={{ color: '#7A8290' }}>¿Es desinformación?</span>
                                <span className={`text-sm font-bold ${analysisResult.content_analysis.fake_news.is_fake_news ? 'text-red-500' : 'text-green-500'}`}>
                                  {analysisResult.content_analysis.fake_news.is_fake_news ? 'SÍ' : 'NO'}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Error */}
                  {error && (
                    <div className="mt-4 rounded-lg border p-4" style={{ backgroundColor: '#1E1416', borderColor: '#E85D5D' }}>
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
