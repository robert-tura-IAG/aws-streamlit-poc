# ✈️ MyFindings

Agente de consulta SQL para mantenimiento aeronáutico con FastAPI (API), LangGraph/LangChain + OpenAI (LLM), Streamlit (UI), Langfuse y Comet (observabilidad), y Postgres por Docker Compose.

## Estructura
- **API**: `app/api` (FastAPI, agente, herramientas)
- **UI**: `app/streamlit_app.py`
- **Datos**: `docker-compose.yml` levanta Postgres; cargamos CSV con `scripts/load_data.py`
- **Observabilidad**: Langfuse + Comet (versionado de prompts incluido)
- **CSV de ejemplo**: `data/failure.dataset_mock_100.csv`

## Requisitos
- Docker + Docker Compose
- Python 3.11+
- Claves de: OpenAI, (opcional) Langfuse y Comet

## 1) Configuración
```bash
cp .env.example .env

```

> Si tu fichero original se llama `failure.datqaset_mock_100` (con esa grafía), renómbralo a `failure.dataset_mock_100.csv` o cambia `DATA_FILE` en `.env` para evitar errores.

## 2) Levantar Postgres
```bash
docker-compose up -d
```

## 3) Instalar dependencias
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 4) Cargar datos
Pon tu CSV en `data/` o usa el CSV de ejemplo ya incluido:
```bash
python scripts/load_data.py
```

## 5) Arrancar API
```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 6) Arrancar UI (Streamlit)
```bash
streamlit run app/streamlit_app.py
```

Abre `http://localhost:8501`. Escribe en el chat y pulsa **Enter** para enviar. Cambia el selector **Texto / SQL** para ver el SQL exacto generado.

## Observabilidad
- **Langfuse**: tracking de llamadas LLM y herramientas (requiere tus claves en `.env`)
- **Comet**: callback de LangChain + logging manual del prompt con nombre/versión para versionado reproducible.
- **Opik**


### Notas
- El agente sólo ejecuta **SELECT** y evita `SELECT *` (salvo `COUNT(*)`).
- Por defecto excluye `non_relevant = TRUE`.
- En exploración aplica `LIMIT 50` y ordena por fecha descendente cuando tenga sentido.

## pgAdmin
Accede a `http://localhost:8080` (usuario: `admin@local`, pass: `admin`) y añade un servidor manualmente apuntando a `postgres:5432` con user `postgres`, pass `postgres`.
