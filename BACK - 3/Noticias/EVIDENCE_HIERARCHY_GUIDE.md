# Sistema de Jerarquía de Evidencia - AMALLU-IA

## Descripción General

El sistema de jerarquía de evidencia es una innovación en cómo AMALLU-IA busca y prioriza información. En lugar de simplemente hacer búsquedas genéricas, el sistema:

1. **Clasifica la pregunta del usuario** automáticamente
2. **Determina qué tipo de fuentes son más confiables** para esa pregunta
3. **Busca primero en fuentes de máxima autoridad** (nivel 0-3)
4. **Si no encuentra, continúa en niveles secundarios** (nivel 4-8)
5. **Etiqueta la evidencia** con su nivel de autoridad

## Niveles de Evidencia (0-8)

### Nivel 0: Fuentes Jurídicas Primarias
- **Registro Oficial del Ecuador** (registrooficial.gob.ec)
- Documentos oficiales y normativa vigente
- **Uso**: Leyes, decretos, reglamentos, resoluciones

### Nivel 1: Corte Constitucional
- **Corte Constitucional del Ecuador** (corteconstitucional.gob.ec)
- Sentencias y jurisprudencia
- **Uso**: Derechos constitucionales, interpretación de normas

### Nivel 2: Asamblea Nacional / Legislatura
- **Asamblea Nacional** (asambleanacional.gob.ec)
- Constitución, leyes, códigos
- **Uso**: Legislación, procesos legislativos

### Nivel 3: Instituciones Oficiales
- Ministerios específicos por tema
- Banco Central del Ecuador (estadísticas económicas)
- INEC (estadísticas nacionales)
- CNE (información electoral)
- Presidencia, SRI, etc.
- **Uso**: Información oficial, estadísticas, políticas

### Nivel 4: Datos Abiertos
- Portal Datos Abiertos (datosabiertos.gob.ec)
- SERCOP OCDS
- Datasets oficiales
- **Uso**: Datos cuantitativos, análisis estadístico

### Nivel 5: Medios de Verificación
- Ecuador Chequea
- Lupa Media
- **Uso**: Fact-checking, identificación de desinformación

### Nivel 6: Medios de Comunicación Tradicionales
- Primicias, El Universo, El Comercio
- Ecuavisa, Teleamazonas
- **Uso**: Noticias, actualidad, cobertura periodística

### Nivel 7: Medios Nativos Digitales
- Plan V, GK, Código Vidrio
- Wambra, Eco Amazónico
- **Uso**: Investigación periodística, análisis

### Nivel 8: Redes Sociales y Cuentas Digitales
- Twitter/X, Instagram, Facebook, TikTok
- Cuentas digitales diversas
- **Uso**: Punto de partida, detección de tendencias
- **Importante**: Nunca como evidencia definitiva sin corroboración

## Categorías de Preguntas

El sistema detecta automáticamente la categoría:

### 1. **Factcheck / Desinformación** (Mayor prioridad)
- Palabras clave: "¿es verdad", "verificar", "viral", "fake", "falso"
- Orden: Verificadores → Constitucional → Instituciones → Datos → Medios
- Busca primero en **Ecuador Chequea** y **Lupa Media**

### 2. **Legal**
- Palabras clave: "ley", "decreto", "norma", "reglamento"
- Orden: Registro Oficial → Corte Constitucional → Asamblea → Instituciones
- Busca primero en **registrooficial.gob.ec**

### 3. **Constitucional**
- Palabras clave: "constitución", "derecho", "garantía", "debido proceso"
- Orden: Asamblea → Corte Constitucional → Registro Oficial → Instituciones
- Busca primero en **asambleanacional.gob.ec**

### 4. **Electoral**
- Palabras clave: "elección", "candidato", "voto", "comicio"
- Orden: CNE → Medios tradicionales → Verificadores
- Busca primero en **CNE** (cne.gob.ec)

### 5. **Estadística**
- Palabras clave: "cuántos", "porcentaje", "cifra", "estadística"
- Orden: INEC → Datos Abiertos → Medios → Verificadores
- Busca primero en **INEC** (inec.gob.ec) y **datosabiertos.gob.ec**

### 6. **Económica**
- Palabras clave: "inflación", "PIB", "presupuesto", "tasa cambio"
- Orden: BCE → MEF → INEC → Datos Abiertos → Medios
- Busca primero en **Banco Central** (bce.ec)

### 7. **Noticias Actuales**
- Palabras clave: "hoy", "ahora", "reciente", "última hora"
- Orden: Medios tradicionales → Instituciones → Datos → Verificadores
- Busca primero en **Primicias**, **El Universo**, **El Comercio**

### 8. **General**
- Cuando no se detecta categoría específica
- Orden por defecto: Medios → Instituciones → Medios digitales → Verificadores

## Cómo Funciona

### En ask_kuybot():

```python
# 1. Clasifica la pregunta
strategy = _determine_research_strategy(payload)
# → Retorna: {"category": "legal", "hierarchy_order": [0, 1, 2, 3, ...]}

# 2. Busca en fuentes primarias primero
search_results = await _search_web_results(payload)
# → Intenta primero: site:registrooficial.gob.ec
# → Luego: site:corteconstitucional.gob.ec
# → Finalmente: sitios generales

# 3. Etiqueta la evidencia
# Cada resultado incluye: {"evidence_level": 0, "evidence_level_name": "Jurídica Primaria"}
```

### En _search_web_results():

```python
# Construye búsquedas jerárquicas
hierarchical_queries = _build_hierarchical_search_query(payload, max_levels=2)
# [
#   {"query": "site:registrooficial.gob.ec nueva ley", "level": 0, "primary": true},
#   {"query": "site:corteconstitucional.gob.ec nueva ley", "level": 1, "primary": true}
# ]

# Busca en orden de autoridad
# Si encuentra en nivel 0-3, puede parar
# Sino, continúa a niveles secundarios
```

## Casos de Uso

### Caso 1: "¿Es verdad que el CNE aprobó 1,200 candidatos?"
```
1. Categoría detectada: factcheck_desinformation + electoral
2. Jerarquía: Verificadores → CNE → Medios
3. Búsqueda:
   - site:ecuadorchequea.org candidatos CNE
   - site:lupamedia.com candidatos CNE
   - site:cne.gob.ec candidatos 1200
4. Resultado: "✓ Confirmado por CNE" (Nivel 3, Institucional)
```

### Caso 2: "¿Cuál es la tasa de inflación?"
```
1. Categoría detectada: statistical + economic
2. Jerarquía: BCE → INEC → Datos Abiertos → Medios
3. Búsqueda:
   - site:bce.ec inflación 2026
   - site:datosabiertos.gob.ec inflación
4. Resultado: "8.5% según BCE" (Nivel 3, Institución)
```

### Caso 3: "¿Es legal que una empresa requiera vacuna COVID?"
```
1. Categoría detectada: legal + health
2. Jerarquía: Registro Oficial → Corte Constitucional → Asamblea
3. Búsqueda:
   - site:registrooficial.gob.ec vacuna requisito empresa
   - site:corteconstitucional.gob.ec vacuna mandato
4. Resultado: "Según Decreto X del Registro Oficial..." (Nivel 0, Jurídica Primaria)
```

### Caso 4: "¿Qué pasó con la ley de educación?"
```
1. Categoría detectada: legal + news_current_events
2. Jerarquía: Registro Oficial → Asamblea → Medios tradicionales
3. Búsqueda:
   - site:registrooficial.gob.ec ley educación
   - site:asambleanacional.gob.ec ley educación
   - site:primicias.ec ley educación
4. Resultado: Mezcla de fuente oficial + cobertura periodística
```

## Reglas de la Jerarquía

1. **Competencia sobre autoridad**: Una fuente con competencia directa en un tema prevalece sobre una fuente más general de mayor autoridad.
   - Ejemplo: INEC para estadísticas (aunque no es nivel 0-1)
   - Ejemplo: CNE para procesos electorales

2. **Temporal**: 
   - Eventos pasados → buscar en fuentes históricas/archivos
   - Eventos futuros → buscar anuncio oficial o decreto
   - Eventos recientes → combinar oficial + medios

3. **Corroboración**:
   - Para contradictions: requiere al menos 2 fuentes independientes
   - Para facts complejos: busca que al menos 2 niveles confirmen

4. **Redes Sociales**:
   - Punto de partida, nunca conclusión
   - Buscar siempre la fuente original mencionada en post
   - Verificar en nivel correspondiente

5. **Editorial**:
   - NO usar para determinar veracidad
   - SI usar para identificar perspectivas y sesgos
   - Comparar entre fuentes con distintas líneas editoriales

## Respuestas Mejoradas

Las respuestas ahora incluyen:

```
✓ Confirmado por Registro Oficial
- Fuente: registrooficial.gob.ec
- Nivel de confianza: Fuente Jurídica Primaria

Contexto: Según El Universo (Nivel 6, Medio Tradicional)...

? No confirmado: No se encontró en datosabiertos.gob.ec (Nivel 4, Datos Abiertos)
```

## Configuración

La jerarquía se define en: `data/evidence_hierarchy.json`

Para agregar nuevas fuentes o modificar prioridades:

```json
{
  "level_3_official_institutions": {
    "sources": [
      {
        "domain": "nuevoministrio.gob.ec",
        "name": "Nuevo Ministerio",
        "use_for": ["tema1", "tema2"]
      }
    ]
  }
}
```

## Testing

Ejecutar tests de clasificación:
```bash
py -3.12 -m pytest tests/test_research_classifier.py -v
```

Ejecutar tests de integración:
```bash
py -3.12 -m pytest tests/test_kuybot.py -v
```

## Módulos

- **`app/services/research_classifier.py`**: Lógica de clasificación y jerarquía
- **`data/evidence_hierarchy.json`**: Configuración de fuentes y niveles
- **`app/services/kuybot.py`**: Integración en orquestación
- **`tests/test_research_classifier.py`**: Suite de tests

## Mejoras Futuras

- [ ] Logging de qué nivel de fuente fue utilizado
- [ ] Dashboard de "confidence by evidence level"
- [ ] Configuración por usuario de tolerancia a niveles
- [ ] Historial de búsquedas por categoría
- [ ] Análisis de cobertura de fuentes por tema
