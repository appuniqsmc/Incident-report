import streamlit as st
import graphviz
import pandas as pd
import re
from datetime import datetime

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(page_title="ICU Safety Intelligence Platform", layout="wide")

st.markdown("""
# 🏥 ICU Safety Intelligence Platform  
Institutional RCA + Severity Grading + Training Simulation
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
# MEDICATION ERROR SUBCLASSIFICATION
# ==========================================================

def classify_medication_error(text):
    text = text.lower()

    if "wrong dose" in text or "overdose" in text:
        return "Wrong Dose"
    if "missed" in text or "omitted" in text:
        return "Omission Error"
    if "wrong drug" in text:
        return "Wrong Drug"
    if "wrong route" in text:
        return "Wrong Route"
    if "wrong time" in text:
        return "Wrong Time"
    return "Not Applicable"

# ==========================================================
# SEVERITY CLASSIFICATION + SENTINEL FLAG
# ==========================================================

def classify_severity(text, detection_time):

    text = text.lower()
    sentinel = False

    if any(word in text for word in ["death", "expired"]):
        sentinel = True
        return "Death", "ICU Grade 5", "NCC MERP I", sentinel

    if any(word in text for word in ["cardiac arrest", "organ failure", "shock"]):
        sentinel = True
        return "Severe Harm", "ICU Grade 4", "NCC MERP H", sentinel

    if any(word in text for word in ["icu transfer", "reintubation", "major bleed"]):
        return "Severe Harm", "ICU Grade 4", "NCC MERP H", sentinel

    if any(word in text for word in ["prolonged stay", "intervention required"]):
        return "Moderate Harm", "ICU Grade 3", "NCC MERP F-G", sentinel

    if any(word in text for word in ["temporary", "minor injury", "hypoglycemia"]):
        return "Mild Harm", "ICU Grade 2", "NCC MERP E", sentinel

    if detection_time < 10:
        return "Near Miss", "ICU Grade 1", "NCC MERP B-D", sentinel

    return "No Harm", "ICU Grade 1", "NCC MERP A-B", sentinel

# ==========================================================
# DOMAIN CLASSIFICATION
# ==========================================================

DOMAIN_RULES = {
    "People / Staff": ["missed", "error", "incorrect", "forgot", "fatigue"],
    "Communication": ["handover", "verbal", "unclear", "not informed"],
    "Policies / Procedures": ["protocol", "guideline", "checklist", "delay"],
    "Equipment / Technology": ["pump", "alarm", "malfunction", "ventilator"],
    "Environment": ["busy", "overcrowded", "noise", "shortage"],
    "Patient Factors": ["unstable", "complex"]
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
# WHAT-IF TRAINING SIMULATION
# ==========================================================

def simulate_training_effect(severity_grade):

    grade_map = {
        "ICU Grade 5": 5,
        "ICU Grade 4": 4,
        "ICU Grade 3": 3,
        "ICU Grade 2": 2,
        "ICU Grade 1": 1
    }

    baseline = grade_map[severity_grade]

    improved = max(1, baseline - 1)

    return baseline, improved

# ==========================================================
# RCA GENERATION
# ==========================================================

if st.button("🚀 Generate Full ICU Analysis"):

    med_subtype = classify_medication_error(description)
    severity_label, icu_grade, ncc_merp, sentinel_flag = classify_severity(description, time_to_detection)
    detected_domains = classify_domains(description)

    # ------------------------------------------------------
    # SEVERITY OUTPUT
    # ------------------------------------------------------

    st.markdown("## 📊 Severity & Grading Classification")

    severity_df = pd.DataFrame({
        "Metric": ["Severity", "ICU-Specific Grade", "NCC MERP Category",
                   "Sentinel Event Flag", "Medication Error Subtype"],
        "Result": [
            severity_label,
            icu_grade,
            ncc_merp,
            "YES" if sentinel_flag else "NO",
            med_subtype
        ]
    })

    st.table(severity_df)

    # ------------------------------------------------------
    # DOMAIN OUTPUT
    # ------------------------------------------------------

    st.markdown("## 🔎 Contributing Domains")
    for d in detected_domains:
        st.markdown(f"- **{d}**")

    # ------------------------------------------------------
    # FISHBONE
    # ------------------------------------------------------

    st.markdown("## 🐟 Fishbone Diagram")

    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("Effect", problem_statement if problem_statement else "ICU Incident")

    for d in detected_domains:
        dot.node(d)
        dot.edge(d, "Effect")

    st.graphviz_chart(dot)

    # ------------------------------------------------------
    # 5 WHYS
    # ------------------------------------------------------

    st.markdown("## 🔍 5 Whys Analysis")

    why_df = pd.DataFrame({
        "Level": ["Problem", "Why 1", "Why 2", "Why 3", "Why 4", "Why 5"],
        "Statement": [
            problem_statement,
            f"Failure in {detected_domains[0]} domain",
            "Barrier weakness",
            "Monitoring gap",
            "System design limitation",
            "Organizational reliability gap"
        ]
    })

    st.table(why_df)

    # ------------------------------------------------------
    # WHAT-IF SIMULATION
    # ------------------------------------------------------

    st.markdown("## 🎓 What-If Training Simulation")

    baseline_grade, improved_grade = simulate_training_effect(icu_grade)

    st.write(f"Baseline ICU Grade: {baseline_grade}")
    st.write(f"If detection improved by 50% or checklist enforced:")
    st.write(f"Projected ICU Grade: {improved_grade}")

    if sentinel_flag:
        st.error("⚠ Sentinel Event – Immediate institutional review required")

    st.success("Comprehensive ICU Safety Analysis Completed")


