
import streamlit as st
import graphviz
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np
import re
from datetime import datetime

# ==========================================================
# PAGE CONFIG & STYLING
# ==========================================================

st.set_page_config(
    page_title="ICU Safety Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    .main {background-color: #0d1117;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}

    h1, h2, h3 {font-family: 'IBM Plex Mono', monospace !important; color: #e8eaf0 !important;}

    .metric-card {
        background: linear-gradient(135deg, #1a2332 0%, #151d2b 100%);
        border: 1px solid #2a3a52;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-val {font-size: 2.2rem; font-weight: 700; color: #4fc3f7;}
    .metric-label {font-size: 0.75rem; color: #8899aa; text-transform: uppercase; letter-spacing: 1px;}

    .severity-badge {
        display: inline-block;
        padding: 4px 16px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 1px;
        font-family: 'IBM Plex Mono', monospace;
    }

    .sentinel-banner {
        background: linear-gradient(90deg, #7f1d1d, #991b1b);
        border: 2px solid #ef4444;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: 700;
        color: #fca5a5;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: 2px;
        animation: pulse 2s infinite;
        margin-bottom: 20px;
    }

    @keyframes pulse {
        0%, 100% {opacity: 1;}
        50% {opacity: 0.75;}
    }

    .section-header {
        background: linear-gradient(90deg, #1a2332, transparent);
        border-left: 3px solid #4fc3f7;
        padding: 8px 16px;
        margin: 20px 0 10px 0;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.9rem;
        color: #4fc3f7;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .summary-box {
        background: #111827;
        border: 1px solid #2a3a52;
        border-radius: 8px;
        padding: 24px;
        margin: 10px 0;
    }

    .action-item {
        background: #1a2332;
        border-left: 3px solid #22c55e;
        padding: 10px 16px;
        margin: 6px 0;
        border-radius: 0 4px 4px 0;
        font-size: 0.9rem;
        color: #d1fae5;
    }

    .warning-item {
        background: #1a1a1a;
        border-left: 3px solid #f59e0b;
        padding: 10px 16px;
        margin: 6px 0;
        border-radius: 0 4px 4px 0;
        font-size: 0.9rem;
        color: #fde68a;
    }

    div[data-testid="stTable"] {color: #d0d7de;}
    div[data-testid="stMetric"] {background: #1a2332; padding: 15px; border-radius: 8px; border: 1px solid #2a3a52;}
    .stSelectbox > label, .stTextInput > label, .stNumberInput > label, .stTextArea > label,
    .stDateInput > label {color: #8899aa !important; font-size: 0.8rem !important; letter-spacing: 1px !important; text-transform: uppercase;}

    .stButton > button {
        background: linear-gradient(135deg, #0ea5e9, #2563eb);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 2rem;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.9rem;
        letter-spacing: 1px;
        font-weight: 600;
        width: 100%;
        margin-top: 10px;
    }
    .stButton > button:hover {background: linear-gradient(135deg, #38bdf8, #3b82f6);}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# HEADER
# ==========================================================

st.markdown("# 🏥 ICU Safety Intelligence Dashboard")
st.markdown('<p style="color:#8899aa;font-size:0.9rem;font-family:\'IBM Plex Mono\',monospace;letter-spacing:2px;">COMPREHENSIVE INSTITUTIONAL INCIDENT ANALYSIS PLATFORM — v2.0</p>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================================
# SIDEBAR — Incident Metadata
# ==========================================================

with st.sidebar:
    st.markdown("### 🗂 Incident Metadata")
    incident_date = st.date_input("Incident Date", datetime.today())
    shift = st.selectbox("Shift", ["Morning (06:00–14:00)", "Evening (14:00–22:00)", "Night (22:00–06:00)"])
    unit = st.selectbox("ICU Unit", ["Medical ICU", "Surgical ICU", "Cardiac ICU", "Neuro ICU", "Burn ICU", "Paediatric ICU"])
    nurse_patient_ratio = st.selectbox("Nurse-Patient Ratio", ["1:1", "1:2", "1:3", "1:4+"])
    staffing_level = st.selectbox("Staffing Level at Time", ["Fully Staffed", "1 Short", "2 Short", "Critically Understaffed"])
    experience_level = st.selectbox("Staff Experience Level (Primary)", ["Junior (<2 yrs)", "Mid-level (2–5 yrs)", "Senior (>5 yrs)", "Locum/Agency"])

st.subheader("📋 Incident Information")

col1, col2 = st.columns(2)

with col1:
    incident_type = st.selectbox("Incident Type", [
        "Medication Error",
        "Ventilator Event",
        "Central Line Event",
        "Procedure Error",
        "Communication Failure",
        "Equipment Failure",
        "Fall/Patient Safety",
        "Pressure Injury",
        "Diagnostic Delay",
        "Handover Failure",
        "Other"
    ])
    time_to_detection = st.number_input("Time to Detection (minutes)", 0, 1440, 30)
    time_to_report = st.number_input("Time to Formal Report (hours)", 0, 72, 2)

with col2:
    problem_statement = st.text_input("Problem Statement (1 sentence)", placeholder="e.g. Incorrect insulin dose administered during handover")
    patient_outcome = st.selectbox("Immediate Patient Outcome", [
        "No apparent harm",
        "Near miss — intercepted",
        "Temporary harm — no treatment",
        "Temporary harm — treatment required",
        "Permanent harm",
        "Death"
    ])
    prior_incidents = st.number_input("Similar Prior Incidents This Unit (last 12 months)", 0, 50, 0)

description = st.text_area("Detailed Incident Description", height=180,
    placeholder="Describe the sequence of events, people involved, actions taken, contributing conditions, and immediate aftermath...")

contributing_factors = st.multiselect("Known Contributing Factors (select all that apply)", [
    "Fatigue / Sleep deprivation",
    "Communication breakdown",
    "Inadequate training",
    "High workload",
    "Equipment failure",
    "Unclear protocol",
    "Distraction / interruption",
    "Incomplete handover",
    "Medication labelling issue",
    "Documentation error",
    "Patient complexity",
    "Environmental factors",
    "Supervision gap",
    "Knowledge deficit"
])

st.markdown("---")

# ==========================================================
# SEVERITY CLASSIFICATION (NCC MERP / WHO adapted)
# ==========================================================

SEVERITY_CONFIG = {
    5: {"label": "Death", "color": "#7f1d1d", "badge": "#ef4444", "ncc": "I"},
    4: {"label": "Severe Harm", "color": "#92400e", "badge": "#f97316", "ncc": "H"},
    3: {"label": "Moderate Harm", "color": "#78350f", "badge": "#f59e0b", "ncc": "F-G"},
    2: {"label": "Mild Harm", "color": "#1e3a5f", "badge": "#3b82f6", "ncc": "D-E"},
    1: {"label": "Near Miss / No Harm", "color": "#14532d", "badge": "#22c55e", "ncc": "A-C"},
}

def classify_severity(text, outcome, detection_time):
    sentinel = False
    text = text.lower()
    outcome_l = outcome.lower()

    if "death" in outcome_l or "death" in text or "expired" in text or "fatal" in text:
        sentinel = True
        return 5, sentinel
    if "permanent harm" in outcome_l or any(w in text for w in ["cardiac arrest", "organ failure", "anoxic", "respiratory arrest", "permanent"]):
        sentinel = True
        return 4, sentinel
    if "temporary harm — treatment" in outcome_l or any(w in text for w in ["prolonged stay", "icu transfer", "emergency intervention", "resuscitation"]):
        return 3, sentinel
    if "temporary harm — no treatment" in outcome_l or any(w in text for w in ["temporary", "minor injury", "hypoglycaemia", "hypotension"]):
        return 2, sentinel
    return 1, sentinel

# ==========================================================
# DOMAIN CLASSIFICATION (expanded)
# ==========================================================

DOMAIN_RULES = {
    "People / Human Factors":       ["missed", "error", "incorrect", "forgot", "fatigue", "tired", "distracted", "oversight", "confusion"],
    "Communication":                 ["handover", "verbal", "unclear", "misunderstood", "not documented", "not informed", "not communicated"],
    "Policies / Procedures":         ["protocol", "guideline", "checklist", "procedure", "policy", "standard", "not followed"],
    "Equipment / Technology":        ["pump", "alarm", "malfunction", "device", "infusion", "ventilator", "monitor", "failure", "broken"],
    "Environment / Workload":        ["busy", "overcrowded", "noise", "interruption", "workload", "understaffed", "short staffed", "high acuity"],
    "Training / Knowledge":          ["unaware", "not trained", "inexperienced", "knowledge gap", "unfamiliar", "locum"],
    "Patient / Clinical Complexity": ["unstable", "complex", "deteriorating", "multiple comorbidities", "non-compliant"],
    "Supervision / Leadership":      ["unsupervised", "no review", "consultant", "escalation missed", "not escalated"],
}

def classify_domains(text, factors):
    text = (text + " " + " ".join(factors)).lower()
    scores = {}
    matched_keywords = {}
    for domain, keywords in DOMAIN_RULES.items():
        found = [kw for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", text)]
        scores[domain] = len(found)
        matched_keywords[domain] = found
    return scores, matched_keywords

# ==========================================================
# RPN CALCULATION (FMEA-style)
# ==========================================================

def calculate_rpn(severity_score, likelihood_score, detectability_score):
    return severity_score * likelihood_score * detectability_score

def get_risk_category(rpn):
    if rpn >= 80:
        return "CRITICAL", "#ef4444"
    elif rpn >= 40:
        return "HIGH", "#f97316"
    elif rpn >= 20:
        return "MODERATE", "#f59e0b"
    else:
        return "LOW", "#22c55e"

# ==========================================================
# GENERATE FULL DASHBOARD
# ==========================================================

if st.button("🚀 Generate Full Incident Dashboard"):

    severity_score, sentinel_flag = classify_severity(description, patient_outcome, time_to_detection)
    sev_info = SEVERITY_CONFIG[severity_score]
    domain_scores, matched_kw = classify_domains(description, contributing_factors)

    # FMEA scores
    likelihood_score = min(5, prior_incidents + 1)
    detectability_score = min(5, max(1, int(time_to_detection / 20) + 1))
    rpn = calculate_rpn(severity_score, likelihood_score, detectability_score)
    risk_cat, risk_color = get_risk_category(rpn)

    # --- SENTINEL BANNER ---
    if sentinel_flag:
        st.markdown(f'<div class="sentinel-banner">⚠ SENTINEL EVENT DETECTED — IMMEDIATE EXECUTIVE & GOVERNANCE REVIEW REQUIRED ⚠</div>', unsafe_allow_html=True)

    # ==========================================================
    # SECTION 1: KEY METRICS
    # ==========================================================
    st.markdown('<div class="section-header">01 — KEY METRICS</div>', unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Severity Level", f"{severity_score}/5")
        st.caption(sev_info["label"])
    with m2:
        st.metric("NCC MERP Category", sev_info["ncc"])
    with m3:
        st.metric("FMEA Risk Priority Number", rpn)
        st.caption(risk_cat)
    with m4:
        st.metric("Detection Delay", f"{time_to_detection} min")
    with m5:
        st.metric("Reporting Delay", f"{time_to_report} hrs")

    st.markdown("---")

    # ==========================================================
    # SECTION 2: STANDARDIZED INCIDENT REPORT
    # ==========================================================
    st.markdown('<div class="section-header">02 — STANDARDIZED INCIDENT REPORT</div>', unsafe_allow_html=True)

    report_df = pd.DataFrame({
        "Field": [
            "Date", "Shift", "Unit", "Incident Type",
            "Patient Outcome", "Severity Classification (NCC MERP)",
            "Nurse-Patient Ratio", "Staffing Level",
            "Staff Experience Level",
            "Time to Detection (min)", "Time to Formal Report (hrs)",
            "Similar Prior Incidents (12 mo)", "Sentinel Event", "FMEA RPN"
        ],
        "Value": [
            str(incident_date), shift, unit, incident_type,
            patient_outcome, f"{sev_info['label']} — Category {sev_info['ncc']}",
            nurse_patient_ratio, staffing_level,
            experience_level,
            time_to_detection, time_to_report,
            prior_incidents, "YES ⚠" if sentinel_flag else "NO",
            f"{rpn} ({risk_cat})"
        ]
    })

    st.table(report_df)

    st.markdown("---")

    # ==========================================================
    # SECTION 3: RISK MATRIX + FMEA
    # ==========================================================
    st.markdown('<div class="section-header">03 — FMEA RISK ANALYSIS</div>', unsafe_allow_html=True)

    colA, colB = st.columns([1, 1])

    with colA:
        st.markdown("#### Risk Priority Number (RPN)")
        st.markdown(f"**RPN = Severity × Likelihood × Detectability**")
        st.markdown(f"RPN = **{severity_score}** × **{likelihood_score}** × **{detectability_score}** = <span style='color:{risk_color};font-size:1.5rem;font-weight:700;font-family:monospace'>{rpn}</span> — **{risk_cat}**", unsafe_allow_html=True)

        fig_fmea, ax_fmea = plt.subplots(figsize=(5, 4))
        fig_fmea.patch.set_facecolor('#0d1117')
        ax_fmea.set_facecolor('#111827')

        categories = ['Severity', 'Likelihood', 'Detectability']
        values_fmea = [severity_score, likelihood_score, detectability_score]
        colors_fmea = ['#ef4444', '#f97316', '#f59e0b']
        bars = ax_fmea.barh(categories, values_fmea, color=colors_fmea, height=0.5)
        for bar, val in zip(bars, values_fmea):
            ax_fmea.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                        f'{val}/5', va='center', color='white', fontsize=11, fontweight='bold')
        ax_fmea.set_xlim(0, 6)
        ax_fmea.set_xlabel('Score (out of 5)', color='#8899aa')
        ax_fmea.tick_params(colors='#8899aa')
        for spine in ax_fmea.spines.values():
            spine.set_edgecolor('#2a3a52')
        ax_fmea.set_title('FMEA Component Scores', color='#e8eaf0', pad=10)
        st.pyplot(fig_fmea)

    with colB:
        st.markdown("#### Risk Matrix (5×5 Heatmap)")
        fig_matrix, ax_matrix = plt.subplots(figsize=(5, 4))
        fig_matrix.patch.set_facecolor('#0d1117')
        ax_matrix.set_facecolor('#111827')

        matrix = np.zeros((5, 5))
        for s in range(1, 6):
            for l in range(1, 6):
                matrix[s-1][l-1] = s * l

        im = ax_matrix.imshow(matrix, cmap='RdYlGn_r', vmin=1, vmax=25, aspect='auto')
        ax_matrix.scatter(likelihood_score-1, severity_score-1, s=300, c='white',
                         marker='*', zorder=5, label='This Incident')
        ax_matrix.set_xticks(range(5))
        ax_matrix.set_yticks(range(5))
        ax_matrix.set_xticklabels([f'L{i+1}' for i in range(5)], color='#8899aa')
        ax_matrix.set_yticklabels([f'S{i+1}' for i in range(5)], color='#8899aa')
        ax_matrix.set_xlabel('Likelihood →', color='#8899aa')
        ax_matrix.set_ylabel('Severity →', color='#8899aa')
        ax_matrix.set_title('Severity × Likelihood Matrix\n★ = This Incident', color='#e8eaf0', pad=10)
        plt.colorbar(im, ax=ax_matrix, label='Risk Score')
        for spine in ax_matrix.spines.values():
            spine.set_edgecolor('#2a3a52')
        st.pyplot(fig_matrix)

    st.markdown("---")

    # ==========================================================
    # SECTION 4: DOMAIN ANALYSIS (RADAR)
    # ==========================================================
    st.markdown('<div class="section-header">04 — CONTRIBUTING DOMAIN ANALYSIS</div>', unsafe_allow_html=True)

    colC, colD = st.columns([1, 1])

    with colC:
        labels = list(domain_scores.keys())
        values_r = list(domain_scores.values())
        N = len(labels)
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
        values_r_plot = values_r + [values_r[0]]
        angles_plot = angles + [angles[0]]

        fig_radar, ax_radar = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True))
        fig_radar.patch.set_facecolor('#0d1117')
        ax_radar.set_facecolor('#0d1117')

        ax_radar.plot(angles_plot, values_r_plot, color='#4fc3f7', linewidth=2.5)
        ax_radar.fill(angles_plot, values_r_plot, color='#4fc3f7', alpha=0.15)

        # Gridlines
        for gridval in [1, 2, 3]:
            ax_radar.plot(angles_plot, [gridval]*len(angles_plot), color='#2a3a52', linewidth=0.7, linestyle='--')

        ax_radar.set_xticks(angles)
        short_labels = [l.split('/')[0].strip() for l in labels]
        ax_radar.set_xticklabels(short_labels, color='#8899aa', size=7.5)
        ax_radar.set_yticklabels([], color='#2a3a52')
        ax_radar.set_ylim(0, max(max(values_r), 3) + 1)
        ax_radar.set_title('Domain Contribution Radar', color='#e8eaf0', pad=20)
        ax_radar.spines['polar'].set_color('#2a3a52')
        st.pyplot(fig_radar)

    with colD:
        st.markdown("#### Domain Breakdown & Matched Keywords")
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        for domain, score in sorted_domains:
            pct = (score / max(max(domain_scores.values()), 1)) * 100
            kws = matched_kw.get(domain, [])
            color = '#4fc3f7' if score > 0 else '#2a3a52'
            st.markdown(f"""
            <div style="margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;color:#d0d7de;font-size:0.82rem;margin-bottom:3px;">
                    <span>{domain}</span><span style="font-family:monospace;color:{color}">{score} match{'es' if score != 1 else ''}</span>
                </div>
                <div style="background:#1a2332;border-radius:4px;height:8px;width:100%;">
                    <div style="background:{color};border-radius:4px;height:8px;width:{min(pct,100):.0f}%;"></div>
                </div>
                <div style="font-size:0.7rem;color:#5a6a7a;margin-top:2px;">
                    {', '.join(kws) if kws else '—'}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================================
    # SECTION 5: FISHBONE DIAGRAM (Ishikawa) — ENHANCED
    # ==========================================================
    st.markdown('<div class="section-header">05 — ISHIKAWA FISHBONE DIAGRAM (6M Framework)</div>', unsafe_allow_html=True)

    fish = graphviz.Digraph()
    fish.attr(rankdir="LR", bgcolor="#111827",
              fontname="IBM Plex Mono", fontcolor="#e8eaf0", fontsize="11")

    # Effect node
    fish.node("Effect",
              label=f"<<B>INCIDENT EFFECT</B><BR/>{problem_statement or 'ICU Incident'}>",
              shape="box", style="filled,rounded", fillcolor="#7f1d1d",
              fontcolor="#fca5a5", fontsize="12", penwidth="2", color="#ef4444")

    # Spine
    fish.node("Spine", label="", shape="point", color="#4fc3f7", width="0.1")
    fish.edge("Spine", "Effect", color="#4fc3f7", penwidth="3")

    # 6M categories mapped to our domains
    bone_map = {
        "Man\n(Human Factors)":       ["People / Human Factors", "Training / Knowledge", "Supervision / Leadership"],
        "Method\n(Procedures)":       ["Policies / Procedures"],
        "Machine\n(Equipment)":       ["Equipment / Technology"],
        "Milieu\n(Environment)":      ["Environment / Workload"],
        "Material\n(Supplies/Meds)":  [],
        "Measurement\n(Monitoring)":  [],
    }

    bone_colors = {
        "Man\n(Human Factors)":      "#ef4444",
        "Method\n(Procedures)":      "#f97316",
        "Machine\n(Equipment)":      "#eab308",
        "Milieu\n(Environment)":     "#22c55e",
        "Material\n(Supplies/Meds)": "#3b82f6",
        "Measurement\n(Monitoring)": "#a855f7",
    }

    top_categories = ["Man\n(Human Factors)", "Machine\n(Equipment)", "Material\n(Supplies/Meds)"]
    bot_categories = ["Method\n(Procedures)", "Milieu\n(Environment)", "Measurement\n(Monitoring)"]

    # Add category bones
    for cat in bone_map:
        safe_id = cat.replace("\n", "_").replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
        cat_color = bone_colors[cat]
        fish.node(safe_id, label=cat, shape="ellipse", style="filled",
                  fillcolor=cat_color, fontcolor="white", fontsize="10", penwidth="1.5")
        fish.edge(safe_id, "Spine", color=cat_color, penwidth="2")

        # Add domain keywords as sub-bones
        relevant_domains = bone_map[cat]
        sub_items = []
        for dom in relevant_domains:
            kws = matched_kw.get(dom, [])
            sub_items.extend(kws[:2])  # top 2 keywords per domain

        # Also add selected contributing factors
        if cat == "Man\n(Human Factors)":
            for cf in contributing_factors:
                if any(w in cf.lower() for w in ["fatigue", "supervision", "training", "knowledge", "workload"]):
                    sub_items.append(cf)
        if cat == "Milieu\n(Environment)":
            for cf in contributing_factors:
                if any(w in cf.lower() for w in ["environment", "interruption", "staffing", "high workload"]):
                    sub_items.append(cf)

        seen = set()
        sub_items_clean = [x for x in sub_items if not (x in seen or seen.add(x))][:4]

        for i, item in enumerate(sub_items_clean):
            node_id = f"{safe_id}_sub{i}"
            fish.node(node_id, label=item.replace(" ", "\n"), shape="box",
                      style="filled,rounded", fillcolor="#1a2332",
                      fontcolor="#8899aa", fontsize="8", penwidth="1", color="#2a3a52")
            fish.edge(node_id, safe_id, color="#2a3a52", penwidth="1")

    st.graphviz_chart(fish)

    st.markdown("---")

    # ==========================================================
    # SECTION 6: SWISS CHEESE MODEL (enhanced)
    # ==========================================================
    st.markdown('<div class="section-header">06 — SWISS CHEESE BARRIER FAILURE MODEL</div>', unsafe_allow_html=True)

    cheese = graphviz.Digraph()
    cheese.attr(rankdir="LR", bgcolor="#111827", fontname="IBM Plex Mono", fontcolor="#e8eaf0")

    cheese.node("Hazard", label="HAZARD\nLATENT CONDITIONS",
                shape="diamond", style="filled", fillcolor="#450a0a", fontcolor="#fca5a5",
                fontsize="10", color="#ef4444", penwidth="2")

    layers = [
        ("L1", "ORGANIZATIONAL\nCULTURE\n& LEADERSHIP", "#1e3a5f"),
        ("L2", "SUPERVISION\n& ESCALATION\nSYSTEMS",   "#1e3a5f"),
        ("L3", "POLICIES\n& PROCEDURES",               "#1e3a5f"),
        ("L4", "TRAINING\n& COMPETENCY",               "#1e3a5f"),
        ("L5", "MONITORING\n& ALARMS",                 "#1e3a5f"),
        ("L6", "PATIENT-SIDE\nDEFENCES",               "#1e3a5f"),
    ]

    failed_layers = set()
    if domain_scores.get("Policies / Procedures", 0) > 0:        failed_layers.add("L3")
    if domain_scores.get("Supervision / Leadership", 0) > 0:     failed_layers.add("L2")
    if domain_scores.get("Training / Knowledge", 0) > 0:         failed_layers.add("L4")
    if domain_scores.get("Equipment / Technology", 0) > 0:       failed_layers.add("L5")
    if domain_scores.get("Environment / Workload", 0) > 0:       failed_layers.add("L1")
    if domain_scores.get("Patient / Clinical Complexity", 0) > 0: failed_layers.add("L6")

    cheese.node("Hazard")
    prev = "Hazard"
    for lid, label, base_color in layers:
        fill = "#7f1d1d" if lid in failed_layers else "#1e3a5f"
        border = "#ef4444" if lid in failed_layers else "#2a3a52"
        font = "#fca5a5" if lid in failed_layers else "#93c5fd"
        suffix = "\n⚠ FAILED" if lid in failed_layers else "\n✓ Held"
        cheese.node(lid, label=label + suffix, shape="box", style="filled,rounded",
                    fillcolor=fill, fontcolor=font, fontsize="9", color=border, penwidth="2")
        cheese.edge(prev, lid, color="#4fc3f7", penwidth="2", style="dashed")
        prev = lid

    cheese.node("Incident", label="INCIDENT\nOCCURRED", shape="octagon",
                style="filled", fillcolor="#7f1d1d", fontcolor="#fca5a5",
                fontsize="11", color="#ef4444", penwidth="3")
    cheese.edge(prev, "Incident", color="#ef4444", penwidth="3")

    st.graphviz_chart(cheese)

    st.markdown("---")

    # ==========================================================
    # SECTION 7: 5 WHYS ROOT CAUSE CHAIN
    # ==========================================================
    st.markdown('<div class="section-header">07 — 5 WHYS ROOT CAUSE ANALYSIS SCAFFOLD</div>', unsafe_allow_html=True)

    whys = graphviz.Digraph()
    whys.attr(rankdir="TB", bgcolor="#111827", fontname="IBM Plex Mono")

    whys.node("P", label=f"PROBLEM:\n{problem_statement or 'ICU Incident'}", shape="box",
              style="filled,rounded", fillcolor="#7f1d1d", fontcolor="#fca5a5", fontsize="10", color="#ef4444")

    top_domains = [d for d, s in sorted(domain_scores.items(), key=lambda x: x[1], reverse=True) if s > 0][:3]

    why_nodes = []
    for i, dom in enumerate(top_domains):
        nid = f"W{i+1}"
        kws = matched_kw.get(dom, ["(details not detected)"])
        label = f"WHY {i+1}: {dom}\n[{', '.join(kws[:2])}]"
        whys.node(nid, label=label, shape="box", style="filled,rounded",
                  fillcolor="#1e3a5f", fontcolor="#93c5fd", fontsize="9", color="#2a3a52")
        if i == 0:
            whys.edge("P", nid, color="#4fc3f7", penwidth="2")
        else:
            whys.edge(f"W{i}", nid, color="#4fc3f7", penwidth="2")
        why_nodes.append(nid)

    if why_nodes:
        whys.node("RC", label="ROOT CAUSE:\nSystem & Latent Conditions", shape="diamond",
                  style="filled", fillcolor="#14532d", fontcolor="#86efac", fontsize="10", color="#22c55e")
        whys.edge(why_nodes[-1], "RC", color="#22c55e", penwidth="2")

    st.graphviz_chart(whys)

    st.markdown("---")

    # ==========================================================
    # SECTION 8: DRIVER DIAGRAM
    # ==========================================================
    st.markdown('<div class="section-header">08 — DRIVER DIAGRAM FOR IMPROVEMENT</div>', unsafe_allow_html=True)

    driver = graphviz.Digraph()
    driver.attr(rankdir="LR", bgcolor="#111827", fontname="IBM Plex Mono")

    driver.node("Aim", label=f"AIM:\nEliminate similar\nICU incidents\nwithin 6 months",
                shape="box", style="filled,rounded", fillcolor="#1e3a5f",
                fontcolor="#93c5fd", fontsize="11", color="#3b82f6", penwidth="2")

    primary_drivers = [
        ("PD1", "Safe staffing\n& workload management"),
        ("PD2", "Reliable communication\nsystems"),
        ("PD3", "Protocol adherence\n& usability"),
        ("PD4", "Technology\nreliability"),
    ]
    secondary_map = {
        "PD1": ["Nurse-patient ratio audit", "Fatigue risk policy", "Escalation support"],
        "PD2": ["Structured handover (ISBAR)", "Critical results protocol", "Closed-loop comms training"],
        "PD3": ["Checklist review & redesign", "Simulation-based drills", "Near-miss reporting culture"],
        "PD4": ["Equipment PM schedules", "Alarm management program", "Rapid response to failures"],
    }

    for pid, plabel in primary_drivers:
        driver.node(pid, label=plabel, shape="box", style="filled,rounded",
                    fillcolor="#1a2332", fontcolor="#d0d7de", fontsize="9", color="#2a3a52")
        driver.edge("Aim", pid, color="#4fc3f7", penwidth="2")
        for j, sd in enumerate(secondary_map[pid]):
            sid = f"{pid}_s{j}"
            driver.node(sid, label=sd, shape="box", style="filled,rounded",
                        fillcolor="#0d1117", fontcolor="#5a6a7a", fontsize="8", color="#1a2332")
            driver.edge(pid, sid, color="#2a3a52", penwidth="1")

    st.graphviz_chart(driver)

    st.markdown("---")

    # ==========================================================
    # SECTION 9: TIME-LINE ANALYSIS
    # ==========================================================
    st.markdown('<div class="section-header">09 — TIME-TO-DETECTION & REPORTING ANALYSIS</div>', unsafe_allow_html=True)

    fig_time, ax_time = plt.subplots(figsize=(10, 3))
    fig_time.patch.set_facecolor('#0d1117')
    ax_time.set_facecolor('#111827')

    timeline_events = [0, time_to_detection, time_to_detection + time_to_report * 60]
    labels_t = ["Incident\nOccurred", f"Detected\n(+{time_to_detection}m)", f"Reported\n(+{time_to_report}h)"]
    colors_t = ['#f97316', '#4fc3f7', '#22c55e']

    ax_time.hlines(0.5, 0, max(timeline_events) * 1.1, colors='#2a3a52', linewidths=3, zorder=1)
    for i, (x, lbl, col) in enumerate(zip(timeline_events, labels_t, colors_t)):
        ax_time.scatter(x, 0.5, s=200, color=col, zorder=3)
        ax_time.text(x, 0.7 if i % 2 == 0 else 0.3, lbl, ha='center', va='bottom' if i % 2 == 0 else 'top',
                    color=col, fontsize=8.5, fontfamily='monospace')

    # Benchmark zones
    ax_time.axvspan(0, 10, alpha=0.07, color='#22c55e', label='Optimal detection (<10min)')
    ax_time.axvspan(10, 30, alpha=0.07, color='#f59e0b', label='Acceptable (10-30min)')
    ax_time.axvspan(30, max(timeline_events)*1.1, alpha=0.07, color='#ef4444', label='Delayed (>30min)')

    ax_time.set_xlim(0, max(timeline_events) * 1.1 if max(timeline_events) > 0 else 10)
    ax_time.set_ylim(0, 1)
    ax_time.set_xlabel('Time (minutes from incident)', color='#8899aa')
    ax_time.set_yticks([])
    ax_time.legend(loc='upper right', fontsize=7, facecolor='#1a2332', labelcolor='#8899aa', edgecolor='#2a3a52')
    ax_time.tick_params(colors='#8899aa')
    for spine in ax_time.spines.values():
        spine.set_edgecolor('#2a3a52')
    ax_time.set_title('Incident Detection & Reporting Timeline', color='#e8eaf0', pad=10)

    st.pyplot(fig_time)

    st.markdown("---")

    # ==========================================================
    # SECTION 10: COMPREHENSIVE SUMMARY REPORT
    # ==========================================================
    st.markdown('<div class="section-header">10 — COMPREHENSIVE INCIDENT ANALYSIS SUMMARY</div>', unsafe_allow_html=True)

    active_domains = [d for d, s in domain_scores.items() if s > 0]
    failed_layer_labels = {
        "L1": "Organisational Culture & Leadership",
        "L2": "Supervision & Escalation",
        "L3": "Policies & Procedures",
        "L4": "Training & Competency",
        "L5": "Monitoring & Alarms",
        "L6": "Patient-side Defences"
    }
    failed_barriers = [failed_layer_labels[l] for l in failed_layers]

    # Detection quality
    if time_to_detection < 10:
        det_quality = "OPTIMAL — Incident detected within target window"
    elif time_to_detection <= 30:
        det_quality = "ACCEPTABLE — Detection within expected range"
    else:
        det_quality = "DELAYED — Detection exceeded safe threshold; investigate monitoring gaps"

    st.markdown('<div class="summary-box">', unsafe_allow_html=True)

    st.markdown(f"""
### Incident Classification
- **Date / Shift / Unit:** {incident_date} | {shift} | {unit}
- **Type:** {incident_type}
- **Severity:** {sev_info['label']} (NCC MERP Category {sev_info['ncc']}, Score {severity_score}/5)
- **Risk Priority Number (FMEA):** {rpn}/125 — **{risk_cat}**
- **Sentinel Event:** {"YES — Mandatory root cause analysis and executive review" if sentinel_flag else "NO"}
    """)

    st.markdown(f"""
### System Analysis
- **Primary Contributing Domains:** {', '.join(active_domains) if active_domains else 'None detected from description'}
- **Failed Safety Barriers (Swiss Cheese):** {', '.join(failed_barriers) if failed_barriers else 'None identified'}
- **Detection Performance:** {det_quality}
- **Contributing Factors (Reported):** {', '.join(contributing_factors) if contributing_factors else 'None selected'}
    """)

    st.markdown("### Recommended Immediate Actions")
    immediate = [
        "Complete mandatory incident report in hospital risk management system within 24 hours",
        "Debrief involved staff using structured non-punitive approach (same shift where possible)",
        "Conduct equipment check or protocol review relevant to incident type",
    ]
    if sentinel_flag:
        immediate.insert(0, "Notify CNO / CMO / Risk Management immediately — Sentinel Event Protocol activated")
    for item in immediate:
        st.markdown(f'<div class="action-item">✅ {item}</div>', unsafe_allow_html=True)

    st.markdown("### Recommended System Improvement Actions")
    system_actions = [
        f"Formal Root Cause Analysis (RCA) to address: {', '.join(active_domains[:3]) if active_domains else 'all identified domains'}",
        "Review and update relevant clinical protocols or standing orders",
        "Design or refresh staff education — simulation-based training preferred",
        "Audit compliance with ISBAR handover in this unit over next 30 days",
        f"Review nurse-patient ratio policy — current ratio at time: {nurse_patient_ratio}",
        "Implement or review early warning / monitoring escalation system",
        "Present anonymised case at next unit morbidity & mortality or safety meeting",
    ]
    for item in system_actions:
        st.markdown(f'<div class="warning-item">🔶 {item}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#2a3a52;font-size:0.75rem;font-family:monospace;text-align:center;">ICU Safety Intelligence Dashboard v2.0 — For institutional quality improvement use only. Not a substitute for clinical judgment or formal RCA methodology.</p>', unsafe_allow_html=True)
