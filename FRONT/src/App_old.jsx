import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Link as LinkIcon, Upload, ClipboardList, Search, AlertTriangle, CheckCircle2, XCircle, Activity, Info, TrendingUp, BookOpen, Shield } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts'

function App() {
  const [activeView, setActiveView] = useState('home')
  const [activeTab, setActiveTab] = useState('link')
  const [chatOpen, setChatOpen] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [urlValue, setUrlValue] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hola. Soy el asistente de AMA-LLU-IA. Puedes preguntarme sobre verificación de contenido electoral.' }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const chatEndRef = useRef(null)

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

  const handleAnalyze = () => {
    setAnalyzing(true)
    setTimeout(() => setAnalyzing(false), 2500)
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

  return (
    <div className="min-h-screen px-4 py-6 md:py-12" style={{ backgroundColor: '#0B0E14' }}>
      <div className="max-w-[760px] mx-auto">
        {/* ===== HEADER ===== */}
        <header className="mb-6">
          <div
            className="relative overflow-hidden rounded-xl border px-6 py-5"
            style={{
              backgroundColor: '#12161F',
              borderColor: '#1E2433'
            }}
          >
            {/* Scan line / waveform */}
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
        </header>

        {/* ===== MAIN PANEL ===== */}
        <main
          className="rounded-xl border overflow-hidden"
          style={{
            backgroundColor: '#12161F',
            borderColor: '#1E2433'
          }}
        >
          {/* ===== TABS ===== */}
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

          {/* ===== TAB CONTENT ===== */}
          <div className="p-6 md:p-8">
            {/* --- LINK NOTICIA --- */}
            {activeTab === 'link' && (
              <div className="space-y-5">
                <div>
                  <label className="block mb-2">
                    <span className="text-xs font-mono uppercase tracking-wider block mb-2" style={{ color: '#7A8290' }}>
                      URL de la noticia
                    </span>
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

            {/* --- VIDEO / AUDIO --- */}
            {activeTab === 'video' && (
              <div className="space-y-5">
                <div
                  className="rounded-lg p-8 text-center transition-all cursor-pointer"
                  style={{
                    border: '2px dashed #2A3142',
                    backgroundColor: '#0B0E14'
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = '#00C896'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = '#2A3142'}
                >
                  <Upload className="w-10 h-10 mx-auto mb-3" style={{ color: '#7A8290' }} />
                  <p className="text-sm mb-1" style={{ color: '#E8ECF1' }}>
                    Arrastra un archivo o haz clic para seleccionar
                  </p>
                  <p className="text-xs font-mono" style={{ color: '#7A8290' }}>
                    Video o audio · máx. 50MB
                  </p>
                  <input type="file" accept="video/*,audio/*" className="hidden" />
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
              </div>
            )}

            {/* --- AUDITOR --- */}
            {activeTab === 'auditor' && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 mb-4">
                  <ClipboardList className="w-5 h-5" style={{ color: '#00C896' }} />
                  <h3 className="text-base font-semibold text-white">Criterios de evaluación</h3>
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

          {/* ===== CHART SECTION ===== */}
          <div className="p-6 md:p-8" style={{ borderTop: '1px solid #1E2433' }}>
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-base font-semibold text-white">Análisis integral de noticias</h3>
              <span className="text-xs font-mono" style={{ color: '#7A8290' }}>N = 1,247</span>
            </div>

            <div className="flex flex-col md:flex-row items-center gap-6">
              {/* Pie chart */}
              <div className="relative w-48 h-48 flex-shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={85}
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
                  <span className="text-2xl font-bold font-mono text-white">100%</span>
                  <span className="text-xs font-mono" style={{ color: '#7A8290' }}>total</span>
                </div>
              </div>

              {/* Legend with bars */}
              <div className="flex-1 w-full space-y-3">
                {chartData.map((item, index) => {
                  const Icon = index === 0 ? CheckCircle2 : index === 1 ? AlertTriangle : XCircle
                  return (
                    <div key={index} className="flex items-center gap-3">
                      <Icon className="w-4 h-4 flex-shrink-0" style={{ color: item.color }} />
                      <div className="flex-1">
                        <div className="flex items-baseline justify-between mb-1">
                          <span className="text-sm" style={{ color: '#E8ECF1' }}>{item.name}</span>
                          <span className="text-sm font-mono font-bold" style={{ color: item.color }}>{item.value}%</span>
                        </div>
                        <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: '#0B0E14' }}>
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
        </main>

        {/* ===== FOOTER STATUS BAR ===== */}
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

      {/* ===== FLOATING CHAT BUTTON ===== */}
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

      {/* ===== CHAT PANEL ===== */}
      {chatOpen && (
        <div
          className="fixed bottom-20 right-5 w-[calc(100vw-2.5rem)] md:w-96 h-[420px] rounded-xl flex flex-col z-50 overflow-hidden"
          style={{
            backgroundColor: '#12161F',
            border: '1px solid #1E2433'
          }}
        >
          {/* Chat header */}
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

          {/* Messages */}
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

          {/* Input */}
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
