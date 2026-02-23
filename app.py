import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import graphviz

# =============================
# LOAD MODEL AND DATA
# =============================

@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)

@st.cache_data
def load_data():
    return pd.read_csv("ICU_Synthetic_Incidents_500_Advanced.csv")

model = load_model()
df = load_data()

features = [
    'staffing_ratio',
    'avg_experience_years',
    'workload_index',
    'bed_occupancy_rate',
    'checklist_compliance',
    'training_compliance',
    'equipment_maintenance_score',
    'human_factor',
    'communication_issue',
    'protocol_issue',
    'equipment_issue'
]

# =============================
# PAGE TITLE
# =============================

st.title("ICU Safety Digital Twin")
st.caption("Interactive system-level simulation of severe incident risk")

# =============================
# SIDEBAR CONTROLS
# =============================

st.sidebar.header("ICU System Drivers")

training = st.sidebar.slider(
    "Staff Training Compliance (%)",
    40, 100, 70,
    help="Percentage of ICU staff up-to-date with competency training."
) / 100

checklist = st.sidebar.slider(
    "Checklist Adherence (%)",
    50, 100, 80,
    help="Compliance with ICU checklists (handover, central line, ventilator bundle)."
) / 100

workload = st.sidebar.slider(
    "Workload Pressure Index",
    50, 150, 100,
    help="100 = normal workload. >120 indicates surge pressure."
) / 100

staffing = st.sidebar.slider(
    "Nurse-to-Patient Ratio",
    1.5, 3.5, 2.5,
    help="Average number of patients per nurse. Lower is better."
)

# =============================
# APPLY SIMULATION
# =============================

df_sim = df.copy()
df_sim["training_compliance"] = training
df_sim["checklist_compliance"] = checklist
df_sim["workload_index"] = workload
df_sim["staffing_ratio"] = staffing

baseline_prob = model.predict_proba(df[features])[:,1].mean()
new_prob = model.predict_proba(df_sim[features])[:,1].mean()
reduction = (baseline_prob - new_prob) * 100

# =============================
# TRAFFIC LIGHT RISK INDICATOR
# =============================

st.subheader("Predicted Severe Incident Risk")

col1, col2, col3 = st.columns(3)

col1.metric("Baseline Risk", f"{baseline_prob:.3f}")
col2.metric("Simulated Risk", f"{new_prob:.3f}")
col3.metric("Change (%)", f"{reduction:.2f}%")

if new_prob < 0.55:
    st.success("🟢 LOW RISK ZONE")
elif new_prob < 0.70:
    st.warning("🟡 MODERATE RISK ZONE")
else:
    st.error("🔴 HIGH RISK ZONE")

# =============================
# MONTHLY PROJECTION
# =============================

st.subheader("Monthly Severe Risk Projection")

monthly_baseline = df.groupby("month")["severity_binary"].mean()
df_sim["predicted"] = model.predict_proba(df_sim[features])[:,1]
monthly_projection = df_sim.groupby("month")["predicted"].mean()

fig, ax = plt.subplots()
ax.plot(monthly_baseline.index, monthly_baseline.values, label="Baseline", linewidth=2)
ax.plot(monthly_projection.index, monthly_projection.values, label="Simulated", linewidth=2)

# ICU Benchmark Line
ax.axhline(0.60, linestyle="--", label="ICU Risk Benchmark (0.60)")

ax.set_xlabel("Month")
ax.set_ylabel("Severe Incident Probability")
ax.legend()

st.pyplot(fig)

# =============================
# MONTE CARLO SIMULATION
# =============================

st.subheader("Monte Carlo Uncertainty (Training ±5%)")

results = []
for i in range(300):
    rand_training = np.random.uniform(training-0.05, training+0.05)
    df_sim["training_compliance"] = rand_training
    probs = model.predict_proba(df_sim[features])[:,1]
    results.append(probs.mean())

st.write(f"Mean Severe Risk: {np.mean(results):.3f}")
st.write(f"95% Confidence Interval: {np.percentile(results,2.5):.3f} - {np.percentile(results,97.5):.3f}")

# =============================
# MODEL COEFFICIENT DISPLAY
# =============================

st.subheader("Model Coefficients (Interpretability)")

coef_df = pd.DataFrame({
    "Feature": features,
    "Coefficient": model.coef_[0]
}).sort_values(by="Coefficient", ascending=False)

st.dataframe(coef_df)

# =============================
# RULE-BASED RCA ENGINE
# =============================

DOMAIN_RULES = {
    "human_factor": ["fatigue", "calculation error", "inattention", "forgot", "dose error"],
    "communication_issue": ["handover", "not informed", "unclear order", "miscommunication"],
    "protocol_issue": ["protocol not followed", "guideline absent", "no checklist", "deviation"],
    "equipment_issue": ["malfunction", "alarm failure", "pump failure", "device issue"]
}

def classify_domains(text):
    text = text.lower()
    detected = {
        "human_factor": 0,
        "communication_issue": 0,
        "protocol_issue": 0,
        "equipment_issue": 0
    }
    for domain, keywords in DOMAIN_RULES.items():
        for word in keywords:
            if word in text:
                detected[domain] = 1
    return detected

def generate_rca_summary(domains):
    summary = ""
    if domains["human_factor"]:
        summary += "- Human performance factor identified.\n"
    if domains["communication_issue"]:
        summary += "- Communication breakdown detected.\n"
    if domains["protocol_issue"]:
        summary += "- Protocol adherence gap noted.\n"
    if domains["equipment_issue"]:
        summary += "- Equipment-related issue observed.\n"
    if summary == "":
        summary = "- No major contributing factors detected."
    return summary

def draw_fishbone(domains):
    dot = graphviz.Digraph()
    dot.node("Effect", "ICU Incident")
    for domain, value in domains.items():
        if value == 1:
            dot.node(domain, domain.replace("_", " ").title())
            dot.edge(domain, "Effect")
    return dot

def draw_driver_diagram(domains):
    dot = graphviz.Digraph()
    dot.node("AIM", "Reduce ICU Incidents")
    for domain, value in domains.items():
        if value == 1:
            dot.node(domain)
            dot.edge("AIM", domain)
    return dot

# =============================
# NEW INCIDENT ANALYSIS
# =============================

st.divider()
st.header("Analyze New ICU Incident")

incident_text = st.text_area("Enter Incident Description")

if st.button("Run RCA Analysis"):

    domains = classify_domains(incident_text)

    st.subheader("RCA Summary")
    st.write(generate_rca_summary(domains))

    st.subheader("Fishbone Diagram")
    st.graphviz_chart(draw_fishbone(domains))

    st.subheader("Driver Diagram")
    st.graphviz_chart(draw_driver_diagram(domains))

    input_row = df.iloc[0][features].copy()
    input_row.update(domains)
    input_df = pd.DataFrame([input_row])
    prob = model.predict_proba(input_df)[0][1]

    st.subheader("Predicted Severe Probability")
    st.write(f"{prob:.3f}")
