# scripts/load_data.py
import os
import time
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT / ".env", override=True)

# --- Config ---
DATABASE_URL  = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/aero")

# Acepta EXCEL_FILE o DATA_FILE (por compatibilidad). Usa Excel por defecto.
DATA_FILE     = os.getenv("EXCEL_FILE", os.getenv("DATA_FILE", "data/failure_dataset_mock_100.xlsx"))
# Acepta EXCEL_SHEET o DATA_SHEET. OJO: None en pandas devuelve dict; mejor 0 (primera hoja).
SHEET_ENV     = os.getenv("EXCEL_SHEET", os.getenv("DATA_SHEET", "")).strip()
TARGET_SCHEMA = os.getenv("TARGET_SCHEMA", "aircraft_data")
TARGET_TABLE  = os.getenv("TARGET_TABLE", "findings_raw")
IF_EXISTS     = os.getenv("IF_EXISTS", "replace")  # replace | append | fail

# --- Helpers ---
def wait_for_db(url: str, timeout: int = 60):
    eng = create_engine(url, pool_pre_ping=True)
    start, last = time.time(), None
    while time.time() - start < timeout:
        try:
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
                return eng
        except OperationalError as e:
            last = e
            time.sleep(2)
    raise SystemExit(f"[ERROR] No pude conectar a Postgres: {url}\nÚltimo error: {last}")

def dedupe_columns(cols):
    seen = {}
    out = []
    for c in cols:
        c = str(c)
        n = seen.get(c, 0) + 1
        seen[c] = n
        out.append(c if n == 1 else f"{c}__{n}")
    return out

def read_any(path: Path, sheet_hint: str) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"[ERROR] No existe el fichero: {path}")
    ext = path.suffix.lower()
    print(f"[INFO] Leyendo: {path}")
    if ext in (".xlsx", ".xls"):
        # IMPORTANTE: no pasar None; usa 0 (primera hoja) si no se especifica
        if sheet_hint == "" or sheet_hint.lower() == "none":
            sheet = 0
        else:
            # índice numérico o nombre de hoja
            sheet = int(sheet_hint) if sheet_hint.isdigit() else sheet_hint
        return pd.read_excel(path, sheet_name=sheet)
    else:
        # CSV: intenta encodings comunes
        last = None
        for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
            try:
                print(f"[INFO] Intentando CSV con encoding={enc}")
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError as e:
                last = e
        raise SystemExit(f"[ERROR] No pude leer el CSV con utf-8/utf-8-sig/cp1252/latin1.\nÚltimo error: {last}")

def main():
    # Resolver ruta del archivo
    p = Path(DATA_FILE)
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    print(f"[INFO] CWD: {Path.cwd()}")
    print(f"[INFO] Archivo esperado: {p}")
    print(f"[INFO] Hoja: {'<primera (0)>' if SHEET_ENV in ('', 'None', 'none') else SHEET_ENV}")

    # Leer a DataFrame (no dict)
    df = read_any(p, SHEET_ENV)

    # Asegurar nombres string y sin duplicados
    df.columns = dedupe_columns([str(c) for c in df.columns])
    print(f"[INFO] Filas: {len(df):,}  Columnas: {len(df.columns)}")
    print(f"[INFO] Primeras columnas: {df.columns[:10].tolist()}")

    # Conectar y crear esquema
    engine = wait_for_db(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{TARGET_SCHEMA}";'))

    # Escribir tal cual (sin renombrar)
    print(f"[INFO] Escribiendo en {TARGET_SCHEMA}.{TARGET_TABLE} (if_exists={IF_EXISTS}) …")
    df.to_sql(
        TARGET_TABLE,
        con=engine,
        schema=TARGET_SCHEMA,
        if_exists=IF_EXISTS,  # replace/append/fail
        index=False,
        chunksize=1000,
    )

    print(f"[OK] Carga completada: {TARGET_SCHEMA}.{TARGET_TABLE}")

if __name__ == "__main__":
    main()
