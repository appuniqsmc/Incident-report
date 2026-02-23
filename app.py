import streamlit as st
import graphviz
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

st.title("ICU Automated Root Cause Analysis Platform")
st.caption("Enter incident description → Automatic Fishbone + 5 Whys")

# =====================================================
# INCIDENT INPUT
# =====================================================

st.header("Incident Information")

col1, col2 = st.columns(2)

with col1:
    incident_date = st.date_input("Incident Date", datetime.today())
    shift = st.selectbox("Shift", ["Morning", "Evening", "Night"])
    unit = st.selectbox("ICU Unit",
                        ["Medical ICU", "Surgical ICU", "Cardiac ICU", "Neuro ICU"])

with col2:
    severity = st.selectbox("Severity",
                            ["Near Miss", "Mild", "Moderate", "Severe", "Sentinel"])
    incident_type = st.text_input("Incident Type")
    problem_statement = st.text_input("Problem Statement")

description = st.text_area("Detailed Incident Description")

# =====================================================
# AUTOMATIC DOMAIN RULE ENGINE
# =====================================================

DOMAIN_RULES = {
    "People / Staff": ["fatigue", "inattention", "error", "calculation", "forgot"],
    "Policies / Procedures": ["protocol", "guideline", "no checklist", "not followed"],
    "Equipment / Technology": ["malfunction", "pump", "alarm", "device"],
    "Environment": ["busy", "overcrowded", "noise"],
    "Communication": ["handover", "miscommunication", "not informed", "unclear"],
    "Patient Factors": ["non-compliant", "complex", "high risk", "unstable"]
}

AUTO_CAUSE_LIBRARY = {
    "People / Staff": [
        "Inadequate competency validation",
        "Fatigue-related performance decline",
        "Calculation error risk"
    ],
    "Policies / Procedures": [
        "Protocol non-adherence",
        "Checklist gap",
        "Standard operating procedure deviation"
    ],
    "Equipment / Technology": [
        "Equipment reliability issue",
        "Alarm management failure",
        "Maintenance delay"
    ],
    "Environment": [
        "High workload pressure",
        "Environmental distractions",
        "ICU overcrowding"
    ],
    "Communication": [
        "Incomplete handover",
        "Failure of escalation",
        "Documentation gap"
    ],
    "Patient Factors": [
        "High acuity",
        "Complex comorbidity",
        "Unpredictable clinical course"
    ]
}

def classify_domains(text):
    text = text.lower()
    detected = []
    for domain, keywords in DOMAIN_RULES.items():
        for word in keywords:
            if word in text:
                detected.append(domain)
                break
    return detected

# =====================================================
# GENERATE ANALYSIS
# =====================================================

if st.button("Generate Automated RCA"):

    detected_domains = classify_domains(description)

    st.divider()
    st.header("Structured RCA Summary")

    if detected_domains:
        for d in detected_domains:
            st.write(f"- Contributing Domain Identified: **{d}**")
    else:
        st.write("No explicit domain keywords detected — manual review advised.")

    # =====================================================
    # AUTO FISHBONE
    # =====================================================

    st.subheader("Auto-Generated Fishbone Diagram")

    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir="LR")
    dot.node("Effect", problem_statement if problem_statement else "ICU Incident")

    for d in detected_domains:
        dot.node(d)
        dot.edge(d, "Effect")

        for cause in AUTO_CAUSE_LIBRARY[d]:
            dot.node(f"{d}_{cause}", cause)
            dot.edge(f"{d}_{cause}", d)

    st.graphviz_chart(dot)

    # =====================================================
    # AUTO 5 WHYS
    # =====================================================

    st.subheader("5 Whys (Auto-Structured)")

    why_chain = []

    why_chain.append(problem_statement)

    if detected_domains:
        why_chain.append(f"Because of issues related to {detected_domains[0]}")
        why_chain.append("Because system safeguards were inadequate")
        why_chain.append("Because monitoring/audit process failed")
        why_chain.append("Because of latent organizational gap")
        why_chain.append("Root cause: System reliability weakness")
    else:
        why_chain.append("Why requires manual exploration")
        why_chain += ["", "", "", ""]

    why_df = pd.DataFrame({
        "Level": ["Problem", "Why 1", "Why 2", "Why 3", "Why 4", "Why 5"],
        "Statement": why_chain
    })

    st.table(why_df)

    # =====================================================
    # INCIDENT SUMMARY
    # =====================================================

    st.subheader("Incident Summary")

    summary_df = pd.DataFrame({
        "Field": [
            "Date", "Shift", "Unit",
            "Severity", "Incident Type"
        ],
        "Value": [
            incident_date,
            shift,
            unit,
            severity,
            incident_type
        ]
    })

    st.table(summary_df)

    st.success("Automated RCA Completed")
