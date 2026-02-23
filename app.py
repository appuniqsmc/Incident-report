import streamlit as st
import graphviz
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
from datetime import datetime

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(page_title="ICU Safety Intelligence Dashboard", layout="wide")

st.title("🏥 ICU Incident Intelligence Dashboard")
st.markdown("Comprehensive Institutional Incident Analysis Platform")

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
    time_to_detection = st.number_input("Time to Detection (minutes)", 0, 1440, 30)

with col2:
    incident_type = st.selectbox("Incident Type",
                                 ["Medication Error",
                                  "Ventilator Event",
                                  "Central Line Event",
                                  "Procedure Error",
                                  "Communication Failure",
                                  "Equipment Failure",
                                  "Other"])
    problem_statement = st.text_input("Problem Statement")

description = st.text_area("Detailed Incident Description", height=150)

st.markdown("---")

# ==========================================================
# SEVERITY CLASSIFICATION
# ==========================================================

def classify_severity(text, detection_time):
    text = text.lower()
    sentinel = False

    if any(word in text for word in ["death", "expired"]):
        sentinel = True
        return 5, "Death", sentinel
    if any(word in text for word in ["cardiac arrest", "organ failure", "shock"]):
        sentinel = True
        return 4, "Severe Harm", sentinel
    if any(word in text for word in ["prolonged stay", "intervention required"]):
        return 3, "Moderate Harm", sentinel
    if any(word in text for word in ["temporary", "minor injury"]):
        return 2, "Mild Harm", sentinel
    if detection_time < 10:
        return 1, "Near Miss", sentinel

    return 1, "No Harm", sentinel

# ==========================================================
# DOMAIN CLASSIFICATION
# ==========================================================

DOMAIN_RULES = {
    "People / Staff": ["missed", "error", "incorrect", "forgot", "fatigue"],
    "Communication": ["handover", "verbal", "unclear"],
    "Policies / Procedures": ["protocol", "guideline", "checklist"],
    "Equipment / Technology": ["pump", "alarm", "malfunction"],
    "Environment": ["busy", "overcrowded", "noise"],
    "Patient Factors": ["unstable", "complex"]
}

def classify_domains(text):
    text = text.lower()
    scores = {}
    for domain, keywords in DOMAIN_RULES.items():
        score = 0
        for word in keywords:
            if re.search(r"\b" + re.escape(word) + r"\b", text):
                score += 1
        scores[domain] = score
    return scores

# ==========================================================
# GENERATE ANALYSIS
# ==========================================================

if st.button("🚀 Generate Full Incident Dashboard"):

    severity_score, severity_label, sentinel_flag = classify_severity(description, time_to_detection)
    domain_scores = classify_domains(description)

    # ------------------------------------------------------
    # STANDARD INCIDENT REPORT SUMMARY
    # ------------------------------------------------------

    st.markdown("## 📊 Standardized Incident Reporting Summary")

    report_df = pd.DataFrame({
        "Field": ["Date", "Shift", "Unit", "Incident Type",
                  "Severity", "Time to Detection (min)", "Sentinel Event"],
        "Value": [incident_date, shift, unit, incident_type,
                  severity_label, time_to_detection,
                  "YES" if sentinel_flag else "NO"]
    })

    st.table(report_df)

    st.markdown("---")

    # ------------------------------------------------------
    # RISK MATRIX (Likelihood × Severity)
    # ------------------------------------------------------

    st.markdown("## 🔥 Risk Matrix")

    likelihood = min(5, max(1, int(time_to_detection / 30) + 1))
    risk_score = severity_score * likelihood

    st.write(f"Severity Score: {severity_score}")
    st.write(f"Likelihood Score (based on detection delay): {likelihood}")
    st.write(f"Overall Risk Score: {risk_score}")

    # Heatmap-like visual
    fig, ax = plt.subplots()
    matrix = np.zeros((5, 5))
    matrix[severity_score-1][likelihood-1] = risk_score
    ax.imshow(matrix, cmap="Reds")
    ax.set_title("Risk Position")
    st.pyplot(fig)

    st.markdown("---")

    # ------------------------------------------------------
    # TIME TO DETECTION BAR
    # ------------------------------------------------------

    st.markdown("## ⏱ Time-to-Detection Analysis")

    fig2, ax2 = plt.subplots()
    ax2.bar(["Detection Time"], [time_to_detection])
    ax2.set_ylabel("Minutes")
    st.pyplot(fig2)

    st.markdown("---")

    # ------------------------------------------------------
    # DOMAIN RADAR CHART
    # ------------------------------------------------------

    st.markdown("## 🧠 Contributing Domain Analysis")

    labels = list(domain_scores.keys())
    values = list(domain_scores.values())

    fig3 = plt.figure()
    ax3 = fig3.add_subplot(111, polar=True)
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
    values += values[:1]
    angles = np.concatenate((angles, [angles[0]]))

    ax3.plot(angles, values)
    ax3.fill(angles, values, alpha=0.25)
    ax3.set_xticks(angles[:-1])
    ax3.set_xticklabels(labels)
    st.pyplot(fig3)

    st.markdown("---")

    # ------------------------------------------------------
    # FISHBONE
    # ------------------------------------------------------

    st.markdown("## 🐟 Fishbone Diagram")

    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("Effect", problem_statement if problem_statement else "ICU Incident")

    for domain, score in domain_scores.items():
        if score > 0:
            dot.node(domain)
            dot.edge(domain, "Effect")

    st.graphviz_chart(dot)

    st.markdown("---")

    # ------------------------------------------------------
    # SWISS CHEESE MODEL
    # ------------------------------------------------------

    st.markdown("## 🧀 Swiss Cheese Safety Layer Model")

    cheese = graphviz.Digraph()
    cheese.attr(rankdir="LR")
    cheese.node("Layer1", "Protocol Layer")
    cheese.node("Layer2", "Training Layer")
    cheese.node("Layer3", "Monitoring Layer")
    cheese.node("Event", "Incident Occurred")

    cheese.edge("Layer1", "Layer2")
    cheese.edge("Layer2", "Layer3")
    cheese.edge("Layer3", "Event")

    st.graphviz_chart(cheese)

    st.markdown("---")

    # ------------------------------------------------------
    # DRIVER DIAGRAM
    # ------------------------------------------------------

    st.markdown("## 🎯 Driver Diagram")

    driver = graphviz.Digraph()
    driver.attr(rankdir="LR")

    driver.node("Aim", "Reduce Similar ICU Incidents")
    driver.node("Primary", "System Reliability")
    driver.node("Secondary", "Checklist & Training")
    driver.node("Intervention", "Audit & Monitoring")

    driver.edge("Aim", "Primary")
    driver.edge("Primary", "Secondary")
    driver.edge("Secondary", "Intervention")

    st.graphviz_chart(driver)

    st.markdown("---")

    # ------------------------------------------------------
    # FINAL INSTITUTIONAL SUMMARY
    # ------------------------------------------------------

    st.markdown("## 📑 Institutional Incident Analysis Summary")

    st.markdown(f"""
**Severity Classification:** {severity_label}  
**Overall Risk Score:** {risk_score}  
**Primary Contributing Domains:** {', '.join([d for d, s in domain_scores.items() if s > 0])}  

**Recommended Actions:**
- Reinforce checklist adherence  
- Conduct structured audit  
- Improve detection time  
- Staff education & system redesign  

""")

    if sentinel_flag:
        st.error("⚠ Sentinel Event Detected — Immediate Executive Review Required")

    st.success("Comprehensive ICU Incident Dashboard Generated")

