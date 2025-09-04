# app/api/tools.py
from typing import List, Dict, Any, Optional, Tuple
import re
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|MERGE|CALL|EXECUTE)\b", re.IGNORECASE)

def get_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)

def is_safe_select(sql: str) -> Tuple[bool, Optional[str]]:
    s = sql.strip().strip(";")
    if not s.lower().startswith("select"):
        return False, "Solo se permiten consultas SELECT."
    if FORBIDDEN.search(s):
        return False, "Consulta contiene palabras prohibidas (DML/DDL)."
    # Prohibir SELECT * salvo COUNT(*)
    if re.search(r"select\s+\*", s, flags=re.IGNORECASE) and not re.search(r"count\s*\(\s*\*\s*\)", s, flags=re.IGNORECASE):
        return False, "Evita SELECT *; especifica columnas."
    return True, None

class ListTablesInput(BaseModel):
    schema: Optional[str] = Field(None, description="Nombre del esquema (opcional).")

class DescribeTableInput(BaseModel):
    schema_table: str = Field(..., description="Nombre completo schema.table")

class SampleRowsInput(BaseModel):
    schema_table: str = Field(..., description="Nombre completo schema.table")
    limit: int = Field(50, ge=1, le=200, description="Límite de filas")

class RunSqlInput(BaseModel):
    sql: str = Field(..., description="Consulta SELECT segura")
    thought: str = Field(..., description="Breve plan (no se muestra al usuario)")

def list_schemas_tool(engine: Engine):
    def _list_schemas() -> List[str]:
        insp = inspect(engine)
        schemas = [s for s in insp.get_schema_names() if s not in ("information_schema", "pg_catalog", "pg_toast") ]
        return sorted(schemas)
    return StructuredTool.from_function(
        name="list_schemas",
        description="Lista esquemas disponibles en la base de datos.",
        func=_list_schemas
    )

def list_tables_tool(engine: Engine):
    def _list_tables(schema: Optional[str] = None) -> List[str]:
        insp = inspect(engine)
        schemas = [schema] if schema else [s for s in insp.get_schema_names() if s not in ("information_schema", "pg_catalog", "pg_toast") ]
        out = []
        for sch in schemas:
            try:
                for t in insp.get_table_names(schema=sch):
                    out.append(f"{sch}.{t}")
            except Exception:
                continue
        return sorted(out)
    return StructuredTool.from_function(
        name="list_tables",
        description="Lista tablas; si pasas schema, filtra por ese esquema.",
        func=_list_tables,
        args_schema=ListTablesInput
    )

def describe_table_tool(engine: Engine):
    def _describe(schema_table: str) -> List[Dict[str, Any]]:
        insp = inspect(engine)
        if "." not in schema_table:
            raise ValueError("Usa schema.table")
        schema, table = schema_table.split(".", 1)
        cols = insp.get_columns(table, schema=schema)
        return [{"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable", True)} for c in cols]
    return StructuredTool.from_function(
        name="describe_table",
        description="Describe columnas de una tabla (schema.table).",            func=_describe,
        args_schema=DescribeTableInput
    )

def sample_rows_tool(engine: Engine):
    def _sample(schema_table: str, limit: int = 50) -> Dict[str, Any]:
        if "." not in schema_table:
            raise ValueError("Usa schema.table")
        sql = f"SELECT * FROM {schema_table} ORDER BY 1 DESC LIMIT :limit"
        with engine.begin() as conn:
            rs = conn.execute(text(sql), {"limit": limit})
            rows = [dict(r._mapping) for r in rs]
            cols = list(rows[0].keys()) if rows else []
        return {"columns": cols, "rows": rows, "limit": limit}
    return StructuredTool.from_function(
        name="sample_rows",
        description="Muestra filas de una tabla (schema.table).",            func=_sample,
        args_schema=SampleRowsInput
    )

def run_sql_tool(engine: Engine):
    def _run(sql: str, thought: str) -> Dict[str, Any]:
        ok, err = is_safe_select(sql)
        if not ok:
            raise ValueError(err)
        with engine.begin() as conn:
            rs = conn.execute(text(sql))
            rows = [dict(r._mapping) for r in rs]
            cols = list(rows[0].keys()) if rows else []
        return {"sql": sql.strip().rstrip(";"), "columns": cols, "rows": rows}
    return StructuredTool.from_function(
        name="run_sql",
        description="Ejecuta un SELECT seguro y devuelve columnas/filas.",
        func=_run,
        args_schema=RunSqlInput
    )
