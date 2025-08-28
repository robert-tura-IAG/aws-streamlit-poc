# app/api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .agent import ask_agent



app = FastAPI(title="MyFindings API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

class QueryRequest(BaseModel):
    question: str
    output_mode: str | None = None # "sql" | "text"

class QueryResponse(BaseModel):
    answer_text: str | None = None
    sql: str | None = None
    columns: list[str] = []
    rows: list[dict] = []

@app.get("/healthz")
def healthz():
    return {"status":"ok"}

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        
        result = ask_agent(req.question)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
