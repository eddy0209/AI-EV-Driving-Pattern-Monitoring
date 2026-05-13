import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="EV Driving Pattern Monitoring System",
    layout="wide"
)

# =========================================================
# PROJECT TITLE
# =========================================================

st.title("🚗 AI-Based Driving Pattern Monitoring & Range Estimation System")

st.markdown("""
This dashboard simulates an **AI-Based Electric Vehicle (EV) Driving Pattern Monitoring System**
that analyzes driving behaviour and estimates vehicle range using AI-based logic.

### The system monitors:
- Throttle Input
- Vehicle Speed
- Current Consumption
- Power Usage
- Driving Behaviour Pattern
- Estimated Remaining Range
""")

st.markdown("---")

# =========================================================
# SIDEBAR : DRIVER INPUT
# =========================================================

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

# =========================================================
# SIMULATED SENSOR PARAMETERS
# =========================================================

# Simulated Speed
speed = throttle * 0.8

# Simulated Current Consumption
current = throttle * 0.15

# Constant Voltage
voltage = 24

# Power Calculation
power = voltage * current

# Battery Capacity Assumption
battery_capacity = 240  # Wh

# Estimated Range Calculation
if power == 0:
    estimated_range = 0
else:
    estimated_range = (battery_capacity / power) * speed

# Battery Percentage Simulation
battery_percentage = max(100 - (current * 2), 5)

# =========================================================
# AI-BASED DRIVING PATTERN CLASSIFICATION
# =========================================================

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

# =========================================================
# REAL-TIME VEHICLE PARAMETERS
# =========================================================

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

# =========================================================
# BATTERY MONITORING SECTION
# =========================================================

st.header("🔋 Battery Monitoring")

st.write("### Remaining Battery Percentage")

st.progress(int(battery_percentage))

st.write(f"Battery Remaining: **{battery_percentage:.1f}%**")

st.markdown("""
Battery percentage decreases as current consumption increases.
Aggressive driving results in faster battery discharge.
""")

st.markdown("---")

# =========================================================
# AI DRIVING PATTERN DETECTION
# =========================================================

st.header("🧠 AI Driving Pattern Detection")

if status == "success":
    st.success(f"Driving Pattern Detected: {driving_pattern}")

elif status == "warning":
    st.warning(f"Driving Pattern Detected: {driving_pattern}")

else:
    st.error(f"Driving Pattern Detected: {driving_pattern}")

st.write("### 📢 Driver Feedback")
st.write(feedback)

st.markdown("""
The AI system classifies driving behaviour based on:
- Throttle Variation
- Speed
- Current Consumption
- Power Usage
""")

st.markdown("---")

# =========================================================
# HARDWARE SIMULATION PANEL
# =========================================================

st.header("🔌 Virtual Hardware Simulation")

sensor_col1, sensor_col2 = st.columns(2)

with sensor_col1:
    st.subheader("📡 Sensor Outputs")

    st.write(f"Throttle Sensor Output: {throttle}%")
    st.write(f"Current Sensor (ACS712): {current:.2f} A")
    st.write(f"Voltage Sensor Output: {voltage} V")
    st.write(f"Rotary Encoder Speed: {speed:.2f} km/h")

with sensor_col2:
    st.subheader("🖥️ Controller Status")

    st.success("ESP32 Status: ACTIVE")
    st.success("PWM Signal Generated")
    st.success("Sensor Data Acquisition Running")

    st.info("Raspberry Pi AI Processing Running")

st.markdown("---")

# =========================================================
# LCD DISPLAY SIMULATION
# =========================================================

st.header("📺 LCD Display Simulation")

lcd_html = f'''
<div style="
background-color:black;
padding:20px;
border-radius:10px;
font-family:monospace;
color:#00FF00;
font-size:20px;
width:420px;
box-shadow: 0px 0px 10px #00FF00;
">
Driving Pattern : {driving_pattern}<br>
Speed           : {speed:.1f} km/h<br>
Current         : {current:.1f} A<br>
Range           : {estimated_range:.1f} km
</div>
'''

st.markdown(lcd_html, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# ENERGY ANALYSIS GRAPH
# =========================================================

st.header("📈 Energy Consumption Analysis")

# Simulated graph data
speed_data = []
power_data = []

for i in range(10):
    speed_data.append(speed + i * 0.5)
    power_data.append(power + i * 2)

# Plot Graph
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