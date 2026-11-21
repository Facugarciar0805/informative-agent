# Daily News Agent

Agente autónomo de noticias diseñado para recopilar la actualidad del día, filtrar únicamente las historias relevantes según intereses definidos y entregar un resumen claro, estructurado y listo para leer en pocos minutos.

El objetivo del proyecto es reemplazar la lectura manual y dispersa de portales por un *briefing* diario automatizado, construido sobre una arquitectura modular pensada para incorporar nuevas fuentes, criterios de curación y canales de entrega sin reescribir el núcleo.

---

## Cómo funciona

El flujo se organiza en tres etapas desacopladas:

1. **Recolección:** los scrapers obtienen los titulares recientes de las fuentes configuradas y exponen sus datos bajo un modelo común.
2. **Selección y síntesis:** un agente con *tool calling* evalúa la portada, descarta temas fuera de interés, lee en profundidad el cuerpo de las notas más relevantes y redacta el resumen agrupado por categoría.
3. **Entrega:** el resultado se adapta y envía a través del canal de notificación activo (actualmente mensajería, con soporte previsto para nuevos canales como correo electrónico).

---

## Arquitectura

```text
├── main.py              # Entrypoint y configuración de logging / dependencias
├── src/
│   ├── agent.py         # Definición del agente, system prompt y registro de tools
│   ├── tools.py         # Tools expuestas al agente y resolución determinística de links
│   ├── service.py       # Casos de uso, reintentos y fallback entre modelos
│   ├── models.py        # DTOs inmutables de dominio
│   ├── utils.py         # Helpers compartidos
│   ├── scrappers/       # Contrato (Protocol) e implementaciones por medio
│   └── notifiers/       # Contrato (Protocol) e implementaciones por canal de entrega
└── .github/workflows/   # Ejecución programada en GitHub Actions
```

La separación mediante contratos (`Protocol`) en `src/scrappers/` y `src/notifiers/` permite extender el sistema agregando nuevos portales o canales sin acoplar la lógica de orquestación ni el prompt del agente a una implementación particular.

---

## Stack

- **Lenguaje:** Python 3.13+
- **Orquestación de agente:** Strands Agents (`strands-agents`)
- **LLM:** Google Gemini (`google-genai`)
- **Scraping:** `requests` + `beautifulsoup4`
- **Automatización:** GitHub Actions

---

## Ejecución local

1. Crear y activar el entorno virtual e instalar dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configurar variables de entorno tomando [.env.example](.env.example) como plantilla:

```bash
cp .env.example .env
```

3. Ejecutar el resumen diario:

```bash
python main.py
```

---

## Automatización con GitHub Actions

El repositorio incluye un workflow programado para ejecutarse de forma diaria y permitir disparos manuales desde la pestaña **Actions** (`workflow_dispatch`).

Para habilitarlo en GitHub, configurá los siguientes **Repository Secrets** en *Settings → Secrets and variables → Actions*:

| Secret | Obligatorio | Descripción |
| --- | --- | --- |
| `GEMINI_API_KEY` | Sí | Clave de API de Google AI Studio / Gemini |
| `GEMINI_MODEL` | Sí | Identificador del modelo principal a utilizar |
| `TELEGRAM_BOT_TOKEN` | Sí | Token del bot emitido por `@BotFather` |
| `TELEGRAM_CHAT_ID` | Sí | Identificador del chat destinatario |
| `GEMINI_FALLBACK_MODELS` | No | Lista separada por comas de modelos de respaldo ante errores transitorios |

Una vez cargados los secrets, podés validar la integración en la nube ejecutando manualmente el workflow **Daily News Briefing** desde la pestaña **Actions**.
