import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt

# Load model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

# Load dataset
df = pd.read_csv("ICU_Synthetic_Incidents_500_Advanced.csv")

st.title("ICU Safety Digital Twin")

st.sidebar.header("Intervention Controls")

# Sliders
training = st.sidebar.slider("Training Compliance", 0.4, 1.0, 0.7)
checklist = st.sidebar.slider("Checklist Compliance", 0.5, 1.0, 0.8)
workload = st.sidebar.slider("Workload Index", 0.5, 1.5, 1.0)
staffing = st.sidebar.slider("Staffing Ratio", 1.5, 3.5, 2.5)

# Apply simulation changes
df_sim = df.copy()
df_sim["training_compliance"] = training
df_sim["checklist_compliance"] = checklist
df_sim["workload_index"] = workload
df_sim["staffing_ratio"] = staffing

X = df_sim[['staffing_ratio',
            'avg_experience_years',
            'workload_index',
            'bed_occupancy_rate',
            'checklist_compliance',
            'training_compliance',
            'equipment_maintenance_score',
            'human_factor',
            'communication_issue',
            'protocol_issue',
            'equipment_issue']]

baseline_X = df[['staffing_ratio',
                 'avg_experience_years',
                 'workload_index',
                 'bed_occupancy_rate',
                 'checklist_compliance',
                 'training_compliance',
                 'equipment_maintenance_score',
                 'human_factor',
                 'communication_issue',
                 'protocol_issue',
                 'equipment_issue']]

baseline_prob = model.predict_proba(baseline_X)[:,1].mean()
new_prob = model.predict_proba(X)[:,1].mean()

st.subheader("Predicted Severe Incident Rate")
st.write(f"Baseline: {baseline_prob:.3f}")
st.write(f"After Intervention: {new_prob:.3f}")
st.write(f"Reduction: {(baseline_prob - new_prob)*100:.2f}%")

# Monthly projection
monthly_baseline = df.groupby("month")["severity_binary"].mean()
monthly_sim = df_sim.copy()
monthly_sim["predicted"] = model.predict_proba(X)[:,1]
monthly_projection = monthly_sim.groupby("month")["predicted"].mean()

fig, ax = plt.subplots()
ax.plot(monthly_baseline.index, monthly_baseline.values, label="Baseline")
ax.plot(monthly_projection.index, monthly_projection.values, label="Simulated")
ax.set_xlabel("Month")
ax.set_ylabel("Severe Incident Probability")
ax.legend()

st.subheader("Monthly Projection")
st.pyplot(fig)

# Monte Carlo
st.subheader("Monte Carlo Simulation (Training Compliance ±5%)")

results = []
for i in range(500):
    rand_training = np.random.uniform(training-0.05, training+0.05)
    df_sim["training_compliance"] = rand_training
    probs = model.predict_proba(df_sim[X.columns])[:,1]
    results.append(probs.mean())

st.write(f"Mean Severe Rate: {np.mean(results):.3f}")
st.write(f"95% CI: {np.percentile(results,2.5):.3f} - {np.percentile(results,97.5):.3f}")
