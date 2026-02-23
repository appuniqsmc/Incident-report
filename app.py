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

# Feature list
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
# DIGITAL TWIN SIMULATION
# =============================

st.title("ICU Safety Digital Twin")

st.sidebar.header("Intervention Controls")

training = st.sidebar.slider("Training Compliance", 0.4, 1.0, 0.7)
checklist = st.sidebar.slider("Checklist Compliance", 0.5, 1.0, 0.8)
workload = st.sidebar.slider("Workload Index", 0.5, 1.5, 1.0)
staffing = st.sidebar.slider("Staffing Ratio", 1.5, 3.5, 2.5)

df_sim = df.copy()
df_sim["training_compliance"] = training
df_sim["checklist_compliance"] = checklist
df_sim["workload_index"] = workload
df_sim["staffing_ratio"] = staffing

baseline_prob = model.predict_proba(df[features])[:,1].mean()
new_prob = model.predict_proba(df_sim[features])[:,1].mean()

st.subheader("Predicted Severe Incident Rate")
st.write(f"Baseline: {baseline_prob:.3f}")
st.write(f"After Intervention: {new_prob:.3f}")
st.write(f"Reduction: {(baseline_prob - new_prob)*100:.2f}%")

# =============================
# MONTHLY PROJECTION
# =============================

monthly_baseline = df.groupby("month")["severity_binary"].mean()
df_sim["predicted"] = model.predict_proba(df_sim[features])[:,1]
monthly_projection = df_sim.groupby("month")["predicted"].mean()

fig, ax = plt.subplots()
ax.plot(monthly_baseline.index, monthly_baseline.values, label="Baseline")
ax.plot(monthly_projection.index, monthly_projection.values, label="Simulated")
ax.set_xlabel("Month")
ax.set_ylabel("Severe Incident Probability")
ax.legend()

st.subheader("Monthly Projection")
st.pyplot(fig)

# =============================
# MONTE CARLO SIMULATION
# =============================

st.subheader("Monte Carlo Simulation (Training ±5%)")

results = []
for i in range(300):
    rand_training = np.random.uniform(training-0.05, training+0.05)
    df_sim["training_compliance"] = rand_training
    probs = model.predict_proba(df_sim[features])[:,1]
    results.append(probs.mean())

st.write(f"Mean Severe Rate: {np.mean(results):.3f}")
st.write(f"95% CI: {np.percentile(results,2.5):.3f} - {np.percentile(results,97.5):.3f}")

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
    summary = "Root Cause Analysis:\n\n"

    if domains["human_factor"]:
        summary += "- Human performance factor identified.\n"
    if domains["communication_issue"]:
        summary += "- Communication breakdown detected.\n"
    if domains["protocol_issue"]:
        summary += "- Protocol adherence gap noted.\n"
    if domains["equipment_issue"]:
        summary += "- Equipment-related issue observed.\n"

    if sum(domains.values()) == 0:
        summary += "- No major contributing factors detected by rule engine.\n"

    return summary


def draw_fishbone(domains):
    dot = graphviz.Digraph()
    dot.node("Effect", "ICU Incident")

    for domain, value in domains.items():
        if value == 1:
            dot.node(domain, domain.replace("_", " ").title())
            dot.edge(domain, "Effect")

    return dot


DRIVER_MAP = {
    "human_factor": ("Staff Competency", "Training Compliance"),
    "communication_issue": ("Structured Handover", "Checklist Use"),
    "protocol_issue": ("Protocol Reliability", "Audit System"),
    "equipment_issue": ("Device Safety", "Maintenance Program")
}

def draw_driver_diagram(domains):
    dot = graphviz.Digraph()
    dot.node("AIM", "Reduce ICU Incidents")

    for domain, value in domains.items():
        if value == 1:
            primary, secondary = DRIVER_MAP[domain]
            dot.node(primary)
            dot.node(secondary)
            dot.edge("AIM", primary)
            dot.edge(primary, secondary)

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

    # Proper 2D input fix
    input_row = df.iloc[0][features].copy()

    input_row["human_factor"] = domains["human_factor"]
    input_row["communication_issue"] = domains["communication_issue"]
    input_row["protocol_issue"] = domains["protocol_issue"]
    input_row["equipment_issue"] = domains["equipment_issue"]

    input_df = pd.DataFrame([input_row])

    prob = model.predict_proba(input_df)[0][1]

    st.subheader("Predicted Severe Probability")
    st.write(f"{prob:.3f}")
