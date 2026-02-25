"""
Zomato AI Restaurant Recommendation Service — Streamlit Frontend
Clean centred UI. No sidebar. Compact aligned filter card + single-line CTA.
"""
from __future__ import annotations
import os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
except ImportError:
    pass

import streamlit as st

try:
    for k, v in st.secrets.items():
        if isinstance(v, str):
            os.environ.setdefault(k, v)
except Exception:
    pass

from zomato_ai.phase1.ingestion import DEFAULT_DB_URL, ingest_huggingface_dataset
from zomato_ai.phase2.models import UserPreference
from zomato_ai.phase2.repository import (
    create_engine_for_url,
    fetch_unique_cuisines,
    fetch_unique_locations,
)
from zomato_ai.phase5.pipeline import run_pipeline

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Zomato AI — Find Your Perfect Restaurant",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@700;800&display=swap');

html,body,[class*="css"]{ font-family:'Inter',sans-serif!important; }
.stApp{ background:#faf9f6!important; }

/* Hide chrome */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
#MainMenu,footer,header{ visibility:hidden!important; display:none!important; }

/* Tight centered container */
.block-container{
    padding-top:0!important;
    padding-bottom:48px!important;
    max-width:780px!important;
}

/* ────────────── NAV ────────────── */
.zai-nav{
    background:#fff; border-bottom:1px solid #e5e1d8;
    padding:13px 28px; margin-bottom:0;
    display:flex; align-items:center; justify-content:space-between;
    box-shadow:0 1px 8px rgba(0,0,0,.06);
}
.zai-logo{ font-family:'Playfair Display',serif; font-size:19px; font-weight:800; color:#c0392b; letter-spacing:-.3px; }
.zai-logo span{ color:#111; }
.zai-navlinks{ display:flex; gap:22px; list-style:none; }
.zai-navlinks a{ font-size:13px; font-weight:500; color:#6b6b6b; text-decoration:none; }
.zai-navlinks a.on{ color:#c0392b; font-weight:700; }

/* ────────────── HERO ────────────── */
.zai-hero{
    background:#fff; border-bottom:1px solid #e5e1d8;
    text-align:center; padding:40px 80px 34px;
    margin-bottom:26px;
}
.zai-badge{
    display:inline-flex; align-items:center; gap:5px;
    font-size:10px; font-weight:700; letter-spacing:1px; text-transform:uppercase;
    color:#c0392b; background:#fdf0ef;
    border:1px solid rgba(192,57,43,.2); border-radius:999px;
    padding:4px 12px; margin-bottom:12px;
}
.zai-dot{ width:5px; height:5px; background:#c0392b; border-radius:50%; display:inline-block; animation:pulse 2s ease-in-out infinite; }
@keyframes pulse{ 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.7)} }
.zai-h1{
    font-family:'Playfair Display',serif;
    font-size:clamp(24px,4vw,42px); font-weight:800; line-height:1.18;
    margin-bottom:10px; color:#111;
}
.zai-h1 .r{ color:#c0392b; }
.zai-sub{ font-size:14px; color:#6b6b6b; max-width:400px; margin:0 auto; line-height:1.65; }


/* ────────────── FILTER CARD ────────────── */
/* Target the stVerticalBlock that wraps our filter widgets */
div[data-testid="stVerticalBlock"].filter-wrap > div[data-testid="stVerticalBlock"]{
    background:#fff;
    border:1.5px solid #e5e1d8;
    border-radius:16px;
    padding:22px 24px 20px!important;
    box-shadow:0 4px 18px rgba(0,0,0,.07);
    margin-bottom:0;
}

/* Compact label sizing */
.stSelectbox > label,
.stMultiSelect > label,
.stNumberInput > label{
    font-size:11px!important; font-weight:600!important;
    color:#6b6b6b!important; letter-spacing:.3px!important;
    margin-bottom:2px!important; line-height:1.2!important;
}

/* Compact input height */
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div{
    min-height:36px!important; font-size:13px!important;
    border-radius:8px!important;
    background:#faf9f6!important; border-color:#e5e1d8!important;
}
.stNumberInput [data-baseweb="input"]{
    min-height:36px!important; font-size:13px!important;
    border-radius:8px!important;
    background:#faf9f6!important; border-color:#e5e1d8!important;
}

/* Tighten column gaps */
div[data-testid="column"]{
    padding-left:5px!important; padding-right:5px!important;
}
div[data-testid="column"]:first-child{ padding-left:0!important; }
div[data-testid="column"]:last-child { padding-right:0!important; }

/* Reduce spacing between form rows */
.stSelectbox,.stMultiSelect,.stNumberInput{ margin-bottom:0!important; }
div[data-testid="stHorizontalBlock"]{ gap:10px!important; margin-bottom:10px!important; }

/* ────────────── CTA BUTTON ────────────── */
/* Force single-line, centred pill button */
div[data-testid="stButton"]{
    display:flex!important;
    justify-content:center!important;
}
div[data-testid="stButton"] > button{
    padding:11px 52px!important;
    background:#111!important; color:#fff!important;
    border:none!important; border-radius:999px!important;
    font-family:'Inter',sans-serif!important;
    font-size:15px!important; font-weight:700!important;
    letter-spacing:.3px!important; white-space:nowrap!important;
    box-shadow:0 5px 18px rgba(0,0,0,.2)!important;
    transition:transform .18s,box-shadow .18s,background .18s!important;
    cursor:pointer!important; line-height:1.5!important;
    min-width:220px!important; width:auto!important;
}
div[data-testid="stButton"] > button:hover{
    background:#333!important; transform:translateY(-2px)!important;
    box-shadow:0 9px 26px rgba(0,0,0,.28)!important;
}

/* ────────────── RESULTS ────────────── */
.zai-summary{
    background:#fff; border-left:4px solid #111; border-radius:10px;
    padding:12px 16px; font-size:13px; line-height:1.7;
    color:#6b6b6b; margin-bottom:16px;
    box-shadow:0 2px 10px rgba(0,0,0,.05);
}
.zai-rh{ display:flex; align-items:center; gap:10px; margin:10px 0 14px; }
.zai-rh-t{ font-family:'Playfair Display',serif; font-size:20px; font-weight:800; color:#1a1a1a; }
.zai-rh-c{
    font-size:11px; font-weight:700;
    background:#f2f0eb; color:#6b6b6b;
    border:1px solid #e5e1d8; border-radius:999px; padding:3px 11px;
}
.zai-rc{
    background:#fff; border:1.5px solid #e5e1d8; border-radius:14px;
    padding:16px 18px; margin-bottom:14px;
    box-shadow:0 3px 12px rgba(0,0,0,.06);
    transition:transform .2s,border-color .2s,box-shadow .2s;
    animation:fadeUp .38s ease both;
}
.zai-rc:hover{ transform:translateY(-3px); border-color:#111; box-shadow:0 10px 26px rgba(0,0,0,.1); }
@keyframes fadeUp{ from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
.zai-rc-top{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; }
.zai-rc-name{ font-size:15px; font-weight:700; color:#1a1a1a; flex:1; margin-right:8px; line-height:1.3; }
.zai-rc-rat{
    display:inline-flex; align-items:center; gap:4px;
    font-size:12px; font-weight:700; color:#92400e;
    background:#fefce8; border:1px solid #fde68a;
    border-radius:7px; padding:3px 8px; white-space:nowrap; flex-shrink:0;
}
.zai-rc-meta{ display:flex; flex-wrap:wrap; gap:5px; margin-bottom:7px; }
.zai-rc-pill{
    font-size:11px; padding:2px 9px;
    border-radius:999px; border:1px solid #e5e1d8;
    color:#6b6b6b; background:#faf9f6;
}
.zai-rc-cuis{ font-size:11px; color:#aaa; margin-bottom:8px; }
.zai-rc-why{
    font-size:12px; line-height:1.55; color:#6b6b6b;
    padding-top:9px; border-top:1px solid #f0ece4;
}
.zai-rc-why strong{ color:#c0392b; }

/* ────────────── FOOTER ────────────── */
.zai-ft{
    text-align:center; font-size:11px; color:#bbb;
    border-top:1px solid #e5e1d8; padding:18px 0 26px; margin-top:40px;
}
.zai-ft a{ color:#111; text-decoration:none; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Cached helpers ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_engine():
    return create_engine_for_url(os.getenv("ZOMATO_DB_URL") or DEFAULT_DB_URL)

@st.cache_data(show_spinner=False, ttl=3600)
def get_locations():
    return fetch_unique_locations(get_engine())

@st.cache_data(show_spinner=False, ttl=3600)
def get_cuisines():
    return fetch_unique_cuisines(get_engine())

def _ensure_data():
    from sqlalchemy import text
    try:
        with get_engine().connect() as c:
            n = c.execute(text("SELECT COUNT(*) FROM restaurants")).scalar()
        if n == 0: raise ValueError
    except Exception:
        with st.spinner("⏳ First run: ingesting Zomato dataset…"):
            ingest_huggingface_dataset()
        st.cache_data.clear()

_ensure_data()

# ─────────────────────────────────────────────────────────────────────────────
# NAV
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="zai-nav">
  <div class="zai-logo">Zomato<span>AI</span></div>
  <ul class="zai-navlinks">
    <li><a href="#" class="on">Home</a></li>
    <li><a href="http://localhost:8000/docs" target="_blank">API Docs</a></li>
  </ul>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HERO  (emojis inline, not absolutely positioned → no overlap in narrow layout)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="zai-hero">
  <div class="zai-badge"><span class="zai-dot"></span>&nbsp;AI-Powered</div>
  <div class="zai-h1"><span class="r">Explore</span> the <span style="color:#111">World's</span> Cuisines!</div>
  <div class="zai-sub">Discover the perfect restaurant — filtered from thousands of options and ranked by AI, just for you.</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FILTER CARD  (card styled via CSS on the st.container)
# ─────────────────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(
        "<p style='font-size:10px;font-weight:700;text-transform:uppercase;"
        "letter-spacing:1px;color:#bbb;margin-bottom:12px;'>Your Preferences</p>",
        unsafe_allow_html=True,
    )
    # Row 1
    c1, c2 = st.columns([3, 2])
    with c1:
        loc_opts = [""] + get_locations()
        location = st.selectbox(
            "📍 Location",
            options=loc_opts,
            format_func=lambda x: "All locations" if x == "" else x,
        )
    with c2:
        min_rating = st.number_input(
            "⭐ Min Rating", min_value=0.0, max_value=5.0,
            value=None, step=0.1, placeholder="e.g. 4.0", format="%.1f",
        )

    # Row 2
    c3, c4, c5 = st.columns([2, 2, 3])
    with c3:
        min_price = st.number_input(
            "💰 Min Price (₹)", min_value=0, value=None, step=100, placeholder="e.g. 200",
        )
    with c4:
        max_price = st.number_input(
            "💰 Max Price (₹)", min_value=0, value=None, step=100, placeholder="e.g. 1500",
        )
    with c5:
        cuisines = st.multiselect("🍽️ Cuisines", options=get_cuisines(), placeholder="e.g. Italian")

# ─────────────────────────────────────────────────────────────────────────────
# CTA — pill button, perfectly centred, single line
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
# Centre the button via columns
_l, _m, _r = st.columns([1.8, 2.4, 1.8])
with _m:
    go = st.button("🔍  Get Recommendations", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────────────────
if go:
    prefs = UserPreference(
        location=location or None,
        min_rating=float(min_rating) if min_rating is not None else None,
        min_price=int(min_price) if min_price else None,
        max_price=int(max_price) if max_price else None,
        preferred_cuisines=cuisines or None,
        limit=5,
    )
    with st.spinner("🤖 AI is ranking the best restaurants for you…"):
        try:
            result = run_pipeline(engine=get_engine(), preferences=prefs)
        except RuntimeError as e:
            st.error(f"⚠️ Configuration error: {e}"); st.stop()
        except Exception as e:
            st.error(f"❌ Something went wrong: {e}"); st.stop()

    recs = result.recommendations
    if not recs:
        st.warning("No restaurants matched. Try broadening your filters.")
    else:
        st.markdown(f"""
<div class="zai-rh">
  <span class="zai-rh-t">Recommendations</span>
  <span class="zai-rh-c">{len(recs)} found</span>
</div>""", unsafe_allow_html=True)

        if result.summary:
            st.markdown(f'<div class="zai-summary">{result.summary}</div>', unsafe_allow_html=True)

        lc, rc = st.columns(2)
        for i, r in enumerate(recs):
            rating = f"⭐ {r.rating:.1f}" if r.rating is not None else "⭐ —"
            price  = f"₹{r.price_range:,}" if r.price_range is not None else "—"
            cuis   = f'<div class="zai-rc-cuis">{r.cuisines}</div>' if r.cuisines else ""
            card   = f"""
<div class="zai-rc" style="animation-delay:{i*0.06}s">
  <div class="zai-rc-top">
    <div class="zai-rc-name">{r.name}</div>
    <div class="zai-rc-rat">{rating}</div>
  </div>
  <div class="zai-rc-meta">
    <span class="zai-rc-pill">📍 {r.location or "—"}</span>
    <span class="zai-rc-pill">💰 {price}</span>
  </div>
  {cuis}
  <div class="zai-rc-why"><strong>Why this pick:</strong> {r.reason or "—"}</div>
</div>"""
            (lc if i % 2 == 0 else rc).markdown(card, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="zai-ft">
  Built with FastAPI + Groq LLM &middot;
  <a href="https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation" target="_blank">
    Zomato Dataset (HuggingFace)
  </a>
</div>
""", unsafe_allow_html=True)
