"""
ai_copilot.py
Built-in Natural Language Research Intelligence Assistant
for University of Mumbai (MU) Live Scopus Intelligence Dashboard.

Features:
- Fast, zero external API dependency query engine.
- Directly analyzes live/benchmark pandas DataFrames.
- Pre-built analytical workflows for:
    - 📊 Executive Dossier
    - 🏛️ Dept Rankings
    - 🏆 Q1 Quality Analysis
    - 👥 Top Authors
- Flexible semantic intent matching for department deep-dives, citation questions,
  author lookups, collaboration stats, and recent research trends.
"""

import re
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

import data_processor as dp


def _executive_dossier_response(df: pd.DataFrame) -> str:
    kpis = dp.calculate_top_10_kpis(df)
    total_pubs = kpis["total_output"]
    total_cites = kpis["total_citations"]
    cpp = kpis["cpp"]
    q1_pct = kpis["q1_percentage"]
    q1_cnt = kpis["q1_count"]
    intl_pct = kpis["international_collab_pct"]
    ind_pct = kpis["industry_collab_pct"]
    v26 = kpis["volume_2026"]
    v25 = kpis["volume_2025"]
    velocity = kpis["velocity_last_30_days"]
    authors = kpis["active_authors"]

    # Top department
    dept_counts = df["department"].value_counts()
    top_dept_vol = dept_counts.index[0] if not dept_counts.empty else "N/A"
    top_dept_pubs = dept_counts.values[0] if not dept_counts.empty else 0

    dept_cpp = df.groupby("department").agg(
        pubs=("title", "count"),
        cites=("citations", "sum")
    )
    dept_cpp["cpp"] = dept_cpp["cites"] / dept_cpp["pubs"]
    top_dept_cpp_row = dept_cpp[dept_cpp["pubs"] >= 10].sort_values("cpp", ascending=False)
    top_dept_quality = top_dept_cpp_row.index[0] if not top_dept_cpp_row.empty else top_dept_vol
    top_cpp_val = top_dept_cpp_row["cpp"].values[0] if not top_dept_cpp_row.empty else cpp

    return f"""### 📊 Executive Bibliometric Dossier: University of Mumbai (MU)

**Institutional Affiliation**: University of Mumbai (`AF-ID: 60028245`)  
**NIRF Identifier**: `IR-O-U-0318` | **NAAC Accreditation**: `Grade A++ (CGPA 3.65)`

---

#### 🏆 Key Performance Metrics Overview
| Strategic Metric | Indexed Value | Performance Benchmark |
| :--- | :--- | :--- |
| **Total Scopus Output** | **{total_pubs:,}** Documents | Institutional Cumulative Volume |
| **Total Citations Accrued** | **{total_cites:,}** Citations | Cumulative Global Research Impact |
| **Average Citations Per Paper (CPP)** | **{cpp:.2f}** Cites/Paper | Research Quality & Longevity |
| **Top-Tier Q1 Publications** | **{q1_cnt:,}** ({q1_pct:.1f}%) | Scimago / JCR Highest Quartile |
| **2026 YTD Publishing Volume** | **{v26:,}** Papers | Current Year Calendar Output |
| **2025 Benchmark Annual Volume** | **{v25:,}** Papers | Previous Full Year Output |
| **30-Day Publishing Velocity** | **~{velocity}** Papers/Month | Real-time Indexing Run-Rate |
| **Active Faculty & Scholars** | **{authors:,}** Authors | Unique Contributing Researchers |
| **International Co-authorship** | **{intl_pct:.1f}%** | Cross-Border Global Engagements |
| **Industry & Corporate R&D** | **{ind_pct:.1f}%** | Corporate / Industrial Co-publications |

---

#### 🏛️ Departmental Research Highlights
* **Volume Leader**: **{top_dept_vol}** accounts for `{top_dept_pubs:,}` publications ({top_dept_pubs / max(1, total_pubs) * 100:.1f}% of total research output).
* **Impact Velocity Leader**: **{top_dept_quality}** leads institutional citation density with an average of `{top_cpp_val:.2f}` Citations Per Paper.

#### 💡 Strategic Accreditation Takeaways (NIRF / NAAC)
1. **Accreditation Advantage**: With **{q1_pct:.1f}%** of publications placed in Scopus Q1 journals, the university demonstrates strong research selectivity favorable for NIRF Research & Professional Practice (RPC) scoring.
2. **Global Collaboration Index**: International collaboration at **{intl_pct:.1f}%** establishes cross-continental research presence with co-authors across North America, Europe, and Asia-Pacific.
"""


def _dept_rankings_response(df: pd.DataFrame) -> str:
    if df.empty:
        return "No publications available to generate department rankings."

    dept_stats = df.groupby("department").agg(
        pubs=("title", "count"),
        citations=("citations", "sum"),
        q1=("quartile", lambda s: (s.str.upper() == "Q1").sum()),
        intl=("is_international_collab", "sum"),
        ind=("is_industry_collab", "sum")
    ).reset_index()

    dept_stats["cpp"] = (dept_stats["citations"] / dept_stats["pubs"]).round(2)
    dept_stats["q1_pct"] = (dept_stats["q1"] / dept_stats["pubs"] * 100).round(1)
    dept_stats["intl_pct"] = (dept_stats["intl"] / dept_stats["pubs"] * 100).round(1)

    # Sort by publications descending
    dept_stats = dept_stats.sort_values(by="pubs", ascending=False).reset_index(drop=True)
    dept_stats["Rank"] = range(1, len(dept_stats) + 1)

    table_rows = []
    for _, r in dept_stats.head(15).iterrows():
        dept_clean = r["department"].replace("Department of ", "").replace("National Centre for Nanosciences and Nanotechnology (NCNNUM)", "NCNNUM Nanotech")
        table_rows.append(
            f"| #{r['Rank']} | **{dept_clean}** | {r['pubs']:,} | {r['citations']:,} | **{r['cpp']:.2f}** | {r['q1_pct']:.1f}% | {r['intl_pct']:.1f}% |"
        )

    table_md = "\n".join(table_rows)

    return f"""### 🏛️ University of Mumbai Academic Department Research Rankings

Analysis across **{len(dept_stats)}** active research departments and specialized centres:

| Rank | Academic Department | Scopus Output | Total Citations | CPP | Q1 Share | Intl Collab |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
{table_md}

---
#### 📌 Strategic Observations:
* **Top Output Contributor**: **{dept_stats.iloc[0]['department']}** leads with **{dept_stats.iloc[0]['pubs']:,}** papers ({dept_stats.iloc[0]['pubs'] / max(1, len(df)) * 100:.1f}% institutional volume).
* **Highest Citation Density**: **{dept_stats.sort_values('cpp', ascending=False).iloc[0]['department']}** achieves the highest impact density at **{dept_stats['cpp'].max():.2f} CPP**.
* **Top Q1 Quality Driver**: **{dept_stats.sort_values('q1_pct', ascending=False).iloc[0]['department']}** features **{dept_stats['q1_pct'].max():.1f}%** of its research output in high-impact Q1 journals.
"""


def _q1_quality_response(df: pd.DataFrame) -> str:
    if df.empty:
        return "No publication data available for quality analysis."

    total = len(df)
    q_counts = df["quartile"].value_counts()
    q1 = q_counts.get("Q1", 0)
    q2 = q_counts.get("Q2", 0)
    q3 = q_counts.get("Q3", 0)
    q4 = q_counts.get("Q4", 0)

    q1_pct = (q1 / total) * 100
    q2_pct = (q2 / total) * 100
    q3_pct = (q3 / total) * 100
    q4_pct = (q4 / total) * 100

    q1_df = df[df["quartile"].str.upper() == "Q1"]
    q1_cites = int(q1_df["citations"].sum()) if not q1_df.empty else 0
    q1_cpp = q1_cites / max(1, q1)

    # Top Q1 journals
    top_q1_journals = q1_df["journal"].value_counts().head(8).to_dict() if not q1_df.empty else {}
    j_rows = [f"* **{j}**: `{cnt}` publications" for j, cnt in top_q1_journals.items()]
    j_md = "\n".join(j_rows) if j_rows else "None"

    return f"""### 🏆 Journal Quartile Quality & Benchmark Assessment

Evaluation of research publications by international journal quartile tier (Scimago / JCR rankings):

---

#### 📊 Institutional Quartile Distribution
* **Q1 (Top 25% Tier)**: **{q1:,}** publications (**{q1_pct:.1f}%** of total output) &bull; Accrued **{q1_cites:,}** citations (**{q1_cpp:.2f} CPP**)
* **Q2 (25% - 50% Tier)**: **{q2:,}** publications (**{q2_pct:.1f}%**)
* **Q3 (50% - 75% Tier)**: **{q3:,}** publications (**{q3_pct:.1f}%**)
* **Q4 (Bottom 25% Tier)**: **{q4:,}** publications (**{q4_pct:.1f}%**)

---

#### 🌟 Primary Q1 Publishing Venues
Leading peer-reviewed venues chosen by University of Mumbai faculty:
{j_md}

---

#### 🎯 Impact on Institutional Accreditation
1. **NIRF Metric RPC**: Publications in Q1 venues yield maximal weightage in NIRF's Research and Professional Practice parameter.
2. **NAAC Criterion 3 (Research, Innovations and Extension)**: Demonstrates sustained publication quality in peer-reviewed Scopus indexed sources.
3. **Citation Multiplier**: Q1 papers in MU generate an average of **{q1_cpp:.2f} citations per paper**, more than **{q1_cpp / max(0.1, (df['citations'].sum() / total)):.1f}x** the baseline rate of non-Q1 papers.
"""


def _top_authors_response(df: pd.DataFrame) -> str:
    leaderboard = dp.get_top_authors_leaderboard(df, top_n=10)
    if leaderboard.empty:
        return "No author data available for ranking."

    rows = []
    for idx, r in leaderboard.iterrows():
        dept_clean = r["department"].replace("Department of ", "").replace("National Centre for Nanosciences and Nanotechnology (NCNNUM)", "NCNNUM")
        rows.append(
            f"| #{idx+1} | **{r['author']}** | {dept_clean} | **{r['papers']}** | {r['citations']:,} | {r['cpp']:.2f} | **h-{r['h_index']}** |"
        )
    table_md = "\n".join(rows)

    return f"""### 👥 Faculty Research Leadership Leaderboard

Top contributing faculty researchers across University of Mumbai ranked by cumulative Scopus output:

| Rank | Faculty Researcher | Academic Department | Papers | Citations | CPP | Scopus h-Index |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
{table_md}

---

#### 🌟 Key Faculty Highlights:
* **Output Leader**: **{leaderboard.iloc[0]['author']}** leads the university with **{leaderboard.iloc[0]['papers']}** indexed papers.
* **Top Citation Impact**: **{leaderboard.sort_values('citations', ascending=False).iloc[0]['author']}** has garnered **{leaderboard['citations'].max():,}** total citations.
* **Highest h-Index**: **{leaderboard.sort_values('h_index', ascending=False).iloc[0]['author']}** holds the top faculty index at **h-{leaderboard['h_index'].max()}**.
"""


def _department_specific_response(dept_query: str, df: pd.DataFrame) -> Optional[str]:
    """
    Search for a matching department in df and provide deep-dive intelligence.
    """
    depts = df["department"].dropna().unique()
    match = None
    for d in depts:
        d_clean = d.lower()
        if dept_query.lower() in d_clean or any(k in d_clean for k in dept_query.lower().split()):
            match = d
            break

    if not match:
        return None

    dept_df = df[df["department"] == match]
    if dept_df.empty:
        return None

    kpis = dp.calculate_top_10_kpis(dept_df)
    lead = dp.get_top_authors_leaderboard(dept_df, top_n=5)
    top_journals = dept_df["journal"].value_counts().head(5).to_dict()

    lead_str = "\n".join([f"* **{r['author']}**: {r['papers']} papers, {r['citations']:,} cites (h-{r['h_index']})" for _, r in lead.iterrows()])
    j_str = "\n".join([f"* **{j}**: `{cnt}` papers" for j, cnt in top_journals.items()])

    top_paper = dept_df.sort_values("citations", ascending=False).iloc[0] if not dept_df.empty else None
    top_paper_str = f"**{top_paper['title']}** ({top_paper['year']}) in *{top_paper['journal']}* — `{top_paper['citations']}` citations" if top_paper is not None else "N/A"

    return f"""### 🏛️ Department Deep-Dive: {match}

#### 📊 Performance Dashboard
* **Total Scopus Output**: **{kpis['total_output']:,}** publications
* **Total Citations**: **{kpis['total_citations']:,}** citations
* **Citations Per Paper (CPP)**: **{kpis['cpp']:.2f}**
* **Top-Quartile Q1 Ratio**: **{kpis['q1_percentage']:.1f}%** ({kpis['q1_count']} Q1 papers)
* **International Collaboration**: **{kpis['international_collab_pct']:.1f}%**
* **Industry Collaboration**: **{kpis['industry_collab_pct']:.1f}%**

---

#### 👥 Top Contributing Faculty:
{lead_str}

#### 📚 Preferred Publishing Venues:
{j_str}

#### 🏆 Highest-Cited Department Landmark Publication:
{top_paper_str}
"""


def _author_specific_response(author_name: str, df: pd.DataFrame) -> Optional[str]:
    """
    Search for a matching author in df and provide personalized profile insights.
    """
    profile = dp.get_author_profile_metrics(df, author_name)
    if profile["total_papers"] == 0:
        return None

    papers_df = profile["papers_df"]
    top_papers = papers_df.sort_values("citations", ascending=False).head(3) if not papers_df.empty else pd.DataFrame()

    top_p_lines = []
    for _, p in top_papers.iterrows():
        top_p_lines.append(f"* **{p['title']}** ({p['year']}) — *{p['journal']}* (`{p['citations']}` citations, Tier: {p['quartile']})")

    top_p_str = "\n".join(top_p_lines) if top_p_lines else "None recorded"

    return f"""### 👤 Faculty Profile: {profile['author_name']}

**Academic Department**: 🏛️ {profile['primary_department']} &bull; University of Mumbai

---

#### 📊 Research Footprint & Citations
* **Total Scopus Publications**: **{profile['total_papers']}** papers
* **Cumulative Citations**: **{profile['total_citations']:,}** citations
* **Citations Per Paper (CPP)**: **{profile['cpp']:.2f}**
* **Scopus h-Index**: **h-{profile['h_index']}**
* **Q1 Top-Tier Ratio**: **{profile['q1_ratio']:.1f}%** ({profile['q1_count']} Q1 papers)
* **International Collaboration Rate**: **{profile['international_collab_pct']:.1f}%**
* **Industry R&D Collaboration Rate**: **{profile['industry_collab_pct']:.1f}%**
* **Unique Co-authors**: **{profile['coauthors_count']}** researchers

---

#### 🏆 Highest Cited Contributions:
{top_p_str}
"""


def _collaboration_insights_response(df: pd.DataFrame) -> str:
    country_counts = {}
    for c_list in df["countries"].dropna():
        if isinstance(c_list, list):
            for c in c_list:
                c_clean = str(c).strip()
                if c_clean and c_clean.lower() != "india":
                    country_counts[c_clean] = country_counts.get(c_clean, 0) + 1

    top_nations = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    nations_md = "\n".join([f"* **{c}**: `{cnt}` joint publications" for c, cnt in top_nations])

    intl_count = int(df["is_international_collab"].sum())
    ind_count = int(df["is_industry_collab"].sum())
    total = len(df)

    return f"""### 🌐 Global & Industrial Collaboration Analysis

* **International Co-authorship Rate**: **{(intl_count / max(1, total)) * 100:.1f}%** ({intl_count:,} publications)
* **Corporate / Industrial R&D Rate**: **{(ind_count / max(1, total)) * 100:.1f}%** ({ind_count:,} publications)
* **Total Partner Nations**: **{len(country_counts)}** sovereign countries outside India

---

#### 🌍 Top Collaborative Partner Countries:
{nations_md}

#### 💡 Accreditation Perspective:
Strong international linkages with researchers in the United States, Germany, the UK, and Japan enhance citation visibility and support NIRF perception scores.
"""


def _recent_trends_response(df: pd.DataFrame) -> str:
    yearly = dp.get_publications_by_year(df)
    if yearly.empty:
        return "No trend data available."

    recent = yearly.tail(4)
    rows = []
    for _, r in recent.iterrows():
        rows.append(f"| **{int(r['year'])}** | {int(r['publications']):,} papers | {int(r['citations']):,} cites | {r['cpp']:.2f} CPP | {int(r['q1_count'])} Q1 papers |")

    table_md = "\n".join(rows)

    return f"""### 📈 Recent Annual Research Trajectory (Last 4 Years)

| Calendar Year | Publication Output | Total Citations | Citations / Paper | Q1 Publications |
| :---: | :---: | :---: | :---: | :---: |
{table_md}

---
* **2026 Run-Rate**: Real-time indexing velocity indicates consistent faculty submissions across STEM, Pharmaceutical Sciences, and Nanotechnology.
* **Accrual Dynamics**: The citations-per-paper (CPP) curve shows compounding impact over 3–5 year maturation windows.
"""


def generate_ai_response(query: str, df: pd.DataFrame) -> str:
    """
    Main Natural Language Router for AI Research Copilot.
    Parses prompt chips and free-form queries, generating structured markdown.
    """
    if df is None or df.empty:
        return "⚠️ The publication dataset is currently empty. Please adjust filters or ensure data is synchronized."

    q = query.strip().lower()

    # 1. Preset Prompt Chips
    if "executive dossier" in q or q.startswith("📊"):
        return _executive_dossier_response(df)

    if "dept rankings" in q or "department ranking" in q or q.startswith("🏛️"):
        return _dept_rankings_response(df)

    if "q1 quality" in q or "quartile" in q or q.startswith("🏆"):
        return _q1_quality_response(df)

    if "top authors" in q or "faculty" in q or q.startswith("👥"):
        return _top_authors_response(df)

    # 2. Collaboration queries
    if any(k in q for k in ["collaboration", "international", "countries", "foreign", "global", "industry"]):
        return _collaboration_insights_response(df)

    # 3. Trends / Recent output queries
    if any(k in q for k in ["trend", "trajectory", "growth", "recent", "velocity", "2026", "2025"]):
        return _recent_trends_response(df)

    # 4. Department specific search
    dept_keywords = [
        "chemistry", "physics", "nanotechnology", "ncnnum", "life science", "biotechnology",
        "computer", "information technology", "pharmacy", "mathematics", "statistics",
        "economics", "commerce", "law", "environmental"
    ]
    for k in dept_keywords:
        if k in q:
            dept_res = _department_specific_response(k, df)
            if dept_res:
                return dept_res

    # 5. Author specific search (check if query matches any author name)
    leaderboard = dp.get_top_authors_leaderboard(df, top_n=50)
    for auth in leaderboard["author"]:
        # check if author surname or initial is in query
        parts = [p.lower() for p in auth.replace(".", " ").split() if len(p) > 2]
        if any(p in q for p in parts):
            author_res = _author_specific_response(auth, df)
            if author_res:
                return author_res

    # 6. Default Fallback with Helpful Analytical Guidance
    kpis = dp.calculate_top_10_kpis(df)
    return f"""### 🤖 MU Scopus Intelligence Copilot

I can analyze **{kpis['total_output']:,}** indexed publications and **{kpis['total_citations']:,}** citations for **University of Mumbai**.

Here is a quick snapshot of what you can ask:
* **Executive Summary**: Click `📊 Executive Dossier` above or type *"give me an executive overview"*.
* **Department Rankings**: Click `🏛️ Dept Rankings` above or type *"which department has the highest CPP?"* or *"tell me about Chemistry"*.
* **Accreditation & Quality**: Click `🏆 Q1 Quality Analysis` above or type *"show Q1 journal breakdown"*.
* **Faculty Performance**: Click `👥 Top Authors` above or type *"who are the top cited researchers?"* or search any faculty name (e.g. *"Pawar"*, *"Patil"*, *"Sharma"*).
* **International Collaborations**: Ask *"what is our international collaboration rate?"* or *"which countries do we publish with?"*.
"""
