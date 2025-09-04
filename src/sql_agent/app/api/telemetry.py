# app/api/telemetry.py
from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
import os
import uuid
import io
import csv
import json
import re

# Langfuse (callback de LangChain)
from langfuse.langchain import CallbackHandler as LangfuseHandler
# Comet
from comet_ml import Experiment

# Para el score_node
from langchain_core.messages import AIMessage

# ---------------------------
# Utilidades comunes
# ---------------------------
def strip_sql_blocks(text: str) -> str:
    """Elimina bloques ```sql ...``` y otros bloques con SELECT del texto."""
    if not isinstance(text, str):
        return ""
    t = re.sub(r"```sql\s*[\s\S]*?```", "", text, flags=re.IGNORECASE)

    def _maybe_drop(m):
        return "" if re.search(r"\bSELECT\b", m.group(0), re.IGNORECASE) else m.group(0)

    t = re.sub(r"```[\s\S]*?```", _maybe_drop, t)
    t = re.sub(r"`[^`]*SELECT[^`]*`", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t


def _maybe_json(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        try:
            return json.loads(x.strip())
        except Exception:
            return {}
    return {}


# ---------------------------
# Langfuse
# ---------------------------
def get_langfuse_handler() -> LangfuseHandler:
    """Devuelve el callback handler de Langfuse para LangChain."""
    return LangfuseHandler()


# ---------------------------
# Comet
# ---------------------------
class _DummyComet:
    def log_other(self, *a, **k): ...
    def log_parameter(self, *a, **k): ...
    def log_text(self, *a, **k): ...
    def log_asset_data(self, *a, **k): ...
    def get_url(self): return "COMET_DISABLED"


class CometTelemetry:
    """
    Encapsula la inicialización de Comet + handler seguro
    y utilidades para loguear por turno.
    """
    def __init__(self, settings, system_prompt: str, safe_handler_cls, tags: Optional[List[str]] = None):
        self.enabled = bool(settings.comet_api_key and settings.comet_workspace and settings.comet_project_name)

        # Normaliza variables de entorno
        if settings.comet_api_key:
            os.environ["COMET_API_KEY"] = settings.comet_api_key
        if settings.comet_workspace:
            os.environ["COMET_WORKSPACE"] = settings.comet_workspace
        if settings.comet_project_name:
            os.environ["COMET_PROJECT_NAME"] = settings.comet_project_name

        if self.enabled:
            self.exp = Experiment(
                api_key=settings.comet_api_key,
                project_name=settings.comet_project_name,
                workspace=settings.comet_workspace,
                parse_args=False,
                auto_param_logging=False,
                auto_metric_logging=False,
                auto_log_co2=False,
            )
            self.exp.set_name("aero-sql-agent-session")
            self.exp.log_parameter("prompt_name", settings.prompt_name)
            self.exp.log_parameter("prompt_version", settings.prompt_version)
            self.exp.log_text(
                system_prompt,
                metadata={"kind": "system_prompt", "name": settings.prompt_name, "version": settings.prompt_version},
            )
            tag_list = tags or []
            try:
                self.handler = safe_handler_cls(
                    experiment=self.exp,
                    tags=tag_list + [f"prompt:{settings.prompt_name}", f"version:{settings.prompt_version}"],
                )
            except Exception:
                self.handler = None

            try:
                self.exp.log_other("startup", True)
                self.exp.log_asset_data("hello from agent", name="startup/hello.txt")
                if hasattr(self.exp, "get_url"):
                    print("[COMET] Experiment URL:", self.exp.get_url())
                else:
                    print("[COMET] get_url() no disponible (OK). Abre el experimento reciente en tu proyecto.")
            except Exception as e:
                print("[COMET] Startup log fallo:", e)
        else:
            self.exp = _DummyComet()
            self.handler = None

    def log_turn(self,
                 question: str,
                 answer_text: str,
                 sql: Optional[str],
                 columns: List[str],
                 rows: List[List[Any]]) -> None:
        """Sube a Comet assets legibles por cada turno + text logs."""
        try:
            run_id = uuid.uuid4().hex[:8]
            prefix = f"trace/{run_id}"
            # Text tab
            try:
                self.exp.log_text(question or "", metadata={"role": "user"})
                self.exp.log_text(answer_text or "", metadata={"role": "assistant"})
            except Exception:
                pass
            # Assets
            self.exp.log_asset_data(question or "", name=f"{prefix}/question.txt")
            if sql:
                self.exp.log_asset_data(sql, name=f"{prefix}/final_sql.sql")
                self.exp.log_other("last_sql", sql)
            self.exp.log_asset_data(answer_text or "", name=f"{prefix}/answer.txt")
            if rows and columns:
                buf = io.StringIO()
                w = csv.writer(buf)
                w.writerow(columns)
                for r in rows[:200]:
                    w.writerow(r)
                self.exp.log_asset_data(buf.getvalue(), name=f"{prefix}/result_sample.csv")
            self.exp.log_other("run_id", run_id)
            self.exp.log_other("app_component", "agent.py")
        except Exception as e:
            print("[COMET] Fallo al loguear assets del turno:", e)


# ---------------------------
# Opik
# ---------------------------
def init_opik_tracer(app_graph, settings, default_tags: Optional[List[str]] = None):
    """Inicializa OpikTracer con xray si es posible. Devuelve el tracer o None."""
    tracer = None
    try:
        from opik.integrations.langchain import OpikTracer  # integración oficial

        # Propaga .env (si se definieron en settings)
        if getattr(settings, "opik_api_key", None):
            os.environ["OPIK_API_KEY"] = settings.opik_api_key
        if getattr(settings, "opik_workspace", None):
            os.environ["OPIK_WORKSPACE"] = settings.opik_workspace
        if getattr(settings, "opik_project_name", None):
            os.environ["OPIK_PROJECT_NAME"] = settings.opik_project_name
        if getattr(settings, "opik_url_override", None):
            os.environ["OPIK_URL_OVERRIDE"] = settings.opik_url_override

        tags = default_tags or []
        try:
            tracer = OpikTracer(graph=app_graph.get_graph(xray=True), tags=tags)
        except Exception as e_xray:
            print("[OPIK] app_graph.get_graph(xray=True) falló:", repr(e_xray))
            tracer = OpikTracer(tags=tags)

        print("[OPIK] OpikTracer habilitado.")
    except Exception as e:
        print("[OPIK] OpikTracer init failed:", repr(e))
    print("[OPIK] workspace =", os.getenv("OPIK_WORKSPACE"))
    print("[OPIK] project   =", os.getenv("OPIK_PROJECT_NAME"))
    print("[OPIK] url       =", os.getenv("OPIK_URL_OVERRIDE", "default-cloud"))
    print("[OPIK] enabled   =", bool(tracer))
    return tracer


def build_root_callbacks(langfuse_handler, comet_handler, opik_tracer) -> List[Any]:
    """Callbacks que se aplican SOLO en la invocación raíz del grafo."""
    cbs: List[Any] = [langfuse_handler]
    if comet_handler:
        cbs.append(comet_handler)
    if opik_tracer:
        cbs.append(opik_tracer)
    return cbs


def make_score_node() -> Callable[[Any], Dict[str, Any]]:
    """
    Devuelve una función 'score_node(state)' que calcula métricas deterministas
    y las envía a Opik usando el contexto ACTUAL (update_current_trace).
    """
    def score_node(state):
        messages = state["messages"]
        raw_text = ""
        for m in reversed(messages):
            if isinstance(m, AIMessage):
                raw_text = m.content or ""
                break

        sql = None
        columns: List[str] = []
        rows: List[List[Any]] = []
        tool_executed = False

        for m in reversed(messages):
            if getattr(m, "type", None) == "tool":
                payload = _maybe_json(getattr(m, "content", {}))
                candidate_sql = payload.get("sql")
                if candidate_sql:
                    sql = candidate_sql
                    columns = payload.get("columns") or payload.get("column_names") or []
                    rows = payload.get("rows") or []
                    tool_executed = True
                    break

        clean_text = strip_sql_blocks(raw_text or "")

        try:
            from opik.opik_context import update_current_trace
            metrics = [
                {
                    "name": "has_sql",
                    "value": 1.0 if sql else 0.0,
                    "reason": "El agente produjo SQL final" if sql else "No se detectó SQL final",
                },
                {
                    "name": "tool_executed",
                    "value": 1.0 if tool_executed else 0.0,
                    "reason": "Se ejecutó run_sql" if tool_executed else "No se ejecutó ninguna tool",
                },
                {
                    "name": "rows_returned",
                    "value": min(float(len(rows) if rows is not None else 0) / 100.0, 1.0),
                    "reason": f"{len(rows) if rows is not None else 0} filas devueltas (cap 100)",
                },
                {
                    "name": "answer_len_norm",
                    "value": min(float(len(clean_text)) / 800.0, 1.0),
                    "reason": f"{len(clean_text)} caracteres en respuesta (cap 800)",
                },
            ]
            update_current_trace(feedback_scores=metrics)
        except Exception as e:
            print("[OPIK] score_node no pudo registrar feedback:", repr(e))

        return {}
    return score_node
