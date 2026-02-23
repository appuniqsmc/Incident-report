import streamlit as st
import graphviz
import pandas as pd
import re
from datetime import datetime
from openai import OpenAI

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(page_title="ICU RCA Intelligence Platform", layout="wide")

st.markdown("""
# 🏥 ICU Root Cause Analysis Intelligence Platform
Structured Deterministic Classification + Advanced AI Institutional Analysis
""")

st.markdown("---")

# ==========================================================
# INITIALIZE OPENAI
# ==========================================================

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ==========================================================
# INCIDENT INPUT PANEL
# ==========================================================

with st.container():
    st.subheader("📋 Incident Information")

    col1, col2 = st.columns(2)

    with col1:
        incident_date = st.date_input("Incident Date", datetime.today())
        shift = st.selectbox("Shift", ["Morning", "Evening", "Night"])
        unit = st.selectbox(
            "ICU Unit",
            ["Medical ICU", "Surgical ICU", "Cardiac ICU", "Neuro ICU"]
        )

    with col2:
        severity = st.selectbox(
            "Severity Classification",
            ["Near Miss", "Mild Harm", "Moderate Harm", "Severe Harm", "Sentinel Event"]
        )
        incident_type = st.text_input("Incident Type")
        problem_statement = st.text_input("Problem Statement")

    description = st.text_area("Detailed Incident Description", height=150)

st.markdown("---")

# ==========================================================
# DETERMINISTIC DOMAIN ENGINE
# ==========================================================

DOMAIN_RULES = {
    "People / Staff": ["missed", "dose", "error", "incorrect", "forgot",
                       "fatigue", "calculation", "insulin", "medication"],
    "Communication": ["handover", "verbal", "unclear", "miscommunication",
                      "not informed", "order"],
    "Policies / Procedures": ["protocol", "guideline", "checklist",
                              "policy", "delay", "deviation"],
    "Equipment / Technology": ["pump", "alarm", "malfunction",
                               "device", "ventilator", "monitor"],
    "Environment": ["busy", "overcrowded", "noise",
                    "workload", "staff shortage"],
    "Patient Factors": ["unstable", "complex", "non-compliant"]
}

def classify_domains(text):
    text = text.lower()
    detected = []
    for domain, keywords in DOMAIN_RULES.items():
        for word in keywords:
            if re.search(r"\b" + re.escape(word) + r"\b", text):
                detected.append(domain)
                break
    if not detected:
        detected = ["People / Staff"]
    return detected

# ==========================================================
# AI GENERATOR
# ==========================================================

def generate_advanced_ai_rca(text, domains):

    prompt = f"""
You are a senior ICU safety and systems engineering consultant.

Perform an in-depth institutional-grade Root Cause Analysis.

Incident:
{text}

Detected Domains:
{domains}

Generate structured report with:

1. Executive Summary
2. Event Reconstruction
3. Active Failures
4. Contributing Factors by Domain
5. Latent System Failures (Swiss Cheese model)
6. Barrier Analysis (which safeguards failed)
7. Risk Matrix Commentary (likelihood × severity)
8. Corrective Actions (Immediate)
9. Preventive System Redesign (Long-term)
10. Detailed Driver Diagram:
    - Aim
    - Primary Drivers
    - Secondary Drivers
    - Example Interventions

Write in professional healthcare quality language.
Be specific, analytical, and non-generic.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an ICU patient safety expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content

# ==========================================================
# GENERATE RCA
# ==========================================================

if st.button("🚀 Generate Advanced RCA"):

    detected_domains = classify_domains(description)

    st.markdown("## 🔎 Deterministic Domain Classification")
    for d in detected_domains:
        st.markdown(f"- **{d}**")

    st.markdown("---")

    # ======================================================
    # FISHBONE DIAGRAM
    # ======================================================

    st.markdown("## 🐟 Fishbone Diagram")

    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("Effect", problem_statement if problem_statement else "ICU Incident")

    for d in detected_domains:
        dot.node(d)
        dot.edge(d, "Effect")

    st.graphviz_chart(dot)

    st.markdown("---")

    # ======================================================
    # 5 WHYS
    # ======================================================

    st.markdown("## 🔍 5 Whys Analysis")

    why_df = pd.DataFrame({
        "Level": ["Problem", "Why 1", "Why 2", "Why 3", "Why 4", "Why 5"],
        "Statement": [
            problem_statement,
            f"Failure within {detected_domains[0]} domain",
            "Safeguard weakness",
            "Monitoring gap",
            "System design limitation",
            "Organizational reliability weakness"
        ]
    })

    st.table(why_df)

    st.markdown("---")

    # ======================================================
    # AI REPORT
    # ======================================================

    with st.spinner("Generating Institutional AI RCA Report..."):
        ai_report = generate_advanced_ai_rca(description, detected_domains)

    st.markdown("## 📑 Institutional RCA Report")

    with st.expander("View Detailed AI Analysis", expanded=True):
        st.markdown(ai_report)

    st.success("RCA Analysis Completed Successfully")

