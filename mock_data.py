"""
mock_data.py
Benchmark Publication Data Generator for University of Mumbai (MU).
Generates realistic publication datasets across academic departments for offline mode
and fallback operations.
"""

import random
import time
import uuid
import pandas as pd

# Departments active in research at University of Mumbai
MU_DEPARTMENTS = [
    "Department of Chemistry",
    "Department of Physics",
    "Department of Life Sciences",
    "Department of Biotechnology",
    "Department of Computer Science",
    "Department of Information Technology",
    "Department of Mathematics",
    "Department of Statistics",
    "National Centre for Nanosciences and Nanotechnology (NCNNUM)",
    "Department of Pharmaceutical Sciences",
    "Mumbai School of Economics and Public Policy",
    "Department of Commerce & Management Studies",
    "Department of Law",
    "Department of Environmental Sciences",
    "Department of Biophysics",
    "Department of Geography",
    "Department of Sociology"
]

# Faculty and researcher names representative of University of Mumbai
FIRST_NAMES = [
    "Rajesh", "Santosh", "Sneha", "Anuradha", "Amit", "Priya", "Sunil", "Pooja",
    "Nitin", "Vandana", "Mahesh", "Kavita", "Sanjay", "Deepak", "Asha", "Pradeep",
    "Shalini", "Sachin", "Meena", "Girish", "Manish", "Swati", "Ashok", "Neeta",
    "Milind", "Shubhangi", "Ramesh", "Chetan", "Archana", "Vijay", "Rohit", "Tanvi"
]

LAST_NAMES = [
    "Patil", "Deshmukh", "Kulkarni", "Sawant", "Joshi", "Sharma", "Mehta", "Fernandes",
    "Pawar", "Shinde", "Nair", "Merchant", "More", "Bhide", "Chavan", "Tendulkar",
    "Godbole", "Kamat", "Gaikwad", "Tambe", "Shetty", "Salunkhe", "Bapat", "Gore",
    "Kelkar", "Gokhale", "Bhat", "Rane", "Pandey", "Khan", "Chitale", "D'Souza"
]

# Journal catalog categorized by department domain with SJR, CiteScore, and Quartile
JOURNAL_CATALOG = {
    "Department of Chemistry": [
        {"journal": "Journal of Materials Chemistry A", "citescore": 18.2, "sjr": 2.85, "quartile": "Q1"},
        {"journal": "ACS Applied Materials & Interfaces", "citescore": 16.5, "sjr": 2.45, "quartile": "Q1"},
        {"journal": "Chemical Communications", "citescore": 10.4, "sjr": 1.75, "quartile": "Q1"},
        {"journal": "RSC Advances", "citescore": 6.8, "sjr": 0.85, "quartile": "Q2"},
        {"journal": "Inorganica Chimica Acta", "citescore": 5.2, "sjr": 0.65, "quartile": "Q2"},
        {"journal": "Journal of Molecular Structure", "citescore": 4.8, "sjr": 0.58, "quartile": "Q3"},
        {"journal": "Asian Journal of Chemistry", "citescore": 1.2, "sjr": 0.22, "quartile": "Q4"}
    ],
    "Department of Physics": [
        {"journal": "Physical Review B", "citescore": 7.4, "sjr": 1.62, "quartile": "Q1"},
        {"journal": "Applied Physics Letters", "citescore": 7.1, "sjr": 1.48, "quartile": "Q1"},
        {"journal": "Materials Research Bulletin", "citescore": 8.9, "sjr": 1.15, "quartile": "Q2"},
        {"journal": "Journal of Applied Physics", "citescore": 5.5, "sjr": 0.82, "quartile": "Q2"},
        {"journal": "Radiation Physics and Chemistry", "citescore": 5.4, "sjr": 0.74, "quartile": "Q2"},
        {"journal": "Physica B: Condensed Matter", "citescore": 4.6, "sjr": 0.55, "quartile": "Q3"}
    ],
    "National Centre for Nanosciences and Nanotechnology (NCNNUM)": [
        {"journal": "ACS Nano", "citescore": 27.5, "sjr": 5.12, "quartile": "Q1"},
        {"journal": "Nanoscale", "citescore": 12.1, "sjr": 1.95, "quartile": "Q1"},
        {"journal": "Sensors and Actuators B: Chemical", "citescore": 14.8, "sjr": 2.05, "quartile": "Q1"},
        {"journal": "Applied Surface Science", "citescore": 11.2, "sjr": 1.55, "quartile": "Q1"},
        {"journal": "Journal of Nanoparticle Research", "citescore": 4.5, "sjr": 0.62, "quartile": "Q2"}
    ],
    "Department of Life Sciences": [
        {"journal": "PLOS ONE", "citescore": 6.2, "sjr": 0.95, "quartile": "Q1"},
        {"journal": "International Journal of Biological Macromolecules", "citescore": 13.4, "sjr": 1.68, "quartile": "Q1"},
        {"journal": "Frontiers in Microbiology", "citescore": 8.5, "sjr": 1.42, "quartile": "Q1"},
        {"journal": "Biocatalysis and Agricultural Biotechnology", "citescore": 6.0, "sjr": 0.78, "quartile": "Q2"},
        {"journal": "Current Microbiology", "citescore": 4.1, "sjr": 0.52, "quartile": "Q3"}
    ],
    "Department of Biotechnology": [
        {"journal": "Bioresource Technology", "citescore": 19.8, "sjr": 2.95, "quartile": "Q1"},
        {"journal": "Biotechnology Advances", "citescore": 26.2, "sjr": 4.20, "quartile": "Q1"},
        {"journal": "Applied Biochemistry and Biotechnology", "citescore": 5.8, "sjr": 0.72, "quartile": "Q2"},
        {"journal": "Journal of Genetic Engineering and Biotechnology", "citescore": 4.9, "sjr": 0.64, "quartile": "Q2"},
        {"journal": "Biotechnology Reports", "citescore": 5.1, "sjr": 0.59, "quartile": "Q3"}
    ],
    "Department of Pharmaceutical Sciences": [
        {"journal": "European Journal of Medicinal Chemistry", "citescore": 11.5, "sjr": 1.78, "quartile": "Q1"},
        {"journal": "Biomedicine & Pharmacotherapy", "citescore": 12.0, "sjr": 1.65, "quartile": "Q1"},
        {"journal": "Journal of Drug Delivery Science and Technology", "citescore": 9.2, "sjr": 1.18, "quartile": "Q1"},
        {"journal": "Journal of Pharmacy and Pharmacology", "citescore": 5.0, "sjr": 0.72, "quartile": "Q2"},
        {"journal": "Indian Journal of Pharmaceutical Sciences", "citescore": 1.8, "sjr": 0.28, "quartile": "Q3"}
    ],
    "Department of Computer Science": [
        {"journal": "IEEE Transactions on Neural Networks and Learning Systems", "citescore": 22.4, "sjr": 3.85, "quartile": "Q1"},
        {"journal": "Expert Systems with Applications", "citescore": 15.6, "sjr": 2.10, "quartile": "Q1"},
        {"journal": "Pattern Recognition Letters", "citescore": 9.8, "sjr": 1.25, "quartile": "Q2"},
        {"journal": "Multimedia Tools and Applications", "citescore": 6.7, "sjr": 0.82, "quartile": "Q2"},
        {"journal": "Journal of Intelligent & Fuzzy Systems", "citescore": 3.8, "sjr": 0.48, "quartile": "Q3"}
    ],
    "Department of Information Technology": [
        {"journal": "IEEE Internet of Things Journal", "citescore": 20.1, "sjr": 3.42, "quartile": "Q1"},
        {"journal": "Computers & Security", "citescore": 11.2, "sjr": 1.62, "quartile": "Q1"},
        {"journal": "Journal of Supercomputing", "citescore": 6.3, "sjr": 0.79, "quartile": "Q2"},
        {"journal": "Cluster Computing", "citescore": 5.9, "sjr": 0.71, "quartile": "Q2"},
        {"journal": "Wireless Personal Communications", "citescore": 3.9, "sjr": 0.46, "quartile": "Q3"}
    ],
    "Department of Mathematics": [
        {"journal": "Applied Mathematics and Computation", "citescore": 7.9, "sjr": 1.15, "quartile": "Q1"},
        {"journal": "Journal of Mathematical Analysis and Applications", "citescore": 5.1, "sjr": 0.88, "quartile": "Q1"},
        {"journal": "Linear Algebra and its Applications", "citescore": 3.8, "sjr": 0.76, "quartile": "Q2"},
        {"journal": "Differential Equations and Dynamical Systems", "citescore": 2.1, "sjr": 0.38, "quartile": "Q3"}
    ],
    "Department of Statistics": [
        {"journal": "Journal of the Royal Statistical Society: Series B", "citescore": 8.5, "sjr": 2.95, "quartile": "Q1"},
        {"journal": "Computational Statistics & Data Analysis", "citescore": 4.8, "sjr": 0.94, "quartile": "Q2"},
        {"journal": "Journal of Statistical Planning and Inference", "citescore": 3.2, "sjr": 0.65, "quartile": "Q2"},
        {"journal": "Communications in Statistics - Theory and Methods", "citescore": 1.9, "sjr": 0.35, "quartile": "Q3"}
    ],
    "Mumbai School of Economics and Public Policy": [
        {"journal": "World Development", "citescore": 11.8, "sjr": 2.65, "quartile": "Q1"},
        {"journal": "Energy Economics", "citescore": 16.5, "sjr": 2.85, "quartile": "Q1"},
        {"journal": "Economic and Political Weekly", "citescore": 2.2, "sjr": 0.48, "quartile": "Q2"},
        {"journal": "Applied Economics Letters", "citescore": 2.8, "sjr": 0.42, "quartile": "Q3"}
    ],
    "Department of Commerce & Management Studies": [
        {"journal": "Journal of Business Research", "citescore": 16.2, "sjr": 2.45, "quartile": "Q1"},
        {"journal": "Technological Forecasting and Social Change", "citescore": 18.9, "sjr": 2.80, "quartile": "Q1"},
        {"journal": "International Journal of Bank Marketing", "citescore": 8.4, "sjr": 1.15, "quartile": "Q2"},
        {"journal": "Global Business Review", "citescore": 4.1, "sjr": 0.54, "quartile": "Q3"}
    ],
    "Department of Law": [
        {"journal": "Computer Law & Security Review", "citescore": 5.4, "sjr": 0.95, "quartile": "Q1"},
        {"journal": "International Journal of Law and Management", "citescore": 3.2, "sjr": 0.55, "quartile": "Q2"},
        {"journal": "Asian Journal of Comparative Law", "citescore": 1.6, "sjr": 0.32, "quartile": "Q3"},
        {"journal": "Journal of Intellectual Property Rights", "citescore": 0.9, "sjr": 0.21, "quartile": "Q4"}
    ],
    "Department of Environmental Sciences": [
        {"journal": "Environmental Science & Technology", "citescore": 20.4, "sjr": 3.12, "quartile": "Q1"},
        {"journal": "Science of The Total Environment", "citescore": 17.5, "sjr": 2.25, "quartile": "Q1"},
        {"journal": "Environmental Pollution", "citescore": 14.2, "sjr": 1.85, "quartile": "Q1"},
        {"journal": "Marine Pollution Bulletin", "citescore": 10.5, "sjr": 1.35, "quartile": "Q2"},
        {"journal": "Environmental Science and Pollution Research", "citescore": 8.1, "sjr": 0.92, "quartile": "Q2"}
    ]
}

# Generic fallback journals
GENERIC_JOURNALS = [
    {"journal": "PLOS ONE", "citescore": 6.2, "sjr": 0.95, "quartile": "Q1"},
    {"journal": "Scientific Reports", "citescore": 7.5, "sjr": 1.15, "quartile": "Q1"},
    {"journal": "Heliyon", "citescore": 5.6, "sjr": 0.68, "quartile": "Q2"},
    {"journal": "Current Science", "citescore": 2.1, "sjr": 0.35, "quartile": "Q3"}
]

# Topic templates mapped by department for realistic title generation
TITLE_TEMPLATES = {
    "Department of Chemistry": [
        "Synthesis, characterization, and catalytic efficiency of {chem_compound} nanoparticles in {reaction_type}",
        "Green synthesis of {nano_mat} using coastal flora of Mumbai for {app_type}",
        "Electrochemical sensing of {target_analyte} based on {chem_compound} modified glassy carbon electrodes",
        "Novel {chem_compound} complexes as potent antimicrobial and antioxidant agents: Design and DFT calculations",
        "Heterogeneous photocatalytic degradation of organic dyes using {nano_mat} under solar irradiation",
        "Development of porous metal-organic frameworks for selective carbon dioxide capture and sequestration"
    ],
    "Department of Physics": [
        "Structural, magnetic, and dielectric properties of substituted {physics_mat} ferrites synthesized via sol-gel method",
        "High-pressure Raman and XRD investigations on {physics_mat} multiferroic thin films",
        "Optical properties and band gap tuning of {nano_mat} for photovoltaic applications",
        "Investigation of transport mechanisms in flexible organic field-effect transistors",
        "Temperature-dependent thermoelectric power and electrical conductivity of {physics_mat} compounds",
        "Gamma radiation shielding capability of polymer composites reinforced with {physics_mat}"
    ],
    "National Centre for Nanosciences and Nanotechnology (NCNNUM)": [
        "Hierarchical 2D {nano_mat} heterostructures for high-performance supercapacitors and energy storage",
        "Microfluidic synthesis of targeted {nano_mat} for biomedical imaging and controlled drug delivery",
        "Surface plasmon resonance biosensors based on gold-{nano_mat} nanocomposites for early pathogen detection",
        "Engineering defective graphene-{nano_mat} interfaces for enhanced oxygen reduction reaction kinetics",
        "Flexible transparent conducting electrodes fabricated using hybrid silver nanowire-{nano_mat} meshes"
    ],
    "Department of Life Sciences": [
        "Metagenomic profiling of microbial diversity in the Arabian Sea along the Mumbai coastline",
        "Evaluation of bioactive phytochemicals from {plant_name} against multidrug-resistant clinical isolates",
        "Oxidative stress biomarkers and heavy metal bioaccumulation in marine benthic fauna of Thane Creek",
        "Therapeutic potential of marine bioactive peptides in downregulating inflammatory cytokines in vitro",
        "Comparative genomics of virulence factors in clinical Pseudomonas aeruginosa strains from Mumbai tertiary hospitals"
    ],
    "Department of Biotechnology": [
        "Optimization of bioethanol production from agricultural residues using immobilized {enzyme_type}",
        "CRISPR-Cas9 mediated transcriptional regulation of lipid biosynthetic pathways in oleaginous yeast",
        "Bioprocess scale-up for recombinant production of {biotech_protein} in Pichia pastoris",
        "Biosorption of heavy metals from industrial effluents using engineered bacterial biofilms",
        "Enhanced production of industrial enzymes via solid-state fermentation using lignocellulosic biomass"
    ],
    "Department of Pharmaceutical Sciences": [
        "Formulation and in-vitro evaluation of nano-lipid carriers for targeted delivery of {pharma_drug}",
        "Design, molecular docking, and pharmacokinetic evaluation of novel quinazoline derivatives as kinase inhibitors",
        "Development of gastroretentive floating drug delivery systems for sustained release of {pharma_drug}",
        "Topical polymeric nanogels for enhanced transdermal permeation: In vitro and ex vivo characterization",
        "Quality by Design (QbD) approach for analytical method validation of {pharma_drug} formulations"
    ],
    "Department of Computer Science": [
        "Deep transfer learning with convolutional neural networks for early diagnostic classification of {cs_domain}",
        "Hybrid attention-based Transformer models for Marathi-English multilingual sentiment analysis",
        "Blockchain-enabled decentralized framework for secure and verifiable academic credential verification",
        "Federated learning architecture for privacy-preserving disease prediction across distributed hospital nodes",
        "Real-time edge computing framework for urban traffic congestion monitoring in Greater Mumbai"
    ],
    "Department of Information Technology": [
        "Zero-trust authentication protocol for industrial IoT nodes against zero-day distributed attacks",
        "Reinforcement learning-based dynamic resource allocation in multi-tier 5G/6G edge networks",
        "Explainable AI framework for automated malware categorization in enterprise cyber systems",
        "Lightweight cryptographic primitive for ultra-constrained sensory devices in smart city deployments",
        "Deep autoencoder networks for anomaly detection in cloud computing microservice architectures"
    ],
    "Department of Mathematics": [
        "Existence and uniqueness of mild solutions for fractional differential equations with state-dependent delays",
        "Spectral properties and eigenvalues of adjacency matrices for generalized Cayley graphs",
        "Analytical solutions to Navier-Stokes equations under non-Newtonian boundary conditions",
        "Topological data analysis for pattern recognition in high-dimensional biological data spaces"
    ],
    "Department of Statistics": [
        "Bayesian inference for generalized Lindley distribution under progressive type-II censoring schemes",
        "Stochastic modeling and forecasting of extreme monsoon rainfall events in coastal Maharashtra",
        "Robust estimation of high-dimensional covariance matrices with heavy-tailed distributed outliers",
        "Survival analysis models with time-varying covariates in longitudinal clinical studies"
    ],
    "Mumbai School of Economics and Public Policy": [
        "Impact of digital payments and UPI penetration on informal sector productivity in Western Maharashtra",
        "Fiscal decentralization, municipal infrastructure finance, and urban growth in Mumbai Metropolitan Region",
        "Climate change vulnerability and adaptation strategies among coastal fishing communities of Konkan",
        "Evaluating the socioeconomic impact of PM-KISAN direct benefit transfers on smallholder farm households"
    ],
    "Department of Commerce & Management Studies": [
        "Determinants of ESG disclosure and its impact on corporate financial performance in BSE 500 firms",
        "Consumer adoption behavior of omni-channel retail platforms: An empirical study across urban demographics",
        "Fintech adoption, risk perception, and financial resilience among micro-enterprises in Maharashtra",
        "Sustainable supply chain practices and operational performance in pharmaceutical manufacturing clusters"
    ],
    "Department of Law": [
        "Regulatory challenges in artificial intelligence and algorithmic bias: Comparative analysis under Indian jurisprudence",
        "Data privacy governance post Digital Personal Data Protection Act 2023: Implications for cross-border data flows",
        "Intellectual property rights and public health flexibilities under TRIPS: An empirical evaluation",
        "Corporate criminal liability and environmental torts in coastal industrial zones of Maharashtra"
    ],
    "Department of Environmental Sciences": [
        "Assessment of microplastic contamination and chemical burden in coastal sediment and fish across Mumbai beaches",
        "Atmospheric particulate matter (PM2.5 and PM10) source apportionment using positive matrix factorization in Mumbai",
        "Eco-toxicological assessment of endocrine disrupting compounds in untreated municipal wastewater discharge",
        "Impact of sea-level rise and storm surges on coastal urban infrastructure along the Konkan coast"
    ]
}

FILLERS = {
    "chem_compound": ["graphene oxide", "cerium dioxide", "chitosan-titania", "cobalt ferrite", "mesoporous silica", "organocatalyst"],
    "reaction_type": ["Knoevenagel condensation", "Suzuki-Miyaura cross-coupling", "click chemistry", "dye degradation", "esterification"],
    "nano_mat": ["zinc oxide quantum dots", "gold-palladium nanoparticles", "MXene nanosheets", "silver nanorods", "carbon dots"],
    "app_type": ["photocatalytic wastewater remediation", "antimicrobial coatings", "supercapacitor electrodes", "electrochemical biosensing"],
    "target_analyte": ["heavy metal ions (Pb2+, Cd2+)", "dopamine and uric acid", "organophosphate pesticides", "antibiotic residues"],
    "physics_mat": ["bismuth ferrite (BiFeO3)", "lanthanum manganite", "lead-free perovskite", "zinc sulfide phosphors"],
    "plant_name": ["Avicennia marina (Mangrove)", "Catharanthus roseus", "Moringa oleifera", "Terminalia arjuna", "Ocimum sanctum"],
    "enzyme_type": ["thermostable alpha-amylase", "lignin peroxidase", "fungal cellulase", "lipase", "tannase"],
    "biotech_protein": ["human insulin analogues", "monoclonal antibodies", "streptokinase", "therapeutic lactoferrin"],
    "pharma_drug": ["curcumin", "metformin hydrochloride", "atorvastatin", "sorafenib", "doxorubicin", "ciprofloxacin"],
    "cs_domain": ["pulmonary tuberculosis from chest radiographs", "cardiac arrhythmia in ECG streams", "diabetic retinopathy fundus images", "crop disease symptoms"]
}

COLLAB_COUNTRIES = [
    "United States", "United Kingdom", "Germany", "Japan", "South Korea",
    "Australia", "Singapore", "Canada", "France", "Saudi Arabia",
    "Italy", "Netherlands", "Sweden", "Switzerland", "South Africa"
]

INDUSTRY_PARTNERS = [
    "Reliance Industries Ltd (R&D)", "Tata Consultancy Services Research",
    "Cipla Pharmaceuticals Ltd", "Lupin Research Park", "Sun Pharma Advanced Research",
    "Godrej Industries Chemical Division", "Dr. Reddy's Laboratories", "Bharat Petroleum Corporate R&D"
]


def _generate_authors():
    num_authors = random.choices([1, 2, 3, 4, 5, 6], weights=[0.05, 0.25, 0.35, 0.20, 0.10, 0.05])[0]
    authors_list = []
    for _ in range(num_authors):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        authors_list.append(f"{last} {first[0]}.")
    primary_author = authors_list[0]
    return ", ".join(authors_list), primary_author


def _generate_title(department):
    templates = TITLE_TEMPLATES.get(department)
    if not templates:
        templates = [
            "Empirical investigation of advanced research paradigms in {app_type}",
            "Comparative analysis of sustainable systems and methodologies in regional development"
        ]
    tmpl = random.choice(templates)
    title = tmpl.format(
        chem_compound=random.choice(FILLERS["chem_compound"]),
        reaction_type=random.choice(FILLERS["reaction_type"]),
        nano_mat=random.choice(FILLERS["nano_mat"]),
        app_type=random.choice(FILLERS["app_type"]),
        target_analyte=random.choice(FILLERS["target_analyte"]),
        physics_mat=random.choice(FILLERS["physics_mat"]),
        plant_name=random.choice(FILLERS["plant_name"]),
        enzyme_type=random.choice(FILLERS["enzyme_type"]),
        biotech_protein=random.choice(FILLERS["biotech_protein"]),
        pharma_drug=random.choice(FILLERS["pharma_drug"]),
        cs_domain=random.choice(FILLERS["cs_domain"])
    )
    return title


def generate_mock_publications(count: int = 2500, seed: int = 42) -> list[dict]:
    """
    Generate realistic benchmark publication records for University of Mumbai.
    
    Parameters:
        count: Number of publications to generate (~2,500 by default).
        seed: Random seed for deterministic reproducibility.
        
    Returns:
        List of publication dictionaries with all required Scopus schema fields.
    """
    random.seed(seed)
    publications = []

    # Distribution of years (2018 to 2026, progressive growth)
    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
    year_weights = [0.07, 0.09, 0.10, 0.12, 0.14, 0.16, 0.17, 0.11, 0.04]

    # Department selection weights (STEM fields have higher Scopus volume in MU)
    dept_weights = [
        0.18,  # Chemistry (Autonomous, massive Scopus output)
        0.12,  # Physics
        0.09,  # Life Sciences
        0.09,  # Biotechnology
        0.10,  # Computer Science
        0.07,  # Information Technology
        0.05,  # Mathematics
        0.04,  # Statistics
        0.08,  # Nanotechnology (NCNNUM)
        0.08,  # Pharmaceutical Sciences
        0.03,  # Economics
        0.02,  # Commerce
        0.02,  # Law
        0.03   # Environmental Sciences
    ]
    selected_depts = MU_DEPARTMENTS[:len(dept_weights)]

    base_scopus_id = 85100000000

    for i in range(count):
        dept = random.choices(selected_depts, weights=dept_weights)[0]
        year = random.choices(years, weights=year_weights)[0]
        authors_str, primary_author = _generate_authors()
        title = _generate_title(dept)

        # Journal selection
        journals = JOURNAL_CATALOG.get(dept, GENERIC_JOURNALS)
        journal_info = random.choice(journals)
        journal_name = journal_info["journal"]
        citescore = journal_info["citescore"]
        sjr = journal_info["sjr"]
        quartile = journal_info["quartile"]

        # Realistic citations based on paper age (older papers accumulated more)
        years_active = max(1, 2026 - year + 1)
        base_rate = random.expovariate(1.0 / (3.5 * (sjr ** 0.6)))
        citations = int(round(base_rate * years_active))
        if random.random() < 0.03:
            # Highly-cited breakout paper
            citations += random.randint(80, 400)

        # Collaboration metrics
        is_international = random.random() < 0.32  # 32% international collaboration
        is_industry = random.random() < 0.14       # 14% industry collaboration

        countries = ["India"]
        if is_international:
            num_foreign = random.choices([1, 2, 3], weights=[0.8, 0.16, 0.04])[0]
            foreign_countries = random.sample(COLLAB_COUNTRIES, num_foreign)
            countries.extend(foreign_countries)

        doi_prefix = random.choice(["10.1016", "10.1021", "10.1039", "10.1109", "10.1007", "10.1371"])
        doi = f"{doi_prefix}/mu.{year}.{100000 + i}"
        scopus_id = str(base_scopus_id + i)

        record = {
            "title": title,
            "authors": authors_str,
            "primary_author": primary_author,
            "department": dept,
            "journal": journal_name,
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
        publications.append(record)

    return publications


def get_mock_dataframe(count: int = 2500, seed: int = 42) -> pd.DataFrame:
    """
    Get mock publications as a typed pandas DataFrame.
    """
    data = generate_mock_publications(count=count, seed=seed)
    df = pd.DataFrame(data)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    df["citations"] = pd.to_numeric(df["citations"], errors="coerce").astype(int)
    df["citescore"] = pd.to_numeric(df["citescore"], errors="coerce").astype(float)
    df["sjr"] = pd.to_numeric(df["sjr"], errors="coerce").astype(float)
    return df


if __name__ == "__main__":
    records = generate_mock_publications(count=2500)
    df = pd.DataFrame(records)
    print(f"Generated {len(records)} mock publications.")
    print("Year breakdown:\n", df["year"].value_counts().sort_index())
    print("\nQuartile breakdown:\n", df["quartile"].value_counts())
    print(f"\nInternational Collab: {df['is_international_collab'].mean():.1%}")
    print(f"Industry Collab: {df['is_industry_collab'].mean():.1%}")
    print(f"Top Department:\n{df['department'].value_counts().head(5)}")
