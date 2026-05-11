import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="EV Driving Pattern Monitor",
    layout="wide"
)

# ---------------- TITLE ----------------
st.title("🚗 AI-Based EV Driving Pattern Monitoring & Range Estimation")

st.markdown("---")

# ---------------- SIDEBAR ----------------
st.sidebar.header("Driver Controls")

throttle = st.sidebar.slider("Throttle Input (%)", 0, 100, 30)

# ---------------- SIMULATED PARAMETERS ----------------
speed = throttle * 0.8
current = throttle * 0.15
voltage = 24

power = voltage * current

battery_capacity = 240  # Wh

if power == 0:
    estimated_range = 0
else:
    estimated_range = (battery_capacity / power) * speed

# Battery percentage simulation
battery_percent = max(100 - (current * 2), 5)

# ---------------- AI CLASSIFICATION ----------------
if throttle < 30:
    pattern = "Eco"
    color = "green"
elif throttle < 70:
    pattern = "Normal"
    color = "orange"
else:
    pattern = "Aggressive"
    color = "red"

# ---------------- TOP METRICS ----------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Speed", f"{speed:.1f} km/h")
col2.metric("Current", f"{current:.1f} A")
col3.metric("Power", f"{power:.1f} W")
col4.metric("Estimated Range", f"{estimated_range:.1f} km")

st.markdown("---")

# ---------------- BATTERY BAR ----------------
st.subheader("🔋 Battery Status")

st.progress(int(battery_percent))

st.write(f"Battery Remaining: {battery_percent:.1f}%")

# ---------------- AI PANEL ----------------
st.subheader("🧠 AI Driving Pattern Detection")

if pattern == "Eco":
    st.success(f"Driving Pattern Detected: {pattern}")
elif pattern == "Normal":
    st.warning(f"Driving Pattern Detected: {pattern}")
else:
    st.error(f"Driving Pattern Detected: {pattern}")

# ---------------- DRIVER FEEDBACK ----------------
st.subheader("📢 Driver Feedback")

if pattern == "Eco":
    st.info("Efficient driving detected. Battery usage is optimized.")
elif pattern == "Normal":
    st.warning("Moderate energy consumption detected.")
else:
    st.error("Aggressive driving detected! High energy consumption.")

# ---------------- LIVE GRAPH ----------------
st.subheader("📈 Live Energy Consumption Graph")

# Simulated graph data
speed_data = []
power_data = []

for i in range(10):
    speed_data.append(speed + i * 0.5)
    power_data.append(power + i * 2)

fig, ax = plt.subplots()

ax.plot(speed_data, power_data, marker='o')

ax.set_xlabel("Speed (km/h)")
ax.set_ylabel("Power Consumption (W)")
ax.set_title("Speed vs Power Consumption")

st.pyplot(fig)

# ---------------- SYSTEM WORKFLOW ----------------
st.markdown("---")

st.subheader("⚙️ System Workflow")

st.code("""
Throttle Input
      ↓
Speed & Current Generation
      ↓
AI Driving Pattern Classification
      ↓
Energy Consumption Calculation
      ↓
Range Estimation
""")

# ---------------- FOOTER ----------------
st.markdown("---")

st.caption("Final Year Project Prototype - Electrical Engineering")