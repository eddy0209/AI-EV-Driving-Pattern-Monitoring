import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="AI EV Range Optimization Dashboard",
    layout="wide"
)

st.title("🚗 AI-Based Driving Pattern Monitoring & Range Optimization System")

st.markdown("""
### Smart Electric Vehicle Optimization Dashboard

This system simulates:
- AI-Based Driving Pattern Detection
- EV Energy Consumption Monitoring
- Dynamic Range Optimization
- Battery Efficiency Improvement
- PWM-Based Power Optimization
""")

st.markdown("---")

st.sidebar.header("⚙️ Driver Control Panel")

throttle = st.sidebar.slider(
    "Throttle Input (%)",
    0,
    100,
    30
)

speed = throttle * 1.2
current = 1 + (throttle * 0.14)
voltage = 24
power = voltage * current
rpm = speed * 85

if throttle < 30:
    driving_pattern = "Eco Driving"
    confidence = 94
    pwm_output = throttle
    optimization_status = "Optimization Not Required"
    efficiency_score = 95
    feedback = "Efficient driving detected."

elif throttle < 70:
    driving_pattern = "Normal Driving"
    confidence = 88
    pwm_output = throttle * 0.90
    optimization_status = "Moderate Optimization Active"
    efficiency_score = 78
    feedback = "Power usage optimized moderately."

else:
    driving_pattern = "Aggressive Driving"
    confidence = 97
    pwm_output = throttle * 0.70
    optimization_status = "High Optimization Active"
    efficiency_score = 60
    feedback = "PWM reduced to minimize power wastage."

optimized_current = current * (pwm_output / throttle) if throttle > 0 else current

optimized_power = voltage * optimized_current

optimized_range = 140 - (optimized_current * 5)

if optimized_range < 0:
    optimized_range = 0

battery_percentage = optimized_range / 1.4

if battery_percentage < 5:
    battery_percentage = 5

power_saved = power - optimized_power

st.header("📊 Real-Time Vehicle Parameters")

col1, col2, col3, col4 = st.columns(4)

col1.metric("🚘 Speed", f"{speed:.1f} km/h")
col2.metric("⚡ Current", f"{optimized_current:.1f} A")
col3.metric("🔌 Power", f"{optimized_power:.1f} W")
col4.metric("🛣️ Optimized Range", f"{optimized_range:.1f} km")

st.markdown("---")

st.header("⚙️ Optimization Parameters")

opt_col1, opt_col2 = st.columns(2)

with opt_col1:

    st.subheader("⚡ PWM Optimization")

    st.progress(int(pwm_output))

    st.write(f"Optimized PWM Output: {pwm_output:.1f}%")

with opt_col2:

    st.subheader("🔋 Efficiency Score")

    st.progress(int(efficiency_score))

    st.write(f"Battery Efficiency: {efficiency_score}%")

st.markdown("---")

st.header("🔋 Battery Monitoring")

st.progress(int(battery_percentage))

st.write(f"Battery Remaining: **{battery_percentage:.1f}%**")

if battery_percentage > 70:
    st.success("Battery Status: Healthy")

elif battery_percentage > 40:
    st.warning("Battery Status: Moderate")

else:
    st.error("Battery Status: Low Battery")

st.markdown("---")

st.header("🧠 AI Driving Pattern Detection")

if driving_pattern == "Eco Driving":
    st.success(f"Driving Pattern: {driving_pattern}")

elif driving_pattern == "Normal Driving":
    st.warning(f"Driving Pattern: {driving_pattern}")

else:
    st.error(f"Driving Pattern: {driving_pattern}")

st.write(f"### AI Confidence Level: {confidence}%")

st.info(feedback)

st.markdown("---")

st.header("⚡ Optimization Status")

st.success(optimization_status)

st.write(f"Original Current Consumption : {current:.2f} A")
st.write(f"Optimized Current Consumption : {optimized_current:.2f} A")

st.write(f"Original Power Consumption : {power:.2f} W")
st.write(f"Optimized Power Consumption : {optimized_power:.2f} W")

st.write(f"Estimated Power Saved : {power_saved:.2f} W")

st.markdown("---")

st.header("📺 LCD Display Simulation")

lcd_html = f'''
<div style="
background-color:black;
padding:20px;
border-radius:12px;
font-family:monospace;
color:#00FF00;
font-size:22px;
width:480px;
box-shadow: 0px 0px 20px #00FF00;
">
Driving Pattern : {driving_pattern}<br>
PWM Output      : {pwm_output:.1f}%<br>
Power Saved     : {power_saved:.1f} W<br>
Optimized Range : {optimized_range:.1f} km
</div>
'''

st.markdown(lcd_html, unsafe_allow_html=True)

st.markdown("---")

st.header("⚡ EV Optimization Flow")

optimization_flow = f"""
Throttle Input ({throttle}%)
        ↓
AI Driving Pattern Detection
        ↓
PWM Optimization Applied
        ↓
Motor Power Reduced
        ↓
Current Consumption Reduced
        ↓
Battery Efficiency Improved
        ↓
Optimized EV Range ({optimized_range:.1f} km)
"""

st.code(optimization_flow)

st.markdown("---")

st.caption("Final Year B.Tech Project | Department of Electrical Engineering")