# AMA-LLU-IA Video/Audio Analyzer

Microservicio de detección de contenido de audio y video generado por IA para el proyecto MediaHack II.

## 🎯 Objetivo

Detectar si archivos de audio o video han sido generados por inteligencia artificial (deepfakes) mediante análisis heurístico y técnicas de procesamiento de señales.

## 🚀 Instalación

### Requisitos previos
- Python 3.9+
- pip

### Configuración

1. **Crear entorno virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env según necesidades
```

## 🏃 Ejecución

### Desarrollo
```bash
python -m app.main
```

O con uvicorn directamente:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Producción
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## 📡 API Endpoints

### Health Check
```http
GET /api/v1/health
```

### Analizar Audio (Archivo)
```http
POST /api/v1/analyze/audio
Content-Type: multipart/form-data

file: <audio_file>
```

### Analizar desde URL
```http
POST /api/v1/analyze/url
Content-Type: application/json

{
  "url": "https://example.com/audio.mp3"
}
```

### Analizar Video (Programador 2)
```http
POST /api/v1/analyze/video
Content-Type: multipart/form-data

file: <video_file>
```

## 📊 Respuesta de Análisis

```json
{
  "is_ai_generated": true,
  "confidence": 0.87,
  "analysis_type": "audio",
  "audio_details": {
    "spectral_score": 0.92,
    "pitch_consistency": 0.85,
    "noise_detection": 0.84,
    "artifacts": [
      {
        "type": "spectral_discontinuity",
        "confidence": 0.75,
        "description": "Abrupt spectral changes detected"
      }
    ]
  },
  "metadata": {
    "duration": 45.3,
    "format": "mp3",
    "size": 1024000,
    "sample_rate": 44100,
    "channels": 2
  },
  "analyzed_at": "2026-08-14T14:00:00Z",
  "processing_time": 2.34
}
```

## 🧪 Testing

```bash
pytest tests/
```

## 📁 Estructura del Proyecto

```
BACK - 3/Video-Audio/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio_analyzer.py    # Audio analysis (Programador 1)
│   │   └── video_analyzer.py    # Video analysis (Programador 2)
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py  # File operations
├── tests/
│   └── __init__.py
├── temp/                    # Temporary files (gitignored)
├── uploads/                 # Uploaded files (gitignored)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔬 Metodología de Análisis

### Audio (Programador 1)
- **Análisis espectral:** Detección de patrones espectrales artificiales
- **Consistencia de pitch:** Variación de tono poco natural
- **Ruido artificial:** Patrones de ruido sintético
- **Artefactos:** Clipping, silencios anormales, discontinuidades

### Video (Programador 2)
- **Análisis facial:** Inconsistencias en movimientos faciales
- **Frame artifacts:** Artefactos entre frames
- **Anomalías de compresión:** Patrones de compresión inusuales

## 🛡️ Cumplimiento Ético

Este proyecto cumple con el **Marco de Gobernanza Ética** del MediaHack II:

✅ **Supervisión humana:** Resultados son sugerencias, no decisiones finales  
✅ **Transparencia:** Código abierto y metodología documentada  
✅ **Neutralidad política:** No favorece candidatos ni partidos  
✅ **Privacidad:** No almacena datos personales  
✅ **Documentación:** Código y proceso completamente documentados

## 👥 División de Trabajo

### Programador 1 (Backend Core + Audio)
- ✅ Estructura base del proyecto
- ✅ FastAPI setup y endpoints
- ✅ Análisis de audio con librosa
- ✅ File handling y validación

### Programador 2 (Video + ML)
- ✅ Análisis de video con OpenCV (heurísticas: jitter facial, artefactos de compresión, flicker)
- ✅ Modelo de ML para detección (clasificador real/fake por frame, HuggingFace)
- ✅ Testing e integración (`POST /api/v1/analyze/video` conectado en `main.py`)

## 📝 Notas de Desarrollo

- Usar prefijo `[AUDIO]` en commits del Programador 1
- Usar prefijo `[VIDEO]` en commits del Programador 2
- Hacer `git pull` frecuente para evitar conflictos
- Trabajar en archivos separados cuando sea posible

## 📚 Documentación API

Una vez iniciado el servidor, accede a:
- Swagger UI: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

## 🐛 Troubleshooting

### Error: "Module not found"
```bash
pip install -r requirements.txt
```

### Error: "Permission denied" en temp/
```bash
mkdir temp uploads
chmod 755 temp uploads
```

## 📄 Licencia

Proyecto desarrollado para MediaHack II - 2026
