"""
scopus_api.py
Elsevier Scopus Search API Integration and Cache Management Module
for University of Mumbai (MU).

Features:
- Connects to Elsevier Scopus Search API using multi-variant query.
- Implements cursor pagination (cursor=*) with automatic fallback to offset pagination.
- Extracts comprehensive bibliometric fields: title, authors, primary_author, department,
  journal, year, citations, citescore, sjr, quartile (Q1-Q4), doi, scopus_id,
  is_international_collab, is_industry_collab, countries.
- Caches data to data/mu_scopus_cache.json with timestamp and source metadata.
- Auto-sync mechanism: checks cache age against 3600s TTL, supporting background
  refresh and manual force refresh.
- Offline fallback to mock_data.py benchmark dataset when offline or rate-limited.
"""

import os
import json
import time
import math
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import requests
from dotenv import load_dotenv

from config import UNIVERSITY_CONFIG
import mock_data

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Constants and Configurations
SCOPUS_SEARCH_ENDPOINT = "https://api.elsevier.com/content/search/scopus"
DEFAULT_CACHE_FILE = UNIVERSITY_CONFIG.get("cache_file", "data/mu_scopus_cache.json")
DEFAULT_CACHE_TTL = UNIVERSITY_CONFIG.get("cache_ttl_seconds", 3600)
DEFAULT_QUERY = UNIVERSITY_CONFIG.get(
    "scopus_query",
    "AF-ID(60028245) OR AFFIL({University of Mumbai}) OR AFFIL({University of Bombay}) OR AFFIL({Mumbai University}) OR AFFIL({MU Mumbai})"
)

# Threading lock and state for background sync
_sync_lock = threading.Lock()
_sync_state = {
    "is_syncing": False,
    "last_sync_time": None,
    "last_status": "Idle",
    "last_error": None,
    "total_records": 0,
    "source": None
}

# Journal metrics catalog for CiteScore, SJR, and Quartiles
JOURNAL_METRICS_MAP = {
    "acs nano": {"citescore": 27.5, "sjr": 5.12, "quartile": "Q1"},
    "biotechnology advances": {"citescore": 26.2, "sjr": 4.20, "quartile": "Q1"},
    "ieee transactions on neural networks and learning systems": {"citescore": 22.4, "sjr": 3.85, "quartile": "Q1"},
    "environmental science & technology": {"citescore": 20.4, "sjr": 3.12, "quartile": "Q1"},
    "ieee internet of things journal": {"citescore": 20.1, "sjr": 3.42, "quartile": "Q1"},
    "bioresource technology": {"citescore": 19.8, "sjr": 2.95, "quartile": "Q1"},
    "technological forecasting and social change": {"citescore": 18.9, "sjr": 2.80, "quartile": "Q1"},
    "journal of materials chemistry a": {"citescore": 18.2, "sjr": 2.85, "quartile": "Q1"},
    "science of the total environment": {"citescore": 17.5, "sjr": 2.25, "quartile": "Q1"},
    "acs applied materials & interfaces": {"citescore": 16.5, "sjr": 2.45, "quartile": "Q1"},
    "energy economics": {"citescore": 16.5, "sjr": 2.85, "quartile": "Q1"},
    "journal of business research": {"citescore": 16.2, "sjr": 2.45, "quartile": "Q1"},
    "expert systems with applications": {"citescore": 15.6, "sjr": 2.10, "quartile": "Q1"},
    "sensors and actuators b: chemical": {"citescore": 14.8, "sjr": 2.05, "quartile": "Q1"},
    "environmental pollution": {"citescore": 14.2, "sjr": 1.85, "quartile": "Q1"},
    "international journal of biological macromolecules": {"citescore": 13.4, "sjr": 1.68, "quartile": "Q1"},
    "nanoscale": {"citescore": 12.1, "sjr": 1.95, "quartile": "Q1"},
    "biomedicine & pharmacotherapy": {"citescore": 12.0, "sjr": 1.65, "quartile": "Q1"},
    "world development": {"citescore": 11.8, "sjr": 2.65, "quartile": "Q1"},
    "european journal of medicinal chemistry": {"citescore": 11.5, "sjr": 1.78, "quartile": "Q1"},
    "applied surface science": {"citescore": 11.2, "sjr": 1.55, "quartile": "Q1"},
    "computers & security": {"citescore": 11.2, "sjr": 1.62, "quartile": "Q1"},
    "marine pollution bulletin": {"citescore": 10.5, "sjr": 1.35, "quartile": "Q2"},
    "chemical communications": {"citescore": 10.4, "sjr": 1.75, "quartile": "Q1"},
    "pattern recognition letters": {"citescore": 9.8, "sjr": 1.25, "quartile": "Q2"},
    "journal of drug delivery science and technology": {"citescore": 9.2, "sjr": 1.18, "quartile": "Q1"},
    "materials research bulletin": {"citescore": 8.9, "sjr": 1.15, "quartile": "Q2"},
    "journal of the royal statistical society: series b": {"citescore": 8.5, "sjr": 2.95, "quartile": "Q1"},
    "frontiers in microbiology": {"citescore": 8.5, "sjr": 1.42, "quartile": "Q1"},
    "international journal of bank marketing": {"citescore": 8.4, "sjr": 1.15, "quartile": "Q2"},
    "environmental science and pollution research": {"citescore": 8.1, "sjr": 0.92, "quartile": "Q2"},
    "applied mathematics and computation": {"citescore": 7.9, "sjr": 1.15, "quartile": "Q1"},
    "scientific reports": {"citescore": 7.5, "sjr": 1.15, "quartile": "Q1"},
    "physical review b": {"citescore": 7.4, "sjr": 1.62, "quartile": "Q1"},
    "applied physics letters": {"citescore": 7.1, "sjr": 1.48, "quartile": "Q1"},
    "rsc advances": {"citescore": 6.8, "sjr": 0.85, "quartile": "Q2"},
    "multimedia tools and applications": {"citescore": 6.7, "sjr": 0.82, "quartile": "Q2"},
    "journal of supercomputing": {"citescore": 6.3, "sjr": 0.79, "quartile": "Q2"},
    "plos one": {"citescore": 6.2, "sjr": 0.95, "quartile": "Q1"},
    "bmc oral health": {"citescore": 4.5, "sjr": 0.72, "quartile": "Q2"},
    "biocatalysis and agricultural biotechnology": {"citescore": 6.0, "sjr": 0.78, "quartile": "Q2"},
    "cluster computing": {"citescore": 5.9, "sjr": 0.71, "quartile": "Q2"},
    "applied biochemistry and biotechnology": {"citescore": 5.8, "sjr": 0.72, "quartile": "Q2"},
    "heliyon": {"citescore": 5.6, "sjr": 0.68, "quartile": "Q2"},
    "journal of applied physics": {"citescore": 5.5, "sjr": 0.82, "quartile": "Q2"},
    "radiation physics and chemistry": {"citescore": 5.4, "sjr": 0.74, "quartile": "Q2"},
    "computer law & security review": {"citescore": 5.4, "sjr": 0.95, "quartile": "Q1"},
    "inorganica chimica acta": {"citescore": 5.2, "sjr": 0.65, "quartile": "Q2"},
    "journal of mathematical analysis and applications": {"citescore": 5.1, "sjr": 0.88, "quartile": "Q1"},
    "biotechnology reports": {"citescore": 5.1, "sjr": 0.59, "quartile": "Q3"},
    "journal of pharmacy and pharmacology": {"citescore": 5.0, "sjr": 0.72, "quartile": "Q2"},
    "journal of genetic engineering and biotechnology": {"citescore": 4.9, "sjr": 0.64, "quartile": "Q2"},
    "computational statistics & data analysis": {"citescore": 4.8, "sjr": 0.94, "quartile": "Q2"},
    "journal of molecular structure": {"citescore": 4.8, "sjr": 0.58, "quartile": "Q3"},
    "physica b: condensed matter": {"citescore": 4.6, "sjr": 0.55, "quartile": "Q3"},
    "journal of nanoparticle research": {"citescore": 4.5, "sjr": 0.62, "quartile": "Q2"},
    "global business review": {"citescore": 4.1, "sjr": 0.54, "quartile": "Q3"},
    "current microbiology": {"citescore": 4.1, "sjr": 0.52, "quartile": "Q3"},
    "wireless personal communications": {"citescore": 3.9, "sjr": 0.46, "quartile": "Q3"},
    "journal of intelligent & fuzzy systems": {"citescore": 3.8, "sjr": 0.48, "quartile": "Q3"},
    "linear algebra and its applications": {"citescore": 3.8, "sjr": 0.76, "quartile": "Q2"},
    "international journal of law and management": {"citescore": 3.2, "sjr": 0.55, "quartile": "Q2"},
    "journal of statistical planning and inference": {"citescore": 3.2, "sjr": 0.65, "quartile": "Q2"},
    "applied economics letters": {"citescore": 2.8, "sjr": 0.42, "quartile": "Q3"},
    "economic and political weekly": {"citescore": 2.2, "sjr": 0.48, "quartile": "Q2"},
    "current science": {"citescore": 2.1, "sjr": 0.35, "quartile": "Q3"},
    "differential equations and dynamical systems": {"citescore": 2.1, "sjr": 0.38, "quartile": "Q3"},
    "communications in statistics - theory and methods": {"citescore": 1.9, "sjr": 0.35, "quartile": "Q3"},
    "indian journal of pharmaceutical sciences": {"citescore": 1.8, "sjr": 0.28, "quartile": "Q3"},
    "asian journal of comparative law": {"citescore": 1.6, "sjr": 0.32, "quartile": "Q3"},
    "asian journal of chemistry": {"citescore": 1.2, "sjr": 0.22, "quartile": "Q4"},
    "journal of intellectual property rights": {"citescore": 0.9, "sjr": 0.21, "quartile": "Q4"}
}


def get_scopus_api_key() -> str:
    """
    Retrieve and sanitize Scopus API Key from environment.
    Strips brackets, spaces, and quotes.
    """
    key = os.getenv("SCOPUS_API_KEY", "")
    return key.strip(" []\"'")


def _infer_department(title: str, journal: str, affil_text: str) -> str:
    """
    Infers the most appropriate academic department at University of Mumbai
    based on publication title, journal name, and affiliation string.
    """
    content = f"{title} {journal} {affil_text}".lower()

    if any(k in content for k in ["nanoparticle", "nanomaterial", "nanocomposite", "nanosheet", "nanotube", "nanoscale", "nanotech"]):
        return "National Centre for Nanosciences and Nanotechnology (NCNNUM)"
    if any(k in content for k in ["synthesis", "cataly", "spectroscop", "polymer", "inorganic", "organic chem", "coordination", "crystal structure", "chemical"]):
        return "Department of Chemistry"
    if any(k in content for k in ["ferrite", "magnetic", "dielectric", "thin film", "superconduct", "physic", "band gap", "semiconductor", "plasma", "optical"]):
        return "Department of Physics"
    if any(k in content for k in ["drug", "delivery", "pharmac", "formulation", "docking", "dosage", "tablet", "in vitro", "bioavailability"]):
        return "Department of Pharmaceutical Sciences"
    if any(k in content for k in ["neural network", "machine learning", "deep learning", "artificial intelligence", "algorithm", "blockchain", "cloud", "security", "software", "pattern recognition"]):
        return "Department of Computer Science"
    if any(k in content for k in ["iot", "wireless", "routing", "network", "edge computing", "cyber", "internet of things", "sensor node"]):
        return "Department of Information Technology"
    if any(k in content for k in ["bioethanol", "bioprocess", "fermentation", "crispr", "enzyme", "biomass", "recombinant", "biotech"]):
        return "Department of Biotechnology"
    if any(k in content for k in ["microb", "antimicrobial", "bacteria", "marine", "algae", "fauna", "flora", "cell", "protein", "dna", "plant", "life science"]):
        return "Department of Life Sciences"
    if any(k in content for k in ["differential equation", "algebra", "numerical", "topology", "manifold", "mathemat"]):
        return "Department of Mathematics"
    if any(k in content for k in ["bayesian", "stochastic", "estimation", "statistical", "regression", "time series", "sampling"]):
        return "Department of Statistics"
    if any(k in content for k in ["pollution", "wastewater", "microplastic", "heavy metal", "air quality", "climate change", "ecology", "environment"]):
        return "Department of Environmental Sciences"
    if any(k in content for k in ["economic", "monetary", "fiscal", "inflation", "gdp", "trade", "poverty", "policy", "welfare"]):
        return "Mumbai School of Economics and Public Policy"
    if any(k in content for k in ["finance", "banking", "esg", "marketing", "consumer", "corporate", "supply chain", "commerce"]):
        return "Department of Commerce & Management Studies"
    if any(k in content for k in ["law", "legal", "court", "jurisprudence", "intellectual property", "patent", "human rights", "constitution"]):
        return "Department of Law"

    return "Department of Chemistry"


def _estimate_metrics(journal: str, citations: int, year: int) -> Tuple[float, float, str]:
    """
    Look up or calculate CiteScore, SJR, and Quartile for a given journal.
    """
    j_clean = journal.strip().lower()
    if j_clean in JOURNAL_METRICS_MAP:
        m = JOURNAL_METRICS_MAP[j_clean]
        return m["citescore"], m["sjr"], m["quartile"]

    # Fuzzy match lookup
    for j_key, m in JOURNAL_METRICS_MAP.items():
        if j_key in j_clean or j_clean in j_key:
            return m["citescore"], m["sjr"], m["quartile"]

    # Dynamic estimation heuristic based on accumulated citations and paper age
    years_active = max(1, 2026 - year + 1)
    annual_rate = citations / years_active

    if annual_rate >= 8.0:
        citescore = round(min(25.0, 10.0 + annual_rate * 0.8), 1)
        sjr = round(min(4.5, 1.8 + annual_rate * 0.12), 2)
        quartile = "Q1"
    elif annual_rate >= 3.0:
        citescore = round(min(10.0, 5.0 + annual_rate * 0.7), 1)
        sjr = round(min(1.8, 0.9 + annual_rate * 0.08), 2)
        quartile = "Q1" if citescore >= 7.0 else "Q2"
    elif annual_rate >= 1.0:
        citescore = round(min(5.0, 2.5 + annual_rate * 0.6), 1)
        sjr = round(min(0.9, 0.5 + annual_rate * 0.06), 2)
        quartile = "Q2" if citescore >= 4.0 else "Q3"
    else:
        citescore = round(max(0.8, 1.5 + annual_rate * 0.5), 1)
        sjr = round(max(0.18, 0.3 + annual_rate * 0.05), 2)
        quartile = "Q3" if citescore >= 2.0 else "Q4"

    return citescore, sjr, quartile


def _parse_scopus_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize all required bibliometric fields from a single Scopus API entry.
    """
    title = entry.get("dc:title") or "Untitled Document"
    primary_author = entry.get("dc:creator") or "Unknown Author"

    # Authors list representation
    authors_data = entry.get("author", [])
    if isinstance(authors_data, list) and len(authors_data) > 0:
        authors_names = []
        for a in authors_data:
            name = a.get("authname") or f"{a.get('surname', '')} {a.get('given-name', '')}".strip()
            if name:
                authors_names.append(name)
        authors_str = ", ".join(authors_names) if authors_names else primary_author
    else:
        authors_str = primary_author

    journal = entry.get("prism:publicationName") or "Academic Source"

    # Year extraction
    cover_date = entry.get("prism:coverDate") or ""
    try:
        year = int(cover_date.split("-")[0]) if "-" in cover_date else int(cover_date)
    except (ValueError, IndexError):
        try:
            year = int(entry.get("prism:coverDisplayDate", "2024")[-4:])
        except Exception:
            year = 2024

    # Citations
    try:
        citations = int(entry.get("citedby-count", 0))
    except (ValueError, TypeError):
        citations = 0

    # Scopus ID & DOI
    raw_id = entry.get("dc:identifier") or entry.get("eid") or ""
    scopus_id = raw_id.replace("SCOPUS_ID:", "").strip()
    doi = entry.get("prism:doi") or ""

    # Affiliations & Collaborations
    raw_affil = entry.get("affiliation", [])
    if isinstance(raw_affil, dict):
        raw_affil = [raw_affil]

    countries = []
    affil_names = []
    for aff in raw_affil:
        c = aff.get("affiliation-country")
        if c and c not in countries:
            countries.append(c)
        name = aff.get("affilname")
        if name:
            affil_names.append(name)

    if not countries:
        countries = ["India"]

    # International collaboration check
    is_international = any(c.strip().lower() != "india" for c in countries)

    # Industry collaboration check
    industry_keywords = [
        "ltd", "limited", "pvt", "inc", "corp", "corporation", "pharma",
        "laboratories", "industries", "research centre", "r&d", "solutions"
    ]
    affil_text = " ".join(affil_names).lower()
    is_industry = any(k in affil_text for k in industry_keywords)

    # Department classification
    department = _infer_department(title, journal, affil_text)

    # Journal metrics
    citescore, sjr, quartile = _estimate_metrics(journal, citations, year)

    return {
        "title": title,
        "authors": authors_str,
        "primary_author": primary_author,
        "department": department,
        "journal": journal,
        "year": year,
        "citations": citations,
        "citescore": citescore,
        "sjr": sjr,
        "quartile": quartile,
        "doi": doi,
        "scopus_id": scopus_id,
        "is_international_collab": is_international,
        "is_industry_collab": is_industry,
        "countries": countries
    }


def fetch_scopus_data_from_api(
    query: str = DEFAULT_QUERY,
    max_records: Optional[int] = None,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query Elsevier Scopus Search API using multi-variant query.
    Attempts cursor pagination (cursor=*).
    If cursor pagination is prohibited by key tier (403), gracefully falls back
    to standard offset pagination.
    """
    key = api_key or get_scopus_api_key()
    if not key:
        logger.warning("No SCOPUS_API_KEY found in environment. Falling back to offline benchmark generator.")
        return mock_data.generate_mock_publications(count=max_records or 2500)

    headers = {
        "X-ELS-APIKey": key,
        "Accept": "application/json",
        "User-Agent": "UniversityOfMumbaiScopusDashboard/1.0"
    }

    publications = []
    use_cursor = True
    cursor = "*"
    start_offset = 0
    page_size = 25  # Standard Elsevier limit per search request

    logger.info("Connecting to Elsevier Scopus Search API...")
    logger.info(f"Query: {query}")

    while True:
        params: Dict[str, Any] = {
            "query": query,
            "count": page_size
        }

        if use_cursor:
            params["cursor"] = cursor
        else:
            params["start"] = start_offset

        try:
            resp = requests.get(SCOPUS_SEARCH_ENDPOINT, headers=headers, params=params, timeout=20)

            # Handle cursor restriction (403)
            if resp.status_code == 403 and use_cursor:
                logger.info("Cursor pagination requires institutional entitlement (HTTP 403). Falling back to offset pagination.")
                use_cursor = False
                start_offset = 0
                continue

            if resp.status_code == 429:
                logger.warning("Scopus API rate limit encountered (HTTP 429). Stopping fetch.")
                break

            if resp.status_code != 200:
                logger.error(f"Scopus API HTTP Error {resp.status_code}: {resp.text[:200]}")
                break

            payload = resp.json()
            search_results = payload.get("search-results", {})
            total_available = int(search_results.get("opensearch:totalResults", 0))
            entries = search_results.get("entry", [])

            if not entries:
                logger.info("No further entries returned by Scopus API.")
                break

            for entry in entries:
                if "error" in entry:
                    continue
                parsed = _parse_scopus_entry(entry)
                publications.append(parsed)

                if max_records and len(publications) >= max_records:
                    break

            logger.info(f"Fetched {len(publications)} / {total_available} records...")

            if max_records and len(publications) >= max_records:
                break

            if use_cursor:
                # Obtain next cursor token
                cursor_info = search_results.get("cursor", {})
                next_cursor = cursor_info.get("@next")
                if not next_cursor or next_cursor == cursor:
                    # Check next link
                    links = search_results.get("link", [])
                    next_link = next((l.get("@href") for l in links if l.get("@ref") == "next"), None)
                    if not next_link:
                        break
                    cursor = next_cursor
                else:
                    cursor = next_cursor
            else:
                start_offset += page_size
                if start_offset >= total_available or start_offset >= 5000:
                    # Elsevier hard ceiling for offset pagination is 5,000
                    break

            time.sleep(0.15)  # Rate limiting courtesy pause

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while querying Scopus API: {e}")
            break

    logger.info(f"Scopus API fetch completed. Total records retrieved: {len(publications)}")
    return publications


def save_cache_to_file(
    records: List[Dict[str, Any]],
    cache_file: str = DEFAULT_CACHE_FILE,
    source: str = "Scopus Search API (Live)"
) -> None:
    """
    Save publications list to cache JSON file with timestamp metadata.
    """
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    cache_payload = {
        "timestamp": time.time(),
        "last_updated": datetime.now().isoformat(),
        "cache_ttl_seconds": DEFAULT_CACHE_TTL,
        "total_records": len(records),
        "source": source,
        "query": DEFAULT_QUERY,
        "data": records
    }
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache_payload, f, ensure_ascii=False, indent=2)
    logger.info(f"Cached {len(records)} records to '{cache_file}' (Source: {source})")


def read_cache_from_file(cache_file: str = DEFAULT_CACHE_FILE) -> Optional[Dict[str, Any]]:
    """
    Read cache JSON file and return metadata payload, or None if unavailable.
    """
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                return data
    except Exception as e:
        logger.warning(f"Error reading cache file '{cache_file}': {e}")
    return None


def is_cache_valid(cache_file: str = DEFAULT_CACHE_FILE, ttl_seconds: int = DEFAULT_CACHE_TTL) -> bool:
    """
    Check if the local cache is present and within the TTL (3600 seconds).
    """
    cache = read_cache_from_file(cache_file)
    if not cache:
        return False
    age = time.time() - cache.get("timestamp", 0)
    return age < ttl_seconds and len(cache.get("data", [])) > 0


def _background_sync_worker(cache_file: str, max_records: Optional[int]) -> None:
    """
    Background worker function executed in separate daemon thread.
    """
    global _sync_state
    with _sync_lock:
        _sync_state["is_syncing"] = True
        _sync_state["last_status"] = "Syncing with Scopus API in background..."
        _sync_state["last_error"] = None

    try:
        logger.info("[Background Sync] Starting background sync with Scopus API...")
        records = fetch_scopus_data_from_api(query=DEFAULT_QUERY, max_records=max_records)
        source = "Scopus Search API (Live Background Sync)"

        if not records:
            # Fallback to benchmark mock dataset if API was empty or limited
            logger.info("[Background Sync] API returned no records. Generating realistic benchmark dataset.")
            records = mock_data.generate_mock_publications(count=2500)
            source = "Benchmark Mock Dataset (Offline Fallback)"

        save_cache_to_file(records, cache_file=cache_file, source=source)

        with _sync_lock:
            _sync_state["is_syncing"] = False
            _sync_state["last_sync_time"] = datetime.now().isoformat()
            _sync_state["last_status"] = "Synchronized successfully"
            _sync_state["total_records"] = len(records)
            _sync_state["source"] = source

        logger.info(f"[Background Sync] Background sync finished successfully: {len(records)} records.")

    except Exception as e:
        logger.error(f"[Background Sync] Error during background sync: {e}")
        with _sync_lock:
            _sync_state["is_syncing"] = False
            _sync_state["last_status"] = "Sync failed"
            _sync_state["last_error"] = str(e)


def trigger_background_sync(cache_file: str = DEFAULT_CACHE_FILE, max_records: Optional[int] = None) -> bool:
    """
    Trigger automatic background synchronization thread if not already running.
    Returns True if thread was spawned, False if already syncing.
    """
    global _sync_state
    with _sync_lock:
        if _sync_state["is_syncing"]:
            logger.info("Background sync is already in progress. Skipping duplicate request.")
            return False

    thread = threading.Thread(
        target=_background_sync_worker,
        args=(cache_file, max_records),
        daemon=True,
        name="ScopusSyncThread"
    )
    thread.start()
    return True


def get_sync_status() -> Dict[str, Any]:
    """
    Retrieve current background sync status metadata.
    """
    with _sync_lock:
        return dict(_sync_state)


def load_scopus_data(
    cache_file: str = DEFAULT_CACHE_FILE,
    force_refresh: bool = False,
    max_records: Optional[int] = None,
    allow_mock_fallback: bool = True
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Main entry point for loading University of Mumbai Scopus publication data.
    
    Auto-Sync Logic:
    1. If valid cache exists (< 3600s) and not force_refresh:
       Returns cached data immediately.
    2. If cache exists but is expired (> 3600s) and not force_refresh:
       Returns current cached data immediately to keep UI fast,
       and automatically spawns a background thread to sync fresh data.
    3. If cache does not exist or force_refresh is True:
       Fetches from Scopus API synchronously, saves to cache, and returns data.
       If API is unavailable/limited, falls back to realistic 2,500 mock benchmark.
       
    Returns:
        (publications_list, metadata_dict)
    """
    cache = read_cache_from_file(cache_file)
    cache_valid = is_cache_valid(cache_file, DEFAULT_CACHE_TTL)

    # 1. Valid and fresh cache
    if cache_valid and not force_refresh:
        logger.info(f"Loaded {len(cache['data'])} records from valid local cache.")
        return cache["data"], {
            "source": cache.get("source", "Local Cache"),
            "last_updated": cache.get("last_updated"),
            "is_fresh": True,
            "total_records": len(cache["data"])
        }

    # 2. Expired cache exists -> Return cached immediately and trigger background sync
    if cache and not force_refresh:
        age_minutes = round((time.time() - cache.get("timestamp", 0)) / 60, 1)
        logger.info(f"Local cache is stale ({age_minutes}m old > {DEFAULT_CACHE_TTL // 60}m). Launching background sync...")
        trigger_background_sync(cache_file=cache_file, max_records=max_records)
        return cache["data"], {
            "source": f"{cache.get('source', 'Local Cache')} (Stale - Syncing in background)",
            "last_updated": cache.get("last_updated"),
            "is_fresh": False,
            "total_records": len(cache["data"])
        }

    # 3. Synchronous fetch required (force_refresh=True or initial cold start without cache)
    logger.info("Executing synchronous fetch for University of Mumbai publications...")
    records = fetch_scopus_data_from_api(query=DEFAULT_QUERY, max_records=max_records)
    source = "Scopus Search API (Live Synchronous)"

    if not records and allow_mock_fallback:
        logger.info("API returned no records or offline. Generating 2,500 benchmark publications for MU.")
        records = mock_data.generate_mock_publications(count=max_records or 2500)
        source = "Benchmark Mock Dataset (Offline Initializer)"

    save_cache_to_file(records, cache_file=cache_file, source=source)

    metadata = {
        "source": source,
        "last_updated": datetime.now().isoformat(),
        "is_fresh": True,
        "total_records": len(records)
    }
    return records, metadata


if __name__ == "__main__":
    print("Testing scopus_api.py...")
    data, meta = load_scopus_data(max_records=100)
    print(f"Loaded {len(data)} records.")
    print(f"Metadata: {meta}")
    if data:
        print("Sample Record:")
        print(json.dumps(data[0], indent=2))
