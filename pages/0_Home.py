# pages/0_Home.py
import streamlit as st
import pandas as pd
import numpy as np
from plotly import graph_objects as go
from datetime import date, timedelta

from src.data_load import get_local_csv_data
from src.utils import set_base_session_sates, filter_data

# Captura de clics en Plotly (un plus)
try:
    from streamlit_plotly_events import plotly_events
    _HAS_PLOTLY_EVENTS = True
except Exception:
    _HAS_PLOTLY_EVENTS = False

st.set_page_config(page_title="Top 10 Tasks by Findings Ratio", layout="wide")
set_base_session_sates()

# -------------------- Carga de datos --------------------
df = get_local_csv_data().copy()

# -------------------- Filtro de fechas (rango o manual) --------------------
st.subheader("Filters")
mode = st.radio("Date Range", ["Range", "Manual"], horizontal=True)

if mode == "Range":  # <<< antes ponía 'Rango'
    start_default = min(st.session_state.end_date, st.session_state.ini_date)
    end_default   = max(st.session_state.end_date, st.session_state.ini_date)
    date_interval = st.date_input("Time Window (range)", (start_default, end_default))

    if isinstance(date_interval, (list, tuple)) and len(date_interval) == 2:
        start, end = sorted(date_interval)
    elif isinstance(date_interval, (list, tuple)) and len(date_interval) == 1:
        end = date_interval[0]; start = end - timedelta(days=365)
    else:
        end = date.today(); start = end - timedelta(days=365)
else:
    c1, c2 = st.columns(2)
    with c1:
        start = st.date_input("Start date", min(st.session_state.end_date, st.session_state.ini_date))
    with c2:
        end   = st.date_input("End date",   max(st.session_state.end_date, st.session_state.ini_date))
    if start > end:
        st.warning("Start date > End date. Swapping to keep a valid range.")
        start, end = end, start

# Para utils.filter_data
st.session_state.end_date = start   # inicio
st.session_state.ini_date = end     # fin

# -------------------- Aplicar filtros --------------------
filtered_df = filter_data(df).copy()

# Normaliza fechas
if "Date" in filtered_df.columns:
    filtered_df["Date"] = pd.to_datetime(filtered_df["Date"], errors="coerce")
if "issue_date" in filtered_df.columns:
    filtered_df["issue_date"] = pd.to_datetime(filtered_df["issue_date"], errors="coerce")

# --- ID de finding (F) ---  lo esto yusando apra contar findins unicos porqe si el set no lo tiene se va a inventar indices
if "finding_id" not in filtered_df.columns:
    filtered_df["finding_id"] = filtered_df.index.astype(str)
else:
    filtered_df["finding_id"] = filtered_df["finding_id"].astype(str)

# --- ID de ejecución (E): task_id + ac_registration_id + issue_date(día) ---
if "issue_date" in filtered_df.columns and filtered_df["issue_date"].notna().any():
    exec_day = filtered_df["issue_date"].dt.strftime("%Y-%m-%d").fillna("NA")
elif "Date" in filtered_df.columns and filtered_df["Date"].notna().any():
    exec_day = filtered_df["Date"].dt.strftime("%Y-%m-%d").fillna("NA")
else:
    exec_day = pd.Series(["NA"] * len(filtered_df))

task = filtered_df.get("task_id", pd.Series(["NA"] * len(filtered_df))).astype(str).fillna("NA")
reg  = filtered_df.get("ac_registration_id", pd.Series(["NA"] * len(filtered_df))).astype(str).fillna("NA")
filtered_df["__exec_id__"] = task.str.cat(reg, sep="|").str.cat(exec_day, sep="|")

# -------------------- Stats por task y Top-10 --------------------
st.markdown("### Top 10 tasks by **ratio (F/E)**")
st.caption("Click on a bar to see the details of the task.")

if filtered_df.empty:
    st.warning("No data for the selected period.")
    st.stop()

stats_by_task = (
    filtered_df.groupby("task_id", dropna=False)
    .agg(F=("finding_id", "nunique"), E=("__exec_id__", "nunique"))
    .reset_index()
)
stats_by_task = stats_by_task[stats_by_task["E"] > 0]
if stats_by_task.empty:
    st.warning("No tasks with executions (E > 0) under the selected range.")
    st.stop()

stats_by_task["ratio"] = stats_by_task["F"] / stats_by_task["E"]

# Top-10 por ratio (desc)
top10 = stats_by_task.sort_values("ratio", ascending=False).head(10).copy()

# Mapa etiqueta->valor original (para filtrar sin perder dtype)
id_map = {str(k): k for k in top10["task_id"].tolist()}

# -------------------- Gráfico (X = task_id, Y = ratio) --------------------
cat_labels = [str(x) for x in top10["task_id"].tolist()]
max_ratio = float(top10["ratio"].max())

# Tooltip con el hover (no dependemos de customdata)
hovertext = [
    f"Task: {x}<br>"
    f"Ratio (F/E): {r:.2f}<br>"
    f"#Findings (F): {int(f)}<br>"
    f"Executions (E): {int(e)}"
    for x, r, f, e in zip(cat_labels, top10["ratio"], top10["F"], top10["E"])
]

fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=cat_labels,
        y=top10["ratio"].to_list(),
        orientation="v",
        text=[f"{v:.2f}" for v in top10["ratio"].to_numpy()],  # etiqueta fija
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="white", size=12),
        cliponaxis=False,
        hovertext=hovertext,
        hovertemplate="%{hovertext}<extra></extra>",
        marker=dict(color="blue"),
    )
)

fig.update_xaxes(
    type="category",
    categoryorder="array",
    categoryarray=cat_labels,
    automargin=True,
)
fig.update_yaxes(automargin=True, range=[0, max_ratio * 1.10], tickformat=".2f")
fig.update_layout(
    height=480,
    margin=dict(l=20, r=20, t=10, b=40),
    xaxis_title="Task",
    yaxis_title="Ratio (F/E)",
    dragmode="pan",
    uniformtext_minsize=10,
    uniformtext_mode="show",
)

# Cursor "pointer" ------------> NO ME FUNCIONA =(
# st.markdown(
#     """
#     <style>
#     .js-plotly-plot .plotly .bar,
#     .js-plotly-plot .plotly .point,
#     .js-plotly-plot .plotly .bars path { cursor: pointer !important; }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# --- Render & selección ---
if _HAS_PLOTLY_EVENTS:
    selected = plotly_events(
        fig, click_event=True, hover_event=False, select_event=False,
        key="top10_plot_ratio", override_width="100%", override_height=480
    )
    selected_label = str(selected[0]["x"]) if selected else str(top10.iloc[0]["task_id"])
else:
    st.plotly_chart(fig, use_container_width=True)
    selected_label = st.selectbox(
        "Select a task from the Top 10 to see the detail:",
        options=cat_labels,
        index=0
    )

# Valor ORIGINAL de task_id (mismo dtype que en filtered_df)
selected_task_id = id_map.get(selected_label, selected_label)

# -------------------- Detalle de la task seleccionada --------------------
st.markdown(f"#### Detail of the selected: **{selected_label}**")

row_stat = top10[top10["task_id"] == selected_task_id]
if row_stat.empty:
    row_stat = stats_by_task[stats_by_task["task_id"].astype(str) == str(selected_task_id)]

F_top = int(row_stat["F"].iloc[0]) if not row_stat.empty else 0
E_top = int(row_stat["E"].iloc[0]) if not row_stat.empty else 0
ratio_top = float(row_stat["ratio"].iloc[0]) if not row_stat.empty else 0.0

task_block = filtered_df[filtered_df["task_id"] == selected_task_id].copy()

F_calc = task_block["finding_id"].nunique()
E_calc = task_block["__exec_id__"].nunique()
ratio_calc = (F_calc / E_calc) if E_calc else 0.0

st.write(
    f"**Overview** → Ratio = **{ratio_top:.2f}** (F/E) · "
    f"Findings (F): **{F_top}** · Executions (E): **{E_top}**"
)
if (F_top != F_calc) or (E_top != E_calc):
    st.warning(
        f"Note: recomputing on rows gives F={F_calc}, E={E_calc} (ratio={ratio_calc:.2f}). "
        f"Check if `issue_date` is empty in some rows; execution is defined as "
        f"`task_id + ac_registration_id + issue_date(day)`."
    )

# ===== Distribuciones de Location y Aircraft Model =====
c1, c2 = st.columns(2)

# --- Location ---
# --- Location ---
loc_col = "location" if "location" in task_block.columns else (
    "defect_location" if "defect_location" in task_block.columns else None
)
with c1:
    if loc_col:
        tmp = task_block.copy()
        tmp[loc_col] = tmp[loc_col].astype("string").fillna("no data")
        tmp.loc[tmp[loc_col].str.strip().eq(""), loc_col] = "no data"

        loc_df = (
            tmp.groupby(loc_col, dropna=False)["finding_id"]
               .nunique()
               .reset_index(name="#Findings")
        )
        total_for_pct = F_calc if F_calc > 0 else int(loc_df["#Findings"].sum())
        # calcula primero el % que muestras
        loc_df["% of Findings"] = (100 * loc_df["#Findings"] / max(total_for_pct, 1)).round(2)
        loc_df.rename(columns={loc_col: "Location"}, inplace=True)

        # ordena por % desc y, en empate, por Location asc
        loc_df = loc_df.sort_values(
            by=["% of Findings", "Location"],
            ascending=[False, True],
            kind="mergesort"  # estable
        )

        st.markdown("**Distribution by Location**")
        st.dataframe(
            loc_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Location": st.column_config.TextColumn("Location", width="large"),
                "#Findings": st.column_config.NumberColumn("#Findings", format="%d", width="small"),
                "% of Findings": st.column_config.NumberColumn("% of Findings", format="%.2f %%", width="small"),
            },
        )
    else:
        st.info("No 'location' nor 'defect_location' column found to compute percentages by location.")


# --- Aircraft Model ---
with c2:
    if "ac_model" in task_block.columns:
        mod_df = (
            task_block.groupby("ac_model", dropna=False)["finding_id"]
                      .nunique()
                      .reset_index(name="#Findings")
                      .sort_values("#Findings", ascending=False)
        )
        total_for_pct = F_calc if F_calc > 0 else int(mod_df["#Findings"].sum())
        mod_df["% of Findings"] = (100 * mod_df["#Findings"] / max(total_for_pct, 1)).round(2)
        mod_df.rename(columns={"ac_model": "Aircraft Model"}, inplace=True)

        st.markdown("**Distribution by Aircraft Model**")
        st.dataframe(
            mod_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Aircraft Model": st.column_config.TextColumn("Aircraft Model", width="large"),
                "#Findings": st.column_config.NumberColumn("#Findings", format="%d", width="small"),
                "% of Findings": st.column_config.NumberColumn("% of Findings", format="%.2f %%", width="small"),
            },
        )
    else:
        st.info("No 'ac_model' column found to compute percentages by aircraft model.")

# -------------------- Log de filas (detalle de findings) --------------------
st.markdown("**Records (findings) of the selected task**")

detail_df = task_block.copy()

# --- Date a mostrar: prioriza issue_date y si no, usa Date ---
if "issue_date" in detail_df.columns and detail_df["issue_date"].notna().any():
    detail_df["Date_out"] = pd.to_datetime(detail_df["issue_date"], errors="coerce")
elif "Date" in detail_df.columns:
    detail_df["Date_out"] = pd.to_datetime(detail_df["Date"], errors="coerce")
else:
    detail_df["Date_out"] = pd.NaT  # si no hay ninguna

# --- Location a mostrar: usa 'location', si no 'defect_location'; rellena vacíos con "no data" ---
loc_col = "location" if "location" in detail_df.columns else (
    "defect_location" if "defect_location" in detail_df.columns else None
)
if loc_col:
    detail_df["Location_out"] = detail_df[loc_col].astype("string").fillna("no data")
    detail_df.loc[detail_df["Location_out"].str.strip().eq(""), "Location_out"] = "no data"
else:
    detail_df["Location_out"] = "no data"

# --- Description Failure: elegimos la mejor columna disponible ---
# orden de preferencia (ajústalo si tu CSV usa otro nombre)
desc_col = next(
    (c for c in [
        "failure_description", "finding_description", "description",
        "description_failure", "defect_reason"
    ] if c in detail_df.columns),
    None
)
if desc_col:
    detail_df["Description Failure"] = detail_df[desc_col].astype("string")
else:
    detail_df["Description Failure"] = ""  # si no hay ninguna columna descriptiva

# --- Nombres que pidio Alex ---
display_cols_map = {
    "Date_out": "Date",                  
    "task_id": "Task",                  
    "ac_model": "Aircraft Type",        
    "ata_chapter_code": "ATA",           
    "ac_registration_id": "A/C",       
    "Location_out": "Location",          
    "Description Failure": "Description Failure",  
   
}

# selecciona solo las claves que existan en el DataFrame
sel_keys = [k for k in display_cols_map.keys() if k in detail_df.columns]
out_df = detail_df[sel_keys].rename(columns=display_cols_map)

# Orden: Date primero; si quieres otro orden, reordena aquí
desired_order = ["Date", "Task", "Aircraft Type", "ATA", "A/C", "Location", "Description Failure", "exec_id"]
out_df = out_df[[c for c in desired_order if c in out_df.columns]]

# Ordena por fecha si existe; si no, deja como está
if "Date" in out_df.columns:
    out_df = out_df.sort_values("Date")


st.dataframe(
    out_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD", width="small"),
        "Task": st.column_config.TextColumn("Task", width="medium"),
        "Aircraft Type": st.column_config.TextColumn("Aircraft Type", width="small"),
        "ATA": st.column_config.TextColumn("ATA", width="small"),
        "A/C": st.column_config.TextColumn("A/C", width="small"),
        "Location": st.column_config.TextColumn("Location", width="medium"),
        "Description Failure": st.column_config.TextColumn("Description Failure", width="large"),
        "exec_id": st.column_config.TextColumn("exec_id", width="medium"),
    },
)
