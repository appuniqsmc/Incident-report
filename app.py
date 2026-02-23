import streamlit as st
import pandas as pd
import graphviz
from datetime import datetime

st.set_page_config(page_title="ICU Incident RCA Platform", layout="wide")

st.title("ICU Incident Reporting & Root Cause Analysis Platform")
st.caption("Structured ICU safety event reporting with automated RCA, Fishbone and Driver diagrams")

# ================================
# INCIDENT REPORTING FORM
# ================================

st.header("New ICU Incident Report")

with st.form("incident_form"):

    col1, col2 = st.columns(2)

    with col1:
        incident_date = st.date_input("Incident Date", datetime.today())
        shift = st.selectbox("Shift", ["Morning", "Evening", "Night"])
        location = st.selectbox("ICU Location", ["Medical ICU", "Surgical ICU", "Cardiac ICU", "Neuro ICU"])
        severity = st.selectbox("Severity Level",
                                ["Near Miss", "Mild Harm", "Moderate Harm", "Severe Harm", "Sentinel Event"])

    with col2:
        incident_type = st.selectbox("Incident Type",
                                     ["Medication Error", "Airway/Ventilator Event", "Central Line Issue",
                                      "Sepsis Delay", "Diagnostic Delay", "Equipment Malfunction",
                                      "Handover Communication", "Fall", "Pressure Injury",
                                      "Transfusion Reaction"])

        patient_age = st.number_input("Patient Age", 0, 100, 60)
        nurse_patient_ratio = st.slider("Nurse-to-Patient Ratio", 1.0, 4.0, 2.5)
        workload_level = st.slider("Workload Pressure (1=Normal)", 0.5, 2.0, 1.0)

    description = st.text_area("Detailed Incident Description")

    submitted = st.form_submit_button("Generate RCA Analysis")

# ================================
# RULE-BASED RCA ENGINE
# ================================

DOMAIN_RULES = {
    "Human Factors": ["fatigue", "calculation", "forgot", "inattention", "dose error"],
    "Communication": ["handover", "not informed", "miscommunication", "unclear"],
    "Protocol/Process": ["protocol not followed", "no checklist", "guideline absent", "delay"],
    "Equipment": ["malfunction", "alarm failure", "pump failure", "device"],
    "Environment": ["busy", "overcrowded", "noise"],
    "Staffing": ["short staff", "no senior", "inadequate staffing"]
}

DRIVER_MAP = {
    "Human Factors": {
        "Primary": "Staff Competency & Fatigue Management",
        "Secondary": "Training & Rest Compliance",
        "Intervention": "Quarterly competency audit + fatigue monitoring"
    },
    "Communication": {
        "Primary": "Structured Handover Reliability",
        "Secondary": "SBAR & Checklist Use",
        "Intervention": "Mandatory SBAR digital template"
    },
    "Protocol/Process": {
        "Primary": "Protocol Standardization",
        "Secondary": "Checklist Enforcement",
        "Intervention": "Monthly compliance audit"
    },
    "Equipment": {
        "Primary": "Device Reliability",
        "Secondary": "Preventive Maintenance",
        "Intervention": "Automated maintenance tracking"
    },
    "Environment": {
        "Primary": "ICU Workflow Optimization",
        "Secondary": "Noise & Distraction Control",
        "Intervention": "Environmental safety rounds"
    },
    "Staffing": {
        "Primary": "Adequate Staffing Model",
        "Secondary": "Skill Mix Optimization",
        "Intervention": "Dynamic staffing allocation model"
    }
}

def classify_domains(text):
    text = text.lower()
    detected = []
    for domain, keywords in DOMAIN_RULES.items():
        for word in keywords:
            if word in text:
                detected.append(domain)
                break
    return list(set(detected))

# ================================
# RCA GENERATION
# ================================

if submitted:

    st.divider()
    st.header("Root Cause Analysis Output")

    detected_domains = classify_domains(description)

    # Structured RCA Narrative
    st.subheader("Structured RCA Narrative")

    rca_text = f"""
    Incident Type: {incident_type}

    The event occurred during the {shift} shift in the {location}.
    Severity classified as: {severity}.

    Based on the description and contextual parameters (staffing ratio: {nurse_patient_ratio}, workload index: {workload_level}),
    the following contributing domains were identified:
    """

    if detected_domains:
        for d in detected_domains:
            rca_text += f"\n- {d}"
    else:
        rca_text += "\n- No explicit domain detected (requires manual review)."

    st.write(rca_text)

    # ================================
    # FISHBONE DIAGRAM
    # ================================

    st.subheader("Fishbone Diagram")

    dot = graphviz.Digraph()
    dot.node("Incident", incident_type)

    for d in detected_domains:
        dot.node(d)
        dot.edge(d, "Incident")

    st.graphviz_chart(dot)

    # ================================
    # DRIVER DIAGRAM
    # ================================

    st.subheader("Driver Diagram")

    driver_dot = graphviz.Digraph()
    driver_dot.node("Aim", "Reduce Similar ICU Incidents")

    for d in detected_domains:
        primary = DRIVER_MAP[d]["Primary"]
        secondary = DRIVER_MAP[d]["Secondary"]
        intervention = DRIVER_MAP[d]["Intervention"]

        driver_dot.node(primary)
        driver_dot.node(secondary)
        driver_dot.node(intervention)

        driver_dot.edge("Aim", primary)
        driver_dot.edge(primary, secondary)
        driver_dot.edge(secondary, intervention)

    st.graphviz_chart(driver_dot)

    # ================================
    # INCIDENT REPORT SUMMARY TABLE
    # ================================

    st.subheader("Incident Reporting Summary")

    summary_df = pd.DataFrame({
        "Parameter": [
            "Date", "Shift", "Location", "Incident Type",
            "Severity", "Patient Age", "Nurse-Patient Ratio", "Workload Index"
        ],
        "Value": [
            incident_date, shift, location, incident_type,
            severity, patient_age, nurse_patient_ratio, workload_level
        ]
    })

    st.table(summary_df)

    st.success("RCA Analysis Generated Successfully")

