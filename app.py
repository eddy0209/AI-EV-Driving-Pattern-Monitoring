import streamlit as st
import pandas as pd

st.title("AI-Based EV Driving Pattern Monitoring")

# User Input
throttle = st.slider("Throttle Input", 0, 100, 30)

# Simulated Parameters
speed = throttle * 0.8
current = throttle * 0.15
voltage = 24

# Driving Pattern Classification
if throttle < 30:
    pattern = "Eco"
elif throttle < 70:
    pattern = "Normal"
else:
    pattern = "Aggressive"

# Power Calculation
power = voltage * current

# Range Estimation
battery_capacity = 240  # Wh

if power == 0:
    estimated_range = 0
else:
    estimated_range = (battery_capacity / power) * speed

# Display Results
st.subheader("Vehicle Parameters")
st.write(f"Speed: {speed:.1f} km/h")
st.write(f"Current Consumption: {current:.1f} A")
st.write(f"Voltage: {voltage} V")

st.subheader("AI Classification")
st.success(f"Driving Pattern: {pattern}")

st.subheader("Energy Analysis")
st.write(f"Power Consumption: {power:.1f} W")
st.write(f"Estimated Remaining Range: {estimated_range:.1f} km")

# Feedback
if pattern == "Aggressive":
    st.error("High energy consumption detected!")
elif pattern == "Eco":
    st.info("Energy-efficient driving detected.")
else:
    st.warning("Moderate energy usage.")