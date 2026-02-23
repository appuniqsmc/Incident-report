import streamlit as st
import graphviz
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

st.title("ICU Incident Root Cause Analysis Platform")
st.caption("Fishbone Diagram + Driver Thinking + 5 Whys Technique")

# =====================================================
# INCIDENT BASIC DETAILS
# =====================================================

st.header("Incident Details")

col1, col2 = st.columns(2)

with col1:
    incident_date = st.date_input("Incident Date", datetime.today())
    shift = st.selectbox("Shift", ["Morning", "Evening", "Night"])
    unit = st.selectbox("ICU Unit",
                        ["Medical ICU", "Surgical ICU", "Cardiac ICU", "Neuro ICU"])

with col2:
    severity = st.selectbox("Severity",
                            ["Near Miss", "Mild", "Moderate", "Severe", "Sentinel"])
    incident_type = st.text_input("Incident Type (e.g., Medication Error)")
    problem_statement = st.text_input("Problem Statement (Effect)")

st.divider()

# =====================================================
# FISHBONE INPUT SECTIONS
# =====================================================

st.header("Fishbone Contributing Factors")

categories = [
    "People / Staff",
    "Policies / Procedures",
    "Equipment / Technology",
    "Environment",
    "Communication",
    "Patient Factors"
]

causes = {}

for cat in categories:
    st.subheader(cat)
    text = st.text_area(
        f"List causes under {cat} (one per line)",
        height=120,
        key=cat
    )
    causes[cat] = [c.strip() for c in text.split("\n") if c.strip() != ""]

st.divider()

# =====================================================
# GENERATE FISHBONE DIAGRAM
# =====================================================

if st.button("Generate Fishbone Diagram"):

    st.subheader("Fishbone Diagram")

    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir="LR")
    dot.node("Effect", problem_statement if problem_statement else "ICU Incident")

    for cat in categories:
        if causes[cat]:
            dot.node(cat)
            dot.edge(cat, "Effect")

            for cause in causes[cat]:
                dot.node(f"{cat}_{cause}", cause)
                dot.edge(f"{cat}_{cause}", cat)

    st.graphviz_chart(dot)

# =====================================================
# DRIVER THINKING (Improvement Logic)
# =====================================================

st.divider()
st.header("Driver Diagram (Improvement Planning)")

aim = st.text_input("Aim Statement (e.g., Reduce Medication Errors by 30%)")

primary_drivers = st.text_area("Primary Drivers (one per line)")
secondary_drivers = st.text_area("Secondary Drivers (one per line)")
interventions = st.text_area("Change Ideas / Interventions (one per line)")

if st.button("Generate Driver Diagram"):

    driver_dot = graphviz.Digraph(format="png")
    driver_dot.attr(rankdir="LR")

    driver_dot.node("Aim", aim if aim else "Improve ICU Safety")

    primary_list = [x.strip() for x in primary_drivers.split("\n") if x.strip()]
    secondary_list = [x.strip() for x in secondary_drivers.split("\n") if x.strip()]
    intervention_list = [x.strip() for x in interventions.split("\n") if x.strip()]

    for p in primary_list:
        driver_dot.node(p)
        driver_dot.edge("Aim", p)

        for s in secondary_list:
            driver_dot.node(s)
            driver_dot.edge(p, s)

            for i in intervention_list:
                driver_dot.node(i)
                driver_dot.edge(s, i)

    st.graphviz_chart(driver_dot)

# =====================================================
# 5 WHYS TECHNIQUE
# =====================================================

st.divider()
st.header("5 Whys Root Cause Exploration")

why1 = st.text_input("Why 1?")
why2 = st.text_input("Why 2?")
why3 = st.text_input("Why 3?")
why4 = st.text_input("Why 4?")
why5 = st.text_input("Why 5?")

if st.button("Generate 5 Whys Analysis"):

    st.subheader("5 Whys Chain")

    why_chain = pd.DataFrame({
        "Level": ["Problem", "Why 1", "Why 2", "Why 3", "Why 4", "Why 5"],
        "Statement": [
            problem_statement,
            why1,
            why2,
            why3,
            why4,
            why5
        ]
    })

    st.table(why_chain)

    st.success("5 Whys Analysis Completed")

# =====================================================
# SUMMARY EXPORT VIEW
# =====================================================

st.divider()
st.header("Incident Summary")

summary_df = pd.DataFrame({
    "Field": [
        "Date", "Shift", "Unit",
        "Severity", "Incident Type", "Problem Statement"
    ],
    "Value": [
        incident_date,
        shift,
        unit,
        severity,
        incident_type,
        problem_statement
    ]
})

st.table(summary_df)


