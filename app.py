"""
ICU Safety Intelligence Dashboard — Deep Analysis Engine v4.0
AI-powered incident analysis via Claude API + PDF export + multi-incident comparison
"""

import streamlit as st
import graphviz
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import re
import io
import json
import time
from datetime import datetime

import requests

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable, PageBreak,
                                 KeepTogether)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="ICU Deep Analysis Engine", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;500;600;700&display=swap');

html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#070c18;}
.block-container{padding-top:1.5rem;padding-bottom:3rem;}
h1,h2,h3{font-family:'JetBrains Mono',monospace!important;color:#f0f4ff!important;}

.chip{
  display:inline-block;padding:3px 12px;border-radius:20px;
  font-size:0.72rem;font-weight:600;letter-spacing:1px;
  text-transform:uppercase;font-family:'JetBrains Mono',monospace;
  margin:2px;
}

.section-hdr{
  background:linear-gradient(90deg,#0d1f3c 0%,transparent 100%);
  border-left:4px solid #38bdf8;padding:8px 18px;
  margin:26px 0 12px 0;font-family:'JetBrains Mono',monospace;
  font-size:0.72rem;color:#38bdf8;letter-spacing:3px;text-transform:uppercase;
}

.ai-box{
  background:linear-gradient(135deg,#0d1f3c 0%,#0a1628 100%);
  border:1px solid #1e3a5f;border-left:4px solid #38bdf8;
  border-radius:10px;padding:20px 24px;margin:10px 0;
  font-size:0.9rem;color:#cbd5e1;line-height:1.75;
}

.ai-box h4{color:#38bdf8!important;font-family:'JetBrains Mono',monospace!important;
  font-size:0.8rem!important;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;}

.timeline-step{
  display:flex;gap:16px;align-items:flex-start;
  background:#0d1f3c;border-radius:8px;padding:12px 16px;margin:6px 0;
}
.tnum{
  min-width:32px;height:32px;background:#38bdf8;color:#070c18;
  border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:0.82rem;font-family:'JetBrains Mono',monospace;flex-shrink:0;
}
.ttext{color:#94a3b8;font-size:0.85rem;line-height:1.6;padding-top:4px;}
.tbold{color:#e2e8f0;font-weight:600;}

.action-card{
  background:#0a1f0f;border:1px solid #166534;border-radius:8px;
  padding:14px 18px;margin:8px 0;
}
.action-card .ac-title{
  color:#4ade80;font-weight:600;font-size:0.88rem;margin-bottom:6px;
}
.action-card .ac-meta{
  display:flex;gap:12px;flex-wrap:wrap;margin-top:8px;
}
.ac-badge{
  font-size:0.7rem;padding:2px 10px;border-radius:4px;
  font-family:'JetBrains Mono',monospace;font-weight:600;
}

.warn-card{
  background:#1a1200;border:1px solid #78350f;border-radius:8px;
  padding:14px 18px;margin:8px 0;
}
.warn-card .wc-title{color:#fbbf24;font-weight:600;font-size:0.88rem;margin-bottom:4px;}

.crit-card{
  background:#1a0010;border:1px solid #881337;border-radius:8px;
  padding:14px 18px;margin:8px 0;
}
.crit-card .cc-title{color:#fb7185;font-weight:600;font-size:0.88rem;margin-bottom:4px;}

.bench-bar-wrap{
  background:#0d1f3c;border-radius:8px;padding:14px 18px;margin:6px 0;
}

.sentinel-banner{
  background:linear-gradient(90deg,#4c0519,#7f1d1d);
  border:2px solid #f43f5e;border-radius:8px;
  padding:16px 24px;text-align:center;
  font-size:1rem;font-weight:700;color:#fda4af;
  font-family:'JetBrains Mono',monospace;letter-spacing:2px;margin-bottom:20px;
}

.compare-card{
  background:#0d1f3c;border:1px solid #1e3a5f;border-radius:10px;
  padding:16px 18px;margin:6px 0;
}

div[data-testid="stMetric"]{
  background:#0d1f3c;border:1px solid #1e3a5f;
  padding:14px;border-radius:8px;
}

.stButton>button{
  background:linear-gradient(135deg,#0ea5e9,#2563eb);
  color:white;border:none;border-radius:8px;
  padding:0.65rem 2rem;font-family:'JetBrains Mono',monospace;
  font-size:0.88rem;letter-spacing:1px;font-weight:600;width:100%;
}
.stButton>button:hover{background:linear-gradient(135deg,#38bdf8,#3b82f6);}

.stTextArea textarea{
  background:#0d1f3c!important;border:1px solid #1e3a5f!important;
  color:#e2e8f0!important;font-family:'Inter',sans-serif!important;
}
.stSelectbox>label,.stTextInput>label,.stNumberInput>label,
.stTextArea>label,.stDateInput>label{
  color:#475569!important;font-size:0.75rem!important;
  letter-spacing:1px!important;text-transform:uppercase;
}
footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("# 🏥 ICU Deep Analysis Engine")
st.markdown('<p style="color:#475569;font-size:0.78rem;font-family:\'JetBrains Mono\',monospace;letter-spacing:3px;margin-top:-10px;">AI-POWERED INCIDENT INTELLIGENCE · v4.0</p>', unsafe_allow_html=True)
st.markdown("---")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input("Anthropic API Key", type="password",
                            help="Get yours at console.anthropic.com")
    st.caption("Key is never stored. Used only for this session.")
    st.markdown("---")
    st.markdown("### 🏥 Facility Context")
    facility_name   = st.text_input("Facility / Hospital Name", value="General Hospital ICU")
    unit_type       = st.selectbox("ICU Unit", ["Medical ICU","Surgical ICU","Cardiac ICU",
                                                 "Neuro ICU","Burn ICU","Paediatric ICU","Trauma ICU"])
    bed_count       = st.number_input("ICU Bed Count", 4, 200, 20)
    accreditation   = st.selectbox("Accreditation Body", ["JCI","NABH","ACHS","CCHSA","None"])
    st.markdown("---")
    st.markdown("### 📊 Benchmark Reference")
    benchmark_rpn   = st.number_input("Facility Avg RPN (benchmark)", 0, 125, 35)
    benchmark_detect= st.number_input("Facility Avg Detection Time (min)", 0, 300, 25)
    benchmark_report= st.number_input("Facility Avg Report Time (hrs)", 0, 72, 4)

# ─────────────────────────────────────────────
# SESSION STATE — incident store
# ─────────────────────────────────────────────
if "incidents" not in st.session_state:
    st.session_state.incidents = []

# ─────────────────────────────────────────────
# CLASSIFICATION ENGINE
# ─────────────────────────────────────────────
SEVERITY_CFG = {
    5: {"label":"Death",               "ncc":"I",   "color":"#f43f5e"},
    4: {"label":"Severe Harm",         "ncc":"H",   "color":"#f97316"},
    3: {"label":"Moderate Harm",       "ncc":"F-G", "color":"#f59e0b"},
    2: {"label":"Mild Harm",           "ncc":"D-E", "color":"#3b82f6"},
    1: {"label":"Near Miss / No Harm", "ncc":"A-C", "color":"#22c55e"},
}

DOMAIN_RULES = {
    "Human Factors":      ["missed","error","incorrect","forgot","fatigue","tired","distracted","confusion","rush","oversight"],
    "Communication":      ["handover","verbal","unclear","misunderstood","not documented","not informed","sbar","isbar"],
    "Policy / Procedure": ["protocol","guideline","checklist","procedure","policy","standard","not followed","bypassed"],
    "Equipment / Tech":   ["pump","alarm","malfunction","device","ventilator","monitor","failure","broken","alarm fatigue"],
    "Environment":        ["busy","overcrowded","noise","interruption","understaffed","short staffed","high acuity"],
    "Training / Knowledge":["unaware","not trained","inexperienced","knowledge gap","unfamiliar","locum","orientation"],
    "Clinical Complexity":["unstable","complex","deteriorating","comorbidities","non-compliant","agitated"],
    "Supervision":        ["unsupervised","no review","escalation missed","not escalated","no senior","consultant"],
}

def auto_severity(text, outcome=""):
    text=(text+" "+outcome).lower(); sentinel=False
    if any(w in text for w in ["death","fatal","died","expired"]): sentinel=True; return 5,sentinel
    if any(w in text for w in ["permanent harm","cardiac arrest","organ failure","anoxic","respiratory arrest"]): sentinel=True; return 4,sentinel
    if any(w in text for w in ["prolonged stay","emergency intervention","resuscitation","icu transfer","treatment required"]): return 3,sentinel
    if any(w in text for w in ["temporary","minor injury","hypoglycaemia","hypotension","temporary harm"]): return 2,sentinel
    return 1,sentinel

def classify_domains(text):
    text=text.lower(); scores={}; matched={}
    for dom,kws in DOMAIN_RULES.items():
        found=[kw for kw in kws if re.search(r"\b"+re.escape(kw)+r"\b",text)]
        scores[dom]=len(found); matched[dom]=found
    return scores,matched

def rpn(sev,like,detect): return sev*like*detect

def risk_cat(r):
    if r>=80: return "CRITICAL","#f43f5e"
    if r>=40: return "HIGH","#f97316"
    if r>=20: return "MODERATE","#f59e0b"
    return "LOW","#22c55e"

# ─────────────────────────────────────────────
# CLAUDE AI ANALYSIS
# ─────────────────────────────────────────────
def call_claude(api_key, system_prompt, user_prompt, max_tokens=2000):
    """Call Claude claude-sonnet-4-20250514 via REST API."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role":"user","content": user_prompt}],
    }
    try:
        resp = requests.post("https://api.anthropic.com/v1/messages",
                             headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]
    except requests.exceptions.HTTPError as e:
        return f"API_ERROR: {e.response.status_code} — {e.response.text[:300]}"
    except Exception as e:
        return f"API_ERROR: {str(e)}"

SYSTEM_PROMPT = """You are an expert ICU Patient Safety Analyst with deep knowledge of:
- Clinical incident investigation (root cause analysis, FMEA, Swiss Cheese Model)
- ICU nursing and medical practice
- Healthcare quality improvement frameworks (IHI, WHO, JCI standards)
- Patient safety science and human factors engineering

Your analysis is precise, evidence-based, clinically grounded, and actionable.
You write in professional healthcare quality improvement language.
Always structure your response EXACTLY as valid JSON matching the schema requested.
Return ONLY the JSON object — no markdown fences, no preamble, no explanation."""

def ai_full_analysis(api_key, incident_text, sev_score, rpn_val, domain_scores, facility):
    top_domains = [d for d,s in sorted(domain_scores.items(),key=lambda x:-x[1]) if s>0][:4]
    prompt = f"""
Analyze this ICU incident report and return a JSON object with EXACTLY these keys:

{{
  "narrative_summary": "3-4 sentence clinical narrative summarizing what happened and why it matters",
  "clinical_significance": "2-3 sentences on clinical impact and patient safety implications",
  "system_failures": ["list of 4-6 specific system failures identified"],
  "timeline": [
    {{"step":1,"phase":"Pre-incident","event":"...","latent_factor":"..."}},
    {{"step":2,"phase":"Triggering Event","event":"...","latent_factor":"..."}},
    {{"step":3,"phase":"Incident Propagation","event":"...","latent_factor":"..."}},
    {{"step":4,"phase":"Detection","event":"...","latent_factor":"..."}},
    {{"step":5,"phase":"Response","event":"...","latent_factor":"..."}},
    {{"step":6,"phase":"Aftermath","event":"...","latent_factor":"..."}}
  ],
  "root_cause_analysis": {{
    "proximate_cause": "immediate direct cause of the incident",
    "contributory_causes": ["2-4 contributory causes"],
    "root_cause": "the fundamental systemic root cause",
    "latent_conditions": ["2-3 underlying organisational/system conditions"]
  }},
  "five_whys": [
    {{"why":1,"question":"Why did the incident occur?","answer":"..."}},
    {{"why":2,"question":"Why did that happen?","answer":"..."}},
    {{"why":3,"question":"Why did that happen?","answer":"..."}},
    {{"why":4,"question":"Why did that happen?","answer":"..."}},
    {{"why":5,"question":"Why did that happen?","answer":"..."}}
  ],
  "action_plan": [
    {{"id":1,"action":"...","owner":"...","deadline":"...","priority":"CRITICAL","category":"Immediate"}},
    {{"id":2,"action":"...","owner":"...","deadline":"...","priority":"HIGH","category":"Short-term"}},
    {{"id":3,"action":"...","owner":"...","deadline":"...","priority":"HIGH","category":"Short-term"}},
    {{"id":4,"action":"...","owner":"...","deadline":"...","priority":"MODERATE","category":"Medium-term"}},
    {{"id":5,"action":"...","owner":"...","deadline":"...","priority":"MODERATE","category":"Medium-term"}},
    {{"id":6,"action":"...","owner":"...","deadline":"...","priority":"LOW","category":"Long-term"}},
    {{"id":7,"action":"...","owner":"...","deadline":"...","priority":"LOW","category":"Long-term"}}
  ],
  "risk_narrative": "2-3 sentences explaining the risk score and what it means for this unit",
  "benchmark_commentary": "2 sentences comparing this incident to typical ICU incidents of this type",
  "prevention_strategy": "3-4 sentences on the overarching prevention and improvement strategy",
  "learning_points": ["3-5 key learning points for the team"],
  "reporting_obligations": ["list any mandatory reporting obligations based on severity level {sev_score}/5"]
}}

INCIDENT REPORT:
{incident_text}

CONTEXT:
- Facility: {facility}
- Auto-detected severity: {sev_score}/5
- FMEA RPN: {rpn_val}/125
- Top implicated domains: {", ".join(top_domains)}

Return ONLY the JSON. No markdown fences."""
    return call_claude(api_key, SYSTEM_PROMPT, prompt, max_tokens=3000)

# ─────────────────────────────────────────────
# PDF GENERATOR
# ─────────────────────────────────────────────
def build_pdf(inc, ai, facility_name, benchmark_rpn, benchmark_detect, benchmark_report):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=16*mm, leftMargin=16*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()

    def S(name,**kw):
        base = styles.get(name, styles['Normal'])
        return ParagraphStyle(f"custom_{name}_{id(kw)}", parent=base, **kw)

    title_s  = S('Title', fontSize=17, textColor=colors.HexColor('#0c4a6e'),
                 fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=4)
    sub_s    = S('Normal', fontSize=8.5, textColor=colors.HexColor('#64748b'),
                 alignment=TA_CENTER, spaceAfter=10)
    hdr_s    = S('Normal', fontSize=10, textColor=colors.HexColor('#0369a1'),
                 fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=5)
    body_s   = S('Normal', fontSize=8.5, textColor=colors.HexColor('#1e293b'),
                 leading=14, spaceAfter=4)
    bold_s   = S('Normal', fontSize=8.5, textColor=colors.HexColor('#0f172a'),
                 fontName='Helvetica-Bold', leading=14)
    alert_s  = S('Normal', fontSize=9.5, textColor=colors.HexColor('#991b1b'),
                 fontName='Helvetica-Bold', alignment=TA_CENTER,
                 backColor=colors.HexColor('#fef2f2'), spaceAfter=8)
    ai_s     = S('Normal', fontSize=8.5, textColor=colors.HexColor('#1e3a5f'),
                 leading=15, spaceAfter=4, leftIndent=8, rightIndent=8)

    story = []

    # ── Cover
    story.append(Paragraph("ICU Safety Intelligence — Deep Analysis Report", title_s))
    story.append(Paragraph(f"{facility_name} · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · v4.0", sub_s))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0369a1'), spaceAfter=10))

    if inc.get('sentinel'):
        story.append(Paragraph("⚠ SENTINEL EVENT — IMMEDIATE EXECUTIVE REVIEW REQUIRED", alert_s))

    sev = inc['sev_score']; sev_info = SEVERITY_CFG[sev]

    # ── Incident summary table
    story.append(Paragraph("01 — INCIDENT SUMMARY", hdr_s))
    rows = [
        ["Field","Value"],
        ["Incident ID", inc.get('incident_id','—')],
        ["Date / Time", inc.get('date','—')],
        ["Facility / Unit", f"{facility_name} — {inc.get('unit_type','—')}"],
        ["Incident Type (auto-detected)", inc.get('incident_type','—')],
        ["Severity (NCC MERP)", f"{sev_info['label']} — Category {sev_info['ncc']} ({sev}/5)"],
        ["FMEA Risk Priority Number", f"{inc['rpn_val']}/125 — {inc['risk_cat_label']}"],
        ["Detection Time", f"{inc.get('detect_time','—')} min"],
        ["Report Time", f"{inc.get('report_time','—')} hrs"],
        ["Sentinel Event", "YES ⚠" if inc.get('sentinel') else "NO"],
    ]
    t = Table(rows, colWidths=[58*mm, 118*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0c4a6e')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),8.5),
        ('BACKGROUND',(0,1),(0,-1),colors.HexColor('#e0f2fe')),
        ('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),
        ('ROWBACKGROUNDS',(1,1),(-1,-1),[colors.white,colors.HexColor('#f0f9ff')]),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#bae6fd')),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),8),
    ]))
    story.append(t)
    story.append(Spacer(1,8))

    # ── Original incident text
    story.append(Paragraph("02 — INCIDENT REPORT (ORIGINAL TEXT)", hdr_s))
    story.append(Paragraph(inc.get('text','').replace('\n','<br/>'), body_s))

    # ── AI Narrative
    if ai:
        story.append(Paragraph("03 — AI NARRATIVE ANALYSIS", hdr_s))
        story.append(Paragraph(ai.get('narrative_summary','—'), ai_s))
        story.append(Paragraph(f"<b>Clinical Significance:</b> {ai.get('clinical_significance','—')}", ai_s))
        story.append(Spacer(1,6))

        story.append(Paragraph("<b>System Failures Identified:</b>", bold_s))
        for sf in ai.get('system_failures',[]):
            story.append(Paragraph(f"• {sf}", body_s))

        # RCA
        story.append(Paragraph("04 — ROOT CAUSE ANALYSIS", hdr_s))
        rca = ai.get('root_cause_analysis',{})
        rca_rows = [
            ["Component","Detail"],
            ["Proximate Cause", rca.get('proximate_cause','—')],
            ["Root Cause",      rca.get('root_cause','—')],
        ]
        for cc in rca.get('contributory_causes',[]):
            rca_rows.append(["Contributory", cc])
        for lc in rca.get('latent_conditions',[]):
            rca_rows.append(["Latent Condition", lc])
        rt = Table(rca_rows, colWidths=[42*mm, 134*mm])
        rt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),8.5),
            ('BACKGROUND',(0,1),(0,-1),colors.HexColor('#eff6ff')),
            ('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),
            ('ROWBACKGROUNDS',(1,1),(-1,-1),[colors.white,colors.HexColor('#f0f9ff')]),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#bfdbfe')),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LEFTPADDING',(0,0),(-1,-1),8),
        ]))
        story.append(rt)

        # 5 Whys
        story.append(Paragraph("05 — 5 WHYS CHAIN", hdr_s))
        why_rows = [["Why #","Question","Answer"]]
        for w in ai.get('five_whys',[]):
            why_rows.append([str(w.get('why',''))+" →", w.get('question','—'), w.get('answer','—')])
        wt = Table(why_rows, colWidths=[18*mm, 60*mm, 98*mm])
        wt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),8.5),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#eff6ff'),colors.white]),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#bfdbfe')),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LEFTPADDING',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        story.append(wt)

        # Timeline
        story.append(PageBreak())
        story.append(Paragraph("06 — STEP-BY-STEP INCIDENT TIMELINE", hdr_s))
        tl_rows = [["Step","Phase","Event","Latent Factor"]]
        for step in ai.get('timeline',[]):
            tl_rows.append([
                str(step.get('step','')),
                step.get('phase','—'),
                step.get('event','—'),
                step.get('latent_factor','—'),
            ])
        tlt = Table(tl_rows, colWidths=[12*mm, 32*mm, 80*mm, 52*mm])
        tlt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0c4a6e')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),8),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f9ff')]),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#bae6fd')),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LEFTPADDING',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        story.append(tlt)

        # Action plan
        story.append(Paragraph("07 — AUTOMATED ACTION PLAN", hdr_s))
        ap_rows = [["#","Action","Owner","Deadline","Priority","Category"]]
        p_colors = {"CRITICAL":"#fef2f2","HIGH":"#fff7ed","MODERATE":"#fefce8","LOW":"#f0fdf4"}
        for a in ai.get('action_plan',[]):
            ap_rows.append([
                str(a.get('id','')),
                a.get('action','—'),
                a.get('owner','—'),
                a.get('deadline','—'),
                a.get('priority','—'),
                a.get('category','—'),
            ])
        apt = Table(ap_rows, colWidths=[8*mm, 72*mm, 28*mm, 22*mm, 18*mm, 22*mm])
        apt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#166534')),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),7.5),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0fdf4')]),
            ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#86efac')),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LEFTPADDING',(0,0),(-1,-1),5),('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        story.append(apt)

        # Learning points
        story.append(Paragraph("08 — KEY LEARNING POINTS", hdr_s))
        for lp in ai.get('learning_points',[]):
            story.append(Paragraph(f"◆ {lp}", body_s))

        # Prevention
        story.append(Paragraph("09 — PREVENTION STRATEGY", hdr_s))
        story.append(Paragraph(ai.get('prevention_strategy','—'), ai_s))

        # Reporting obligations
        story.append(Paragraph("10 — REPORTING OBLIGATIONS", hdr_s))
        for ro in ai.get('reporting_obligations',[]):
            story.append(Paragraph(f"• {ro}", body_s))

    # Footer
    story.append(Spacer(1,16))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0369a1')))
    story.append(Spacer(1,5))
    story.append(Paragraph(
        f"ICU Safety Intelligence · Deep Analysis Engine v4.0 · {facility_name} · "
        f"For institutional quality improvement use only. Not a substitute for clinical judgment.",
        S('Normal', fontSize=6.5, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)
    ))
    doc.build(story)
    buf.seek(0)
    return buf.read()

# ─────────────────────────────────────────────
# COMPARISON PDF
# ─────────────────────────────────────────────
def build_comparison_pdf(incidents, facility_name):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=16*mm, leftMargin=16*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    def S(name,**kw):
        return ParagraphStyle(f"cs_{id(kw)}", parent=styles.get(name,styles['Normal']), **kw)

    story = []
    story.append(Paragraph("ICU Incident Comparison Report", S('Title',fontSize=16,
        textColor=colors.HexColor('#0c4a6e'),fontName='Helvetica-Bold',alignment=TA_CENTER)))
    story.append(Paragraph(f"{facility_name} · {datetime.now().strftime('%Y-%m-%d')}",
        S('Normal',fontSize=8.5,textColor=colors.HexColor('#64748b'),alignment=TA_CENTER,spaceAfter=10)))
    story.append(HRFlowable(width="100%",thickness=2,color=colors.HexColor('#0369a1'),spaceAfter=10))

    story.append(Paragraph("INCIDENT COMPARISON MATRIX",
        S('Normal',fontSize=10,fontName='Helvetica-Bold',textColor=colors.HexColor('#0369a1'),spaceAfter=6)))

    hdr = ["ID","Type","Severity","RPN","Risk","Detect(m)","Report(h)","Sentinel"]
    rows = [hdr]
    for inc in incidents:
        rows.append([
            inc.get('incident_id','—'),
            inc.get('incident_type','—')[:20],
            f"{SEVERITY_CFG[inc['sev_score']]['label']} ({inc['sev_score']}/5)",
            str(inc['rpn_val']),
            inc['risk_cat_label'],
            str(inc.get('detect_time','—')),
            str(inc.get('report_time','—')),
            "YES ⚠" if inc.get('sentinel') else "NO",
        ])
    mt = Table(rows, colWidths=[14*mm,36*mm,34*mm,14*mm,20*mm,18*mm,16*mm,16*mm])
    mt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0c4a6e')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),7.5),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f9ff')]),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#bae6fd')),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(mt)

    doc.build(story)
    buf.seek(0)
    return buf.read()

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔬 Incident Deep Analysis", "📊 Multi-Incident Comparison"])

# ═══════════════════════════════════════════════════════════════
# TAB 1 — DEEP ANALYSIS
# ═══════════════════════════════════════════════════════════════
with tab1:

    st.markdown('<div class="section-hdr">Paste Incident Report</div>', unsafe_allow_html=True)

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        detect_time  = st.number_input("Time to Detection (min)", 0, 1440, 30, key="dt1")
        report_time  = st.number_input("Time to Formal Report (hrs)", 0, 72, 2, key="rt1")
    with col_meta2:
        prior_sim    = st.number_input("Prior Similar Incidents (12 mo)", 0, 50, 0, key="ps1")
        override_sev = st.selectbox("Override Severity (optional)",
                                    ["Auto-detect","1 — No Harm","2 — Mild","3 — Moderate","4 — Severe","5 — Death"])
    with col_meta3:
        reporter_role= st.selectbox("Reporter Role", ["RN","ICU Fellow","Attending","Charge Nurse","CNO","Other"])
        inc_date     = st.date_input("Incident Date", datetime.today(), key="id1")

    incident_text = st.text_area(
        "Paste Full Incident Report Here",
        height=220,
        placeholder="""Example:
On the night shift of 14 Feb 2025, a 68-year-old male patient in Bay 4 of the Medical ICU received an incorrect dose of intravenous insulin. The nurse, who was covering two patients due to short staffing, prepared the infusion during a busy period. The insulin concentration was 10x the prescribed dose. The patient developed severe hypoglycaemia (BGL 1.2 mmol/L) approximately 40 minutes after infusion commencement, detected during routine vital sign check. Emergency dextrose was administered. The patient recovered without permanent harm. Contributing factors included unclear medication labelling, absence of a second-nurse check, and the nurse being in only their 3rd week in the ICU without adequate supervision...
        """,
        key="incident_text_input"
    )

    run_ai = st.checkbox("Enable AI Deep Analysis (requires API key)", value=True)

    if st.button("🚀 Run Deep Analysis", key="run_deep"):
        if not incident_text.strip():
            st.error("Please paste an incident report first.")
        else:
            # ── Classify
            sev_override = 0
            if override_sev != "Auto-detect":
                sev_override = int(override_sev[0])

            auto_sev, sentinel = auto_severity(incident_text)
            sev_score = sev_override if sev_override else auto_sev
            sev_info  = SEVERITY_CFG[sev_score]

            domain_scores, matched_kw = classify_domains(incident_text)
            like_score   = min(5, prior_sim + 1)
            detect_score = min(5, max(1, int(detect_time / 20) + 1))
            rpn_val      = rpn(sev_score, like_score, detect_score)
            rcat, rcol   = risk_cat(rpn_val)

            # Auto-detect incident type
            text_l = incident_text.lower()
            if any(w in text_l for w in ["insulin","medication","drug","dose","infusion","antibiotic"]):
                inc_type = "Medication Error"
            elif any(w in text_l for w in ["ventilator","extubat","intubat","airway"]):
                inc_type = "Ventilator Event"
            elif any(w in text_l for w in ["line","catheter","central","cvad","clabsi"]):
                inc_type = "Central Line Event"
            elif any(w in text_l for w in ["fall","fell"]):
                inc_type = "Fall Event"
            elif any(w in text_l for w in ["handover","communication","verbal"]):
                inc_type = "Communication Failure"
            else:
                inc_type = "General Safety Event"

            # Build incident dict
            inc_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            inc_record = {
                "incident_id":  inc_id,
                "text":         incident_text,
                "date":         str(inc_date),
                "unit_type":    unit_type,
                "incident_type":inc_type,
                "sev_score":    sev_score,
                "sentinel":     sentinel,
                "rpn_val":      rpn_val,
                "risk_cat_label": rcat,
                "risk_color":   rcol,
                "detect_time":  detect_time,
                "report_time":  report_time,
                "prior_sim":    prior_sim,
                "domain_scores":domain_scores,
                "matched_kw":   matched_kw,
                "ai":           None,
            }

            # ── AI call
            ai_result = None
            if run_ai:
                if not api_key:
                    st.warning("⚠ API key not set — AI analysis skipped. Add your key in the sidebar.")
                else:
                    with st.spinner("🤖 Claude is analysing the incident..."):
                        raw = ai_full_analysis(api_key, incident_text, sev_score,
                                               rpn_val, domain_scores, facility_name)
                    if raw.startswith("API_ERROR"):
                        st.error(f"AI call failed: {raw}")
                    else:
                        try:
                            # Strip possible markdown fences
                            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
                            ai_result = json.loads(clean)
                            inc_record["ai"] = ai_result
                        except json.JSONDecodeError as e:
                            st.error(f"Could not parse AI response as JSON: {e}")
                            st.code(raw[:800])

            # Save to session
            st.session_state.incidents.append(inc_record)

            # ─────────────────────────── RENDER ───────────────────────────

            if sentinel:
                st.markdown('<div class="sentinel-banner">⚠ SENTINEL EVENT — IMMEDIATE EXECUTIVE REVIEW REQUIRED ⚠</div>', unsafe_allow_html=True)

            # ── Metrics row
            st.markdown('<div class="section-hdr">Key Metrics</div>', unsafe_allow_html=True)
            m1,m2,m3,m4,m5,m6 = st.columns(6)
            with m1: st.metric("Severity",    f"{sev_score}/5");    st.caption(sev_info['label'])
            with m2: st.metric("NCC MERP",    sev_info['ncc'])
            with m3: st.metric("FMEA RPN",    f"{rpn_val}/125");    st.caption(rcat)
            with m4: st.metric("Detection",   f"{detect_time}m")
            with m5: st.metric("Report Time", f"{report_time}h")
            with m6: st.metric("Incident ID", inc_id)
            st.markdown("---")

            # ── AI Narrative
            if ai_result:
                st.markdown('<div class="section-hdr">AI Narrative Analysis</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="ai-box">
                  <h4>📋 Clinical Narrative</h4>
                  {ai_result.get('narrative_summary','—')}
                  <br><br>
                  <h4>⚕️ Clinical Significance</h4>
                  {ai_result.get('clinical_significance','—')}
                </div>""", unsafe_allow_html=True)

                # System failures
                st.markdown("#### System Failures Identified")
                sf_list = ai_result.get('system_failures', [])
                cols_sf = st.columns(2)
                for i, sf in enumerate(sf_list):
                    with cols_sf[i % 2]:
                        st.markdown(f'<div class="crit-card"><div class="cc-title">⚠ System Failure {i+1}</div>{sf}</div>', unsafe_allow_html=True)

                st.markdown("---")

                # ── Timeline
                st.markdown('<div class="section-hdr">Step-by-Step Incident Timeline</div>', unsafe_allow_html=True)
                timeline = ai_result.get('timeline', [])
                phase_colors = {
                    "Pre-incident": "#0369a1", "Triggering Event": "#dc2626",
                    "Incident Propagation": "#ea580c", "Detection": "#d97706",
                    "Response": "#16a34a", "Aftermath": "#7c3aed"
                }
                for step in timeline:
                    ph = step.get('phase', '')
                    col = phase_colors.get(ph, "#38bdf8")
                    st.markdown(f"""
                    <div class="timeline-step">
                      <div class="tnum" style="background:{col}">{step.get('step','')}</div>
                      <div class="ttext">
                        <span class="tbold">[{ph}]</span> {step.get('event','—')}
                        <br><span style="color:#475569;font-size:0.78rem">
                          Latent factor: {step.get('latent_factor','—')}</span>
                      </div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")

                # ── Root Cause Analysis
                st.markdown('<div class="section-hdr">Root Cause Analysis</div>', unsafe_allow_html=True)
                rca = ai_result.get('root_cause_analysis', {})
                colr1, colr2 = st.columns(2)
                with colr1:
                    st.markdown(f"""
                    <div class="ai-box">
                      <h4>⚡ Proximate Cause</h4>
                      {rca.get('proximate_cause','—')}
                      <br><br>
                      <h4>🌳 Root Cause</h4>
                      {rca.get('root_cause','—')}
                    </div>""", unsafe_allow_html=True)
                with colr2:
                    contrib = rca.get('contributory_causes', [])
                    latent  = rca.get('latent_conditions', [])
                    contrib_html = "".join(f"<li>{c}</li>" for c in contrib)
                    latent_html  = "".join(f"<li>{l}</li>" for l in latent)
                    st.markdown(f"""
                    <div class="ai-box">
                      <h4>🔗 Contributory Causes</h4>
                      <ul style="color:#94a3b8;margin:0;padding-left:18px">{contrib_html}</ul>
                      <br>
                      <h4>🏛 Latent Conditions</h4>
                      <ul style="color:#94a3b8;margin:0;padding-left:18px">{latent_html}</ul>
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")

                # ── 5 Whys
                st.markdown('<div class="section-hdr">5 Whys Chain (AI-Generated)</div>', unsafe_allow_html=True)
                five_g = graphviz.Digraph()
                five_g.attr(rankdir="TB", bgcolor="#070c18", fontname="JetBrains Mono")
                five_g.node("P", label=f"PROBLEM:\n{inc_type}",
                            shape="box", style="filled,rounded",
                            fillcolor="#4c0519", fontcolor="#fda4af",
                            fontsize="10", color="#f43f5e", penwidth="2")
                prev_n = "P"
                for w in ai_result.get('five_whys', []):
                    nid = f"W{w['why']}"
                    ans = w.get('answer','—')[:80]
                    five_g.node(nid, label=f"WHY {w['why']}:\n{ans}",
                                shape="box", style="filled,rounded",
                                fillcolor="#0d1f3c", fontcolor="#93c5fd",
                                fontsize="9", color="#1e3a5f", penwidth="1.5")
                    five_g.edge(prev_n, nid, label=" WHY?", color="#38bdf8",
                                fontcolor="#475569", fontsize="8")
                    prev_n = nid
                five_g.node("RC", label=f"ROOT CAUSE:\n{rca.get('root_cause','—')[:70]}",
                            shape="diamond", style="filled",
                            fillcolor="#14532d", fontcolor="#86efac",
                            fontsize="9", color="#22c55e", penwidth="2")
                five_g.edge(prev_n, "RC", color="#22c55e", penwidth="2",
                            label=" ROOT CAUSE", fontcolor="#22c55e", fontsize="8")
                st.graphviz_chart(five_g)

                # Cards
                why_c = ["#38bdf8","#0d9488","#d97706","#c026d3","#f43f5e"]
                wcols = st.columns(5)
                for i, (col, w) in enumerate(zip(wcols, ai_result.get('five_whys', []))):
                    with col:
                        st.markdown(f"""
                        <div style="background:#0d1f3c;border:1px solid {why_c[i]};
                            border-radius:8px;padding:12px;min-height:110px;">
                          <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;
                              color:{why_c[i]};letter-spacing:2px;margin-bottom:6px;">WHY {i+1}</div>
                          <div style="color:#94a3b8;font-size:0.78rem;line-height:1.5">
                            {w.get('answer','—')}</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("---")

                # ── Action Plan
                st.markdown('<div class="section-hdr">Automated Action Plan</div>', unsafe_allow_html=True)
                priority_config = {
                    "CRITICAL": ("crit-card","cc-title","#f43f5e","🚨"),
                    "HIGH":     ("warn-card","wc-title","#f97316","🔴"),
                    "MODERATE": ("warn-card","wc-title","#f59e0b","🟡"),
                    "LOW":      ("action-card","ac-title","#22c55e","🟢"),
                }
                cats = ["Immediate","Short-term","Medium-term","Long-term"]
                for cat in cats:
                    actions_in_cat = [a for a in ai_result.get('action_plan',[]) if a.get('category')==cat]
                    if actions_in_cat:
                        st.markdown(f"**{cat} Actions**")
                        for a in actions_in_cat:
                            pri = a.get('priority','LOW')
                            card, title_cls, badge_col, icon = priority_config.get(pri, priority_config["LOW"])
                            st.markdown(f"""
                            <div class="{card}">
                              <div class="{title_cls}">{icon} {a.get('action','—')}</div>
                              <div class="ac-meta">
                                <span class="ac-badge" style="background:{badge_col}22;color:{badge_col};">{pri}</span>
                                <span class="ac-badge" style="background:#1e3a5f;color:#93c5fd;">👤 {a.get('owner','—')}</span>
                                <span class="ac-badge" style="background:#14532d;color:#86efac;">📅 {a.get('deadline','—')}</span>
                              </div>
                            </div>""", unsafe_allow_html=True)

                st.markdown("---")

                # ── Domain radar
                st.markdown('<div class="section-hdr">Domain Analysis & Risk Benchmarking</div>', unsafe_allow_html=True)
                colD1, colD2 = st.columns([1,1])

                with colD1:
                    labels_r = list(domain_scores.keys())
                    vals_r   = list(domain_scores.values())
                    N = len(labels_r)
                    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
                    vp = vals_r + [vals_r[0]]; ap = angles + [angles[0]]
                    fig_r, ax_r = plt.subplots(figsize=(5,5), subplot_kw=dict(polar=True))
                    fig_r.patch.set_facecolor('#070c18'); ax_r.set_facecolor('#070c18')
                    ax_r.plot(ap, vp, color='#38bdf8', linewidth=2.5)
                    ax_r.fill(ap, vp, color='#38bdf8', alpha=0.15)
                    for gv in [1,2,3]:
                        ax_r.plot(ap, [gv]*len(ap), color='#1e3a5f', lw=0.7, ls='--')
                    ax_r.set_xticks(angles)
                    ax_r.set_xticklabels([l.split('/')[0][:12] for l in labels_r],
                                         color='#475569', size=7.5)
                    ax_r.set_yticklabels([])
                    ax_r.set_ylim(0, max(max(vals_r),3)+1)
                    ax_r.set_title('Contributing Domains', color='#e2e8f4', pad=18)
                    ax_r.spines['polar'].set_color('#1e3a5f')
                    st.pyplot(fig_r)

                with colD2:
                    st.markdown("#### Risk Benchmark Comparison")

                    def bench_bar(label, value, benchmark, unit, good_low=True):
                        pct_val   = min(value/max(benchmark*2,1)*100, 100)
                        pct_bench = 50
                        worse = (value > benchmark) if good_low else (value < benchmark)
                        bar_col = "#f43f5e" if worse else "#22c55e"
                        delta_symbol = "▲" if value > benchmark else "▼"
                        st.markdown(f"""
                        <div class="bench-bar-wrap">
                          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                            <span style="color:#e2e8f4;font-size:0.82rem;font-weight:600">{label}</span>
                            <span style="font-family:'JetBrains Mono',monospace;color:{bar_col};font-size:0.82rem">
                              {value} {unit} {delta_symbol} {abs(value-benchmark):.0f} vs benchmark
                            </span>
                          </div>
                          <div style="background:#1e3a5f;border-radius:4px;height:9px;position:relative;margin-bottom:4px;">
                            <div style="background:{bar_col};border-radius:4px;height:9px;width:{pct_val:.0f}%;"></div>
                            <div style="position:absolute;top:-2px;left:{pct_bench}%;
                                width:2px;height:13px;background:#f59e0b;"></div>
                          </div>
                          <div style="display:flex;justify-content:space-between;">
                            <span style="font-size:0.68rem;color:#475569">This incident: {value} {unit}</span>
                            <span style="font-size:0.68rem;color:#f59e0b">│ Benchmark: {benchmark} {unit}</span>
                          </div>
                        </div>""", unsafe_allow_html=True)

                    bench_bar("FMEA RPN",       rpn_val,     benchmark_rpn,    "/125")
                    bench_bar("Detection Time",  detect_time, benchmark_detect, "min")
                    bench_bar("Reporting Time",  report_time, benchmark_report, "hrs")

                    st.markdown("---")
                    st.markdown(f"""
                    <div class="ai-box">
                      <h4>📊 Risk Commentary</h4>
                      {ai_result.get('risk_narrative','—')}
                      <br><br>
                      <h4>📈 Benchmark Commentary</h4>
                      {ai_result.get('benchmark_commentary','—')}
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")

                # ── Prevention + Learning
                st.markdown('<div class="section-hdr">Prevention Strategy & Learning Points</div>', unsafe_allow_html=True)
                col_p1, col_p2 = st.columns([1,1])
                with col_p1:
                    st.markdown(f"""
                    <div class="ai-box">
                      <h4>🛡 Prevention Strategy</h4>
                      {ai_result.get('prevention_strategy','—')}
                    </div>""", unsafe_allow_html=True)
                with col_p2:
                    lp_html = "".join(f'<div class="action-card" style="margin:4px 0"><div class="ac-title">◆ {lp}</div></div>' for lp in ai_result.get('learning_points',[]))
                    robs_html = "".join(f'<div style="color:#fda4af;font-size:0.83rem;padding:3px 0">• {ro}</div>' for ro in ai_result.get('reporting_obligations',[]))
                    st.markdown(f"""
                    <div class="ai-box">
                      <h4>💡 Key Learning Points</h4>
                      {lp_html}
                      <h4 style="margin-top:14px">📢 Reporting Obligations</h4>
                      {robs_html}
                    </div>""", unsafe_allow_html=True)

            else:
                # No AI — show domain bars only
                st.markdown('<div class="section-hdr">Domain Analysis</div>', unsafe_allow_html=True)
                for d, s in sorted(domain_scores.items(), key=lambda x: -x[1]):
                    pct = (s / max(max(domain_scores.values()),1)) * 100
                    kws = matched_kw.get(d, [])
                    col = "#38bdf8" if s > 0 else "#1e3a5f"
                    st.markdown(f"""
                    <div style="margin-bottom:10px;">
                      <div style="display:flex;justify-content:space-between;color:#cbd5e1;font-size:0.82rem;margin-bottom:3px;">
                        <span>{d}</span><span style="font-family:monospace;color:{col}">{s} hit{'s' if s!=1 else ''}</span>
                      </div>
                      <div style="background:#1e3a5f;border-radius:4px;height:7px;">
                        <div style="background:{col};border-radius:4px;height:7px;width:{min(pct,100):.0f}%;"></div>
                      </div>
                      <div style="font-size:0.7rem;color:#334155;margin-top:2px">{', '.join(kws) if kws else '—'}</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("---")

            # ── PDF Download
            st.markdown('<div class="section-hdr">Download Report</div>', unsafe_allow_html=True)
            with st.spinner("Building PDF..."):
                pdf_bytes = build_pdf(inc_record, ai_result, facility_name,
                                      benchmark_rpn, benchmark_detect, benchmark_report)
            fname = f"ICU_Deep_Analysis_{inc_id}.pdf"
            st.download_button(
                label="📥 Download Full Deep Analysis Report (PDF)",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf"
            )

# ═══════════════════════════════════════════════════════════════
# TAB 2 — MULTI-INCIDENT COMPARISON
# ═══════════════════════════════════════════════════════════════
with tab2:
    incidents = st.session_state.incidents

    if len(incidents) < 1:
        st.info("🔬 Analyse at least one incident in the Deep Analysis tab — they'll appear here automatically.")
    else:
        st.markdown(f'<div class="section-hdr">Comparing {len(incidents)} Incident(s)</div>', unsafe_allow_html=True)

        # ── Comparison table
        df_rows = []
        for inc in incidents:
            df_rows.append({
                "ID":           inc['incident_id'],
                "Date":         inc['date'],
                "Type":         inc['incident_type'],
                "Severity":     inc['sev_score'],
                "NCC MERP":     SEVERITY_CFG[inc['sev_score']]['ncc'],
                "RPN":          inc['rpn_val'],
                "Risk":         inc['risk_cat_label'],
                "Detect (min)": inc['detect_time'],
                "Report (hr)":  inc['report_time'],
                "Sentinel":     "⚠ YES" if inc['sentinel'] else "NO",
                "AI Analysed":  "✅" if inc['ai'] else "—",
            })
        df = pd.DataFrame(df_rows)
        st.dataframe(df, use_container_width=True)

        st.markdown("---")

        if len(incidents) >= 2:
            # ── RPN trend chart
            st.markdown('<div class="section-hdr">RPN Trend Across Incidents</div>', unsafe_allow_html=True)
            fig_trend, ax_trend = plt.subplots(figsize=(10,3.5))
            fig_trend.patch.set_facecolor('#070c18')
            ax_trend.set_facecolor('#0d1f3c')
            rpns    = [inc['rpn_val']    for inc in incidents]
            detects = [inc['detect_time']for inc in incidents]
            labels_t= [inc['incident_id']for inc in incidents]
            x = range(len(incidents))

            ax_trend.plot(x, rpns, 'o-', color='#38bdf8', lw=2.5, markersize=8, label='RPN')
            ax_trend.axhline(benchmark_rpn, color='#f59e0b', ls='--', lw=1.5, label=f'Benchmark RPN ({benchmark_rpn})')
            ax_trend.fill_between(x, rpns, benchmark_rpn, alpha=0.1,
                                  color='#f43f5e' if any(r>benchmark_rpn for r in rpns) else '#22c55e')
            for xi, rval in zip(x, rpns):
                ax_trend.annotate(str(rval), (xi, rval), textcoords="offset points",
                                  xytext=(0,10), ha='center', color='#38bdf8', fontsize=9)
            ax_trend.set_xticks(list(x)); ax_trend.set_xticklabels(labels_t, color='#475569', fontsize=8)
            ax_trend.set_ylabel('RPN', color='#475569')
            ax_trend.set_title('FMEA Risk Priority Number — Incident Trend', color='#e2e8f4', pad=10)
            ax_trend.tick_params(colors='#475569')
            ax_trend.legend(facecolor='#0d1f3c', labelcolor='#94a3b8', edgecolor='#1e3a5f')
            for s in ax_trend.spines.values(): s.set_edgecolor('#1e3a5f')
            st.pyplot(fig_trend)

            # ── Domain heatmap across incidents
            st.markdown('<div class="section-hdr">Domain Pattern Heatmap</div>', unsafe_allow_html=True)
            domain_names = list(DOMAIN_RULES.keys())
            matrix = np.zeros((len(incidents), len(domain_names)))
            for i, inc in enumerate(incidents):
                for j, d in enumerate(domain_names):
                    matrix[i][j] = inc['domain_scores'].get(d, 0)

            fig_hm, ax_hm = plt.subplots(figsize=(12, max(3, len(incidents)*0.7+1)))
            fig_hm.patch.set_facecolor('#070c18')
            ax_hm.set_facecolor('#070c18')
            im = ax_hm.imshow(matrix, cmap='Blues', aspect='auto')
            ax_hm.set_xticks(range(len(domain_names)))
            ax_hm.set_xticklabels([d[:14] for d in domain_names], color='#94a3b8',
                                   fontsize=8, rotation=30, ha='right')
            ax_hm.set_yticks(range(len(incidents)))
            ax_hm.set_yticklabels([inc['incident_id'] for inc in incidents], color='#94a3b8', fontsize=8)
            plt.colorbar(im, ax=ax_hm, label='Domain Match Score')
            ax_hm.set_title('Domain Patterns Across Incidents', color='#e2e8f4', pad=10)
            st.pyplot(fig_hm)

            # ── Severity distribution
            st.markdown('<div class="section-hdr">Severity & Risk Distribution</div>', unsafe_allow_html=True)
            colS1, colS2 = st.columns(2)
            with colS1:
                sev_counts = {}
                for inc in incidents:
                    lbl = SEVERITY_CFG[inc['sev_score']]['label']
                    sev_counts[lbl] = sev_counts.get(lbl, 0) + 1
                fig_sc, ax_sc = plt.subplots(figsize=(5,4))
                fig_sc.patch.set_facecolor('#070c18'); ax_sc.set_facecolor('#0d1f3c')
                sev_colors = ["#22c55e","#3b82f6","#f59e0b","#f97316","#f43f5e"]
                bars = ax_sc.bar(list(sev_counts.keys()), list(sev_counts.values()),
                                 color=sev_colors[:len(sev_counts)], width=0.5)
                for bar in bars:
                    ax_sc.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                               str(int(bar.get_height())), ha='center', color='white', fontsize=10)
                ax_sc.set_title('Severity Distribution', color='#e2e8f4', pad=10)
                ax_sc.tick_params(colors='#475569')
                for s in ax_sc.spines.values(): s.set_edgecolor('#1e3a5f')
                ax_sc.set_ylabel('Count', color='#475569')
                plt.xticks(rotation=15, ha='right')
                st.pyplot(fig_sc)

            with colS2:
                risk_counts = {}
                for inc in incidents:
                    risk_counts[inc['risk_cat_label']] = risk_counts.get(inc['risk_cat_label'],0)+1
                fig_rc, ax_rc = plt.subplots(figsize=(5,4))
                fig_rc.patch.set_facecolor('#070c18'); ax_rc.set_facecolor('#0d1f3c')
                risk_cols = {"CRITICAL":"#f43f5e","HIGH":"#f97316","MODERATE":"#f59e0b","LOW":"#22c55e"}
                rcols = [risk_cols.get(k,"#38bdf8") for k in risk_counts.keys()]
                ax_rc.pie(list(risk_counts.values()), labels=list(risk_counts.keys()),
                          colors=rcols, autopct='%1.0f%%', textprops={'color':'#e2e8f4'},
                          wedgeprops={'edgecolor':'#070c18','linewidth':2})
                ax_rc.set_title('Risk Category Distribution', color='#e2e8f4', pad=10)
                fig_rc.patch.set_facecolor('#070c18')
                st.pyplot(fig_rc)

            # ── Pattern insights
            st.markdown('<div class="section-hdr">Cross-Incident Pattern Insights</div>', unsafe_allow_html=True)
            top_dom_overall = {}
            for inc in incidents:
                for d, s in inc['domain_scores'].items():
                    top_dom_overall[d] = top_dom_overall.get(d,0) + s
            top_sorted = sorted(top_dom_overall.items(), key=lambda x: -x[1])
            avg_rpn     = np.mean([inc['rpn_val'] for inc in incidents])
            avg_detect  = np.mean([inc['detect_time'] for inc in incidents])
            sentinel_ct = sum(1 for inc in incidents if inc['sentinel'])

            st.markdown(f"""
            <div class="ai-box">
              <h4>📊 Pattern Summary Across {len(incidents)} Incidents</h4>
              <ul style="color:#94a3b8;margin:0;padding-left:18px;line-height:2">
                <li><b>Most recurring domain:</b> {top_sorted[0][0] if top_sorted else '—'} (cumulative score: {top_sorted[0][1] if top_sorted else 0})</li>
                <li><b>Second most recurring:</b> {top_sorted[1][0] if len(top_sorted)>1 else '—'}</li>
                <li><b>Average FMEA RPN:</b> {avg_rpn:.1f} / 125 (facility benchmark: {benchmark_rpn})</li>
                <li><b>Average detection time:</b> {avg_detect:.0f} min (benchmark: {benchmark_detect} min)</li>
                <li><b>Sentinel events:</b> {sentinel_ct} of {len(incidents)}</li>
                <li><b>Above-benchmark RPN:</b> {sum(1 for inc in incidents if inc['rpn_val']>benchmark_rpn)} incidents</li>
              </ul>
            </div>""", unsafe_allow_html=True)

        # ── Comparison PDF
        st.markdown("---")
        if len(incidents) >= 1:
            with st.spinner("Building comparison PDF..."):
                comp_pdf = build_comparison_pdf(incidents, facility_name)
            st.download_button(
                label="📥 Download Multi-Incident Comparison Report (PDF)",
                data=comp_pdf,
                file_name=f"ICU_Comparison_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )

        if st.button("🗑 Clear All Incidents", key="clear"):
            st.session_state.incidents = []
            st.rerun()
