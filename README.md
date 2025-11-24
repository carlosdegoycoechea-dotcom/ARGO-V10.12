# ARGO V10.12 - Enterprise PMO Platform

**Versión:** 10.12
**Fecha:** Noviembre 2025
**Estado:** Production Ready

---

## 🎯 ¿Qué es ARGO?

ARGO es una plataforma inteligente de gestión de proyectos PMO (Project Management Office) que combina:

- **RAG Avanzado** (Retrieval-Augmented Generation) para análisis de documentación
- **Intelligence Pipeline** con 4 plugins de IA avanzada
- **Sistema Prompt Especializado** en PMO (PMBOK, DCMA, GAO, EVM)
- **Arquitectura Modular** con sistema de plugins extensible
- **Interface Moderna** con React + TypeScript + Tailwind

---

## ✨ Características Principales

### Core Features
- ✅ **RAG Engine Avanzado**: HyDE + Reranking + Cache inteligente
- ✅ **Model Router**: GPT-4o + Claude Sonnet con routing automático
- ✅ **Sistema de Plugins**: 6+ plugins funcionales (OCR, Excel, Intelligence)
- ✅ **Database Unificada**: SQLite con schema robusto
- ✅ **API REST + WebSocket**: FastAPI moderno con documentación Swagger

### Intelligence Pipeline (NUEVO en V10.11)
1. **QueryPlanningPlugin**: Clasifica y planifica queries inteligentemente
2. **AgenticRetrievalPlugin**: Recuperación adaptativa con refinamiento
3. **CorrectiveRAGPlugin**: Corrección y optimización de contexto
4. **SelfReflectiveRAGPlugin**: Validación anti-alucinación

### Sistema Prompt PMO (MEJORADO en V10.11)
- ✅ 283 líneas de expertise especializado (vs 17 anterior)
- ✅ DCMA 14-Point Assessment
- ✅ GAO Schedule Assessment
- ✅ Earned Value Management (EVM)
- ✅ Critical Path Method (CPM)
- ✅ Reasoning Framework avanzado

### Preparado para Schedule Analysis
- ✅ PyP6XER (Primavera P6 XER parsing)
- ✅ NetworkX (algoritmos CPM y grafos)
- ✅ Arquitectura lista para plugins PMO

---

## 🚀 Instalación Rápida

### Requisitos Previos

1. **Python 3.10 o superior**
   - Descargar desde: https://www.python.org/

2. **Node.js 18 o superior**
   - Descargar desde: https://nodejs.org/

3. **API Keys**
   - OpenAI API Key (para GPT-4o)
   - Anthropic API Key (para Claude Sonnet)

### Pasos de Instalación

1. **Ejecutar instalación automática:**
   ```bash
   install.bat
   ```

   Este script:
   - Verifica Python y Node.js
   - Instala dependencias del backend (pip)
   - Instala dependencias del frontend (npm)
   - Crea archivo .env desde .env.example

2. **Configurar API Keys:**

   Editar `ARGO/backend/.env`:
   ```env
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   PROJECT_NAME=DEFAULT_PROJECT
   ```

3. **Iniciar ARGO:**
   ```bash
   start_all.bat
   ```

   Esto abre dos ventanas:
   - Backend (http://localhost:8000)
   - Frontend (http://localhost:5173)

---

## 📖 Uso

### Acceso a la Plataforma

1. **Frontend (Interface de Usuario)**
   - URL: http://localhost:5173
   - Dashboard con Chat, Documentos, Analytics

2. **Backend API**
   - URL: http://localhost:8000
   - Documentación Swagger: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Operaciones Principales

#### 1. Chat Inteligente
- Escriba preguntas sobre sus documentos
- El sistema usa Intelligence Pipeline para respuestas precisas
- Incluye fuentes y nivel de confianza

#### 2. Gestión de Documentos
- Suba PDF, Word, Excel, imágenes
- Indexación automática con embeddings
- OCR para documentos escaneados

#### 3. Analytics
- Costos de API (OpenAI + Anthropic)
- Uso de tokens
- Distribución por proyecto

---

## 🏗️ Arquitectura

```
ARGO/
├── backend/                    # FastAPI Backend
│   ├── main.py                # REST API + WebSocket
│   ├── intelligence_pipeline.py  # Intelligence Pipeline
│   └── requirements.txt       # Dependencias Python
│
├── core/                      # ARGO Core Systems
│   ├── bootstrap.py           # Sistema de inicialización
│   ├── config.py              # Configuración
│   ├── rag_engine.py          # Motor RAG
│   ├── model_router.py        # Router LLM
│   ├── system_prompt.py       # Prompt especializado PMO
│   ├── unified_database.py    # Database SQLite
│   └── plugins/               # Sistema de plugins
│       ├── manager.py         # Plugin Manager
│       ├── base.py            # Plugin Base Class
│       └── events.py          # Event Bus
│
├── plugins/                   # Plugins Disponibles
│   ├── intelligence/          # 4 Intelligence Plugins
│   │   ├── query_planning_plugin.py
│   │   ├── agentic_retrieval_plugin.py
│   │   ├── corrective_rag_plugin.py
│   │   └── self_reflective_rag_plugin.py
│   ├── analysis/              # Analysis Plugins (PMO)
│   ├── parsers/               # Document Parsers
│   └── utils/                 # Utility Plugins
│
├── frontend/                  # React + TypeScript Frontend
│   └── client/
│       └── src/
│           ├── components/    # UI Components
│           ├── pages/         # Pages
│           ├── hooks/         # React Hooks
│           └── lib/           # Libraries (api, utils)
│
├── tests/                     # Tests
│   ├── test_plugin_system.py
│   ├── test_intelligence_plugins.py
│   └── conftest.py
│
└── docs/                      # Documentación

Scripts de Inicio (Raíz):
├── install.bat               # Instalación automática
├── start_all.bat            # Iniciar todo
├── start_backend.bat        # Solo backend
└── start_frontend.bat       # Solo frontend
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno (.env)

```env
# API Keys (REQUERIDO)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Proyecto
PROJECT_NAME=DEFAULT_PROJECT

# Modelos
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-sonnet-4

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=10

# Logging
LOG_LEVEL=INFO
```

### Extensión con Plugins

Para crear un nuevo plugin:

```python
from core.plugins.base import ARGOPlugin

class MiPlugin(ARGOPlugin):
    def __init__(self):
        super().__init__(
            name="mi_plugin",
            version="1.0.0",
            description="Mi plugin personalizado"
        )

    def execute(self, **kwargs):
        # Lógica del plugin
        return result
```

Colocar en: `plugins/[categoria]/mi_plugin.py`

El sistema auto-descubre y carga plugins automáticamente.

---

## 📊 Comparación de Versiones

### V10.12 vs V10.11

**Correcciones V10.12:**
- ✅ **CRÍTICO**: Frontend lib directory creado (api.ts, utils.ts, queryClient.ts)
- ✅ Scripts .bat de instalación y ejecución
- ✅ README.md completo con documentación
- ✅ Validación completa del código
- ✅ Sin errores de compilación

**Mantenido de V10.11:**
- ✅ Sistema prompt mejorado (283 líneas)
- ✅ Intelligence Pipeline completo
- ✅ Dependencias PMO (PyP6XER, networkx)
- ✅ Arquitectura core robusta

### V10.11 vs V10.07/V10.10

**Mejoras Significativas V10.11:**
- ✅ Sistema Prompt: 17 líneas → 283 líneas (+1,565%)
- ✅ Intelligence Pipeline: 0 → 4 plugins avanzados
- ✅ PMO Dependencies: Agregadas (PyP6XER, networkx)
- ✅ Reasoning Framework: Implementado

---

## 🐛 Solución de Problemas

### Error: "Module 'plugins.intelligence' not found"
**Solución:** Asegúrese de ejecutar desde el directorio correcto con uvicorn

### Error: "Failed to resolve import './lib/queryClient'"
**Solución:** Ejecute `install.bat` - ahora está corregido en V10.12

### Backend no inicia
**Solución:**
1. Verificar API keys en `.env`
2. Verificar Python 3.10+
3. Revisar `pip install -r requirements.txt`

### Frontend no carga
**Solución:**
1. Verificar Node.js 18+
2. Ejecutar `npm install` en `frontend/client`
3. Verificar puerto 5173 disponible

---

## 📈 Roadmap

### Próximas Versiones

**V10.13 (Planeado):**
- Schedule Analyzer Plugin (XER/MPP parsing)
- DCMA 14-Point Assessment completo
- Critical Path calculation
- Frontend: Funcionalidad completa de botones

**V11.0 (Futuro):**
- GAO Schedule Assessment
- Earned Value Management dashboard
- Resource Loading analysis
- Baseline comparison

---

## 🤝 Soporte

### Documentación
- API Docs: http://localhost:8000/docs
- Plugin System: `docs/plugins/README.md`
- Architecture: `docs/architecture.md`

### Logs
- Backend: `ARGO/logs/argo.log`
- Frontend: Consola del navegador (F12)

---

## 📄 Licencia

Este proyecto es propiedad de su organización. Todos los derechos reservados.

---

## 🎉 Créditos

**ARGO V10.12** - Enterprise PMO Platform

Desarrollado con:
- FastAPI + Python
- React + TypeScript + Tailwind
- LangChain + ChromaDB
- OpenAI GPT-4o + Anthropic Claude

**Versión:** 10.12
**Fecha:** Noviembre 2025
**Status:** ✅ Production Ready

---

## 📞 Quick Start Checklist

- [ ] Python 3.10+ instalado
- [ ] Node.js 18+ instalado
- [ ] API Keys configurados en `.env`
- [ ] Ejecutado `install.bat`
- [ ] Ejecutado `start_all.bat`
- [ ] Frontend accesible en http://localhost:5173
- [ ] Backend accesible en http://localhost:8000

**¡Listo para usar ARGO!** 🚀
