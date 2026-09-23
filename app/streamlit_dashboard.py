import streamlit as st
import pandas as pd
import joblib
from pathlib import Path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EV Driving Pattern & Range Optimization",
    page_icon="🚗",
    layout="wide"
)


# ============================================================
# LOAD ML MODEL
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "ev_energy_consumption_model.joblib"

try:
    model = joblib.load(MODEL_PATH)
    model_loaded = True

except Exception as e:
    model_loaded = False
    model = None

    st.error(
        f"❌ ML model could not be loaded: {e}"
    )


# ============================================================
# TITLE
# ============================================================

st.title("🚗 EV Driving Pattern & Range Optimization")

st.write(
    "The system automatically detects the driving pattern, "
    "simulates vehicle behaviour and predicts energy consumption."
)


# ============================================================
# USER CONTROLS
# ============================================================

st.subheader("🎛️ Vehicle & Driving Controls")

col1, col2, col3 = st.columns(3)


# ------------------------------------------------------------
# COLUMN 1
# ------------------------------------------------------------

with col1:

    soc = st.slider(
        "🔋 Battery SOC (%)",
        min_value=10,
        max_value=100,
        value=70,
        step=1
    )

    soh = st.slider(
        "❤️ Battery SOH (%)",
        min_value=80,
        max_value=100,
        value=95,
        step=1
    )


# ------------------------------------------------------------
# COLUMN 2
# ------------------------------------------------------------

with col2:

    throttle = st.slider(
        "⚡ Throttle (%)",
        min_value=0,
        max_value=100,
        value=40,
        step=1
    )

    vehicle_weight = st.slider(
        "⚖️ Vehicle Weight (kg)",
        min_value=120,
        max_value=1200,
        value=500,
        step=10,
        help="Vehicle + driver + load. Training range: 120–1200 kg."
    )


# ------------------------------------------------------------
# COLUMN 3
# ------------------------------------------------------------

with col3:

    max_motor_power = st.slider(
        "🔧 Maximum Motor Power (W)",
        min_value=1000,
        max_value=15000,
        value=5000,
        step=500
    )

    road_gradient = st.slider(
        "🛣️ Road Gradient (%)",
        min_value=-8.0,
        max_value=8.0,
        value=0.0,
        step=0.5,
        help="Negative = downhill, 0 = flat, positive = uphill."
    )


# ============================================================
# AUTOMATIC DRIVING PATTERN
# ============================================================

if throttle <= 30:

    driving_pattern = "Eco"

    st.success(
        f"🌱 Eco Driving — Throttle: {throttle}%"
    )

elif throttle <= 65:

    driving_pattern = "Normal"

    st.info(
        f"🚗 Normal Driving — Throttle: {throttle}%"
    )

else:

    driving_pattern = "Aggressive"

    st.warning(
        f"🏎️ Aggressive Driving — Throttle: {throttle}%"
    )


st.caption(
    "Driving pattern is automatically detected from throttle input."
)


# ============================================================
# DERIVED BATTERY PARAMETERS
# ============================================================

# Battery nominal voltage
# Kept inside the ML training range: 36–96 V

battery_voltage = (
    48
    + ((soc - 10) / 90) * 24
)

battery_voltage = max(
    36,
    min(96, battery_voltage)
)


# Fixed battery capacity
# Within the training dataset range

battery_capacity = 85.0


# Battery nominal energy

battery_energy = (
    battery_voltage
    * battery_capacity
)


# Motor efficiency

motor_efficiency = 90.0


# Regen efficiency

regen_efficiency = 70.0


# ============================================================
# VEHICLE DYNAMICS
# ============================================================

# Reference vehicle

REFERENCE_WEIGHT = 500.0


# ------------------------------------------------------------
# 1. BASE SPEED FROM THROTTLE
# ------------------------------------------------------------

if throttle <= 30:

    base_speed = (
        20
        + (throttle / 30) * 20
    )

elif throttle <= 65:

    base_speed = (
        40
        + ((throttle - 30) / 35) * 25
    )

else:

    base_speed = (
        65
        + ((throttle - 65) / 35) * 35
    )


# ------------------------------------------------------------
# 2. WEIGHT EFFECT ON SPEED
# ------------------------------------------------------------

# Heavier vehicle -> lower achievable speed
#
# Square-root relationship prevents the effect
# from becoming unrealistically large.

weight_speed_factor = (
    (REFERENCE_WEIGHT / vehicle_weight) ** 0.5
)

weight_speed_factor = max(
    0.65,
    min(1.15, weight_speed_factor)
)


# ------------------------------------------------------------
# 3. ROAD GRADIENT EFFECT ON SPEED
# ------------------------------------------------------------

if road_gradient > 0:

    # Uphill reduces speed

    gradient_speed_factor = (
        1 - (road_gradient * 0.035)
    )

else:

    # Downhill allows speed to increase

    gradient_speed_factor = (
        1 + (abs(road_gradient) * 0.015)
    )


gradient_speed_factor = max(
    0.70,
    min(1.12, gradient_speed_factor)
)


# ------------------------------------------------------------
# 4. FINAL VEHICLE SPEED
# ------------------------------------------------------------

speed = (
    base_speed
    * weight_speed_factor
    * gradient_speed_factor
)


# Keep within ML training range

speed = max(
    5,
    min(120, speed)
)


# ============================================================
# ACCELERATION
# ============================================================

# Base acceleration from throttle

base_acceleration = (
    (throttle - 30) / 70
) * 2.5


# ------------------------------------------------------------
# Weight effect on acceleration
# ------------------------------------------------------------

weight_acceleration_factor = (
    REFERENCE_WEIGHT / vehicle_weight
)

weight_acceleration_factor = max(
    0.40,
    min(1.50, weight_acceleration_factor)
)


# ------------------------------------------------------------
# Gradient effect on acceleration
# ------------------------------------------------------------

# Uphill reduces acceleration.
# Downhill increases acceleration.

gradient_acceleration_effect = (
    -road_gradient * 0.12
)


# Final acceleration

acceleration = (
    base_acceleration
    * weight_acceleration_factor
    + gradient_acceleration_effect
)


# ------------------------------------------------------------
# Low throttle / coasting
# ------------------------------------------------------------

if throttle < 10:

    acceleration -= 0.25


# ------------------------------------------------------------
# Limit to ML training range
# ------------------------------------------------------------

acceleration = max(
    -3,
    min(3, acceleration)
)


# ============================================================
# BATTERY TEMPERATURE
# ============================================================

battery_temperature = (
    25
    + throttle * 0.08
    + (100 - soh) * 0.15
    + abs(acceleration) * 0.8
    + max(road_gradient, 0) * 0.15
)

battery_temperature = max(
    15,
    min(45, battery_temperature)
)


# ============================================================
# MOTOR POWER DEMAND
# ============================================================

motor_power_requested = (
    max_motor_power
    * throttle
    / 100
)


motor_power_requested = max(
    0,
    motor_power_requested
)


# ============================================================
# BATTERY CURRENT
# ============================================================

battery_power = (
    motor_power_requested
    / (motor_efficiency / 100)
)


battery_current = (
    battery_power
    / battery_voltage
)


# ============================================================
# POWER OPTIMIZATION
# ============================================================

power_limit = float(
    max_motor_power
)


# ------------------------------------------------------------
# Battery health limitation
# ------------------------------------------------------------

if soh < 85:

    power_limit *= 0.75

elif soh < 90:

    power_limit *= 0.85

elif soh < 95:

    power_limit *= 0.95


# ------------------------------------------------------------
# Temperature limitation
# ------------------------------------------------------------

if battery_temperature > 40:

    power_limit *= 0.70

elif battery_temperature > 35:

    power_limit *= 0.85


# ------------------------------------------------------------
# Aggressive driving limitation
# ------------------------------------------------------------

if driving_pattern == "Aggressive":

    power_limit *= 0.90


# ------------------------------------------------------------
# Heavy vehicle limitation
# ------------------------------------------------------------

if vehicle_weight > 900:

    power_limit *= 0.90


# ------------------------------------------------------------
# Uphill limitation
# ------------------------------------------------------------

if road_gradient > 5:

    power_limit *= 0.90


power_limit = max(
    500,
    power_limit
)


# ============================================================
# OPTIMIZED MOTOR POWER
# ============================================================

optimized_power = min(
    motor_power_requested,
    power_limit
)


# ============================================================
# PWM DUTY
# ============================================================

if max_motor_power > 0:

    pwm_duty = (
        optimized_power
        / max_motor_power
    ) * 100

else:

    pwm_duty = 0


pwm_duty = max(
    0,
    min(100, pwm_duty)
)


# ============================================================
# REGENERATIVE BRAKING
# ============================================================

# Regen is based on:
#
# 1. Downhill gradient
# 2. Low throttle / coasting
# 3. Vehicle speed
# 4. Vehicle weight
#
# There is no separate brake slider, so low throttle
# represents the vehicle entering a coasting/deceleration state.


# ------------------------------------------------------------
# Regen eligibility
# ------------------------------------------------------------

downhill = road_gradient < 0

coasting = throttle <= 20

moving = speed > 10


regen_active = (
    downhill
    and coasting
    and moving
)


# ------------------------------------------------------------
# Calculate regenerative braking power
# ------------------------------------------------------------

if regen_active:

    # Downhill intensity
    gradient_factor = (
        abs(road_gradient) / 8
    )

    gradient_factor = max(
        0,
        min(1, gradient_factor)
    )


    # Vehicle speed effect
    speed_factor = (
        speed / 120
    )

    speed_factor = max(
        0.10,
        min(1, speed_factor)
    )


    # Heavier vehicle has more kinetic/potential energy
    # available for recovery

    weight_factor = (
        vehicle_weight / REFERENCE_WEIGHT
    )

    weight_factor = max(
        0.50,
        min(2.0, weight_factor)
    )


    # Less throttle = stronger coasting/regen request

    throttle_factor = (
        1 - throttle / 20
    )

    throttle_factor = max(
        0,
        min(1, throttle_factor)
    )


    # Calculate recovery power

    recovered_power = (
        max_motor_power
        * 0.25
        * gradient_factor
        * speed_factor
        * weight_factor
        * throttle_factor
        * (regen_efficiency / 100)
    )


    # Prevent recovery from exceeding motor rating

    recovered_power = max(
        0,
        min(max_motor_power * 0.30, recovered_power)
    )

else:

    recovered_power = 0


# ============================================================
# ML MODEL INPUT
# ============================================================

model_input = pd.DataFrame([{

    "Battery_Nominal_V": battery_voltage,

    "Battery_Capacity_Ah": battery_capacity,

    "Battery_Energy_Wh": battery_energy,

    "SOC_pct": soc,

    "SOH_pct": soh,

    "Battery_Temperature_C": battery_temperature,

    "Motor_Rated_Power_kW": (
        max_motor_power / 1000
    ),

    "Motor_Efficiency_pct": motor_efficiency,

    "Total_Mass_kg": vehicle_weight,

    "Vehicle_Speed_kmh": speed,

    "Acceleration_mps2": acceleration,

    "Throttle_pct": throttle,

    "Road_Gradient_pct": road_gradient,

    "Regen_Efficiency_pct": regen_efficiency

}])


# ============================================================
# RANDOM FOREST PREDICTION
# ============================================================

if model_loaded:

    try:

        ml_energy = float(
            model.predict(model_input)[0]
        )

        ml_energy = max(
            1,
            ml_energy
        )


        # ====================================================
        # PHYSICS-BASED CORRECTIONS
        # ====================================================

        # Reference conditions

        reference_motor_power = 5.0


        # ----------------------------------------------------
        # Vehicle weight correction
        # ----------------------------------------------------

        weight_factor = (
            1
            + (
                (vehicle_weight - REFERENCE_WEIGHT)
                * 0.00025
            )
        )

        weight_factor = max(
            0.85,
            min(1.20, weight_factor)
        )


        # ----------------------------------------------------
        # Motor power correction
        # ----------------------------------------------------

        motor_power_kw = (
            max_motor_power / 1000
        )

        motor_power_factor = (
            1
            + (
                (motor_power_kw - reference_motor_power)
                * 0.025
            )
        )

        motor_power_factor = max(
            0.90,
            min(1.25, motor_power_factor)
        )


        # ----------------------------------------------------
        # SOH correction
        # ----------------------------------------------------

        soh_factor = (
            1
            + (
                (100 - soh)
                * 0.004
            )
        )

        soh_factor = max(
            1.00,
            min(1.08, soh_factor)
        )


        # ----------------------------------------------------
        # Road gradient correction
        # ----------------------------------------------------

        gradient_factor = (
            1
            + (
                road_gradient
                * 0.04
            )
        )

        gradient_factor = max(
            0.70,
            min(1.35, gradient_factor)
        )


        # ----------------------------------------------------
        # Final energy consumption
        # ----------------------------------------------------

        predicted_energy = (
            ml_energy
            * weight_factor
            * motor_power_factor
            * soh_factor
            * gradient_factor
        )


        # ----------------------------------------------------
        # Regen correction
        # ----------------------------------------------------

        if regen_active and recovered_power > 0:

            regen_reduction = (
                recovered_power
                / max_motor_power
            ) * 0.15

            predicted_energy *= (
                1 - regen_reduction
            )


        predicted_energy = max(
            1,
            predicted_energy
        )


    except Exception as e:

        predicted_energy = None
        ml_energy = None

        st.error(
            f"❌ ML prediction error: {e}"
        )

else:

    predicted_energy = None
    ml_energy = None


# ============================================================
# ESTIMATED RANGE
# ============================================================

if predicted_energy is not None:

    # SOH determines usable battery capacity

    usable_energy = (
        battery_energy
        * (soc / 100)
        * (soh / 100)
    )


    # Regenerative energy contribution
    #
    # Only a small fraction of recovered power is assumed
    # to be recovered over the simulated distance.

    if regen_active:

        regen_energy_bonus = (
            recovered_power
            * 0.01
        )

        usable_energy += regen_energy_bonus


    estimated_range = (
        usable_energy
        / predicted_energy
    )

else:

    usable_energy = 0
    estimated_range = 0


# ============================================================
# SYSTEM RESULTS
# ============================================================

st.subheader("📊 System Results")

r1, r2, r3, r4 = st.columns(4)


with r1:

    st.metric(
        "⚡ Energy Consumption",
        f"{predicted_energy:.1f} Wh/km"
        if predicted_energy is not None
        else "N/A"
    )


with r2:

    st.metric(
        "🚗 Estimated Range",
        f"{estimated_range:.1f} km"
    )


with r3:

    st.metric(
        "🔋 Usable Battery",
        f"{usable_energy:.0f} Wh"
    )


with r4:

    st.metric(
        "🎛️ PWM Duty",
        f"{pwm_duty:.1f}%"
    )


# ============================================================
# VEHICLE STATUS
# ============================================================

st.subheader("🚘 Vehicle Status")

v1, v2, v3 = st.columns(3)


# ------------------------------------------------------------
# Battery
# ------------------------------------------------------------

with v1:

    st.write(
        f"🔋 **Battery Voltage:** "
        f"{battery_voltage:.1f} V"
    )

    st.write(
        f"⚡ **Battery Current:** "
        f"{battery_current:.1f} A"
    )

    st.write(
        f"🌡️ **Battery Temperature:** "
        f"{battery_temperature:.1f} °C"
    )


# ------------------------------------------------------------
# Vehicle dynamics
# ------------------------------------------------------------

with v2:

    st.write(
        f"🚗 **Vehicle Speed:** "
        f"{speed:.1f} km/h"
    )

    st.write(
        f"📈 **Acceleration:** "
        f"{acceleration:.2f} m/s²"
    )

    st.write(
        f"🛣️ **Road Gradient:** "
        f"{road_gradient:+.1f}%"
    )


# ------------------------------------------------------------
# Vehicle / motor
# ------------------------------------------------------------

with v3:

    st.write(
        f"⚖️ **Vehicle Weight:** "
        f"{vehicle_weight} kg"
    )

    st.write(
        f"🔧 **Motor Power:** "
        f"{optimized_power:.0f} W"
    )

    st.write(
        f"⚙️ **Motor Efficiency:** "
        f"{motor_efficiency:.0f}%"
    )


# ============================================================
# POWER OPTIMIZATION
# ============================================================

st.subheader("⚙️ Power Optimization")


if optimized_power < motor_power_requested:

    st.warning(
        f"Power limited: "
        f"{motor_power_requested:.0f} W → "
        f"{optimized_power:.0f} W"
    )

else:

    st.success(
        f"Power delivery normal: "
        f"{optimized_power:.0f} W"
    )


st.write(
    f"🔧 **Maximum Motor Power:** "
    f"{max_motor_power:.0f} W"
)

st.write(
    f"⚡ **Power Limit:** "
    f"{power_limit:.0f} W"
)


# ============================================================
# REGENERATIVE BRAKING
# ============================================================

st.subheader("♻️ Regenerative Braking")


if regen_active:

    st.success(
        f"♻️ Regenerative Braking ACTIVE"
    )

    st.write(
        f"🔋 Estimated Recovered Power: "
        f"**{recovered_power:.0f} W**"
    )

    st.write(
        f"🛣️ Downhill Gradient: "
        f"**{abs(road_gradient):.1f}%**"
    )

    st.write(
        f"🚗 Vehicle Speed: "
        f"**{speed:.1f} km/h**"
    )

else:

    if road_gradient >= 0:

        st.info(
            "Regenerative braking inactive — "
            "vehicle is not travelling downhill."
        )

    elif throttle > 20:

        st.info(
            "Regenerative braking inactive — "
            "throttle demand is too high."
        )

    elif speed <= 10:

        st.info(
            "Regenerative braking inactive — "
            "vehicle speed is too low."
        )

    else:

        st.info(
            "Regenerative braking inactive."
        )


# ============================================================
# SYSTEM STATUS
# ============================================================

st.subheader("🟢 System Status")

st.success(
    "✓ Sensor data processed\n\n"
    "✓ Driving pattern detected automatically\n\n"
    "✓ Vehicle dynamics calculated\n\n"
    "✓ Random Forest prediction completed\n\n"
    "✓ Power optimization applied\n\n"
    "✓ Regenerative braking monitored"
)


# ============================================================
# ML INFORMATION
# ============================================================

with st.expander("🤖 ML Model Information"):

    st.write(
        "**Model:** Random Forest Regressor"
    )

    st.write(
        "**Target:** Energy Consumption (Wh/km)"
    )

    st.write(
        "**Input Features:** 14"
    )

    if model_loaded and ml_energy is not None:

        st.write(
            f"**Raw ML Prediction:** "
            f"{ml_energy:.2f} Wh/km"
        )

        st.write(
            f"**Final Corrected Prediction:** "
            f"{predicted_energy:.2f} Wh/km"
        )

    st.write(
        "Driving Pattern is automatically detected "
        "from throttle and is not directly supplied "
        "as an ML feature."
    )