import streamlit as st
import graphviz
import pandas as pd
import re
from datetime import datetime

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(page_title="ICU RCA Intelligence Platform", layout="wide")

st.markdown("""
# 🏥 ICU Root Cause Analysis Platform
Deterministic Institutional-Grade RCA Engine (No API Required)
""")

st.markdown("---")

# ==========================================================
# INCIDENT INPUT
# ==========================================================

st.subheader("📋 Incident Information")

col1, col2 = st.columns(2)

with col1:
    incident_date = st.date_input("Incident Date", datetime.today())
    shift = st.selectbox("Shift", ["Morning", "Evening", "Night"])
    unit = st.selectbox("ICU Unit",
                        ["Medical ICU", "Surgical ICU", "Cardiac ICU", "Neuro ICU"])

with col2:
    severity = st.selectbox("Severity Classification",
                            ["Near Miss", "Mild Harm", "Moderate Harm", "Severe Harm", "Sentinel Event"])
    incident_type = st.text_input("Incident Type")
    problem_statement = st.text_input("Problem Statement")

description = st.text_area("Detailed Incident Description", height=150)

st.markdown("---")

# ==========================================================
# SMART DOMAIN ENGINE (NO AI)
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
# RCA GENERATOR (PROGRAMMATIC)
# ==========================================================

def generate_structured_rca(text, domains, severity):

    severity_score = {
        "Near Miss": 1,
        "Mild Harm": 2,
        "Moderate Harm": 3,
        "Severe Harm": 4,
        "Sentinel Event": 5
    }[severity]

    recurrence_risk = "Moderate"
    if severity_score >= 4:
        recurrence_risk = "High"
    elif severity_score <= 2:
        recurrence_risk = "Low"

    report = f"""
## 1. Executive Summary
The incident involving **{incident_type}** occurred in the {unit} during the {shift} shift.
Severity classification: **{severity}**.
Primary contributing domains identified: {', '.join(domains)}.

## 2. Event Reconstruction
Based on the description, the event represents a deviation from expected safe clinical workflow.
The failure likely occurred at the interface between clinical task execution and system safeguards.

## 3. Active Failures
These represent frontline breakdowns in execution:
- Task-level lapse within {domains[0]} domain
- Immediate breakdown in procedural reliability

## 4. Contributing Factors by Domain
"""

    for d in domains:
        report += f"\n### {d}\n"
        report += "- Operational vulnerability detected\n"
        report += "- Safety barrier inadequacy\n"

    report += f"""

## 5. Latent System-Level Failures
- Insufficient redundancy within workflow
- Lack of real-time error detection mechanisms
- Limited feedback loop for safety improvement

## 6. Barrier Analysis (Swiss Cheese Model)
The following safeguards appear insufficient:
- Standard operating procedure enforcement
- Cross-check verification mechanisms
- Supervisory escalation pathways

## 7. Risk Matrix Commentary
Estimated recurrence likelihood: **{recurrence_risk}**
Severity impact: **Level {severity_score} / 5**
Overall risk exposure: Requires structured intervention.

## 8. Immediate Corrective Actions
- Incident review with involved staff
- Immediate workflow clarification
- Reinforcement of critical checklist steps

## 9. Long-Term Preventive Strategy
- Structured audit cycle
- Staff competency reassessment
- Protocol redesign for redundancy
- Monitoring dashboard implementation

## 10. Driver Diagram Framework
**Aim:** Reduce recurrence of similar {incident_type} events  
**Primary Drivers:** Reliability, Communication Integrity, Workflow Standardization  
**Secondary Drivers:** Checklist compliance, Training reinforcement, Escalation clarity  
**Change Ideas:** Digital prompts, double-verification process, monthly safety audit
"""

    return report

# ==========================================================
# RCA GENERATION BUTTON
# ==========================================================

if st.button("🚀 Generate Institutional RCA"):

    detected_domains = classify_domains(description)

    st.markdown("## 🔎 Domain Classification")
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
            "Safeguard breakdown",
            "Monitoring weakness",
            "System design limitation",
            "Organizational reliability gap"
        ]
    })

    st.table(why_df)

    st.markdown("---")

    # ======================================================
    # STRUCTURED RCA REPORT
    # ======================================================

    st.markdown("## 📑 Institutional RCA Report")

    report = generate_structured_rca(description, detected_domains, severity)
    st.markdown(report)

    st.success("RCA Completed Successfully")


