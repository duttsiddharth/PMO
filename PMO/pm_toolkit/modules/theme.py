"""Central visual theme: injected CSS, Plotly chart styling and summary cards.

Streamlit Community Cloud reads .streamlit/config.toml from the repo root, which
is not where this app lives when deployed from a subfolder — so we style at
runtime via injected CSS instead. That makes the look consistent no matter how
the app is deployed. All charts share one Plotly theme via ``style_fig``.
"""
import streamlit as st

# Professional, enterprise-leaning palette --------------------------------
PRIMARY = "#2563EB"
INK = "#0F172A"
MUTED = "#64748B"
LINE = "#E7ECF2"
BG = "#F5F7FA"
CARD = "#FFFFFF"

# Categorical colourway used across every chart.
PALETTE_SEQ = ["#2563EB", "#0EA5E9", "#14B8A6", "#8B5CF6",
               "#F59E0B", "#EF4444", "#10B981", "#6366F1"]

RAG = {"Green": "#16A34A", "Amber": "#F59E0B", "Red": "#DC2626"}

# Set by inject_css so charts/cards can adapt to the active theme.
_DARK = True


def inject_css(dark: bool = True):
    """Inject the global stylesheet. Dark is the default (matches Streamlit
    Cloud's base theme, so data grids stay consistent)."""
    global _DARK
    _DARK = dark
    if dark:
        bg, card, ink, muted, line = "#0B1220", "#111C33", "#E2E8F0", "#94A3B8", "#1E293B"
        bd, field = "#334155", "#0F1B33"
    else:
        bg, card, ink, muted, line = BG, CARD, INK, MUTED, LINE
        bd, field = "#CBD5E1", "#FFFFFF"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }}
    .stApp {{ background: {bg} !important; color: {ink} !important; }}
    .block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1300px; }}

    h1, h2, h3, h4 {{ color: {ink} !important; font-weight: 700 !important; letter-spacing: -.015em; }}
    p, span, label, li {{ color: {ink}; }}

    /* KPI metric cards */
    [data-testid="stMetric"] {{
        background: {card}; border: 1px solid {line}; border-radius: 14px;
        padding: 14px 18px 12px; box-shadow: 0 1px 2px rgba(16,24,40,.05);
    }}
    [data-testid="stMetric"] > div {{ overflow: visible; }}
    [data-testid="stMetricLabel"] p {{
        color: {muted} !important; font-weight: 600 !important; font-size: .72rem !important;
        text-transform: uppercase; letter-spacing: .045em;
    }}
    [data-testid="stMetricValue"] {{ color: {ink} !important; font-weight: 700 !important; font-size: 1.55rem !important; }}
    [data-testid="stMetricDelta"] {{ font-weight: 600 !important; }}

    /* Bordered containers become clean panels */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: {card}; border-radius: 16px; border: 1px solid {line} !important;
        box-shadow: 0 1px 2px rgba(16,24,40,.04);
    }}

    /* Sidebar — dark rail for an enterprise feel */
    [data-testid="stSidebar"] {{ background: #0B1220 !important; border-right: 1px solid #1E293B; }}
    [data-testid="stSidebar"] * {{ color: #CBD5E1 !important; }}
    [data-testid="stSidebar"] h2 {{ color: #FFFFFF !important; }}
    [data-testid="stSidebar"] [data-testid="stMetric"] {{ background: #111C33; border-color: #1E293B; }}

    /* Tabs */
    button[data-baseweb="tab"] {{ font-weight: 600; }}
    [data-baseweb="tab-highlight"] {{ background: {PRIMARY} !important; }}

    /* ---------- Interactive widgets: readable on any base theme ---------- */
    /* Buttons */
    .block-container .stButton > button {{
        background: {card} !important; color: {ink} !important;
        border: 1px solid {bd} !important; border-radius: 10px !important; font-weight: 600 !important;
    }}
    .block-container .stButton > button:hover {{ border-color: {PRIMARY} !important; color: {PRIMARY} !important; }}
    .block-container .stButton > button[kind="primary"],
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {{
        background: {PRIMARY} !important; color: #FFFFFF !important; border: none !important;
        border-radius: 10px !important; font-weight: 600 !important;
    }}
    .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {{ filter: brightness(1.06); color:#fff !important; }}

    /* File uploader */
    [data-testid="stFileUploaderDropzone"], [data-testid="stFileUploader"] section {{
        background: {field} !important; border: 1px dashed {bd} !important;
    }}
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small, [data-testid="stFileUploaderDropzoneInstructions"] * {{ color: {ink} !important; }}
    [data-testid="stFileUploader"] button {{ background: {card} !important; color: {ink} !important; border: 1px solid {bd} !important; }}

    /* Text / number / date inputs, textareas, select display box */
    .block-container [data-baseweb="input"], .block-container [data-baseweb="base-input"],
    .block-container [data-baseweb="select"] > div, .block-container textarea,
    .block-container .stTextInput input, .block-container .stNumberInput input,
    .block-container .stDateInput input {{
        background: {field} !important; color: {ink} !important; border-color: {bd} !important;
    }}
    .block-container [data-baseweb="select"] *, .block-container input, .block-container textarea {{ color: {ink} !important; }}

    /* Dropdown / calendar popovers (rendered at document root) */
    [data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"],
    [data-baseweb="popover"] ul, [data-baseweb="calendar"] {{ background: {card} !important; }}
    [data-baseweb="popover"] [role="option"], [data-baseweb="popover"] li, [role="option"] * {{ color: {ink} !important; }}

    /* Tabs */
    button[data-baseweb="tab"] {{ color: {muted} !important; font-weight: 600; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: {PRIMARY} !important; }}

    /* Expander */
    [data-testid="stExpander"] {{ border: 1px solid {line}; border-radius: 12px; overflow: hidden; }}
    [data-testid="stExpander"] summary {{ background: {card} !important; }}
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {{ color: {ink} !important; }}

    /* Main-area labels, radios, checkboxes, alerts */
    .block-container [data-testid="stWidgetLabel"] *,
    .block-container .stRadio label, .block-container .stCheckbox label {{ color: {ink} !important; }}
    .block-container [data-testid="stAlert"] * {{ color: {ink} !important; }}

    /* Data frames / editors */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {{ border: 1px solid {line}; border-radius: 12px; }}
    [data-testid="stDataFrame"] > div, [data-testid="stDataEditor"] > div {{
        --gdg-bg-cell: {field}; --gdg-bg-cell-medium: {bg}; --gdg-text-dark: {ink};
        --gdg-text-medium: {muted}; --gdg-text-light: {muted}; --gdg-bg-header: {card};
        --gdg-bg-header-hovered: {bg}; --gdg-bg-header-has-focus: {bg};
        --gdg-border-color: {line}; --gdg-text-header: {ink}; --gdg-accent-color: {PRIMARY};
    }}

    /* Section header block */
    .sd-header {{ margin: 0 0 1.1rem 0; }}
    .sd-header h2 {{ margin: 0; font-size: 1.7rem; line-height: 1.2; }}
    .sd-header .sd-sub {{ color: {muted}; font-size: .95rem; margin-top: .15rem; }}
    .sd-header .sd-bar {{ width: 46px; height: 4px; border-radius: 4px;
        background: linear-gradient(90deg, {PRIMARY}, #0EA5E9); margin-bottom: .6rem; }}

    /* Summary cards */
    .sd-card {{ border-radius: 14px; padding: 14px 16px; border: 1px solid {line};
        background: {card}; height: 100%; }}
    .sd-card .sd-card-title {{ font-weight: 700; font-size: .78rem; text-transform: uppercase;
        letter-spacing: .05em; margin-bottom: .4rem; display:flex; align-items:center; gap:.4rem; }}
    .sd-card .sd-card-body {{ color: {ink}; font-size: .92rem; line-height: 1.5; }}
    </style>
    """, unsafe_allow_html=True)


def header(title: str, subtitle: str = ""):
    """Styled section header with accent bar."""
    sub = f"<div class='sd-sub'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"<div class='sd-header'><div class='sd-bar'></div>"
        f"<h2>{title}</h2>{sub}</div>",
        unsafe_allow_html=True,
    )


_TONES = {
    "info": ("#2563EB", "#EFF4FF", "ℹ️"),
    "success": ("#16A34A", "#ECFDF3", "✅"),
    "warning": ("#B45309", "#FFF7ED", "⚠️"),
    "danger": ("#DC2626", "#FEF2F2", "🚨"),
    "neutral": ("#475569", "#F8FAFC", "📄"),
}

_TONES_DARK = {
    "info": ("#60A5FA", "#0F1E38", "ℹ️"),
    "success": ("#4ADE80", "#0C2A1C", "✅"),
    "warning": ("#FBBF24", "#2A1E0A", "⚠️"),
    "danger": ("#F87171", "#2A1414", "🚨"),
    "neutral": ("#94A3B8", "#111C33", "📄"),
}


def summary_card(title: str, body: str, tone: str = "info"):
    tones = _TONES_DARK if _DARK else _TONES
    color, bg, icon = tones.get(tone, tones["info"])
    border = color + "44" if _DARK else color + "22"
    st.markdown(
        f"<div class='sd-card' style='background:{bg};border-color:{border}'>"
        f"<div class='sd-card-title' style='color:{color}'>{icon} {title}</div>"
        f"<div class='sd-card-body'>{body}</div></div>",
        unsafe_allow_html=True,
    )


def rag_pill(health: str) -> str:
    color = RAG.get(health, "#64748B")
    return (f"<span style='background:{color};color:#fff;padding:3px 14px;"
            f"border-radius:999px;font-size:.8rem;font-weight:600'>{health}</span>")


def fg_color() -> str:
    """Foreground text colour for the active theme (inline chart text)."""
    return "#E2E8F0" if _DARK else INK


def style_fig(fig, height: int | None = None, show_legend: bool = True):
    """Apply the shared Plotly theme to any figure (adapts to dark/light)."""
    if _DARK:
        fc, grid, line_c, title_c, hover_bg = "#CBD5E1", "#1E293B", "#334155", "#F1F5F9", "#111C33"
    else:
        fc, grid, line_c, title_c, hover_bg = "#334155", "#EEF2F6", LINE, INK, "#FFFFFF"

    fig.update_layout(
        font=dict(family="Inter, system-ui, sans-serif", size=13, color=fc),
        title=dict(font=dict(size=15.5, color=title_c, family="Inter"),
                   x=0, xanchor="left", pad=dict(b=10)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=PALETTE_SEQ,
        margin=dict(t=52, b=10, l=10, r=10),
        hoverlabel=dict(bgcolor=hover_bg, font_size=12, font_family="Inter",
                        font_color=fc, bordercolor=line_c),
    )
    if show_legend:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                      xanchor="right", x=1, font=dict(size=11, color=fc),
                                      bgcolor="rgba(0,0,0,0)"))
    else:
        fig.update_layout(showlegend=False)
    fig.update_xaxes(showgrid=True, gridcolor=grid, zeroline=False,
                     linecolor=line_c, ticks="outside", tickcolor=line_c,
                     tickfont=dict(size=11, color=fc), title_font=dict(color=fc))
    fig.update_yaxes(showgrid=True, gridcolor=grid, zeroline=False,
                     linecolor=line_c, tickfont=dict(size=11, color=fc),
                     title_font=dict(color=fc))
    if height:
        fig.update_layout(height=height)
    return fig
