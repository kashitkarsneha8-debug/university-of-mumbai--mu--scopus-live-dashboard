"""
app.py
University of Mumbai (MU) Live Scopus Intelligence Dashboard
Accreditation Surveillance & Research Analytics Portal

Features:
- ICARE Glassmorphism design system with full Dark/Light theme support.
- Top 10 Executive KPI cards.
- Multi-dimensional sidebar filters: Year Range, Departments, Quartiles, Collaboration Types.
- Tab 1 (📈 Trends): Dual-axis Annual Publications vs Cumulative Total + Monthly velocity chart.
- Tab 2 (🎯 Impact): Annual citation accrual curve + Department citations horizontal bar + Landmark papers table with live DOI links.
- Tab 3 (🌐 Collaboration): Global collaboration choropleth world map + Top 10 partner countries + Institutional treemap + Industry R&D breakdown.
- Tab 4 (🏆 Quality & Benchmarks): Donut chart for Quartiles + Impact vs. Volume Quadrant Bubble Chart + Department Comparative Radar Chart.
"""

import os
import json
import base64
import io
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from config import UNIVERSITY_CONFIG
import scopus_api
import mock_data
import data_processor as dp
import styles
import ai_copilot

# Page Configuration
st.set_page_config(
    page_title=UNIVERSITY_CONFIG["app_title"],
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Theme State & Styling
# ---------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

if "data_mode" not in st.session_state:
    st.session_state["data_mode"] = "Benchmark Mock (2,500 MU Records)"


def toggle_theme():
    if st.session_state["theme"] == "dark":
        st.session_state["theme"] = "light"
    else:
        st.session_state["theme"] = "dark"


current_theme = st.session_state["theme"]
is_dark = current_theme == "dark"

# Apply custom CSS
st.markdown(styles.get_custom_css(theme=current_theme), unsafe_allow_html=True)


def apply_chart_theme(fig: go.Figure, theme: str = "dark") -> go.Figure:
    """
    Standardize Plotly chart styling according to active theme.
    """
    dark_mode = theme.lower() == "dark"
    bg_color = "rgba(0, 0, 0, 0)"
    grid_color = "rgba(255, 255, 255, 0.08)" if dark_mode else "rgba(0, 0, 0, 0.07)"
    font_color = "#F8FAFC" if dark_mode else "#0F172A"
    axis_color = "#94A3B8" if dark_mode else "#64748B"

    fig.update_layout(
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(family="Plus Jakarta Sans, sans-serif", color=font_color, size=12),
        margin=dict(l=35, r=35, t=55, b=35),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=font_color)
        ),
        hoverlabel=dict(
            bgcolor="#0E172A" if dark_mode else "#FFFFFF",
            font_color="#F8FAFC" if dark_mode else "#0F172A",
            font_family="Plus Jakarta Sans, sans-serif",
            bordercolor="#0284C7"
        )
    )
    fig.update_xaxes(
        gridcolor=grid_color,
        zerolinecolor=grid_color,
        tickfont=dict(color=axis_color, size=11),
        title_font=dict(color=font_color, size=12)
    )
    fig.update_yaxes(
        gridcolor=grid_color,
        zerolinecolor=grid_color,
        tickfont=dict(color=axis_color, size=11),
        title_font=dict(color=font_color, size=12)
    )
    return fig


def make_doi_link(row):
    doi = str(row.get("doi", "")).strip()
    if doi and doi.startswith("10."):
        return f"https://doi.org/{doi}"
    scopus_id = str(row.get("scopus_id", "")).strip()
    if scopus_id:
        return f"https://www.scopus.com/record/display.uri?eid=2-s2.0-{scopus_id}&origin=inward"
    return "#"


# ---------------------------------------------------------
# Sidebar Controls & Navigation
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(styles.clean_html(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
        <div style="font-weight: 800; font-size: 1.15rem; color: {'#F8FAFC' if is_dark else '#0F172A'};">
            🏛️ MU Intelligence
        </div>
    </div>
    """), unsafe_allow_html=True)

    # Theme Toggle Switcher
    theme_col1, theme_col2 = st.columns([1, 1])
    with theme_col1:
        st.caption("UI Theme Mode")
    with theme_col2:
        btn_label = "☀️ Light" if is_dark else "🌙 Dark"
        if st.button(btn_label, key="theme_toggle_btn", use_container_width=True):
            toggle_theme()
            st.rerun()

    st.markdown("---")

    # Data Source Selection
    st.markdown("#### 📡 Data Pipeline")
    data_source_mode = st.radio(
        "Select Active Pipeline:",
        ["Benchmark Mock (2,500 MU Records)", "Live Scopus Cache (API Sync)"],
        index=0 if st.session_state["data_mode"].startswith("Benchmark") else 1,
        help="Switch between the benchmark 2,500 MU records or live Scopus API cached records."
    )
    st.session_state["data_mode"] = data_source_mode

    # Manual Sync / Force Refresh
    sync_status = scopus_api.get_sync_status()
    st.caption(f"Status: **{sync_status['last_status']}**")

    if st.button("🔄 Sync with Scopus API", use_container_width=True):
        with st.spinner("Connecting to Elsevier Scopus API..."):
            scopus_api.trigger_background_sync(max_records=100)
            st.toast("Triggered background sync with Scopus API!", icon="⚡")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 🔍 Filter Research Scope")

# ---------------------------------------------------------
# Data Loading & Preparation
# ---------------------------------------------------------
if st.session_state["data_mode"].startswith("Benchmark"):
    raw_df = mock_data.get_mock_dataframe(count=2500)
    data_source_label = "Offline Benchmark Engine (2,500 Records)"
else:
    cached_records, meta = scopus_api.load_scopus_data(allow_mock_fallback=True)
    raw_df = pd.DataFrame(cached_records)
    data_source_label = meta.get("source", "Live Scopus Cache")

# Ensure required columns are present
if "year" in raw_df.columns:
    raw_df["year"] = pd.to_numeric(raw_df["year"], errors="coerce").fillna(2024).astype(int)
if "citations" in raw_df.columns:
    raw_df["citations"] = pd.to_numeric(raw_df["citations"], errors="coerce").fillna(0).astype(int)

# Sidebar Filter Controls
with st.sidebar:
    min_year = int(raw_df["year"].min()) if not raw_df.empty else 2018
    max_year = int(raw_df["year"].max()) if not raw_df.empty else 2026

    selected_years = st.slider(
        "Publication Window:",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1
    )

    all_depts = sorted(raw_df["department"].dropna().unique().tolist()) if not raw_df.empty else []
    selected_depts = st.multiselect(
        "Academic Department:",
        options=all_depts,
        default=[]
    )

    selected_quartiles = st.multiselect(
        "Journal Quartile:",
        options=["Q1", "Q2", "Q3", "Q4"],
        default=["Q1", "Q2", "Q3", "Q4"]
    )

    selected_collab = st.selectbox(
        "Collaboration Mode:",
        options=["All Publications", "International Collaboration", "Industry Collaboration", "Domestic / Institutional Only"]
    )

    search_query = st.text_input("Search Keyword / Title:", placeholder="e.g. Nanoparticle, AI, Ferrite")

    st.markdown("---")
    st.markdown(styles.clean_html(f"""
    <div style="font-size: 0.75rem; color: {'#94A3B8' if is_dark else '#64748B'}; line-height: 1.4;">
        <strong>University of Mumbai</strong><br>
        Established: 1857 &bull; NIRF: IR-O-U-0318<br>
        NAAC: Grade A++ (CGPA 3.65)<br>
        Scopus AF-ID: 60028245
    </div>
    """), unsafe_allow_html=True)

# Apply Filters
collab_filter_val = None
if selected_collab == "International Collaboration":
    collab_filter_val = ["International"]
elif selected_collab == "Industry Collaboration":
    collab_filter_val = ["Industry"]
elif selected_collab == "Domestic / Institutional Only":
    collab_filter_val = ["National"]

filtered_df = dp.filter_publications(
    raw_df,
    year_range=selected_years,
    depts=selected_depts if selected_depts else None,
    quartiles=selected_quartiles if selected_quartiles else None,
    collab_types=collab_filter_val
)

if search_query and not filtered_df.empty:
    q = search_query.strip().lower()
    filtered_df = filtered_df[
        filtered_df["title"].str.lower().str.contains(q, na=False) |
        filtered_df["journal"].str.lower().str.contains(q, na=False) |
        filtered_df["authors"].str.lower().str.contains(q, na=False)
    ].reset_index(drop=True)

# ---------------------------------------------------------
# Topbar & Hero Banner
# ---------------------------------------------------------
st.markdown(styles.render_icare_topbar(theme=current_theme), unsafe_allow_html=True)

kpis = dp.calculate_top_10_kpis(filtered_df)
hero_total_pubs = kpis["total_output"]
hero_total_cites = kpis["total_citations"]

st.markdown(styles.render_icare_hero(hero_total_pubs, hero_total_cites, theme=current_theme), unsafe_allow_html=True)

# ---------------------------------------------------------
# Top 10 Executive KPI Cards Grid
# ---------------------------------------------------------
st.markdown(
    styles.render_section_header("Executive Bibliometric Intelligence", "Institutional research indicators across active filters", "TOP 10 KPIS", "📊", current_theme),
    unsafe_allow_html=True
)

# Row 1 of 5 KPIs
kpi_r1_c1, kpi_r1_c2, kpi_r1_c3, kpi_r1_c4, kpi_r1_c5 = st.columns(5)
with kpi_r1_c1:
    st.markdown(styles.render_kpi_card("Total Scopus Output", f"{kpis['total_output']:,}", "All indexed papers", "📚", "CORE", "cyan", current_theme), unsafe_allow_html=True)
with kpi_r1_c2:
    st.markdown(styles.render_kpi_card("2026 Volume", f"{kpis['volume_2026']:,}", "Current calendar output", "📅", "LIVE", "cyan", current_theme), unsafe_allow_html=True)
with kpi_r1_c3:
    st.markdown(styles.render_kpi_card("2025 Volume", f"{kpis['volume_2025']:,}", "Full benchmark year", "🗓️", "ANNUAL", "cyan", current_theme), unsafe_allow_html=True)
with kpi_r1_c4:
    st.markdown(styles.render_kpi_card("Total Citations", f"{kpis['total_citations']:,}", "Cumulative citations", "💎", "IMPACT", "gold", current_theme), unsafe_allow_html=True)
with kpi_r1_c5:
    st.markdown(styles.render_kpi_card("Citations Per Paper", f"{kpis['cpp']:.2f}", "CPP = Cites / Pubs", "🎯", "AVG", "gold", current_theme), unsafe_allow_html=True)

# Row 2 of 5 KPIs
kpi_r2_c1, kpi_r2_c2, kpi_r2_c3, kpi_r2_c4, kpi_r2_c5 = st.columns(5)
with kpi_r2_c1:
    st.markdown(styles.render_kpi_card("Q1 Publications", f"{kpis['q1_count']:,}", f"{kpis['q1_percentage']:.1f}% top tier", "⭐", "Q1 SHARE", "purple", current_theme), unsafe_allow_html=True)
with kpi_r2_c2:
    st.markdown(styles.render_kpi_card("International Collab", f"{kpis['international_collab_pct']:.1f}%", "Cross-border research", "🌐", "GLOBAL", "cyan", current_theme), unsafe_allow_html=True)
with kpi_r2_c3:
    st.markdown(styles.render_kpi_card("Industry Collab", f"{kpis['industry_collab_pct']:.1f}%", "Corporate R&D links", "🏢", "R&D", "purple", current_theme), unsafe_allow_html=True)
with kpi_r2_c4:
    st.markdown(styles.render_kpi_card("Active Authors", f"{kpis['active_authors']:,}", "Deduplicated researchers", "👥", "FACULTY", "cyan", current_theme), unsafe_allow_html=True)
with kpi_r2_c5:
    st.markdown(styles.render_kpi_card("Last 30 Days Velocity", f"{kpis['velocity_last_30_days']:,}", "Monthly publication rate", "⚡", "SPEED", "gold", current_theme), unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Tabs: 1 to 7
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Trends (Dual-Axis & Velocity)",
    "🎯 Impact (Accrual & Landmark Papers)",
    "🌐 Collaboration (Global & Industry)",
    "🏆 Quality & Benchmarks (Q1-Q4 & Radar)",
    "👥 Authors (Faculty Dossier & Print)",
    "📡 Live Feed (Search & Export)",
    "🤖 AI Copilot (Natural Language Assistant)"
])

# =========================================================
# TAB 1: 📈 TRENDS
# =========================================================
with tab1:
    st.markdown(
        styles.render_section_header("Annual Publication Output & Growth Trajectory", "Dual-axis tracking of annual publication velocity against cumulative research volume", "MOMENTUM", "📈", current_theme),
        unsafe_allow_html=True
    )

    trends_col1, trends_col2 = st.columns([7, 5])

    with trends_col1:
        # Dual-Axis Annual Output + Cumulative Total
        yearly_df = dp.get_publications_by_year(filtered_df)

        if not yearly_df.empty:
            yearly_df["cumulative"] = yearly_df["publications"].cumsum()

            fig_dual = make_subplots(specs=[[{"secondary_y": True}]])

            # Primary Y-axis: Blue Bars for Annual Publications (#0284C7)
            fig_dual.add_trace(
                go.Bar(
                    x=yearly_df["year"],
                    y=yearly_df["publications"],
                    name="Annual Publications",
                    marker=dict(
                        color="#0284C7",
                        line=dict(color="#38BDF8", width=1.5),
                        opacity=0.9
                    ),
                    text=yearly_df["publications"],
                    textposition="auto",
                    hovertemplate="<b>Year %{x}</b><br>Annual Publications: %{y:,}<extra></extra>"
                ),
                secondary_y=False
            )

            # Secondary Y-axis: Gold Line for Cumulative Total (#F59E0B, width 3)
            fig_dual.add_trace(
                go.Scatter(
                    x=yearly_df["year"],
                    y=yearly_df["cumulative"],
                    name="Cumulative Total",
                    mode="lines+markers",
                    line=dict(color="#F59E0B", width=3, shape="spline"),
                    marker=dict(size=8, color="#F59E0B", symbol="circle", line=dict(color="#FFFFFF", width=1.5)),
                    hovertemplate="<b>Year %{x}</b><br>Cumulative Output: %{y:,}<extra></extra>"
                ),
                secondary_y=True
            )

            fig_dual.update_layout(
                title=dict(text="<b>Annual vs Cumulative Scopus Publications</b>", font=dict(size=14)),
                hovermode="x unified",
                bargap=0.28
            )
            fig_dual.update_xaxes(title_text="Publication Year", dtick=1)
            fig_dual.update_yaxes(title_text="Annual Output (Papers)", secondary_y=False)
            fig_dual.update_yaxes(title_text="Cumulative Total (Papers)", secondary_y=True, showgrid=False)

            apply_chart_theme(fig_dual, current_theme)
            st.plotly_chart(fig_dual, use_container_width=True)
        else:
            st.info("No publication data matching the selected filter criteria.")

    with trends_col2:
        # Monthly Velocity Chart
        st.markdown(f"##### ⏱️ Monthly Publishing Velocity")
        active_years_available = sorted(filtered_df["year"].dropna().unique().tolist(), reverse=True) if not filtered_df.empty else [2025]
        selected_month_year = st.selectbox(
            "Select Calendar Year for Velocity:",
            options=active_years_available,
            index=0 if active_years_available else 0
        )

        monthly_df = dp.get_publications_by_month(filtered_df, selected_month_year)

        fig_month = go.Figure()
        fig_month.add_trace(
            go.Bar(
                x=monthly_df["month_name"].str[:3],
                y=monthly_df["publications"],
                name="Monthly Papers",
                marker=dict(
                    color="#38BDF8",
                    opacity=0.85,
                    line=dict(color="#0284C7", width=1)
                ),
                text=monthly_df["publications"],
                textposition="outside",
                hovertemplate="<b>%{x}</b>: %{y} papers<extra></extra>"
            )
        )

        fig_month.update_layout(
            title=dict(text=f"<b>Monthly Output Cadence ({selected_month_year})</b>", font=dict(size=14)),
            xaxis_title="Month",
            yaxis_title="Papers Published",
            bargap=0.25
        )
        apply_chart_theme(fig_month, current_theme)
        st.plotly_chart(fig_month, use_container_width=True)

    # Secondary Trend Indicators: Annual CPP Growth
    if not yearly_df.empty and len(yearly_df) > 1:
        st.markdown("##### 📈 Citations Per Paper (CPP) Evolution")
        fig_cpp = px.line(
            yearly_df,
            x="year",
            y="cpp",
            markers=True,
            line_shape="spline",
            title="<b>Historical Citations Per Paper (CPP) Maturation Curve</b>"
        )
        fig_cpp.update_traces(
            line=dict(color="#10B981", width=3),
            marker=dict(size=8, color="#10B981", line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>Year %{x}</b><br>CPP: %{y:.2f}<extra></extra>"
        )
        apply_chart_theme(fig_cpp, current_theme)
        st.plotly_chart(fig_cpp, use_container_width=True)


# =========================================================
# TAB 2: 🎯 IMPACT
# =========================================================
with tab2:
    st.markdown(
        styles.render_section_header("Citation Dynamics & Academic Impact", "Accumulation curves, department citations, and high-impact landmark research dossiers", "CITATIONS", "🎯", current_theme),
        unsafe_allow_html=True
    )

    impact_col1, impact_col2 = st.columns([6, 6])

    with impact_col1:
        # Annual Citation Accrual Curve
        if not yearly_df.empty:
            fig_accrual = go.Figure()
            fig_accrual.add_trace(
                go.Scatter(
                    x=yearly_df["year"],
                    y=yearly_df["citations"],
                    fill="tozeroy",
                    mode="lines+markers",
                    name="Annual Citations",
                    line=dict(color="#F59E0B", width=3, shape="spline"),
                    fillcolor="rgba(245, 158, 11, 0.18)" if is_dark else "rgba(245, 158, 11, 0.12)",
                    marker=dict(size=8, color="#F59E0B", line=dict(color="#FFFFFF", width=1.5)),
                    hovertemplate="<b>Year %{x}</b><br>Citations Accrued: %{y:,}<extra></extra>"
                )
            )
            fig_accrual.update_layout(
                title=dict(text="<b>Annual Citation Accrual Curve</b>", font=dict(size=14)),
                xaxis_title="Year",
                yaxis_title="Total Citations Accrued"
            )
            apply_chart_theme(fig_accrual, current_theme)
            st.plotly_chart(fig_accrual, use_container_width=True)

    with impact_col2:
        # Department Citations Horizontal Bar Chart
        if not filtered_df.empty:
            dept_cites = filtered_df.groupby("department")["citations"].sum().reset_index()
            dept_cites = dept_cites.sort_values("citations", ascending=True).tail(10)

            # Shorten department names for crisp display
            dept_cites["dept_short"] = dept_cites["department"].str.replace("Department of ", "").str.replace("National Centre for Nanosciences and Nanotechnology (NCNNUM)", "NCNNUM Nanotech")

            fig_dept_bar = go.Figure(
                go.Bar(
                    x=dept_cites["citations"],
                    y=dept_cites["dept_short"],
                    orientation="h",
                    marker=dict(
                        color=dept_cites["citations"],
                        colorscale="Blues" if is_dark else "Viridis",
                        line=dict(color="#38BDF8", width=1)
                    ),
                    text=dept_cites["citations"].apply(lambda x: f"{x:,}"),
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Citations: %{x:,}<extra></extra>"
                )
            )
            fig_dept_bar.update_layout(
                title=dict(text="<b>Top Departments by Citation Volume</b>", font=dict(size=14)),
                xaxis_title="Cumulative Citations",
                yaxis_title="",
                margin=dict(l=140)
            )
            apply_chart_theme(fig_dept_bar, current_theme)
            st.plotly_chart(fig_dept_bar, use_container_width=True)

    # Landmark Papers Table with Live DOI Links
    st.markdown(
        styles.render_section_header("Landmark Research Publications", "Top cited papers across University of Mumbai with live DOI links", "HIGH IMPACT", "🏆", current_theme),
        unsafe_allow_html=True
    )

    if not filtered_df.empty:
        top_papers_df = filtered_df.sort_values(by="citations", ascending=False).head(20).copy()
        top_papers_df["Rank"] = range(1, len(top_papers_df) + 1)

        # Build clean live DOI link
        def make_doi_link(row):
            doi = str(row["doi"]).strip()
            if doi and doi.startswith("10."):
                return f"https://doi.org/{doi}"
            return f"https://www.scopus.com/record/display.uri?eid=2-s2.0-{row['scopus_id']}&origin=inward"

        top_papers_df["Paper Link"] = top_papers_df.apply(make_doi_link, axis=1)

        display_cols = ["Rank", "title", "primary_author", "journal", "year", "citations", "quartile", "Paper Link"]
        table_df = top_papers_df[display_cols].rename(columns={
            "title": "Title",
            "primary_author": "Lead Author",
            "journal": "Journal",
            "year": "Year",
            "citations": "Citations",
            "quartile": "Quartile"
        })

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", width="small"),
                "Title": st.column_config.TextColumn("Publication Title", width="large"),
                "Lead Author": st.column_config.TextColumn("Lead Author", width="medium"),
                "Journal": st.column_config.TextColumn("Journal / Source", width="medium"),
                "Year": st.column_config.NumberColumn("Year", format="%d", width="small"),
                "Citations": st.column_config.NumberColumn("Citations", format="%d 🔥", width="small"),
                "Quartile": st.column_config.TextColumn("Quartile", width="small"),
                "Paper Link": st.column_config.LinkColumn("DOI ↗", display_text="Open Paper ↗", width="small")
            }
        )

        # BibTeX Export Download Button
        bibtex_code = dp.export_to_bibtex(top_papers_df)
        st.download_button(
            label="📥 Download Landmark Papers BibTeX (.bib)",
            data=bibtex_code,
            file_name="mumbai_university_landmark_papers.bib",
            mime="text/plain"
        )


# =========================================================
# TAB 3: 🌐 COLLABORATION
# =========================================================
with tab3:
    st.markdown(
        styles.render_section_header("Global & Industrial Collaboration Landscape", "Choropleth world mapping, international co-authorship nodes, and corporate R&D linkages", "PARTNERSHIPS", "🌐", current_theme),
        unsafe_allow_html=True
    )

    collab_col1, collab_col2 = st.columns([7, 5])

    # Extract Partner Countries
    country_counts = {}
    for c_list in filtered_df["countries"].dropna():
        if isinstance(c_list, list):
            for country in c_list:
                c_name = str(country).strip()
                if c_name and c_name.lower() != "india":
                    country_counts[c_name] = country_counts.get(c_name, 0) + 1

    country_df = pd.DataFrame([
        {"country": k, "collaborations": v} for k, v in country_counts.items()
    ]).sort_values("collaborations", ascending=False)

    with collab_col1:
        # Global Collaboration Choropleth World Map
        st.markdown("##### 🗺️ International Collaboration World Map")
        if not country_df.empty:
            fig_map = px.choropleth(
                country_df,
                locations="country",
                locationmode="country names",
                color="collaborations",
                hover_name="country",
                color_continuous_scale="Blues" if is_dark else "Viridis",
                labels={"collaborations": "Joint Papers"}
            )
            fig_map.update_geos(
                showcoastlines=True,
                coastlinecolor="rgba(255, 255, 255, 0.2)" if is_dark else "rgba(0, 0, 0, 0.2)",
                showland=True,
                landcolor="rgba(14, 23, 42, 0.6)" if is_dark else "#F1F5F9",
                showocean=True,
                oceancolor="rgba(7, 13, 30, 0.85)" if is_dark else "#E2E8F0",
                showlakes=False,
                bgcolor="rgba(0, 0, 0, 0)",
                projection_type="natural earth"
            )
            fig_map.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_colorbar=dict(
                    title="Joint Pubs",
                    thickness=12,
                    len=0.6,
                    tickfont=dict(color="#F8FAFC" if is_dark else "#0F172A")
                )
            )
            apply_chart_theme(fig_map, current_theme)
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("No international collaboration records found in current filter subset.")

    with collab_col2:
        # Top 10 Partner Countries Horizontal Bar
        st.markdown("##### 🌍 Top 10 International Partner Nations")
        if not country_df.empty:
            top_countries = country_df.head(10).sort_values("collaborations", ascending=True)
            fig_top_c = go.Figure(
                go.Bar(
                    x=top_countries["collaborations"],
                    y=top_countries["country"],
                    orientation="h",
                    marker=dict(
                        color="#38BDF8",
                        line=dict(color="#0284C7", width=1)
                    ),
                    text=top_countries["collaborations"],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b>: %{x} co-authored papers<extra></extra>"
                )
            )
            fig_top_c.update_layout(
                title=dict(text="", font=dict(size=14)),
                xaxis_title="Joint Publications",
                yaxis_title="",
                margin=dict(l=100, t=10)
            )
            apply_chart_theme(fig_top_c, current_theme)
            st.plotly_chart(fig_top_c, use_container_width=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    collab_sec1, collab_sec2 = st.columns([6, 6])

    with collab_sec1:
        # Institutional Treemap: Department -> Quartile
        st.markdown("##### 🌳 Institutional Research Hierarchy (Treemap)")
        if not filtered_df.empty:
            treemap_df = filtered_df.groupby(["department", "quartile"]).agg(
                papers=("title", "count"),
                citations=("citations", "sum")
            ).reset_index()

            fig_treemap = px.treemap(
                treemap_df,
                path=["department", "quartile"],
                values="papers",
                color="citations",
                color_continuous_scale="Blues" if is_dark else "Viridis",
                labels={"papers": "Publications", "citations": "Total Citations"}
            )
            fig_treemap.update_layout(margin=dict(l=10, r=10, t=10, b=10))
            apply_chart_theme(fig_treemap, current_theme)
            st.plotly_chart(fig_treemap, use_container_width=True)

    with collab_sec2:
        # Industry R&D Collaboration Breakdown
        st.markdown("##### 🏭 Industry R&D Collaboration Rate by Department")
        if not filtered_df.empty:
            ind_by_dept = filtered_df.groupby("department").agg(
                total=("title", "count"),
                industry=("is_industry_collab", "sum")
            ).reset_index()
            ind_by_dept["industry_pct"] = (ind_by_dept["industry"] / ind_by_dept["total"] * 100).round(1)
            ind_by_dept = ind_by_dept.sort_values("industry_pct", ascending=True).tail(8)
            ind_by_dept["dept_clean"] = ind_by_dept["department"].str.replace("Department of ", "").str.replace("National Centre for Nanosciences and Nanotechnology (NCNNUM)", "NCNNUM Nano")

            fig_ind = go.Figure(
                go.Bar(
                    x=ind_by_dept["industry_pct"],
                    y=ind_by_dept["dept_clean"],
                    orientation="h",
                    marker=dict(
                        color="#F59E0B",
                        line=dict(color="#D97706", width=1)
                    ),
                    text=ind_by_dept["industry_pct"].apply(lambda x: f"{x:.1f}%"),
                    textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Industry Collab: %{x:.1f}%<extra></extra>"
                )
            )
            fig_ind.update_layout(
                xaxis_title="Industry Collaboration Percentage (%)",
                yaxis_title="",
                margin=dict(l=120, t=10)
            )
            apply_chart_theme(fig_ind, current_theme)
            st.plotly_chart(fig_ind, use_container_width=True)


# =========================================================
# TAB 4: 🏆 QUALITY & BENCHMARKS
# =========================================================
with tab4:
    st.markdown(
        styles.render_section_header("Accreditation Quality & Academic Benchmarking", "Journal quartile distribution, quadrant bubble matrix, and multi-axis department radar benchmarking", "NAAC / NIRF", "🏆", current_theme),
        unsafe_allow_html=True
    )

    bench_col1, bench_col2 = st.columns([5, 7])

    with bench_col1:
        # Quartile Donut Chart (Q1 #10B981, Q2 #3B82F6, Q3 #F59E0B, Q4 #EF4444)
        st.markdown("##### 🍩 Journal Quartile Profile (Scimago / JCR)")
        if not filtered_df.empty:
            quartile_counts = filtered_df["quartile"].value_counts().reindex(["Q1", "Q2", "Q3", "Q4"]).fillna(0)

            quartile_colors = {
                "Q1": "#10B981",  # Emerald Green
                "Q2": "#3B82F6",  # Vibrant Blue
                "Q3": "#F59E0B",  # Gold / Amber
                "Q4": "#EF4444"   # Red
            }

            fig_donut = go.Figure(
                go.Pie(
                    labels=quartile_counts.index,
                    values=quartile_counts.values,
                    hole=0.55,
                    marker=dict(
                        colors=[quartile_colors.get(q, "#94A3B8") for q in quartile_counts.index],
                        line=dict(color="#070D1E" if is_dark else "#FFFFFF", width=2)
                    ),
                    textinfo="label+percent",
                    textfont=dict(size=12, color="#FFFFFF"),
                    hoverinfo="label+value+percent",
                    hovertemplate="<b>Quartile %{label}</b><br>Publications: %{value:,} (%{percent})<extra></extra>"
                )
            )

            # Center Annotation showing total Q1 share
            q1_share = (quartile_counts.get("Q1", 0) / max(1, quartile_counts.sum())) * 100
            fig_donut.add_annotation(
                text=f"<b>{q1_share:.1f}%</b><br><span style='font-size:11px;'>Q1 Ratio</span>",
                x=0.5, y=0.5,
                font=dict(size=18, color="#10B981"),
                showarrow=False
            )

            fig_donut.update_layout(
                showlegend=True,
                legend=dict(orientation="h", y=-0.1, xanchor="center", x=0.5),
                margin=dict(l=20, r=20, t=20, b=20)
            )
            apply_chart_theme(fig_donut, current_theme)
            st.plotly_chart(fig_donut, use_container_width=True)

    with bench_col2:
        # Impact vs. Volume Quadrant Bubble Chart with gold dashed benchmark line
        st.markdown("##### 🔵 Impact vs. Volume Quadrant Matrix")
        if not filtered_df.empty:
            dept_metrics = filtered_df.groupby("department").agg(
                pubs=("title", "count"),
                cites=("citations", "sum"),
                q1=("quartile", lambda s: (s == "Q1").sum())
            ).reset_index()

            dept_metrics["cpp"] = (dept_metrics["cites"] / dept_metrics["pubs"]).round(2)
            dept_metrics["q1_pct"] = (dept_metrics["q1"] / dept_metrics["pubs"] * 100).round(1)
            dept_metrics["dept_short"] = dept_metrics["department"].str.replace("Department of ", "").str.replace("National Centre for Nanosciences and Nanotechnology (NCNNUM)", "NCNNUM Nano")

            avg_cpp = float(filtered_df["citations"].sum() / max(1, len(filtered_df)))

            fig_bubble = px.scatter(
                dept_metrics,
                x="pubs",
                y="cpp",
                size="cites",
                color="q1_pct",
                hover_name="dept_short",
                text="dept_short",
                color_continuous_scale="Viridis" if is_dark else "Plasma",
                labels={
                    "pubs": "Publication Volume",
                    "cpp": "Citations Per Paper (CPP)",
                    "cites": "Total Citations",
                    "q1_pct": "Q1 Share (%)"
                },
                size_max=45
            )

            fig_bubble.update_traces(
                textposition="top center",
                textfont=dict(size=10, color="#F8FAFC" if is_dark else "#0F172A")
            )

            # Gold dashed benchmark line for Average CPP
            fig_bubble.add_hline(
                y=avg_cpp,
                line_dash="dash",
                line_color="#F59E0B",
                line_width=2,
                annotation_text=f"Benchmark Avg CPP: {avg_cpp:.2f}",
                annotation_position="top left",
                annotation_font=dict(color="#F59E0B", size=11)
            )

            fig_bubble.update_layout(
                xaxis_title="Total Publication Volume (Papers)",
                yaxis_title="Average Citations Per Paper (CPP)",
                margin=dict(l=30, r=30, t=30, b=30)
            )
            apply_chart_theme(fig_bubble, current_theme)
            st.plotly_chart(fig_bubble, use_container_width=True)

    # Department Comparative Benchmark Radar Chart
    st.markdown("##### 🕸️ Department Multi-Dimensional Radar Benchmark")
    if not filtered_df.empty:
        # Choose Top 4 Departments by volume for clear radar comparison
        top_radar_depts = filtered_df["department"].value_counts().head(4).index.tolist()

        radar_categories = [
            "Volume",
            "Total Citations",
            "Citations / Paper",
            "Q1 Share (%)",
            "Intl Collab (%)"
        ]

        # Calculate max metrics across all departments to normalize 0-100%
        dept_all = filtered_df.groupby("department").agg(
            pubs=("title", "count"),
            cites=("citations", "sum"),
            q1=("quartile", lambda s: (s == "Q1").sum()),
            intl=("is_international_collab", "sum")
        ).reset_index()

        dept_all["cpp"] = dept_all["cites"] / dept_all["pubs"]
        dept_all["q1_pct"] = dept_all["q1"] / dept_all["pubs"] * 100
        dept_all["intl_pct"] = dept_all["intl"] / dept_all["pubs"] * 100

        max_v = max(1, dept_all["pubs"].max())
        max_c = max(1, dept_all["cites"].max())
        max_cpp = max(0.1, dept_all["cpp"].max())
        max_q1 = 100.0
        max_intl = 100.0

        fig_radar = go.Figure()

        radar_palette = ["#0284C7", "#10B981", "#F59E0B", "#A855F7"]

        for idx, dept in enumerate(top_radar_depts):
            d_row = dept_all[dept_all["department"] == dept]
            if d_row.empty:
                continue
            r_pubs = min(100.0, (d_row["pubs"].values[0] / max_v) * 100)
            r_cites = min(100.0, (d_row["cites"].values[0] / max_c) * 100)
            r_cpp = min(100.0, (d_row["cpp"].values[0] / max_cpp) * 100)
            r_q1 = min(100.0, d_row["q1_pct"].values[0])
            r_intl = min(100.0, d_row["intl_pct"].values[0])

            r_vals = [r_pubs, r_cites, r_cpp, r_q1, r_intl, r_pubs]
            theta_vals = radar_categories + [radar_categories[0]]
            dept_label = dept.replace("Department of ", "").replace("National Centre for Nanosciences and Nanotechnology (NCNNUM)", "NCNNUM")

            fig_radar.add_trace(
                go.Scatterpolar(
                    r=r_vals,
                    theta=theta_vals,
                    fill="toself",
                    name=dept_label,
                    line=dict(color=radar_palette[idx % len(radar_palette)], width=2),
                    opacity=0.65
                )
            )

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    gridcolor="rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.1)",
                    tickfont=dict(size=9, color="#94A3B8" if is_dark else "#64748B")
                ),
                angularaxis=dict(
                    gridcolor="rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.1)",
                    tickfont=dict(size=11, color="#F8FAFC" if is_dark else "#0F172A")
                ),
                bgcolor="rgba(0, 0, 0, 0)"
            ),
            showlegend=True,
            legend=dict(orientation="h", y=-0.15, xanchor="center", x=0.5),
            margin=dict(l=50, r=50, t=30, b=50)
        )
        apply_chart_theme(fig_radar, current_theme)
        st.plotly_chart(fig_radar, use_container_width=True)


# =========================================================
# TAB 5: 👥 AUTHORS
# =========================================================
with tab5:
    st.markdown(
        styles.render_section_header(
            "Faculty Research Intelligence & Academic Dossier",
            "Top laureate podium, researcher profile analytics, and 100% isolated dossier printing",
            "FACULTY DOSSIER",
            "👥",
            current_theme
        ),
        unsafe_allow_html=True
    )

    all_leaderboard = dp.get_top_authors_leaderboard(filtered_df, top_n=250)

    if not all_leaderboard.empty:
        # 1. Top 3 Faculty Podium Cards (Gold, Silver, Bronze)
        st.markdown("##### 🏅 Faculty Research Laureate Podium (Top 3 Publication Output)")
        podium_c1, podium_c2, podium_c3 = st.columns(3)

        if len(all_leaderboard) > 0:
            row1 = all_leaderboard.iloc[0]
            with podium_c1:
                st.markdown(
                    styles.render_faculty_podium_card(
                        1, row1["author"], row1["department"],
                        int(row1["papers"]), int(row1["citations"]),
                        float(row1["cpp"]), int(row1["h_index"]), current_theme
                    ),
                    unsafe_allow_html=True
                )

        if len(all_leaderboard) > 1:
            row2 = all_leaderboard.iloc[1]
            with podium_c2:
                st.markdown(
                    styles.render_faculty_podium_card(
                        2, row2["author"], row2["department"],
                        int(row2["papers"]), int(row2["citations"]),
                        float(row2["cpp"]), int(row2["h_index"]), current_theme
                    ),
                    unsafe_allow_html=True
                )

        if len(all_leaderboard) > 2:
            row3 = all_leaderboard.iloc[2]
            with podium_c3:
                st.markdown(
                    styles.render_faculty_podium_card(
                        3, row3["author"], row3["department"],
                        int(row3["papers"]), int(row3["citations"]),
                        float(row3["cpp"]), int(row3["h_index"]), current_theme
                    ),
                    unsafe_allow_html=True
                )

        # Expandable Full Faculty Leaderboard Table
        with st.expander("📋 View Complete Faculty Research Leaderboard (Top 100)", expanded=False):
            lead_display = all_leaderboard.head(100).copy()
            lead_display["Rank"] = range(1, len(lead_display) + 1)
            st.dataframe(
                lead_display[["Rank", "author", "department", "papers", "citations", "cpp", "h_index"]].rename(columns={
                    "author": "Faculty Member",
                    "department": "Department",
                    "papers": "Scopus Papers",
                    "citations": "Total Citations",
                    "cpp": "CPP",
                    "h_index": "h-Index"
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Faculty Member": st.column_config.TextColumn("Faculty Member", width="medium"),
                    "Department": st.column_config.TextColumn("Academic Department", width="large"),
                    "Scopus Papers": st.column_config.NumberColumn("Scopus Papers", format="%d", width="small"),
                    "Total Citations": st.column_config.NumberColumn("Total Citations", format="%d 🔥", width="small"),
                    "CPP": st.column_config.NumberColumn("CPP", format="%.2f", width="small"),
                    "h-Index": st.column_config.NumberColumn("h-Index", format="%d", width="small")
                }
            )

        st.markdown("---")

        # 2. Interactive Faculty Selector & Print Profile Button
        st.markdown("##### 🔎 Select Faculty Member for Deep-Dive Dossier Inspection")
        author_options = all_leaderboard["author"].tolist()

        sel_col, print_col = st.columns([8, 3])
        with sel_col:
            selected_faculty = st.selectbox(
                "Select Faculty Member:",
                options=author_options,
                index=0,
                label_visibility="collapsed"
            )

        with print_col:
            print_btn = st.button("🖨️ Print Profile", key="print_profile_btn", use_container_width=True)

        # Retrieve deep-dive metrics for selected faculty
        auth_prof = dp.get_author_profile_metrics(filtered_df, selected_faculty)

        # 4. Isolated Printing Trigger via Hidden Iframe
        if print_btn and not auth_prof["papers_df"].empty:
            print_html_content = dp.generate_author_print_html(auth_prof, auth_prof["papers_df"], auth_prof["trend_df"])
            b64_html = base64.b64encode(print_html_content.encode("utf-8")).decode("utf-8")

            iframe_print_script = f"""
            <script>
            (function() {{
            const b64 = "{b64_html}";
            const html = decodeURIComponent(escape(window.atob(b64)));
            const parentDoc = (window.parent && window.parent.document) ? window.parent.document : document;
            let frame = parentDoc.getElementById('author-print-isolated-frame');
            if (frame) frame.remove();
            frame = parentDoc.createElement('iframe');
            frame.id = 'author-print-isolated-frame';
            frame.style.position = 'fixed'; frame.style.right = '0'; frame.style.bottom = '0';
            frame.style.width = '0'; frame.style.height = '0'; frame.style.border = '0';
            parentDoc.body.appendChild(frame);
            const doc = frame.contentWindow.document;
            doc.open(); doc.write(html); doc.close();
            setTimeout(() => {{ frame.contentWindow.focus(); frame.contentWindow.print(); }}, 350);
            }})();
            </script>
            """
            components.html(iframe_print_script, height=0, width=0)
            st.toast(f"Opening isolated print dossier for {selected_faculty}...", icon="🖨️")

        # 3. Dynamic Author Dossier Header Card
        st.markdown(styles.clean_html(f"""
        <div class="glass-card" style="margin-top: 14px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
                <div>
                    <div style="font-size: 1.55rem; font-weight: 800; color: {'#F8FAFC' if is_dark else '#0F172A'};">
                        {auth_prof['author_name']}
                    </div>
                    <div style="font-size: 0.90rem; font-weight: 600; color: #0284C7; margin-top: 2px;">
                        🏛️ {auth_prof['primary_department']} &bull; University of Mumbai
                    </div>
                </div>
                <div style="text-align: right;">
                    <span class="badge-cyan" style="font-size: 0.75rem; padding: 4px 12px; border-radius: 9999px; font-weight: 700;">
                        ● SCOPUS VERIFIED RESEARCHER
                    </span>
                </div>
            </div>

            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px;">
                <span class="kpi-badge badge-gold" style="font-size: 0.74rem; padding: 4px 11px; border-radius: 9999px;">
                    ⭐ {auth_prof['q1_count']} Q1 Publications
                </span>
                <span class="kpi-badge badge-cyan" style="font-size: 0.74rem; padding: 4px 11px; border-radius: 9999px;">
                    🌐 {auth_prof['international_collab_pct']:.1f}% International Co-authorship
                </span>
                <span class="kpi-badge badge-purple" style="font-size: 0.74rem; padding: 4px 11px; border-radius: 9999px;">
                    🏢 {auth_prof['industry_collab_pct']:.1f}% Industry R&D
                </span>
                <span style="
                    background: {'rgba(255,255,255,0.06)' if is_dark else 'rgba(0,0,0,0.05)'};
                    color: {'#94A3B8' if is_dark else '#475569'};
                    border: 1px solid {'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.1)'};
                    font-size: 0.74rem;
                    padding: 4px 11px;
                    border-radius: 9999px;
                    font-weight: 600;
                ">
                    👥 {auth_prof['coauthors_count']} Co-Authors
                </span>
            </div>
        </div>
        """), unsafe_allow_html=True)

        # 5 KPI Chips Row
        ak1, ak2, ak3, ak4, ak5 = st.columns(5)
        with ak1:
            st.markdown(styles.render_kpi_card("Scopus Papers", f"{auth_prof['total_papers']}", "Total publications", "📚", "PUBS", "cyan", current_theme), unsafe_allow_html=True)
        with ak2:
            st.markdown(styles.render_kpi_card("Total Citations", f"{auth_prof['total_citations']:,}", "Citation volume", "💎", "CITES", "gold", current_theme), unsafe_allow_html=True)
        with ak3:
            st.markdown(styles.render_kpi_card("Cites / Paper", f"{auth_prof['cpp']:.2f}", "Average CPP", "🎯", "CPP", "gold", current_theme), unsafe_allow_html=True)
        with ak4:
            st.markdown(styles.render_kpi_card("Scopus h-Index", f"h-{auth_prof['h_index']}", "H-Core metrics", "🏆", "H-INDEX", "purple", current_theme), unsafe_allow_html=True)
        with ak5:
            st.markdown(styles.render_kpi_card("Q1 Ratio", f"{auth_prof['q1_ratio']:.1f}%", f"{auth_prof['q1_count']} Q1 papers", "⭐", "Q1 TIER", "cyan", current_theme), unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        # Author Charts: Dual-axis Velocity + Quartile Donut
        prof_c1, prof_c2 = st.columns([7, 5])

        with prof_c1:
            st.markdown("##### 📈 Annual Publication & Cumulative Velocity")
            author_trend = auth_prof["trend_df"]
            if not author_trend.empty:
                fig_auth_dual = make_subplots(specs=[[{"secondary_y": True}]])
                fig_auth_dual.add_trace(
                    go.Bar(
                        x=author_trend["year"],
                        y=author_trend["publications"],
                        name="Annual Papers",
                        marker=dict(color="#0284C7", line=dict(color="#38BDF8", width=1.2)),
                        text=author_trend["publications"],
                        textposition="auto",
                        hovertemplate="<b>Year %{x}</b><br>Publications: %{y}<extra></extra>"
                    ),
                    secondary_y=False
                )
                fig_auth_dual.add_trace(
                    go.Scatter(
                        x=author_trend["year"],
                        y=author_trend["cumulative"],
                        name="Cumulative Output",
                        mode="lines+markers",
                        line=dict(color="#F59E0B", width=3, shape="spline"),
                        marker=dict(size=7, color="#F59E0B", line=dict(color="#FFFFFF", width=1.5)),
                        hovertemplate="<b>Year %{x}</b><br>Cumulative: %{y}<extra></extra>"
                    ),
                    secondary_y=True
                )
                fig_auth_dual.update_layout(
                    hovermode="x unified",
                    bargap=0.3
                )
                fig_auth_dual.update_xaxes(title_text="Year", dtick=1)
                fig_auth_dual.update_yaxes(title_text="Papers / Year", secondary_y=False)
                fig_auth_dual.update_yaxes(title_text="Cumulative Papers", secondary_y=True, showgrid=False)
                apply_chart_theme(fig_auth_dual, current_theme)
                st.plotly_chart(fig_auth_dual, use_container_width=True)
            else:
                st.info("Insufficient annual records to render trajectory.")

        with prof_c2:
            st.markdown("##### 🍩 Author Quartile Distribution")
            author_pubs_df = auth_prof["papers_df"]
            if not author_pubs_df.empty:
                auth_q_counts = author_pubs_df["quartile"].value_counts().reindex(["Q1", "Q2", "Q3", "Q4"]).fillna(0)
                fig_auth_donut = go.Figure(
                    go.Pie(
                        labels=auth_q_counts.index,
                        values=auth_q_counts.values,
                        hole=0.55,
                        marker=dict(
                            colors=["#10B981", "#3B82F6", "#F59E0B", "#EF4444"],
                            line=dict(color="#070D1E" if is_dark else "#FFFFFF", width=2)
                        ),
                        textinfo="label+percent",
                        hoverinfo="label+value+percent",
                        hovertemplate="<b>Quartile %{label}</b><br>Papers: %{value} (%{percent})<extra></extra>"
                    )
                )
                fig_auth_donut.add_annotation(
                    text=f"<b>{auth_prof['q1_ratio']:.0f}%</b><br><span style='font-size:10px;'>Q1 Share</span>",
                    x=0.5, y=0.5,
                    font=dict(size=16, color="#10B981"),
                    showarrow=False
                )
                fig_auth_donut.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.12, xanchor="center", x=0.5),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                apply_chart_theme(fig_auth_donut, current_theme)
                st.plotly_chart(fig_auth_donut, use_container_width=True)

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        # Top 5 Landmark Contributions
        st.markdown(f"##### 🏆 Top 5 Landmark Publications by {selected_faculty}")
        if not author_pubs_df.empty:
            top5_auth = author_pubs_df.sort_values(by="citations", ascending=False).head(5).copy()
            top5_auth["Rank"] = range(1, len(top5_auth) + 1)
            top5_auth["Paper Link"] = top5_auth.apply(make_doi_link, axis=1)

            st.dataframe(
                top5_auth[["Rank", "title", "journal", "year", "citations", "quartile", "Paper Link"]].rename(columns={
                    "title": "Publication Title",
                    "journal": "Journal / Venue",
                    "year": "Year",
                    "citations": "Citations",
                    "quartile": "Tier"
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "Publication Title": st.column_config.TextColumn("Publication Title", width="large"),
                    "Journal / Venue": st.column_config.TextColumn("Journal / Venue", width="medium"),
                    "Year": st.column_config.NumberColumn("Year", format="%d", width="small"),
                    "Citations": st.column_config.NumberColumn("Citations", format="%d 🔥", width="small"),
                    "Tier": st.column_config.TextColumn("Tier", width="small"),
                    "Paper Link": st.column_config.LinkColumn("DOI ↗", display_text="Open ↗", width="small")
                }
            )

            # Full Publications Table in Expander
            with st.expander(f"📚 View All {auth_prof['total_papers']} Publications by {selected_faculty}", expanded=False):
                all_auth_display = author_pubs_df.sort_values(by=["year", "citations"], ascending=[False, False]).copy()
                all_auth_display["#"] = range(1, len(all_auth_display) + 1)
                all_auth_display["Paper Link"] = all_auth_display.apply(make_doi_link, axis=1)

                st.dataframe(
                    all_auth_display[["#", "title", "journal", "year", "citations", "quartile", "Paper Link"]].rename(columns={
                        "title": "Publication Title",
                        "journal": "Journal / Venue",
                        "year": "Year",
                        "citations": "Citations",
                        "quartile": "Tier"
                    }),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "#": st.column_config.NumberColumn("#", width="small"),
                        "Publication Title": st.column_config.TextColumn("Publication Title", width="large"),
                        "Journal / Venue": st.column_config.TextColumn("Journal / Venue", width="medium"),
                        "Year": st.column_config.NumberColumn("Year", format="%d", width="small"),
                        "Citations": st.column_config.NumberColumn("Citations", format="%d", width="small"),
                        "Tier": st.column_config.TextColumn("Tier", width="small"),
                        "Paper Link": st.column_config.LinkColumn("DOI ↗", display_text="Open ↗", width="small")
                    }
                )

                # Author BibTeX Download
                auth_bibtex_code = dp.export_to_bibtex(author_pubs_df)
                clean_name = selected_faculty.replace(" ", "_").replace(".", "")
                st.download_button(
                    label=f"📥 Download {selected_faculty}'s BibTeX (.bib)",
                    data=auth_bibtex_code,
                    file_name=f"{clean_name}_scopus_publications.bib",
                    mime="text/plain"
                )
    else:
        st.info("No faculty author data available in the selected filter subset.")


# =========================================================
# TAB 6: 📡 LIVE FEED (SEARCH & EXPORT)
# =========================================================
with tab6:
    st.markdown(
        styles.render_section_header(
            "Live Research Feed & Bibliographic Repository",
            "Full-text searchable publication records with live DOI navigation, Excel and BibTeX data exports",
            "RESEARCH ARCHIVE",
            "📡",
            current_theme
        ),
        unsafe_allow_html=True
    )

    feed_df = filtered_df.copy()

    # Feed Search and Limits
    search_c1, search_c2 = st.columns([8, 4])
    with search_c1:
        feed_search = st.text_input(
            "🔍 Search repository by title, author, journal, or department:",
            placeholder="Type any keyword e.g. Synthesis, Sharma, Biotechnology, 2025...",
            key="live_feed_search_input"
        )
    with search_c2:
        row_limit = st.selectbox(
            "Display Rows Limit:",
            options=[50, 100, 250, 500, "All Records"],
            index=1,
            key="feed_row_limit"
        )

    # Filter by search string
    if feed_search and not feed_df.empty:
        fs = feed_search.strip().lower()
        feed_df = feed_df[
            feed_df["title"].str.lower().str.contains(fs, na=False) |
            feed_df["authors"].str.lower().str.contains(fs, na=False) |
            feed_df["primary_author"].str.lower().str.contains(fs, na=False) |
            feed_df["journal"].str.lower().str.contains(fs, na=False) |
            feed_df["department"].str.lower().str.contains(fs, na=False)
        ].reset_index(drop=True)

    # Apply row limits
    if row_limit != "All Records" and not feed_df.empty:
        display_feed_df = feed_df.head(int(row_limit)).copy()
    else:
        display_feed_df = feed_df.copy()

    # Action Buttons: Export Excel (.xlsx) and Export BibTeX (.bib)
    btn_col1, btn_col2, count_col = st.columns([3, 3, 6])

    with btn_col1:
        # Export Excel (.xlsx) via openpyxl
        excel_buffer = io.BytesIO()
        export_excel_df = feed_df.copy()
        if "Paper Link" not in export_excel_df.columns:
            export_excel_df["DOI_URL"] = export_excel_df.apply(make_doi_link, axis=1)

        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            export_excel_df.to_excel(writer, index=False, sheet_name="MU Scopus Publications")
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="📊 Export Excel (.xlsx)",
            data=excel_data,
            file_name="mumbai_university_scopus_publications.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with btn_col2:
        # Export BibTeX (.bib)
        bib_feed_data = dp.export_to_bibtex(feed_df)
        st.download_button(
            label="📑 Export BibTeX (.bib)",
            data=bib_feed_data,
            file_name="mumbai_university_scopus_feed.bib",
            mime="text/plain",
            use_container_width=True
        )

    with count_col:
        st.markdown(styles.clean_html(f"""
        <div style="text-align: right; padding-top: 8px; font-size: 0.85rem; color: {'#94A3B8' if is_dark else '#475569'};">
            Displaying <strong>{len(display_feed_df):,}</strong> of <strong>{len(feed_df):,}</strong> filtered documents
            (Total Repository: {len(raw_df):,})
        </div>
        """), unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    if not display_feed_df.empty:
        display_feed_df["#"] = range(1, len(display_feed_df) + 1)
        display_feed_df["Paper Link"] = display_feed_df.apply(make_doi_link, axis=1)

        feed_cols = ["#", "title", "primary_author", "department", "journal", "year", "citations", "quartile", "Paper Link"]
        st.dataframe(
            display_feed_df[feed_cols].rename(columns={
                "title": "Publication Title",
                "primary_author": "Lead Author",
                "department": "Department",
                "journal": "Journal / Source",
                "year": "Year",
                "citations": "Citations",
                "quartile": "Tier"
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                "#": st.column_config.NumberColumn("#", width="small"),
                "Publication Title": st.column_config.TextColumn("Publication Title", width="large"),
                "Lead Author": st.column_config.TextColumn("Lead Author", width="medium"),
                "Department": st.column_config.TextColumn("Academic Department", width="medium"),
                "Journal / Source": st.column_config.TextColumn("Journal / Source", width="medium"),
                "Year": st.column_config.NumberColumn("Year", format="%d", width="small"),
                "Citations": st.column_config.NumberColumn("Citations", format="%d 🔥", width="small"),
                "Tier": st.column_config.TextColumn("Tier", width="small"),
                "Paper Link": st.column_config.LinkColumn("DOI ↗", display_text="Open ↗", width="small")
            }
        )
    else:
        st.info("No publication records found matching your search query.")


# =========================================================
# TAB 7: 🤖 AI COPILOT (NATURAL LANGUAGE ASSISTANT)
# =========================================================
with tab7:
    st.markdown(
        styles.render_section_header(
            "MU Scopus Intelligence AI Copilot",
            "Fast built-in Python/Pandas natural language research assistant with zero external API dependencies",
            "IN-BUILT AI",
            "🤖",
            current_theme
        ),
        unsafe_allow_html=True
    )

    # Initialize Copilot chat messages in session state
    if "copilot_messages" not in st.session_state or not st.session_state["copilot_messages"]:
        st.session_state["copilot_messages"] = [
            {
                "role": "assistant",
                "content": f"""👋 **Welcome to the University of Mumbai Research AI Copilot!**

I am your built-in research analytics assistant powered directly by the local Scopus bibliometric intelligence engine (**{len(filtered_df):,} active publications**).

**Try our instant prompt chips below or ask any question:**
* 📊 **Executive Dossier**: Get a high-level institutional summary with NIRF/NAAC accreditation benchmarks.
* 🏛️ **Dept Rankings**: View complete departmental volume, citations, and CPP comparisons.
* 🏆 **Q1 Quality Analysis**: Inspect journal quartile distribution, top Q1 venues, and citation velocity.
* 👥 **Top Authors**: Review faculty research leadership rankings and estimated $h$-indices.

Feel free to ask questions like:
* *"Which department has the highest Citations Per Paper (CPP)?"*
* *"Tell me about research output in the Department of Chemistry."*
* *"What is our international collaboration rate and top partner nations?"*
* *"Who is our most cited researcher?"*
"""
            }
        ]

    # Prompt Chips Row
    st.markdown("##### ⚡ Quick Prompt Chips")
    chip_c1, chip_c2, chip_c3, chip_c4, clear_c = st.columns([2.5, 2.5, 2.5, 2.5, 2])

    triggered_prompt = None
    with chip_c1:
        if st.button("📊 Executive Dossier", use_container_width=True, key="chip_dossier"):
            triggered_prompt = "📊 Executive Dossier"
    with chip_c2:
        if st.button("🏛️ Dept Rankings", use_container_width=True, key="chip_dept"):
            triggered_prompt = "🏛️ Dept Rankings"
    with chip_c3:
        if st.button("🏆 Q1 Quality Analysis", use_container_width=True, key="chip_q1"):
            triggered_prompt = "🏆 Q1 Quality Analysis"
    with chip_c4:
        if st.button("👥 Top Authors", use_container_width=True, key="chip_authors"):
            triggered_prompt = "👥 Top Authors"
    with clear_c:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat_btn"):
            st.session_state["copilot_messages"] = []
            st.rerun()

    st.markdown("---")

    # Render Conversation History
    for msg in st.session_state["copilot_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input Box
    user_query = st.chat_input("Ask AI Copilot about University of Mumbai research...")

    active_query = triggered_prompt or user_query

    if active_query:
        # Append User Message
        st.session_state["copilot_messages"].append({"role": "user", "content": active_query})

        # Generate Fast Offline Response via ai_copilot.py
        with st.spinner("Analyzing bibliometric dataset..."):
            response_text = ai_copilot.generate_ai_response(active_query, filtered_df)

        # Append Assistant Response
        st.session_state["copilot_messages"].append({"role": "assistant", "content": response_text})
        st.rerun()


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.markdown(styles.clean_html(f"""
<div style="text-align: center; padding: 18px 0; color: {'#94A3B8' if is_dark else '#64748B'}; font-size: 0.82rem;">
    <strong>University of Mumbai (MU) Live Scopus Intelligence Dashboard</strong> &bull;
    Scopus Institutional Query AF-ID(60028245) &bull; NIRF ID: IR-O-U-0318 &bull;
    Data Pipeline: <em>{data_source_label}</em> &bull; Built with Streamlit & Plotly
</div>
"""), unsafe_allow_html=True)
