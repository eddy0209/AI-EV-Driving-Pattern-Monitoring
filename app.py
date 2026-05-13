import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="EV Driving Pattern Monitoring System",
    layout="wide"
)
st.title("🚗 AI-Based Driving Pattern Monitoring & Range Estimation System")

st.markdown("""
This dashboard simulates an **Electric Vehicle (EV) Driving Pattern Monitoring System**
that analyzes driving behaviour and estimates vehicle range using AI-based logic.

The system monitors:
- Throttle Input
- Vehicle Speed
- Current Consumption
- Energy Usage
- Driving Behaviour Pattern
- Estimated Remaining Range
""")

st.markdown("---")

st.sidebar.header("⚙️ Driver Control Panel")

throttle = st.sidebar.slider(
    "Throttle Input (%)",
    min_value=0,
    max_value=100,
    value=30
)

st.sidebar.markdown("""
### 📌 Simulation Logic
The throttle input acts as the accelerator pedal of the EV.
Increasing throttle increases:
- Vehicle Speed
- Current Consumption
- Power Usage
""")

# Simulated speed calculation
speed = throttle * 0.8

# Simulated current consumption
current = throttle * 0.15

# Constant battery voltage
voltage = 24

# Power Consumption Formula
power = voltage * current

# Battery Capacity Assumption
battery_capacity = 240  # Wh

# Estimated Range Formula
if power == 0:
    estimated_range = 0
else:
    estimated_range = (battery_capacity / power) * speed

# Battery Percentage Simulation
battery_percentage = max(100 - (current * 2), 5)

if throttle < 30:
    driving_pattern = "Eco Driving"
    feedback = "Efficient driving behaviour detected."
    status = "success"

elif throttle < 70:
    driving_pattern = "Normal Driving"
    feedback = "Moderate energy consumption detected."
    status = "warning"

else:
    driving_pattern = "Aggressive Driving"
    feedback = "High energy consumption detected!"
    status = "error"

st.header("📊 Real-Time Vehicle Parameters")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="🚘 Vehicle Speed",
    value=f"{speed:.1f} km/h"
)

col2.metric(
    label="⚡ Current Consumption",
    value=f"{current:.1f} A"
)

col3.metric(
    label="🔌 Power Consumption",
    value=f"{power:.1f} W"
)

col4.metric(
    label="🛣️ Estimated Range",
    value=f"{estimated_range:.1f} km"
)

st.markdown("---")

st.header("🔋 Battery Monitoring")

st.write("### Remaining Battery Percentage")

st.progress(int(battery_percentage))

st.write(f"Battery Remaining: **{battery_percentage:.1f}%**")

st.markdown("""
Battery percentage decreases as current consumption increases.
Aggressive driving results in faster battery discharge.
""")

st.markdown("---")

st.header("🧠 AI Driving Pattern Detection")

if status == "success":
    st.success(f"Driving Pattern Detected: {driving_pattern}")

elif status == "warning":
    st.warning(f"Driving Pattern Detected: {driving_pattern}")

else:
    st.error(f"Driving Pattern Detected: {driving_pattern}")

st.write(f"### 📢 Driver Feedback")
st.write(feedback)

st.markdown("""
The AI system classifies driving behaviour based on:
- Throttle Variation
- Speed
- Current Consumption
- Power Usage
""")

st.markdown("---")

st.header("📈 Energy Consumption Analysis")

# Creating simulated graph data
speed_data = []
power_data = []

for i in range(10):
    speed_data.append(speed + i * 0.5)
    power_data.append(power + i * 2)

# Plotting graph
fig, ax = plt.subplots(figsize=(8, 4))

ax.plot(speed_data, power_data, marker='o')

ax.set_xlabel("Vehicle Speed (km/h)")
ax.set_ylabel("Power Consumption (W)")
ax.set_title("Speed vs Power Consumption")

st.pyplot(fig)

st.markdown("""
This graph shows the relationship between:
- Vehicle Speed
- Power Consumption

Higher speed generally increases energy usage and reduces EV range.
""")

st.markdown("---")

st.caption("Final Year B.Tech Project | Department of Electrical Engineering")