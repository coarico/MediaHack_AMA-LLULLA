# AMALLU-IA Research Hierarchy System

## 🎯 Objetivo

Implementar un sistema inteligente de investigación que prioriza fuentes según su autoridad y competencia en cada tipo de pregunta. En lugar de realizar búsquedas genéricas, el sistema ahora:

- **Identifica automáticamente el tipo de pregunta** (legal, electoral, estadística, etc.)
- **Determina qué fuentes son más confiables** para ese tipo de información
- **Busca primero en fuentes de máxima autoridad** (Registro Oficial, Corte Constitucional, Instituciones)
- **Continúa en fuentes secundarias** si es necesario (Medios, Redes Sociales)
- **Etiqueta toda evidencia** con su nivel de autoridad

---

## 📊 Jerarquía de Evidencia (8 Niveles)

| Nivel | Nombre | Ejemplos | Uso Para |
|-------|--------|----------|----------|
| **0** | Fuentes Jurídicas Primarias | Registro Oficial | Leyes, decretos, normativa oficial |
| **1** | Corte Constitucional | Corte Constitucional | Sentencias, jurisprudencia |
| **2** | Asamblea Nacional | Asamblea, Constitución | Legislación |
| **3** | Instituciones Oficiales | CNE, INEC, BCE, Ministerios | Estadísticas, políticas oficiales |
| **4** | Datos Abiertos | Datosabiertos.gob.ec, SERCOP | Datos cuantitativos |
| **5** | Verificadores | Ecuador Chequea, Lupa Media | Fact-checking, desinformación |
| **6** | Medios Tradicionales | Primicias, El Universo, El Comercio | Noticias, cobertura |
| **7** | Medios Digitales Nativos | Plan V, GK, Wambra | Investigación periodística |
| **8** | Redes Sociales | X/Twitter, Instagram, Facebook | Punto de partida solamente |

---

## 🤖 Categorías de Preguntas (Auto-detectadas)

El sistema reconoce automáticamente 12 categorías:

### 1. **Fact-check / Desinformación** (Mayor Prioridad)
```
Usuario: "¿Es verdad que..."
→ Búsqueda: Verificadores → Instituciones → Medios
```

### 2. **Legal**
```
Usuario: "¿Qué dice la ley sobre...?"
→ Búsqueda: Registro Oficial → Corte Constitucional → Asamblea
```

### 3. **Constitucional**
```
Usuario: "¿Cuál es el derecho a...?"
→ Búsqueda: Asamblea → Corte Constitucional → Instituciones
```

### 4. **Electoral**
```
Usuario: "¿Cuántos candidatos...?"
→ Búsqueda: CNE → Medios → Verificadores
```

### 5. **Estadística**
```
Usuario: "¿Cuál es el porcentaje...?"
→ Búsqueda: INEC → Datos Abiertos → Medios
```

### 6. **Económica**
```
Usuario: "¿Cuál es la inflación...?"
→ Búsqueda: BCE → MEF → Medios
```

### 7. **Noticias Actuales**
```
Usuario: "¿Qué pasó hoy...?"
→ Búsqueda: Medios → Instituciones → Verificadores
```

Más categorías: Política, Seguridad, Salud, Educación, Laboral, General

---

## 🔍 Cómo Funciona

### Paso 1: Clasificación de Pregunta
```python
strategy = _determine_research_strategy(payload)
# → {"category": "legal", "hierarchy_order": [0, 1, 2, 3, ...], ...}
```

### Paso 2: Construcción de Búsquedas Jerárquicas
```python
queries = _build_hierarchical_search_query(payload)
# [
#   {"query": "site:registrooficial.gob.ec nueva ley", "level": 0, "primary": True},
#   {"query": "site:corteconstitucional.gob.ec nueva ley", "level": 1, "primary": True},
#   ...
# ]
```

### Paso 3: Búsqueda en Orden de Autoridad
```python
search_results = await _search_web_results(payload)
# Busca primero en nivel 0, luego 1, luego 2, etc.
# Si encuentra en nivel 0-3, puede parar
# Si no, continúa en niveles secundarios
```

### Paso 4: Etiquetado de Evidencia
```python
{
    "title": "Nueva ley...",
    "url": "registrooficial.gob.ec/...",
    "evidence_level": 0,
    "evidence_level_name": "Fuente Jurídica Primaria"
}
```

---

## 📁 Archivos del Sistema

### Core Implementation
- **`app/services/research_classifier.py`** (300+ líneas)
  - Clase `ResearchClassifier` con 15+ métodos
  - Detección de categorías
  - Gestión de niveles de evidencia
  - Construcción de queries jerárquicas

- **`data/evidence_hierarchy.json`** (Configuración)
  - 8 niveles de evidencia
  - 40+ fuentes configuradas
  - 12 estrategias de categoría
  - Operadores de búsqueda (site:)

### Integración en Kuybot
- **`app/services/kuybot.py`** (Modificado)
  - `_determine_research_strategy()` - Detecta categoría y jerarquía
  - `_build_hierarchical_search_query()` - Construye queries con site:
  - `_search_web_results()` - Busca con jerarquía
  - `_extract_official_sources()` - Prioriza por nivel

### Documentación
- **`EVIDENCE_HIERARCHY_GUIDE.md`** - Guía detallada
- **`README_EVIDENCE.md`** - Este archivo

### Tests (90/90 pasando)
- `tests/test_research_classifier.py` (23 tests)
- `tests/test_kuybot.py` (8 tests)
- `tests/test_evidence_hierarchy_integration.py` (7 tests)

---

## 🚀 Casos de Uso

### Caso 1: Pregunta Legal
**Usuario:** "¿Es legal que mi empresa requiera vacunación COVID?"

**Proceso:**
1. Detecta: Categoría `legal` + `health`
2. Jerarquía: Registro Oficial → Corte Constitucional → Asamblea
3. Busca: 
   - `site:registrooficial.gob.ec vacunación requisito`
   - `site:corteconstitucional.gob.ec vacunación mandato`
4. Resultado: **✓ Confirmado por Decreto X (Registro Oficial, Nivel 0)**

### Caso 2: Pregunta Estadística
**Usuario:** "¿Cuál es la tasa de desempleo en Ecuador?"

**Proceso:**
1. Detecta: Categoría `statistical` + `labor`
2. Jerarquía: INEC → Datos Abiertos → Medios
3. Busca:
   - `site:inec.gob.ec desempleo 2026`
   - `site:datosabiertos.gob.ec desempleo`
4. Resultado: **5.2% según INEC (Institución, Nivel 3)**

### Caso 3: Verificación de Viral
**Usuario:** "¿Es verdad que aprobaron ley que..."

**Proceso:**
1. Detecta: Categoría `factcheck_desinformation`
2. Jerarquía: Verificadores → Instituciones → Medios
3. Busca:
   - `site:ecuadorchequea.org "ley que..."`
   - `site:lupamedia.com "ley que..."`
   - Luego fuentes oficiales
4. Resultado: **? No confirmado** (o **✗ Falso** si verif. lo desmiente)

### Caso 4: Noticia Reciente
**Usuario:** "¿Qué pasó hoy con el CNE?"

**Proceso:**
1. Detecta: Categoría `news_current_events` + `electoral`
2. Jerarquía: Medios → CNE → Verificadores
3. Busca:
   - `site:primicias.ec CNE`
   - `site:eluniverso.com CNE`
   - `site:cne.gob.ec noticia`
4. Resultado: Mezcla de cobertura media + oficial

---

## ⚙️ Uso Programático

### En ask_kuybot()
```python
from app.services.kuybot import ask_kuybot

response = await ask_kuybot(
    question="¿Es verdad que...?",
    news={"title": "...", ...}
)

# response contiene:
# - answer: Texto analizado
# - sources: URLs etiquetadas con nivel de evidencia
# - fact_check: Verificaciones
# - status: "ok"
```

### Acceso Directo al Classifier
```python
from app.services.research_classifier import get_research_classifier

classifier = get_research_classifier()

# Clasificar pregunta
classification = classifier.classify_query(
    query="¿Cuántos candidatos...?",
    topic="Elecciones 2026"
)
# → {"category": "electoral", "confidence": 0.95, ...}

# Obtener nivel de evidencia de URL
level = classifier.get_evidence_level("cne.gob.ec")
# → 3

# Verificar si es fuente primaria
is_primary = classifier.is_primary_source("eluniverso.com")
# → False
```

---

## ✅ Tests

Ejecutar todos los tests:
```bash
cd "c:\...\BACK - 3\Noticias"
py -3.12 -m pytest tests/ -q
# 90 passed in 4.46s ✓
```

Tests específicos:
```bash
# Solo research classifier
py -3.12 -m pytest tests/test_research_classifier.py -v

# Solo kuybot
py -3.12 -m pytest tests/test_kuybot.py -v

# Solo integración
py -3.12 -m pytest tests/test_evidence_hierarchy_integration.py -v
```

---

## 📋 Reglas Clave

1. **Competencia sobre autoridad**
   - Una fuente con competencia directa prevalece sobre una fuente general más "prestigiosa"
   - Ejemplo: INEC para estadísticas (aunque es nivel 3, no 0)

2. **Corroboración**
   - Para contradiciones: requiere mínimo 2 fuentes independientes
   - Para claims complejos: preferir cuando 2+ niveles confirman

3. **Redes Sociales**
   - Punto de partida únicamente
   - Siempre verificar en nivel correspondiente
   - Buscar fuente original mencionada

4. **Orientación Editorial**
   - NO usar para determinar veracidad
   - SÍ usar para identificar perspectivas
   - Comparar entre fuentes con distintas líneas editoriales

---

## 🔄 Próximos Pasos Sugeridos

1. **Desplegar a Railway**
   - Verificar que Google Custom Search respeta site: operators
   - Monitorear performance de búsquedas

2. **Logging Mejorado**
   - Registrar qué nivel de fuente fue usado
   - Analytics por categoría de pregunta

3. **UI/UX**
   - Mostrar badge "Fuente Confiable: Nivel X"
   - Indicador visual de "evidencia primaria" vs "secundaria"

4. **Expansión de Fuentes**
   - Agregar nuevas instituciones según demanda
   - Integrar datos más datasets abiertos

5. **Refinamiento de Categorías**
   - Recolectar feedback de usuarios
   - Ajustar keywords y prioridades

---

## 📞 Soporte

Para modificar la jerarquía o agregar fuentes:
1. Editar `data/evidence_hierarchy.json`
2. Ejecutar tests: `py -3.12 -m pytest tests/test_research_classifier.py`
3. Desplegar cambios

---

**Versión**: 1.0  
**Fecha**: Agosto 2026  
**Status**: ✅ Implementado y Testeado
