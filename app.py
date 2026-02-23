import streamlit as st
import graphviz
import pandas as pd
import re
from datetime import datetime
from openai import OpenAI

# ============================================
# CONFIG
# ============================================

st.set_page_config(layout="wide")
st.title("ICU Intelligent Root Cause Analysis Platform")
st.caption("Deterministic Domain Scoring + OpenAI Enhanced RCA")

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ============================================
# INCIDENT INPUT
# ============================================

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

st.divider()

# ============================================
# SMART DOMAIN SCORING ENGINE
# ============================================

DOMAIN_RULES = {
    "People / Staff": {
        "keywords": [
            "fatigue", "error", "mistake", "calculation",
            "incorrect", "wrong", "forgot", "inattention",
            "missed", "dose", "omitted", "insulin",
            "medication", "drug"
        ],
        "weight": 2
    },
    "Communication": {
        "keywords": [
            "handover", "verbal", "not informed",
            "miscommunication", "documentation",
            "unclear", "order"
        ],
        "weight": 2
    },
    "Policies / Procedures": {
        "keywords": [
            "protocol", "guideline", "checklist",
            "policy", "deviation", "delay"
        ],
        "weight": 2
    },
    "Equipment / Technology": {
        "keywords": [
            "pump", "alarm", "malfunction",
            "device", "ventilator", "monitor"
        ],
        "weight": 2
    },
    "Environment": {
        "keywords": [
            "busy", "overcrowded", "noise",
            "high workload", "staff shortage"
        ],
        "weight": 1
    },
    "Patient Factors": {
        "keywords": [
            "complex", "unstable", "non-compliant"
        ],
        "weight": 1
    }
}

def classify_domains(text):
    text = text.lower()
    scores = {}

    for domain, info in DOMAIN_RULES.items():
        score = 0
        for word in info["keywords"]:
            if re.search(r"\b" + re.escape(word) + r"\b", text):
                score += info["weight"]
        scores[domain] = score

    detected = [d for d, s in scores.items() if s > 0]

    if not detected:
        detected = ["People / Staff"]

    return detected, scores

# ============================================
# OPENAI RCA GENERATION
# ============================================

def generate_ai_rca(text, domains):

    prompt = f"""
You are an ICU quality and safety expert.

Perform a structured Root Cause Analysis.

Incident:
{text}

Detected contributing domains:
{domains}

Provide:
1. Concise RCA narrative
2. Latent system-level root cause
3. Recommended corrective actions
4. Preventive strategies
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a clinical quality improvement specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI generation failed: {str(e)}"

# ============================================
# GENERATE RCA
# ============================================

if st.button("Generate RCA Analysis"):

    detected_domains, scores = classify_domains(description)

    st.subheader("Domain Scoring")

    score_df = pd.DataFrame({
        "Domain": list(scores.keys()),
        "Score": list(scores.values())
    }).sort_values(by="Score", ascending=False)

    st.dataframe(score_df)

    st.subheader("Primary Contributing Domains")

    for d in detected_domains:
        st.write(f"- {d}")

    # ============================================
    # FISHBONE
    # ============================================

    st.subheader("Fishbone Diagram")

    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("Effect", problem_statement if problem_statement else "ICU Incident")

    for d in detected_domains:
        dot.node(d)
        dot.edge(d, "Effect")

    st.graphviz_chart(dot)

    # ============================================
    # 5 WHYS
    # ============================================

    st.subheader("5 Whys Structured Chain")

    why_df = pd.DataFrame({
        "Level": ["Problem", "Why 1", "Why 2", "Why 3", "Why 4", "Why 5"],
        "Statement": [
            problem_statement,
            f"Because of issues related to {detected_domains[0]}",
            "Because system safeguards were insufficient",
            "Because monitoring and audit mechanisms failed",
            "Because organizational learning gap exists",
            "Root Cause: System reliability weakness"
        ]
    })

    st.table(why_df)

    # ============================================
    # AI ENHANCED RCA
    # ============================================

    if st.checkbox("Enhance with OpenAI Narrative"):

        st.subheader("AI-Enhanced RCA")

        ai_output = generate_ai_rca(description, detected_domains)
        st.write(ai_output)

    st.success("RCA Completed Successfully")
