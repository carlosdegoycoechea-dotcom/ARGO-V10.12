# ARGO V10.12 - Enterprise PMO Platform

**Versión:** 10.12
**Fecha:** Noviembre 2025
**Estado:** Production Ready ✅

---

## 🚀 Inicio Rápido

### 1. Instalación

```bash
cd ARGO
INSTALAR.bat
```

### 2. Configuración

Editar `ARGO/.env` con tus API keys:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Iniciar Sistema

```bash
cd ARGO
INICIAR.bat
```

El sistema abrirá automáticamente:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs

---

## 📁 Estructura del Proyecto

```
ARGO-V10.12/
├── ARGO/                   # Sistema principal
│   ├── backend/           # FastAPI backend
│   ├── frontend/          # React + TypeScript frontend
│   ├── core/              # ARGO core systems
│   ├── plugins/           # Sistema de plugins
│   ├── tests/             # Tests
│   ├── INSTALAR.bat       # Script de instalación
│   ├── INICIAR.bat        # Script de inicio
│   └── DETENER.bat        # Script para detener
│
├── docs/                   # Documentación completa
│   ├── README.md          # Guía principal
│   ├── CHANGELOG.md       # Historial de cambios
│   ├── AUDITORIA_V10.12.md  # Auditoría técnica
│   └── ...                # Más documentación
│
└── _archive/              # Archivos históricos
    └── ...                # ZIPs, logs antiguos, etc.
```

---

## 🎯 Características Principales

### Core Systems
✅ **RAG Engine Avanzado**: HyDE + Reranking + Cache
✅ **Intelligence Pipeline**: 4 plugins de IA (Query Planning, Agentic Retrieval, Corrective RAG, Self-Reflective RAG)
✅ **Sistema Prompt PMO**: 283 líneas especializado (DCMA, GAO, EVM, CPM)
✅ **Model Router**: GPT-4o + Claude Sonnet con routing automático
✅ **Plugin System**: 10+ plugins funcionales

### PMO Features
✅ **DCMA 14-Point Assessment**: Análisis completo de calidad de schedule
✅ **XER Parser**: Parseo de Primavera P6 (PyP6XER)
✅ **Critical Path Analysis**: CPM completo con networkx
✅ **Schedule Analyzer**: Router universal XER/XML

### Frontend
✅ **React + TypeScript**: Interface moderna
✅ **Tailwind CSS + shadcn/ui**: Componentes UI
✅ **React Query**: State management
✅ **WebSocket**: Chat en tiempo real

---

## 📖 Documentación

Toda la documentación está en la carpeta `docs/`:

- **README.md** - Guía completa del usuario
- **CHANGELOG.md** - Historial detallado de cambios
- **AUDITORIA_V10.12.md** - Auditoría técnica exhaustiva
- **GUIA_INSTALACION_RAPIDA.md** - Guía rápida de instalación
- **INTELLIGENCE_SYSTEM.md** - Sistema de inteligencia
- Y más...

---

## ⚙️ Requisitos del Sistema

- **Python**: 3.11 o superior
- **Node.js**: 18 o superior
- **Sistema Operativo**: Windows 10/11
- **API Keys**: OpenAI (obligatorio), Anthropic (opcional)

---

## 🔧 Comandos Principales

Todos los comandos se ejecutan desde la carpeta `ARGO/`:

```bash
# Instalación completa
INSTALAR.bat

# Iniciar sistema completo
INICIAR.bat

# Detener sistema
DETENER.bat
```

---

## 🐛 Solución de Problemas

### Python no reconocido
- Asegúrate de tener Python 3.11+ instalado
- Verifica que Python esté en el PATH
- El script usa `py -3.11` automáticamente

### Node.js no reconocido
- Instala Node.js 18+ desde https://nodejs.org/
- Reinicia la terminal después de instalar

### API Keys no funcionan
- Edita `ARGO/.env` con un editor de texto
- Asegúrate de usar API keys válidas
- OpenAI: sk-proj-... o sk-...
- Anthropic: sk-ant-...

### Frontend no carga
- Verifica que el puerto 5173 esté libre
- Revisa la consola del navegador (F12)
- Ejecuta `cd ARGO/frontend/client && npm install`

### Backend no inicia
- Verifica que el puerto 8000 esté libre
- Revisa los logs en la ventana del backend
- Verifica que el entorno virtual esté creado: `ARGO/venv/`

---

## 📊 Comparación de Versiones

| Aspecto | V10.11 | V10.12 |
|---------|--------|--------|
| **Frontend** | ❌ Roto | ✅ Funcional |
| **Scripts .bat** | ❌ No existen | ✅ 3 scripts |
| **Documentación** | ⚠️ Dispersa | ✅ Organizada |
| **Estructura** | ⚠️ Duplicados | ✅ Limpia |
| **Score** | 70/100 | 92/100 |

---

## 🎉 Novedades V10.12

### Correcciones Críticas
- ✅ Frontend lib/ directory creado (BLOQUEANTE en V10.11)
- ✅ Scripts .bat funcionales (INSTALAR, INICIAR, DETENER)
- ✅ Estructura limpia sin duplicados
- ✅ Documentación organizada en `docs/`

### Mejoras
- ✅ Uso de `py` en vez de `python` (compatibilidad Windows)
- ✅ Archivos históricos en `_archive/`
- ✅ 22 documentos consolidados en `docs/`
- ✅ Sin carpetas ARGO duplicadas

---

## 📞 Soporte

Para reportar problemas o solicitar ayuda:

1. Revisa la documentación en `docs/`
2. Verifica los logs del sistema
3. Consulta la sección "Solución de Problemas"

---

## 📄 Licencia

Proyecto propietario. Todos los derechos reservados.

---

**ARGO V10.12** - Production Ready
*Última actualización: Noviembre 24, 2025*
