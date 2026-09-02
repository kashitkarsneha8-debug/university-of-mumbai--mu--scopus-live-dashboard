"""
styles.py
ICARE Glassmorphism Design System and Dark/Light Theme Engine
for University of Mumbai (MU) Live Scopus Intelligence Dashboard.

Features:
- get_custom_css(theme='dark'): Comprehensive CSS design tokens, typography, glassmorphism,
  custom component styles, and responsiveness for Dark and Light themes.
- render_icare_topbar(theme): Top navigation bar with ICARE + MU logos, glowing cyan badge,
  and official university credentials.
- render_icare_hero(total_pubs, total_cites, theme): Hero banner with institutional badges,
  glowing titles, and dual-metric rank box.
- render_kpi_card(title, value, subtitle, icon, badge, trend, theme): Reusable glassmorphic KPI card.
- render_section_header(title, subtitle, badge_text, icon, theme): Themed section header.
"""

import os
import base64
from typing import Optional
import streamlit as st


def get_base64_image(image_path: str) -> str:
    """
    Read an image file from disk and convert it to a base64 data URI string.
    Returns empty string if file is missing.
    """
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_f:
                b64 = base64.b64encode(img_f.read()).decode("utf-8")
                ext = image_path.lower().split(".")[-1]
                mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
                return f"data:{mime};base64,{b64}"
        except Exception:
            return ""
    return ""


# Preload logos as Base64 strings for fast and reliable rendering
ICARE_LOGO_B64 = get_base64_image("icare_logo.jpeg")
MU_LOGO_B64 = get_base64_image("mumbai_university_logo.jpg")


def get_custom_css(theme: str = "dark") -> str:
    """
    Generate comprehensive CSS stylesheet with ICARE Glassmorphism design tokens.
    
    Themes:
        dark: Background #070D1E, Cards #0E172A, Borders 1px solid rgba(255,255,255,0.08),
              Primary Blue #0284C7, Gold #F59E0B.
        light: Background #F8FAFC, Cards #FFFFFF, Text #0F172A, Primary Blue #0284C7.
    """
    is_dark = theme.lower() == "dark"

    # Color Palette Tokens
    bg_color = "#070D1E" if is_dark else "#F8FAFC"
    card_bg = "rgba(14, 23, 42, 0.78)" if is_dark else "rgba(255, 255, 255, 0.90)"
    card_solid = "#0E172A" if is_dark else "#FFFFFF"
    text_primary = "#F8FAFC" if is_dark else "#0F172A"
    text_secondary = "#94A3B8" if is_dark else "#475569"
    text_muted = "#64748B" if is_dark else "#64748B"
    border_color = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.08)"
    border_hover = "rgba(2, 132, 199, 0.45)" if is_dark else "rgba(2, 132, 199, 0.35)"
    primary_blue = "#0284C7"
    cyan_glow = "#38BDF8"
    gold_accent = "#F59E0B"
    card_shadow = "0 8px 32px 0 rgba(0, 0, 0, 0.37)" if is_dark else "0 8px 30px 0 rgba(0, 0, 0, 0.06)"
    hero_grad = (
        "linear-gradient(135deg, rgba(14, 23, 42, 0.92) 0%, rgba(7, 13, 30, 0.88) 100%)"
        if is_dark else
        "linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(241, 245, 249, 0.90) 100%)"
    )

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {{
        --bg-color: {bg_color};
        --card-bg: {card_bg};
        --card-solid: {card_solid};
        --text-primary: {text_primary};
        --text-secondary: {text_secondary};
        --text-muted: {text_muted};
        --border-color: {border_color};
        --border-hover: {border_hover};
        --primary-blue: {primary_blue};
        --cyan-glow: {cyan_glow};
        --gold-accent: {gold_accent};
        --card-shadow: {card_shadow};
    }}

    /* Global Streamlit Body & App Overrides */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-color) !important;
        color: var(--text-primary) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        scroll-behavior: smooth;
    }}

    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: {"rgba(10, 17, 36, 0.95)" if is_dark else "rgba(248, 250, 252, 0.95)"} !important;
        border-right: 1px solid var(--border-color) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
    }}

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: var(--text-primary) !important;
    }}

    /* Main container padding */
    .main .block-container {{
        padding-top: 1.2rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1380px !important;
    }}

    /* Glassmorphic Cards */
    .glass-card {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 22px;
        box-shadow: var(--card-shadow);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.28s ease, box-shadow 0.28s ease;
    }}

    .glass-card:hover {{
        border-color: var(--border-hover);
        transform: translateY(-3px);
        box-shadow: 0 12px 36px 0 {"rgba(2, 132, 199, 0.22)" if is_dark else "rgba(2, 132, 199, 0.12)"};
    }}

    /* Executive KPI Grid & Cards */
    .kpi-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin: 20px 0;
    }}

    .kpi-card {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: var(--card-shadow);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
        transition: all 0.28s ease;
    }}

    .kpi-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-blue), var(--cyan-glow));
        opacity: 0.85;
    }}

    .kpi-card:hover {{
        border-color: var(--cyan-glow);
        transform: translateY(-4px);
        box-shadow: 0 10px 25px {"rgba(2, 132, 199, 0.25)" if is_dark else "rgba(2, 132, 199, 0.15)"};
    }}

    .kpi-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }}

    .kpi-title {{
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-secondary);
    }}

    .kpi-icon {{
        font-size: 1.15rem;
        opacity: 0.9;
    }}

    .kpi-value {{
        font-size: 1.95rem;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1.15;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}

    .kpi-subtitle {{
        font-size: 0.78rem;
        color: var(--text-muted);
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
    }}

    .kpi-badge {{
        font-size: 0.70rem;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 600;
        display: inline-block;
    }}

    .badge-cyan {{
        background: {"rgba(56, 189, 248, 0.15)" if is_dark else "rgba(2, 132, 199, 0.12)"};
        color: {"#38BDF8" if is_dark else "#0284C7"};
        border: 1px solid {"rgba(56, 189, 248, 0.35)" if is_dark else "rgba(2, 132, 199, 0.3)"};
    }}

    .badge-gold {{
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }}

    .badge-purple {{
        background: rgba(168, 85, 247, 0.15);
        color: #C084FC;
        border: 1px solid rgba(168, 85, 247, 0.35);
    }}

    /* Modern Tabs Styling */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 6px !important;
        gap: 8px !important;
        backdrop-filter: blur(12px) !important;
    }}

    [data-testid="stTabs"] [data-baseweb="tab"] {{
        border-radius: 8px !important;
        padding: 8px 18px !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        border: none !important;
        transition: all 0.25s ease !important;
    }}

    [data-testid="stTabs"] [aria-selected="true"] {{
        background: var(--primary-blue) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.45) !important;
    }}

    /* Streamlit Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, var(--primary-blue) 0%, #0369A1 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 10px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35) !important;
        transition: all 0.25s ease !important;
    }}

    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(2, 132, 199, 0.5) !important;
        border-color: var(--cyan-glow) !important;
    }}

    /* Secondary outline button */
    .btn-secondary > button {{
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: none !important;
    }}

    /* Dataframe & Table Modern Polish */
    [data-testid="stDataFrame"], [data-testid="stTable"] {{
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }}

    /* Sleek Scrollbars */
    ::-webkit-scrollbar {{
        width: 7px;
        height: 7px;
    }}

    ::-webkit-scrollbar-track {{
        background: var(--bg-color);
    }}

    ::-webkit-scrollbar-thumb {{
        background: {"rgba(255, 255, 255, 0.18)" if is_dark else "rgba(0, 0, 0, 0.15)"};
        border-radius: 9999px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: var(--primary-blue);
    }}

    /* Pulsing Status Dot */
    .pulse-dot {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse-animation 2s infinite;
        margin-right: 6px;
    }}

    @keyframes pulse-animation {{
        0% {{
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        }}
        70% {{
            box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
        }}
        100% {{
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
        }}
    }}

    /* Responsive Adjustments */
    @media (max-width: 768px) {{
        .hero-banner {{
            flex-direction: column !important;
            gap: 20px !important;
        }}
        .hero-rank-box {{
            width: 100% !important;
        }}
        .topbar-container {{
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 12px !important;
        }}
    }}
    </style>
    """
    return css


def clean_html(html_str: str) -> str:
    """
    Strips HTML comments and leading whitespace from every line so that
    Streamlit's Python-Markdown parser never converts indented lines into <pre><code> blocks.
    """
    import re
    cleaned = re.sub(r'<!--.*?-->', '', html_str, flags=re.DOTALL)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    return " ".join(lines)


def render_icare_topbar(theme: str = "dark") -> str:
    """
    Render ICARE top navigation bar:
    - ICARE logo + Mumbai University logo
    - PORTAL INTELLIGENCE cyan badge with glowing dot
    - University of Mumbai
    - IR-O-U-0318 • Mumbai, Maharashtra in bold #0284C7
    """
    is_dark = theme.lower() == "dark"
    border_col = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.08)"
    bg_bar = "rgba(14, 23, 42, 0.85)" if is_dark else "rgba(255, 255, 255, 0.92)"
    text_main = "#F8FAFC" if is_dark else "#0F172A"

    icare_img_tag = (
        f'<img src="{ICARE_LOGO_B64}" alt="ICARE Logo" style="height: 38px; border-radius: 6px; object-fit: contain;" />'
        if ICARE_LOGO_B64 else '<span style="font-weight: 800; font-size: 1.3rem; color: #0284C7;">ICARE</span>'
    )

    mu_img_tag = (
        f'<img src="{MU_LOGO_B64}" alt="MU Logo" style="height: 42px; border-radius: 6px; object-fit: contain; margin-left: 8px;" />'
        if MU_LOGO_B64 else ''
    )

    html = f"""
    <div class="topbar-container" style="
        background: {bg_bar};
        border-bottom: 1px solid {border_col};
        border-radius: 14px;
        padding: 12px 24px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
    ">
        <!-- Left Side: Logos & Portal Intelligence Badge -->
        <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 8px;">
                {icare_img_tag}
                {mu_img_tag}
            </div>
            <div style="height: 28px; width: 1px; background: {border_col}; margin: 0 4px;"></div>
            <span style="
                background: {"rgba(56, 189, 248, 0.14)" if is_dark else "rgba(2, 132, 199, 0.10)"};
                color: {"#38BDF8" if is_dark else "#0284C7"};
                border: 1px solid {"rgba(56, 189, 248, 0.35)" if is_dark else "rgba(2, 132, 199, 0.25)"};
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                display: inline-flex;
                align-items: center;
                box-shadow: 0 0 12px {"rgba(56, 189, 248, 0.25)" if is_dark else "rgba(2, 132, 199, 0.15)"};
            ">
                <span class="pulse-dot"></span>
                PORTAL INTELLIGENCE
            </span>
        </div>

        <!-- Right Side: University of Mumbai & NIRF Badge -->
        <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end;">
            <div style="font-size: 1.05rem; font-weight: 700; color: {text_main}; letter-spacing: -0.01em;">
                University of Mumbai
            </div>
            <div style="font-size: 0.82rem; font-weight: 700; color: #0284C7; letter-spacing: 0.02em;">
                IR-O-U-0318 &bull; Mumbai, Maharashtra
            </div>
        </div>
    </div>
    """
    return clean_html(html)


def render_icare_hero(total_pubs: int, total_cites: int, theme: str = "dark") -> str:
    """
    Render ICARE Hero Banner:
    - Badges:
      🏆 Scopus Research Dossier
      🏛️ Historic Premier State University (Estd. 1857)
      ⭐ NAAC A++ (CGPA 3.65)
      📜 NIRF Category: University
    - Title: University of Mumbai Live Scopus Intelligence Dashboard
    - Rank Box: #{total_pubs:,} output and {total_cites:,} citations
    """
    is_dark = theme.lower() == "dark"
    card_bg = "rgba(14, 23, 42, 0.85)" if is_dark else "rgba(255, 255, 255, 0.95)"
    border_col = "rgba(255, 255, 255, 0.10)" if is_dark else "rgba(0, 0, 0, 0.08)"
    text_primary = "#F8FAFC" if is_dark else "#0F172A"
    text_secondary = "#94A3B8" if is_dark else "#475569"

    html = f"""
    <div class="hero-banner" style="
        background: {card_bg};
        border: 1px solid {border_col};
        border-radius: 18px;
        padding: 26px 30px;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 28px;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.25);
        position: relative;
        overflow: hidden;
    ">
        <!-- Ambient Blue Corner Glow -->
        <div style="
            position: absolute;
            top: -60px;
            right: -60px;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(2, 132, 199, 0.25) 0%, rgba(2, 132, 199, 0) 70%);
            pointer-events: none;
        "></div>

        <!-- Left Content Section -->
        <div style="flex: 1; min-width: 300px; z-index: 1;">
            <!-- Institutional Badges Row -->
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;">
                <span class="badge-gold" style="font-size: 0.76rem; padding: 4px 11px; border-radius: 9999px; font-weight: 700;">
                    🏆 Scopus Research Dossier
                </span>
                <span style="
                    background: {"rgba(255, 255, 255, 0.06)" if is_dark else "rgba(0, 0, 0, 0.05)"};
                    color: {text_primary};
                    border: 1px solid {border_col};
                    font-size: 0.76rem;
                    padding: 4px 11px;
                    border-radius: 9999px;
                    font-weight: 600;
                ">
                    🏛️ Historic Premier State University (Estd. 1857)
                </span>
                <span style="
                    background: rgba(245, 158, 11, 0.12);
                    color: #F59E0B;
                    border: 1px solid rgba(245, 158, 11, 0.35);
                    font-size: 0.76rem;
                    padding: 4px 11px;
                    border-radius: 9999px;
                    font-weight: 700;
                ">
                    ⭐ NAAC A++ (CGPA 3.65)
                </span>
                <span class="badge-cyan" style="font-size: 0.76rem; padding: 4px 11px; border-radius: 9999px; font-weight: 600;">
                    📜 NIRF Category: University
                </span>
            </div>

            <!-- Main Title -->
            <h1 style="
                font-size: 1.85rem;
                font-weight: 800;
                letter-spacing: -0.02em;
                margin: 0 0 10px 0;
                color: {text_primary};
                line-height: 1.2;
            ">
                University of Mumbai <span style="
                    background: linear-gradient(90deg, #0284C7 0%, #38BDF8 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                ">Live Scopus Intelligence</span> Dashboard
            </h1>

            <p style="
                font-size: 0.90rem;
                color: {text_secondary};
                margin: 0;
                max-width: 680px;
                line-height: 1.5;
            ">
                Real-time bibliometric surveillance, multi-variant institutional publication tracking,
                citation impact dynamics, and department analytics for accreditation benchmarking.
            </p>
        </div>

        <!-- Right Side: Dual Metric Rank Box -->
        <div class="hero-rank-box" style="
            background: {"rgba(7, 13, 30, 0.75)" if is_dark else "rgba(241, 245, 249, 0.85)"};
            border: 1px solid {"rgba(56, 189, 248, 0.30)" if is_dark else "rgba(2, 132, 199, 0.25)"};
            border-radius: 16px;
            padding: 18px 24px;
            min-width: 280px;
            text-align: center;
            box-shadow: 0 8px 24px {"rgba(2, 132, 199, 0.18)" if is_dark else "rgba(2, 132, 199, 0.08)"};
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 1;
        ">
            <div style="
                font-size: 0.72rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: {"#38BDF8" if is_dark else "#0284C7"};
                margin-bottom: 8px;
            ">
                📊 Institutional Research Footprint
            </div>

            <div style="display: flex; justify-content: space-around; align-items: center; gap: 14px; margin: 6px 0;">
                <!-- Output Stat -->
                <div>
                    <div style="font-size: 1.70rem; font-weight: 800; color: {text_primary}; line-height: 1.1;">
                        #{total_pubs:,}
                    </div>
                    <div style="font-size: 0.72rem; font-weight: 600; color: {text_secondary}; text-transform: uppercase; margin-top: 4px;">
                        Scopus Output
                    </div>
                </div>

                <div style="height: 38px; width: 1px; background: {border_col};"></div>

                <!-- Citations Stat -->
                <div>
                    <div style="font-size: 1.70rem; font-weight: 800; color: #F59E0B; line-height: 1.1;">
                        {total_cites:,}
                    </div>
                    <div style="font-size: 0.72rem; font-weight: 600; color: {text_secondary}; text-transform: uppercase; margin-top: 4px;">
                        Citations
                    </div>
                </div>
            </div>

            <div style="
                margin-top: 12px;
                padding-top: 10px;
                border-top: 1px dashed {border_col};
                font-size: 0.72rem;
                color: {text_secondary};
            ">
                🏛️ Scopus AF-ID: <strong>60028245</strong>
            </div>
        </div>
    </div>
    """
    return clean_html(html)


def render_kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: str = "📈",
    badge: Optional[str] = None,
    badge_type: str = "cyan",
    theme: str = "dark"
) -> str:
    """
    Generate clean HTML for an executive KPI metric card.
    """
    badge_html = f'<span class="kpi-badge badge-{badge_type}">{badge}</span>' if badge else ""
    return clean_html(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <span class="kpi-title">{title}</span>
            <span class="kpi-icon">{icon}</span>
        </div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle">
            {badge_html}
            <span>{subtitle}</span>
        </div>
    </div>
    """)


def render_faculty_podium_card(
    rank: int,
    author_name: str,
    dept: str,
    papers: int,
    citations: int,
    cpp: float,
    h_index: int,
    theme: str = "dark"
) -> str:
    """
    Render Top 3 Faculty Podium Card (Gold, Silver, Bronze) with institutional styling.
    """
    is_dark = theme.lower() == "dark"

    medals = {
        1: ("🥇", "GOLD LAUREATE", "#F59E0B", "rgba(245, 158, 11, 0.18)", "rgba(245, 158, 11, 0.45)"),
        2: ("🥈", "SILVER LAUREATE", "#94A3B8", "rgba(148, 163, 184, 0.15)", "rgba(148, 163, 184, 0.45)"),
        3: ("🥉", "BRONZE LAUREATE", "#D97706", "rgba(217, 119, 6, 0.15)", "rgba(217, 119, 6, 0.45)")
    }

    icon, badge_text, border_color, glow_bg, stroke = medals.get(
        rank, ("🏆", f"RANK #{rank}", "#0284C7", "rgba(2, 132, 199, 0.15)", "rgba(2, 132, 199, 0.45)")
    )

    card_bg = (
        f"linear-gradient(135deg, {glow_bg} 0%, rgba(14, 23, 42, 0.88) 100%)"
        if is_dark else
        f"linear-gradient(135deg, {glow_bg} 0%, rgba(255, 255, 255, 0.95) 100%)"
    )

    text_primary = "#F8FAFC" if is_dark else "#0F172A"
    text_secondary = "#94A3B8" if is_dark else "#475569"
    dept_short = dept.replace("Department of ", "").replace("National Centre for Nanosciences and Nanotechnology (NCNNUM)", "NCNNUM Nano")

    return clean_html(f"""
    <div style="
        background: {card_bg};
        border: 1.5px solid {stroke};
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.20);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
        margin-bottom: 12px;
        transition: transform 0.25s ease;
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
            <span style="
                background: {stroke};
                color: #FFFFFF;
                font-size: 0.70rem;
                font-weight: 800;
                letter-spacing: 0.06em;
                padding: 3px 10px;
                border-radius: 9999px;
            ">
                {icon} {badge_text}
            </span>
            <span style="font-size: 1.4rem;">{icon}</span>
        </div>

        <div style="font-size: 1.25rem; font-weight: 800; color: {text_primary}; margin-bottom: 3px;">
            {author_name}
        </div>
        <div style="font-size: 0.78rem; font-weight: 600; color: #0284C7; margin-bottom: 14px;">
            🏛️ {dept_short}
        </div>

        <div style="
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
            background: {'rgba(7, 13, 30, 0.55)' if is_dark else 'rgba(241, 245, 249, 0.75)'};
            border-radius: 10px;
            padding: 10px 8px;
            text-align: center;
        ">
            <div>
                <div style="font-size: 1.10rem; font-weight: 800; color: {text_primary};">{papers}</div>
                <div style="font-size: 0.65rem; color: {text_secondary}; text-transform: uppercase;">Papers</div>
            </div>
            <div>
                <div style="font-size: 1.10rem; font-weight: 800; color: #F59E0B;">{citations:,}</div>
                <div style="font-size: 0.65rem; color: {text_secondary}; text-transform: uppercase;">Cites</div>
            </div>
            <div>
                <div style="font-size: 1.10rem; font-weight: 800; color: #10B981;">{cpp:.1f}</div>
                <div style="font-size: 0.65rem; color: {text_secondary}; text-transform: uppercase;">CPP</div>
            </div>
            <div>
                <div style="font-size: 1.10rem; font-weight: 800; color: #38BDF8;">h-{h_index}</div>
                <div style="font-size: 0.65rem; color: {text_secondary}; text-transform: uppercase;">h-Index</div>
            </div>
        </div>
    </div>
    """)


def render_section_header(
    title: str,
    subtitle: str = "",
    badge_text: Optional[str] = None,
    icon: str = "📌",
    theme: str = "dark"
) -> str:
    """
    Generate styled section header with glassmorphism accent.
    """
    is_dark = theme.lower() == "dark"
    text_primary = "#F8FAFC" if is_dark else "#0F172A"
    text_secondary = "#94A3B8" if is_dark else "#475569"
    badge_html = (
        f'<span class="badge-cyan" style="font-size: 0.72rem; padding: 3px 10px; border-radius: 9999px; font-weight: 700;">{badge_text}</span>'
        if badge_text else ""
    )

    return clean_html(f"""
    <div style="margin: 28px 0 16px 0; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 10px;">
        <div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.25rem;">{icon}</span>
                <h2 style="margin: 0; font-size: 1.35rem; font-weight: 700; color: {text_primary}; letter-spacing: -0.01em;">
                    {title}
                </h2>
                {badge_html}
            </div>
            {f'<p style="margin: 4px 0 0 32px; font-size: 0.84rem; color: {text_secondary};">{subtitle}</p>' if subtitle else ''}
        </div>
    </div>
    """)


if __name__ == "__main__":
    print("styles.py syntax check successful.")
    css_dark = get_custom_css("dark")
    css_light = get_custom_css("light")
    print(f"Dark CSS length: {len(css_dark)} chars")
    print(f"Light CSS length: {len(css_light)} chars")
    topbar_html = render_icare_topbar("dark")
    hero_html = render_icare_hero(11349, 142850, "dark")
    print(f"Topbar HTML length: {len(topbar_html)} chars")
    print(f"Hero HTML length: {len(hero_html)} chars")
