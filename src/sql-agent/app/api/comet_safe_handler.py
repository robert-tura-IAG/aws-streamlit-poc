# app/api/comet_safe_handler.py
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Optional

# Compatibilidad con distintas versiones de LangChain
try:
    # langchain >= 0.2
    from langchain_core.callbacks import BaseCallbackHandler  # type: ignore
except Exception:  # pragma: no cover
    try:
        # langchain <= 0.1
        from langchain.callbacks.base import BaseCallbackHandler  # type: ignore
    except Exception:  # pragma: no cover
        BaseCallbackHandler = object  # fallback mínimo

def _to_json(obj: Any, max_chars: int = 200_000) -> str:
    """Serializa a JSON seguro (corta tamaño para no saturar Comet)."""
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        s = str(obj)
    if len(s) > max_chars:
        return s[:max_chars] + f"... [truncated {len(s) - max_chars} chars]"
    return s

def _payload(obj: Any) -> Dict[str, Any]:
    """Normaliza cualquier cosa a un dict json-serializable."""
    try:
        if isinstance(obj, dict):
            base = obj
        elif isinstance(obj, (list, tuple)):
            base = {"list": list(obj)}
        else:
            base = {"value": obj}
        # fuerza serialización a tipos básicos
        base = json.loads(json.dumps(base, ensure_ascii=False, default=str))
        return base
    except Exception:
        return {"repr": repr(obj)}

def _rid(kwargs: Dict[str, Any]) -> str:
    """Obtiene un run_id estable si LangChain lo proporciona; si no, genera uno."""
    return (
        str(kwargs.get("run_id"))
        or str(kwargs.get("id"))
        or uuid.uuid4().hex[:8]
    )

class SafeCometCallbackHandler(BaseCallbackHandler):
    """
    Callback robusto para Comet:
      - Define flags ignore_* que LangChain consulta.
      - Acepta firmas v0.1/v0.2 con **kwargs sin romper.
      - Serializa payloads a JSON seguro y sube a Assets.
    """

    # ---- Flags que LangChain consulta mediante getattr(...) ----
    ignore_llm: bool = False
    ignore_chain: bool = False
    ignore_agent: bool = False
    ignore_retriever: bool = True
    raise_error: bool = False

    def __init__(
        self,
        experiment,
        tags: Optional[List[str]] = None,
        max_chars: int = 200_000,
        base_prefix: str = "trace",
    ):
        self.exp = experiment
        self.tags = tags or []
        self.max_chars = max_chars
        self.base_prefix = base_prefix

        # Intenta etiquetar el experimento (si no, ignora)
        try:
            for t in self.tags:
                # add_tag es soportado por comet_ml.Experiment
                self.exp.add_tag(t)
        except Exception:
            pass

    # ---------- Helpers ----------
    def _log_asset_json(self, path: str, obj: Any) -> None:
        try:
            self.exp.log_asset_data(_to_json(obj, self.max_chars), name=path)
        except Exception:
            # último recurso: no bloquear el flujo
            try:
                self.exp.log_other(f"trace_error::{path}", True)
            except Exception:
                pass

    def _log_text(self, text: Any, meta: Optional[Dict[str, Any]] = None):
        try:
            self.exp.log_text(_to_json(text, self.max_chars), metadata=meta or {})
        except Exception:
            pass

    # ---------- LLM ----------
    # Firma v0.2: (serialized, prompts, run_id, parent_run_id, tags, metadata, **kwargs)
    # Firma v0.1: (serialized, prompts, **kwargs)
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[Any], **kwargs: Any) -> None:  # type: ignore[override]
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/llm_start.json"
        payload = {
            "ts": time.time(),
            "serialized": _payload(serialized),
            "prompts": _payload([str(p) for p in (prompts or [])]),
        }
        self._log_asset_json(path, payload)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:  # type: ignore[override]
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/llm_end.json"
        payload = {
            "ts": time.time(),
            "response": _payload(response),
        }
        self._log_asset_json(path, payload)

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:  # type: ignore[override]
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/llm_error.json"
        payload = {
            "ts": time.time(),
            "error": _payload({"error": str(error)}),
        }
        self._log_asset_json(path, payload)

    # ---------- Chain ----------
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Any, **kwargs: Any) -> None:  # type: ignore[override]
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/chain_start.json"
        payload = {
            "ts": time.time(),
            "serialized": _payload(serialized),
            "inputs": _payload(inputs),
        }
        self._log_asset_json(path, payload)

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> None:  # type: ignore[override]
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/chain_end.json"
        payload = {
            "ts": time.time(),
            "outputs": _payload(outputs),
        }
        self._log_asset_json(path, payload)

    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:  # type: ignore[override]
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/chain_error.json"
        payload = {
            "ts": time.time(),
            "error": _payload({"error": str(error)}),
        }
        self._log_asset_json(path, payload)

    # ---------- Tool ----------
    def on_tool_start(self, serialized: Dict[str, Any], input_str: Optional[str], **kwargs: Any) -> None:  # type: ignore[override]
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/tool_start.json"
        payload = {
            "ts": time.time(),
            "serialized": _payload(serialized),
            "input": _payload(input_str),
        }
        self._log_asset_json(path, payload)

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:  # type: ignore[override]
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/tool_end.json"
        payload = {
            "ts": time.time(),
            "output": _payload(output),
        }
        self._log_asset_json(path, payload)

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:  # type: ignore[override]
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/tool_error.json"
        payload = {
            "ts": time.time(),
            "error": _payload({"error": str(error)}),
        }
        self._log_asset_json(path, payload)

    # ---------- (Opcional) Retriever ----------
    def on_retriever_start(self, serialized: Dict[str, Any], query: str, **kwargs: Any) -> None:  # type: ignore[override]
        if self.ignore_retriever:
            return
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/retriever_start.json"
        payload = {
            "ts": time.time(),
            "serialized": _payload(serialized),
            "query": _payload(query),
        }
        self._log_asset_json(path, payload)

    def on_retriever_end(self, documents: Any, **kwargs: Any) -> None:  # type: ignore[override]
        if self.ignore_retriever:
            return
        rid = _rid(kwargs)
        path = f"{self.base_prefix}/{rid}/retriever_end.json"
        payload = {
            "ts": time.time(),
            "documents": _payload(documents),
        }
        self._log_asset_json(path, payload)
