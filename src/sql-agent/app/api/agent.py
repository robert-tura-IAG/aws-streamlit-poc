# app/api/agent.py
from typing import Dict, Any, List, Optional
import json
import re
import time

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from .prompts import SYSTEM_PROMPT, FEW_SHOTS
from .tools import (
    get_engine,
    list_schemas_tool, list_tables_tool, describe_table_tool, sample_rows_tool, run_sql_tool
)
from .settings import settings
from .comet_safe_handler import SafeCometCallbackHandler  # se pasa a telemetry

# --- Telemetría centralizada ---
from .telemetry import (
    get_langfuse_handler,
    CometTelemetry,
    init_opik_tracer,
    build_root_callbacks,
    make_score_node,
    strip_sql_blocks,
)

# --------------------------------------------------------------------
# Observabilidad (Langfuse + Comet) inicial
# --------------------------------------------------------------------
langfuse_handler = get_langfuse_handler()
comet = CometTelemetry(
    settings=settings,
    system_prompt=SYSTEM_PROMPT,
    safe_handler_cls=SafeCometCallbackHandler,
    tags=["aero-sql-agent"],
)
comet_exp = comet.exp            # alias exportable si lo usas fuera
comet_handler = comet.handler    # se usará en callbacks

# --------------------------------------------------------------------
# Modelo + Herramientas
# --------------------------------------------------------------------
engine = get_engine(settings.database_url)

tools = [
    list_schemas_tool(engine),
    list_tables_tool(engine),
    describe_table_tool(engine),
    sample_rows_tool(engine),
    run_sql_tool(engine),
]

llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0,
)
llm_with_tools = llm.bind_tools(tools)

# --------------------------------------------------------------------
# Grafo ReAct 
# --------------------------------------------------------------------
graph = StateGraph(MessagesState)

def call_model(state: MessagesState):
    # NO pasar callbacks aquí; heredan del invoke raíz
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph.add_node("model", call_model)
graph.add_node("tools", ToolNode(tools))

# Nodo de métricas “score” (vive dentro del trace de Opik)
graph.add_node("score", make_score_node())

def route_after_model(state: MessagesState) -> str:
    """
    Si el último mensaje del modelo contiene tool_calls -> ir a tools,
    si no -> ir al nodo de métricas 'score'.
    """
    msgs = state["messages"]
    last_ai = None
    for m in reversed(msgs):
        if getattr(m, "type", None) == "ai":
            last_ai = m
            break
    tool_calls = getattr(last_ai, "tool_calls", None) if last_ai else None
    return "tools" if tool_calls else "score"

graph.add_edge(START, "model")
graph.add_conditional_edges("model", route_after_model)
graph.add_edge("tools", "model")   # bucle hasta que ya no haya tools
graph.add_edge("score", END)       # cierre pasando por score

app_graph = graph.compile()

# --------------------------------------------------------------------
# Opik (tracing LangGraph) — pasar SOLO en la invocación raíz
# --------------------------------------------------------------------
opik_tracer = init_opik_tracer(app_graph, settings, default_tags=["aero-sql-agent"])

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def _root_callbacks() -> List[Any]:
    """Callbacks que se aplican SOLO en la invocación raíz del grafo."""
    return build_root_callbacks(langfuse_handler, comet_handler, opik_tracer)

def build_messages(question: str) -> List[Any]:
    msgs: List[Any] = [SystemMessage(content=SYSTEM_PROMPT)]
    for shot in FEW_SHOTS:
        msgs.append(HumanMessage(content=shot["user"]))
        msgs.append(SystemMessage(content=f"SQL de referencia:\n{shot['sql']}"))
    msgs.append(HumanMessage(content=question))
    return msgs

# --------------------------------------------------------------------
# Entrada principal
# --------------------------------------------------------------------
def ask_agent(question: str) -> Dict[str, Any]:
    # Construye mensajes y “nudge” para que EJECUTE run_sql si aplica
    msgs = build_messages(question)
    msgs.append(HumanMessage(content=(
        "IMPORTANTE: Si la pregunta requiere datos, ejecuta la herramienta run_sql "
        "con el SELECT final; no devuelvas solo el SQL en texto."
    )))
    state = {"messages": msgs}

    # Métrica de tiempo global (para Comet; en Opik la latencia puedes meterla con reglas o spans)
    t0 = time.perf_counter()
    out = app_graph.invoke(state, config={"callbacks": _root_callbacks()})
    latency_s = round(time.perf_counter() - t0, 4)

    # Texto del asistente (limpio para Comet)
    assistant_msgs = [m for m in out["messages"] if m.type == "ai"]
    raw_text = assistant_msgs[-1].content if assistant_msgs else ""
    clean_text = strip_sql_blocks(raw_text or "")

    # Último resultado del tool
    sql: Optional[str] = None
    columns: List[str] = []
    rows: List[List[Any]] = []
    for m in reversed(out["messages"]):
        if m.type == "tool":
            try:
                payload = json.loads(m.content) if isinstance(m.content, str) else (m.content or {})
            except Exception:
                payload = {}
            if payload.get("sql"):
                sql = payload.get("sql")
                columns = payload.get("columns") or payload.get("column_names") or []
                rows = payload.get("rows") or []
                break

    # Logs a Comet (independiente de Opik)
    comet.log_turn(
        question=question,
        answer_text=clean_text,
        sql=sql,
        columns=columns,
        rows=rows,
    )
    try:
        comet_exp.log_other("latency_s", latency_s)
    except Exception:
        pass

    return {
        "answer_text": clean_text,
        "sql": sql,
        "columns": columns,
        "rows": rows
    }
