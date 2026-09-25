# app.py  — AI Talent Nexus Dashboard (live MySQL + AI engine)
# Tip: create .streamlit/config.toml with  [theme] base = "light"  for best results.
import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import warnings

from ai_engine import get_connection, ensure_schema, run_screening, fetch_pending, STRONG_THRESHOLD, MODERATE_THRESHOLD

warnings.filterwarnings("ignore")

st.set_page_config(page_title="AI Talent Nexus", layout="wide",
                   initial_sidebar_state="expanded")

# ---------------- COLORS ----------------
COLORS = {
    "text": "#101828", "text_muted": "#667085",
    "accent": "#4338CA", "accent_soft": "#EEF2FF",
}
INDIGO_SCALE = [[0.0, "#7DD3FC"], [0.5, "#6366F1"], [1.0, "#7C3AED"]]
STATUS_PALETTE = ["#3730A3", "#4338CA", "#6366F1", "#818CF8",
                  "#F59E0B", "#0EA5E9", "#94A3B8"]
CHART_LAYOUT_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Manrope, sans-serif", color=COLORS["text"], size=12),
    hoverlabel=dict(bgcolor="#312E81", font=dict(color="#FFFFFF", family="Manrope, sans-serif")),
)

def polish(fig):
    """Shared chart finish: soft dotted grid, quiet axes, rounded bars."""
    fig.update_xaxes(gridcolor="rgba(102,112,133,.16)", griddash="dot", zeroline=False, showline=False,
                     tickfont=dict(color=COLORS["text_muted"]),
                     title_font=dict(color=COLORS["text_muted"], size=12))
    fig.update_yaxes(showgrid=False, zeroline=False, showline=False,
                     tickfont=dict(color="#344054", size=12))
    try:
        fig.update_traces(marker_cornerradius=8, selector=dict(type="bar"))
    except Exception:
        pass
    return fig

_plotly_chart = st.plotly_chart
st.plotly_chart = lambda fig, **kw: _plotly_chart(polish(fig), **kw)   # every chart gets polish()

# ---------------- STYLES ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');

html, body, .stApp, [class*="css"] { font-family: 'Manrope', sans-serif; }

/* ================= SCROLL FIX ================= */
html, body, #root, .stApp, [data-testid="stMain"], .main { background: transparent !important; }
[data-testid="stAppViewContainer"] {
    position: relative !important; z-index: 1 !important; background: transparent !important;
    overflow-y: auto !important; overflow-x: hidden !important; height: 100vh !important;
}
[data-testid="stMain"] { overflow-y: visible !important; height: auto !important; }
.stApp { overflow-y: auto !important; height: auto !important; }
.block-container { overflow-y: visible !important; max-width: 1320px; padding-top: 2.2rem; animation: reveal .9s cubic-bezier(.2,.7,.2,1) both; }

/* ---------- animated background ---------- */
body::before {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background: linear-gradient(-45deg, #3730A3, #6D28D9, #2563EB, #0E7490);
  background-size: 300% 300%; animation: bgShift 24s ease-in-out infinite;
}
.stApp::before {
  content: ""; position: fixed; inset: -25%; z-index: 0; pointer-events: none;
  background: radial-gradient(600px circle at 18% 22%, rgba(255,255,255,.26), transparent 60%),
              radial-gradient(520px circle at 82% 28%, rgba(56,189,248,.34), transparent 60%),
              radial-gradient(700px circle at 52% 88%, rgba(244,114,182,.28), transparent 60%);
  animation: drift 30s ease-in-out infinite alternate;
}
.stApp::after {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: radial-gradient(rgba(255,255,255,.20) 1px, transparent 1px);
  background-size: 30px 30px;
  -webkit-mask-image: linear-gradient(to bottom, #000, transparent 85%);
          mask-image: linear-gradient(to bottom, #000, transparent 85%);
}
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, [data-testid="stDeployButton"], [data-testid="stAppDeployButton"], .stAppDeployButton { display: none !important; }

@keyframes bgShift { 0% {background-position: 0% 50%} 50% {background-position: 100% 50%} 100% {background-position: 0% 50%} }
@keyframes drift   { 0% {transform: translate3d(-3%,-2%,0) scale(1)} 100% {transform: translate3d(3%,3%,0) scale(1.12)} }
@keyframes reveal  { from {opacity: 0; transform: translateY(14px)} to {opacity: 1; transform: none} }
@keyframes shimmer { 0% {background-position: -200% 0} 100% {background-position: 200% 0} }
@keyframes pulse   { 0%,100% {box-shadow: 0 0 0 0 rgba(74,222,128,.6)} 50% {box-shadow: 0 0 0 7px rgba(74,222,128,0)} }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; } }

/* ---------- header ---------- */
.top-accent { height: 3px; border-radius: 3px; margin-bottom: 26px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.95), transparent);
  background-size: 200% 100%; animation: shimmer 5s linear infinite; }
.app-title { 
  font-family: 'Sora', sans-serif; font-weight: 800; font-size: 2.7rem;
  letter-spacing: -0.03em; color: #FFFFFF !important; margin-bottom: 4px;
  text-shadow: 0 6px 30px rgba(15,23,42,.25); display: inline-block;
  user-select: none; /* Prevents selection bug */
}
.app-subtitle { color: rgba(255,255,255,.82); font-size: 1rem; margin-bottom: 14px; }
.live { display: inline-flex; align-items: center; gap: 8px; padding: 5px 13px; margin-bottom: 26px;
  border-radius: 99px; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.32);
  color: #FFFFFF; font-size: .78rem; font-weight: 600; backdrop-filter: blur(8px); }
.live i { width: 7px; height: 7px; border-radius: 50%; background: #4ADE80; animation: pulse 2s infinite; }

/* ---------- KPI CARDS (BUG FIXED) ---------- */
.kpi-card {
  display: flex; flex-direction: column; justify-content: center;
  height: 100%; min-height: 130px;
  background: rgba(255,255,255,.88); border: 1px solid rgba(255,255,255,.75);
  border-radius: 18px; padding: 20px 22px; margin-bottom: 10px; backdrop-filter: blur(16px);
  box-shadow: 0 10px 34px rgba(30,27,75,.22);
  position: relative; overflow: hidden; transition: transform .3s, box-shadow .3s;
  user-select: none; /* Prevents selection bug */
}
.kpi-hero { background: linear-gradient(135deg, #FFFFFF 0%, #E0E7FF 100%); }
.kpi-label { font-size: .84rem; font-weight: 600; color: #667085; margin-bottom: 6px; }
.kpi-hero .kpi-label { color: #4338CA; }
.kpi-value { 
  font-family: 'Sora', sans-serif; font-weight: 700; font-size: 2rem; 
  color: #312E81 !important; /* Solid color to prevent invisible text */
  line-height: 1.15; display: inline-block; margin-bottom: 4px; 
}
.kpi-note { font-size: .78rem; color: #98A2B3; margin-top: 6px; }

/* ---------- glass panels ---------- */
[class*="st-key-panel"] { background: rgba(255,255,255,.90) !important; backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,.8) !important; border-radius: 24px !important;
  padding: 1.2rem 1.3rem !important; box-shadow: 0 16px 48px rgba(30,27,75,.25), inset 0 3px 0 #6366F1;
  overflow: visible !important; }
.section-header { font-family: 'Sora', sans-serif; font-weight: 600; font-size: 1rem; color: #101828; margin: 2px 0 12px 0; }
.section-header::before { content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 9px;
  border-radius: 50%; background: linear-gradient(135deg, #4338CA, #38BDF8); }
[class*="st-key-panel"] .stDownloadButton button { background: linear-gradient(135deg, #4338CA, #6366F1) !important;
  color: #FFFFFF !important; border: none !important; }

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 6px; padding: 6px; width: fit-content; border-radius: 16px;
  background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.28); backdrop-filter: blur(10px); }
.stTabs [data-baseweb="tab"] { height: 40px; padding: 0 22px; border-radius: 11px; font-weight: 600;
  color: rgba(255,255,255,.88); transition: background .25s, color .25s; }
.stTabs [data-baseweb="tab"] p { color: inherit !important; }
.stTabs [data-baseweb="tab"]:hover { background: rgba(255,255,255,.18); }
.stTabs [aria-selected="true"] { background: #FFFFFF !important; color: #3730A3 !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] { background: rgba(255,255,255,.12) !important; backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255,255,255,.26); }
section[data-testid="stSidebar"] > div { background: transparent !important; }
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
section[data-testid="stSidebar"] [data-testid="stSliderThumbValue"],
section[data-testid="stSidebar"] [data-testid="stTickBarMin"],
section[data-testid="stSidebar"] [data-testid="stTickBarMax"] { color: #FFFFFF !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.25); }
div[data-baseweb="select"] > div { background: rgba(255,255,255,.96) !important; border-radius: 12px !important; border: none !important; }
[data-baseweb="slider"] [role="slider"] { background: #FFFFFF !important; border: 3px solid #A5B4FC !important; }

/* ---------- buttons ---------- */
.stButton > button, .stDownloadButton > button { border-radius: 12px; font-weight: 600; color: #FFFFFF;
  background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.36);
  transition: transform .25s, background .25s, box-shadow .25s; }
.stButton > button p, .stDownloadButton > button p { color: inherit !important; }
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-2px);
  background: rgba(255,255,255,.26); box-shadow: 0 10px 26px rgba(15,23,42,.25); }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
  background: #FFFFFF; color: #3730A3; border: none; }
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover { background: #EEF2FF; }

/* ---------- refinements ---------- */
.kpi-card::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 5px; background: var(--a); }
.kpi-card:hover { transform: translateY(-4px); box-shadow: 0 20px 46px rgba(30,27,75,.32); }
[class*="st-key-panel"] [class*="st-key-panel"] { background: none !important; border: none !important;
  box-shadow: none !important; padding: 0 !important; backdrop-filter: none !important; border-radius: 0 !important; }
.tbl-wrap { max-height: 470px; overflow: auto; border-radius: 16px; border: 1px solid #E4E7EC; background: #FFFFFF; }
.tbl { width: 100%; border-collapse: collapse; font-size: .86rem; }
.tbl th { position: sticky; top: 0; z-index: 1; background: #F5F3FF; color: #4338CA; font-weight: 700;
  text-align: left; padding: 11px 14px; white-space: nowrap; }
.tbl td { padding: 10px 14px; border-top: 1px solid #F2F4F7; color: #101828; }
.tbl tr:hover td { background: #F8F7FF; }
.pill { padding: 3px 10px; border-radius: 99px; font-weight: 700; font-size: .76rem; white-space: nowrap; }
.bar { height: 7px; border-radius: 9px; background: #EEF2FF; min-width: 70px; }
.bar b { display: block; height: 100%; border-radius: 9px; background: linear-gradient(90deg, #38BDF8, #6366F1, #7C3AED); }
@keyframes growX { from { transform: scaleX(0); } }
@keyframes growY { from { transform: scaleY(0); } }
[class*="st-key-panel"] .barlayer .point path { transform-box: fill-box; transform-origin: 0 50%;
  animation: growX .9s cubic-bezier(.2,.7,.2,1) both; }
.st-key-panel_hist .barlayer .point path { transform-origin: 50% 100%; animation-name: growY; }

/* ---------- alerts ---------- */
[data-testid="stAlert"] { background: rgba(255,255,255,.92); border-radius: 14px; border: none; box-shadow: 0 8px 26px rgba(30,27,75,.18); }
[data-testid="stAlert"] * { color: #101828 !important; }
</style>
""", unsafe_allow_html=True)


def kpi_card(label, value, note="", accent="#4338CA", hero=False):
    cls = "kpi-card kpi-hero" if hero else "kpi-card"
    st.markdown(f"""<div class="{cls}" style="--a:{accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-note">{note}</div></div>""",
        unsafe_allow_html=True)


def band(score):
    if score is None: return "Unscored"
    if score >= STRONG_THRESHOLD: return "Strong match"
    if score >= MODERATE_THRESHOLD: return "Moderate match"
    return "Low match"


FIT_STYLE = {
    "Strong match":   ("#DCFCE7", "#15803D"),
    "Moderate match": ("#FEF3C7", "#B45309"),
    "Low match":      ("#FEE4E2", "#B42318"),
    "Unscored":       ("#F2F4F7", "#475467"),
}
def fit_style(v):
    bg, fg = FIT_STYLE.get(v, ("#FFFFFF", "#101828"))
    return f"background-color:{bg}; color:{fg}; font-weight:600; border-radius:6px;"


# ---------------- DB ----------------
@st.cache_resource
def _conn():
    c = get_connection()
    ensure_schema(c)
    return c

try:
    conn = _conn()
except Exception as e:
    st.error(f"DB connection failed: {e}")
    st.stop()


@st.cache_data(ttl=15, show_spinner=False)
def load_data():
    q = """
        SELECT a.AppID,
               j.Title AS Job_Role,
               c.FullName AS Candidate,
               a.AI_Match_Score,
               a.Semantic_Score,
               a.Skill_Score,
               a.Matched_Skills,
               a.Missing_Skills,
               a.Recommendation,
               a.Status
        FROM Applications a
        JOIN Candidates   c ON a.CandidateID = c.CandidateID
        JOIN Job_Postings j ON a.JobID       = j.JobID
        ORDER BY a.AI_Match_Score DESC
    """
    return pd.read_sql(q, conn)


def refresh():
    load_data.clear()


# ---------------- SIDEBAR ----------------
st.sidebar.markdown("### Screening")
st.sidebar.caption("Score pending applications in real time")

if st.sidebar.button("Run AI Screening", use_container_width=True, type="primary"):
    pending = fetch_pending(conn)
    if pending.empty:
        st.sidebar.info("No pending applications (Status='Applied').")
    else:
        prog = st.sidebar.progress(0.0, text="Scoring…")
        log  = st.sidebar.empty()
        def cb(done, total, name):
            prog.progress(done/total, text=f"{done}/{total}: {name}")
        stats = run_screening(conn, on_progress=cb)
        prog.empty(); log.success(f"Done: {stats['processed']} scored")
        refresh()
        st.rerun()

if st.sidebar.button("Re-score all (overwrite)", use_container_width=True):
    cur = conn.cursor()
    cur.execute("UPDATE Applications SET Status='Applied'")
    conn.commit(); cur.close()
    refresh()
    st.sidebar.success("Reset to 'Applied'. Now click Run AI Screening.")
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### Filters")

try:
    df = load_data()
except Exception as e:
    st.error(f"Query failed: {e}")
    st.stop()

if df.empty:
    st.markdown('<div class="top-accent"></div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">AI Talent Nexus</div>', unsafe_allow_html=True)
    st.warning("No data in Applications table. Add some rows first.")
    st.stop()

job_opts = ["All roles"] + sorted(df["Job_Role"].dropna().unique().tolist())
sel_job  = st.sidebar.selectbox("Job role", job_opts)
min_score = st.sidebar.slider("Min match score", 0, 100, 0, format="%d%%")
status_opts = ["All"] + sorted(df["Status"].dropna().unique().tolist())
sel_status = st.sidebar.selectbox("Status", status_opts)

f = df.copy()
if sel_job != "All roles": f = f[f["Job_Role"] == sel_job]
if sel_status != "All":    f = f[f["Status"] == sel_status]
f = f[f["AI_Match_Score"].fillna(0) >= min_score]

st.sidebar.caption(f"{len(f)} of {len(df)} applicants")


# ---------------- HEADER ----------------
st.markdown('<div class="top-accent"></div>', unsafe_allow_html=True)
st.markdown('<div class="app-title">Talent Pipeline</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-subtitle">{len(df)} applications across {df["Job_Role"].nunique()} open roles, ranked by AI match score.</div>',
            unsafe_allow_html=True)
st.markdown('<div class="live"><i></i>Live data</div>', unsafe_allow_html=True)

# ---------------- KPI ROW ----------------
has = not f.empty
scored = f["AI_Match_Score"].dropna()
k1, k2, k3, k4 = st.columns(4)
with k1: kpi_card("Total applicants", str(len(f)), "In the current view", "#4338CA", hero=True)
with k2: kpi_card("Average match",
                  f"{scored.mean():.1f}%" if len(scored) else "—", f"Across {len(scored)} scored", "#7C3AED")
with k3: kpi_card("Top score",
                  f"{scored.max():.1f}%" if len(scored) else "—", "Best single match", "#0EA5E9")
with k4: kpi_card("Active roles", str(df["Job_Role"].nunique()), "Open requisitions", "#F59E0B")

st.write("")

if not has:
    st.info("No candidates match these filters. Try lowering the score threshold.")
    st.stop()

f["Fit"] = f["AI_Match_Score"].apply(band)

tab1, tab2, tab3 = st.tabs(["Candidates", "Pipeline insights", "Skill gap"])

# ================= TAB 1 — Candidates =================
with tab1:
    c1, c2 = st.columns([1.3, 1])

    with c1.container(border=True, key="panel_dist"):
        st.markdown('<div class="section-header">Match distribution</div>',
                    unsafe_allow_html=True)
        p = f.dropna(subset=["AI_Match_Score"]).sort_values("AI_Match_Score").tail(15).copy()
        p["Label"] = p["Candidate"] + " · " + p["Job_Role"]
        if p.empty:
            st.info("No scored applicants yet. Click **Run AI Screening**.")
        else:
            fig = px.bar(p, x="AI_Match_Score", y="Label", orientation="h",
                         color="AI_Match_Score", color_continuous_scale=INDIGO_SCALE,
                         text="AI_Match_Score")
            fig.update_traces(texttemplate="%{text:.1f}%",
                              textposition="outside", cliponaxis=False,
                              textfont=dict(size=11, color=COLORS["text_muted"]),
                              hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>")
            fig.update_layout(**CHART_LAYOUT_BASE, coloraxis_showscale=False,
                              height=max(360, 40*len(p)), bargap=0.35,
                              margin=dict(t=10,l=0,r=40,b=0),
                              xaxis=dict(title="Match score (%)",
                                         range=[0, max(100, p["AI_Match_Score"].max()*1.15)]),
                              yaxis=dict(title="", automargin=True))
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})

    with c2.container(border=True, key="panel_short"):
        st.markdown('<div class="section-header">Candidate shortlist</div>',
                    unsafe_allow_html=True)
        tbl = f[["Candidate","Job_Role","AI_Match_Score","Fit",
                 "Recommendation","Status"]].rename(
                 columns={"Job_Role":"Role"})
        from html import escape as esc
        cell = lambda x: "" if pd.isna(x) else esc(str(x))
        rows = ""
        for r in tbl.itertuples(index=False):
            bg, fg = FIT_STYLE.get(r.Fit, ("#F2F4F7", "#475467"))
            sc_html = "—" if pd.isna(r.AI_Match_Score) else (
                f'<div style="display:flex;align-items:center;gap:10px"><div class="bar" style="flex:1">'
                f'<b style="width:{r.AI_Match_Score:.1f}%"></b></div><span>{r.AI_Match_Score:.1f}%</span></div>')
            rows += (f'<tr><td><b>{cell(r.Candidate)}</b></td><td>{cell(r.Role)}</td>'
                     f'<td style="min-width:150px">{sc_html}</td>'
                     f'<td><span class="pill" style="background:{bg};color:{fg}">{r.Fit}</span></td>'
                     f'<td>{cell(r.Recommendation)}</td><td>{cell(r.Status)}</td></tr>')
        st.markdown('<div class="tbl-wrap"><table class="tbl"><thead><tr><th>Candidate</th><th>Role</th>'
                    '<th>Match</th><th>Fit</th><th>Recommendation</th><th>Status</th></tr></thead><tbody>'
                    + rows + '</tbody></table></div>', unsafe_allow_html=True)
        st.download_button("Download CSV",
                           tbl.to_csv(index=False).encode("utf-8"),
                           file_name="shortlist.csv", mime="text/csv")

# ================= TAB 2 — Pipeline =================
with tab2:
    r1, r2 = st.columns(2)

    with r1.container(border=True, key="panel_status"):
        st.markdown('<div class="section-header">Applications by status</div>',
                    unsafe_allow_html=True)
        sc = f["Status"].value_counts().reset_index()
        sc.columns = ["Status","Count"]
        fig = px.pie(sc, names="Status", values="Count", hole=0.62,
                     color_discrete_sequence=STATUS_PALETTE)
        fig.update_traces(textinfo="label+percent",
                          textfont=dict(size=11, color=COLORS["text"]),
                          marker=dict(line=dict(color="#FFF", width=2)),
                          hovertemplate="<b>%{label}</b><br>%{value}<extra></extra>")
        fig.update_layout(**CHART_LAYOUT_BASE, showlegend=False,
                          margin=dict(t=10,l=10,r=10,b=10), height=320,
                          annotations=[dict(text=f"<b>{int(sc['Count'].sum())}</b><br>Total",
                                            showarrow=False,
                                            font=dict(size=18, color=COLORS["text"]))])
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})

    with r2.container(border=True, key="panel_req"):
        st.markdown('<div class="section-header">Applicants by requisition</div>',
                    unsafe_allow_html=True)
        rc = f.groupby("Job_Role").size().reset_index(name="Applicants")\
              .sort_values("Applicants")
        fig = px.bar(rc, x="Applicants", y="Job_Role", orientation="h",
                     text="Applicants", color_discrete_sequence=[COLORS["accent"]])
        fig.update_traces(textposition="outside",
                          textfont=dict(size=12, color=COLORS["text_muted"]))
        fig.update_layout(**CHART_LAYOUT_BASE, margin=dict(t=10,l=0,r=30,b=0),
                          height=320, bargap=0.35,
                          xaxis=dict(title="Applicants"),
                          yaxis=dict(title="", automargin=True))
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False})

    st.write("")
    with st.container(border=True, key="panel_hist"):
        st.markdown('<div class="section-header">Score distribution</div>',
                    unsafe_allow_html=True)
        sd = f.dropna(subset=["AI_Match_Score"])
        if not sd.empty:
            fig = px.histogram(sd, x="AI_Match_Score",
                               nbins=min(14, max(5, sd["AI_Match_Score"].nunique())),
                               color_discrete_sequence=[COLORS["accent"]])
            fig.add_vline(x=sd["AI_Match_Score"].mean(), line_dash="dash",
                          line_color=COLORS["text_muted"],
                          annotation_text=f"Avg {sd['AI_Match_Score'].mean():.1f}%",
                          annotation_position="top right")
            fig.update_layout(**CHART_LAYOUT_BASE, height=300, bargap=0.08,
                              margin=dict(t=30,l=0,r=10,b=0),
                              xaxis=dict(title="Match score (%)"),
                              yaxis=dict(title="Applicants"))
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})

# ================= TAB 3 — Skill gap =================
with tab3:
    with st.container(border=True, key="panel_skills"):
        st.markdown('<div class="section-header">Most common missing skills</div>',
                    unsafe_allow_html=True)
        misses = []
        for s in f["Missing_Skills"].dropna():
            misses += [x.strip() for x in str(s).split(",") if x.strip()]
        if misses:
            mc = pd.Series(misses).value_counts().head(15).reset_index()
            mc.columns = ["Skill","Missing in N candidates"]
            fig = px.bar(mc, x="Missing in N candidates", y="Skill", orientation="h",
                         text="Missing in N candidates", color="Missing in N candidates",
                         color_continuous_scale=[[0, "#FDBA74"], [1, "#E11D48"]])
            fig.update_traces(textposition="outside")
            fig.update_layout(**CHART_LAYOUT_BASE, coloraxis_showscale=False, bargap=0.35,
                              height=max(300, 34*len(mc)),
                              margin=dict(t=10,l=0,r=40,b=0),
                              yaxis=dict(title="", automargin=True))
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No missing-skill data yet. Run AI Screening first.")