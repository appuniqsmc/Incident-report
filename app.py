"""
ICU Safety Intelligence Dashboard — Deep Analysis Engine v5.0
Gemini-Powered ICU Incident Intelligence (FREE TIER)
"""

import streamlit as st
import graphviz
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import re
import io
import json
import requests
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

st.set_page_config(page_title="ICU Deep Analysis Engine", layout="wide")

st.title("🏥 ICU Deep Analysis Engine — Gemini Powered")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("🔑 Gemini Configuration")
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        help="Get FREE key at https://aistudio.google.com/app/apikey"
    )

    st.markdown("---")
    st.header("🏥 Facility Context")
    facility_name = st.text_input("Hospital Name", "General Hospital ICU")
    unit_type = st.selectbox("ICU Type", ["Medical ICU", "Surgical ICU", "Cardiac ICU"])
    benchmark_rpn = st.number_input("Benchmark RPN", 0, 125, 35)

# ─────────────────────────────────────────────
# CLASSIFICATION
# ─────────────────────────────────────────────

SEVERITY_CFG = {
    5: {"label":"Death","ncc":"I"},
    4: {"label":"Severe Harm","ncc":"H"},
    3: {"label":"Moderate Harm","ncc":"F-G"},
    2: {"label":"Mild Harm","ncc":"D-E"},
    1: {"label":"No Harm","ncc":"A-C"},
}

def auto_severity(text):
    t = text.lower()
    if any(x in t for x in ["death","died","expired"]): return 5
    if any(x in t for x in ["arrest","organ failure"]): return 4
    if any(x in t for x in ["intervention","resuscitation"]): return 3
    if any(x in t for x in ["temporary","minor"]): return 2
    return 1

def rpn(sev, like, detect):
    return sev * like * detect

# ─────────────────────────────────────────────
# GEMINI AI ENGINE
# ─────────────────────────────────────────────

GEMINI_MODEL = "gemini-1.5-flash"

SYSTEM_PROMPT = """
You are an ICU Patient Safety Analyst.

Return ONLY valid JSON.
No markdown.
No explanation.
No extra text.
"""

def call_gemini(api_key, prompt, max_tokens=3000):

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts":[{"text": prompt}]}],
        "generationConfig":{
            "temperature":0.2,
            "maxOutputTokens":max_tokens
        }
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

def ai_full_analysis(api_key, incident_text, sev_score, rpn_val):

    prompt = f"""
Analyze ICU incident and return JSON with these keys:

{{
"narrative_summary":"",
"clinical_significance":"",
"system_failures":[],
"root_cause":"",
"five_whys":[],
"action_plan":[],
"risk_narrative":"",
"learning_points":[]
}}

Incident:
{incident_text}

Severity: {sev_score}/5
RPN: {rpn_val}/125
Facility: {facility_name}
"""

    return call_gemini(api_key, SYSTEM_PROMPT + prompt)

# ─────────────────────────────────────────────
# PDF EXPORT
# ─────────────────────────────────────────────

def build_pdf(text, ai_data):

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("ICU Deep Analysis Report", styles["Title"]))
    story.append(Spacer(1,12))

    story.append(Paragraph("Incident Report:", styles["Heading2"]))
    story.append(Paragraph(text, styles["Normal"]))
    story.append(Spacer(1,12))

    if ai_data:
        story.append(Paragraph("AI Narrative:", styles["Heading2"]))
        story.append(Paragraph(ai_data.get("narrative_summary",""), styles["Normal"]))
        story.append(Spacer(1,8))

        story.append(Paragraph("Clinical Significance:", styles["Heading3"]))
        story.append(Paragraph(ai_data.get("clinical_significance",""), styles["Normal"]))
        story.append(Spacer(1,8))

    doc.build(story)
    buf.seek(0)
    return buf.read()

# ─────────────────────────────────────────────
# MAIN INPUT
# ─────────────────────────────────────────────

incident_text = st.text_area("Paste ICU Incident Report", height=200)

detect_time = st.number_input("Time to Detection (min)", 0, 500, 30)
prior_sim = st.number_input("Prior Similar Incidents", 0, 20, 0)

if st.button("🚀 Run Deep Analysis"):

    if not incident_text:
        st.error("Please paste incident report.")
    else:
        sev_score = auto_severity(incident_text)
        like_score = min(5, prior_sim + 1)
        detect_score = min(5, int(detect_time/20)+1)
        rpn_val = rpn(sev_score, like_score, detect_score)

        st.metric("Severity", f"{sev_score}/5")
        st.metric("RPN", f"{rpn_val}/125")

        ai_result = None

        if api_key:
            with st.spinner("🤖 Gemini analysing..."):
                raw = ai_full_analysis(api_key, incident_text, sev_score, rpn_val)

            try:
                clean = re.sub(r"```|json","",raw)
                ai_result = json.loads(clean)
            except:
                st.error("AI response parsing failed.")
                st.code(raw)

        if ai_result:
            st.subheader("AI Narrative Summary")
            st.write(ai_result.get("narrative_summary",""))

            st.subheader("Clinical Significance")
            st.write(ai_result.get("clinical_significance",""))

            st.subheader("System Failures")
            for s in ai_result.get("system_failures",[]):
                st.write("•", s)

        st.markdown("---")

        pdf_bytes = build_pdf(incident_text, ai_result)

        st.download_button(
            "📥 Download PDF Report",
            pdf_bytes,
            file_name=f"ICU_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

