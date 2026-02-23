"""
ICU Safety Intelligence Dashboard v6.0
Gemini Powered — Fishbone + 5 Whys + Driver Diagram + Detailed Analysis
FREE TIER COMPATIBLE
"""

import streamlit as st
import graphviz
import matplotlib.pyplot as plt
import numpy as np
import requests
import json
import re
import io
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

st.set_page_config(page_title="ICU Incident Intelligence", layout="wide")
st.title("🏥 ICU Incident Intelligence Engine v6.0")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("🔑 Gemini API")
    api_key = st.text_input("Google Gemini API Key", type="password",
                            help="Get free key at https://aistudio.google.com/app/apikey")

    st.markdown("---")
    facility = st.text_input("Hospital Name", "General Hospital ICU")
    unit = st.selectbox("ICU Type", ["Medical ICU","Surgical ICU","Cardiac ICU"])

# ─────────────────────────────────────────────
# SEVERITY ENGINE
# ─────────────────────────────────────────────

def auto_severity(text):
    t = text.lower()
    if "death" in t or "expired" in t: return 5
    if "arrest" in t or "organ failure" in t: return 4
    if "intervention" in t or "resuscitation" in t: return 3
    if "minor" in t or "temporary" in t: return 2
    return 1

def calculate_rpn(sev, like, detect):
    return sev * like * detect

# ─────────────────────────────────────────────
# GEMINI ENGINE
# ─────────────────────────────────────────────

GEMINI_MODEL = "gemini-1.5-flash"

SYSTEM_PROMPT = """
You are an ICU patient safety and quality improvement expert.

Return ONLY valid JSON.
No markdown.
No extra text.

JSON must include:
{
"detailed_analysis":"",
"fishbone":{
  "Human Factors":[],
  "Communication":[],
  "Equipment":[],
  "Environment":[],
  "Policy/Procedure":[],
  "Training":[]
},
"five_whys":[{"why":1,"question":"","answer":""}],
"driver_diagram":{
  "aim":"",
  "primary_drivers":[],
  "secondary_drivers":[]
}
}
"""

def call_gemini(api_key, prompt):

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    payload = {
        "contents":[{"parts":[{"text":prompt}]}],
        "generationConfig":{"temperature":0.2,"maxOutputTokens":2500}
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

def run_ai(api_key, incident_text, sev, rpn):

    prompt = f"""
Analyze ICU incident and return JSON as specified.

Incident:
{incident_text}

Severity: {sev}/5
RPN: {rpn}/125
Facility: {facility}
Unit: {unit}
"""

    return call_gemini(api_key, SYSTEM_PROMPT + prompt)

# ─────────────────────────────────────────────
# PDF EXPORT
# ─────────────────────────────────────────────

def build_pdf(incident_text, ai_data):

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("ICU Incident Intelligence Report", styles["Title"]))
    story.append(Spacer(1,12))

    story.append(Paragraph("Incident Description:", styles["Heading2"]))
    story.append(Paragraph(incident_text, styles["Normal"]))
    story.append(Spacer(1,12))

    if ai_data:
        story.append(Paragraph("Detailed Analysis:", styles["Heading2"]))
        story.append(Paragraph(ai_data.get("detailed_analysis",""), styles["Normal"]))
        story.append(Spacer(1,12))

    doc.build(story)
    buf.seek(0)
    return buf.read()

# ─────────────────────────────────────────────
# INPUT
# ─────────────────────────────────────────────

incident_text = st.text_area("Paste ICU Incident Report", height=200)
detect_time = st.number_input("Detection Time (min)",0,300,30)
prior_sim = st.number_input("Prior Similar Incidents",0,20,0)

if st.button("🚀 Run Intelligence Engine"):

    if not incident_text:
        st.error("Paste incident first.")
    else:
        sev = auto_severity(incident_text)
        like = min(5, prior_sim+1)
        detect = min(5, int(detect_time/20)+1)
        rpn = calculate_rpn(sev, like, detect)

        st.metric("Severity", f"{sev}/5")
        st.metric("RPN", f"{rpn}/125")

        if api_key:

            with st.spinner("🤖 Gemini generating analysis..."):
                raw = run_ai(api_key, incident_text, sev, rpn)

            try:
                clean = re.sub(r"```|json","",raw)
                ai_data = json.loads(clean)
            except:
                st.error("AI JSON parsing failed.")
                st.code(raw)
                st.stop()

            # ──────────────────────
            # Detailed Analysis
            # ──────────────────────
            st.header("📋 Detailed Incident Analysis")
            st.write(ai_data.get("detailed_analysis",""))

            # ──────────────────────
            # Fishbone Diagram
            # ──────────────────────
            st.header("🐟 Fishbone (Ishikawa) Diagram")

            fish = ai_data.get("fishbone",{})
            g = graphviz.Digraph()
            g.node("Effect","ICU Incident")
            for category, causes in fish.items():
                g.node(category, category)
                g.edge(category,"Effect")
                for cause in causes:
                    g.node(f"{category}-{cause}", cause)
                    g.edge(f"{category}-{cause}", category)
            st.graphviz_chart(g)

            # ──────────────────────
            # 5 Whys
            # ──────────────────────
            st.header("❓ 5 Whys Analysis")

            five = ai_data.get("five_whys",[])
            g2 = graphviz.Digraph()
            prev = "Problem"
            g2.node(prev,"Incident")
            for w in five:
                node = f"Why{w['why']}"
                g2.node(node, w["answer"])
                g2.edge(prev,node)
                prev = node
            st.graphviz_chart(g2)

            # ──────────────────────
            # Driver Diagram
            # ──────────────────────
            st.header("🚗 Driver Diagram")

            driver = ai_data.get("driver_diagram",{})
            g3 = graphviz.Digraph()
            g3.node("Aim", driver.get("aim","Aim"))
            for p in driver.get("primary_drivers",[]):
                g3.node(p,p)
                g3.edge(p,"Aim")
            for s in driver.get("secondary_drivers",[]):
                g3.node(s,s)
                g3.edge(s,p)
            st.graphviz_chart(g3)

            # PDF
            st.markdown("---")
            pdf = build_pdf(incident_text, ai_data)
            st.download_button("📥 Download PDF Report",
                               pdf,
                               file_name=f"ICU_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                               mime="application/pdf")

        else:
            st.warning("Enter Gemini API key in sidebar.")

