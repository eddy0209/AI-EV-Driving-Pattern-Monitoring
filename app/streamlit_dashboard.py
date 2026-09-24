import streamlit as st
from pathlib import Path
import pandas as pd

from app.main import EVSimulation, EVSimulationConfig



# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EV Driving Pattern & Range Optimization",
    page_icon="🚗",
    layout="wide",
)

st.title("🚗 EV Driving Pattern & Range Optimization")
st.caption(
    "Physics-based EV simulation with power optimization, "
    "regenerative braking, ML energy prediction and range estimation."
)


# ============================================================
# SESSION STATE
# ============================================================

if "simulation" not in st.session_state:
    st.session_state.simulation = None

if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False

if "config_locked" not in st.session_state:
    st.session_state.config_locked = False


# ============================================================
# VEHICLE CONFIGURATION
# ============================================================

st.subheader("⚙️ Vehicle Configuration")
st.caption(
    "Configure the vehicle before START. During the simulation, "
    "Throttle is the main user-controlled input."
)

c1, c2, c3 = st.columns(3)

with c1:
    battery_voltage = st.number_input(
        "🔋 Battery Nominal Voltage (V)",
        min_value=12.0,
        max_value=120.0,
        value=48.0,
        step=1.0,
        disabled=st.session_state.config_locked,
    )

    battery_capacity = st.number_input(
        "🔋 Battery Capacity (Ah)",
        min_value=5.0,
        max_value=300.0,
        value=85.0,
        step=1.0,
        disabled=st.session_state.config_locked,
    )

    initial_soc = st.slider(
        "🔋 Initial SOC (%)",
        min_value=10,
        max_value=100,
        value=70,
        step=1,
        disabled=st.session_state.config_locked,
    )

with c2:
    battery_soh = st.slider(
        "❤️ Battery SOH (%)",
        min_value=50,
        max_value=100,
        value=95,
        step=1,
        disabled=st.session_state.config_locked,
    )

    motor_power_kw = st.number_input(
        "🔧 Motor Rated Power (kW)",
        min_value=0.5,
        max_value=50.0,
        value=5.0,
        step=0.5,
        disabled=st.session_state.config_locked,
    )

    motor_efficiency = st.slider(
        "⚙️ Motor Efficiency (%)",
        min_value=50,
        max_value=99,
        value=90,
        step=1,
        disabled=st.session_state.config_locked,
    )

with c3:
    vehicle_mass = st.number_input(
        "⚖️ Vehicle Total Mass (kg)",
        min_value=100.0,
        max_value=3000.0,
        value=500.0,
        step=10.0,
        disabled=st.session_state.config_locked,
    )

    road_gradient = st.slider(
        "🛣️ Road Gradient (%)",
        min_value=-15.0,
        max_value=15.0,
        value=0.0,
        step=0.5,
        help="Negative = downhill, positive = uphill.",
        disabled=st.session_state.config_locked,
    )

    regen_efficiency = st.slider(
        "♻️ Regen Efficiency (%)",
        min_value=20,
        max_value=95,
        value=70,
        step=1,
        disabled=st.session_state.config_locked,
    )


# ============================================================
# EXTRA SIMULATION SETTINGS
# ============================================================

with st.expander("🔧 Advanced Simulation Settings"):
    a1, a2, a3 = st.columns(3)

    with a1:
        max_regen_power = st.number_input(
            "Maximum Regen Power (kW)",
            min_value=0.1,
            max_value=50.0,
            value=2.0,
            step=0.1,
            disabled=st.session_state.config_locked,
        )

    with a2:
        range_reserve = st.slider(
            "Range Reserve SOC (%)",
            min_value=0,
            max_value=30,
            value=5,
            step=1,
            disabled=st.session_state.config_locked,
        )

    with a3:
        optimization_enabled = st.checkbox(
            "Enable Power Optimization",
            value=True,
            disabled=st.session_state.config_locked,
        )


# ============================================================
# CONFIGURATION / CONTROL BUTTONS
# ============================================================

b1, b2, b3 = st.columns(3)

with b1:
    start_clicked = st.button(
        "▶️ START",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.simulation_running,
    )

with b2:
    stop_clicked = st.button(
        "⏸️ STOP",
        use_container_width=True,
        disabled=not st.session_state.simulation_running,
    )

with b3:
    reset_clicked = st.button(
        "🔄 RESET",
        use_container_width=True,
    )


def make_config():
    return EVSimulationConfig(
        battery_voltage_v=float(battery_voltage),
        battery_capacity_ah=float(battery_capacity),
        initial_soc_pct=float(initial_soc),
        battery_soh_pct=float(battery_soh),
        initial_battery_temp_c=25.0,
        motor_rated_power_kw=float(motor_power_kw),
        motor_efficiency_pct=float(motor_efficiency),
        vehicle_mass_kg=float(vehicle_mass),
        road_gradient_pct=float(road_gradient),
        regen_efficiency_pct=float(regen_efficiency),
        max_regen_power_kw=float(max_regen_power),
        timestep_s=1.0,
        auxiliary_power_w=20.0,
        range_reserve_soc_pct=float(range_reserve),
        optimization_enabled=bool(optimization_enabled),
        max_power_ramp_kw_per_step=0.20,
    )


if start_clicked:
    config = make_config()

    model_path = (
        Path(__file__).resolve().parent
        / "ev_energy_consumption_model.joblib"
    )

    st.session_state.simulation = EVSimulation(
        config=config,
        model_path=model_path,
    )

    st.session_state.simulation.start()
    st.session_state.simulation_running = True
    st.session_state.config_locked = True
    st.rerun()


if stop_clicked:
    if st.session_state.simulation is not None:
        st.session_state.simulation.stop()

    st.session_state.simulation_running = False
    st.rerun()


if reset_clicked:
    if st.session_state.simulation is not None:
        st.session_state.simulation.reset()

    st.session_state.simulation = None
    st.session_state.simulation_running = False
    st.session_state.config_locked = False
    st.rerun()


# ============================================================
# LIVE SIMULATION
# ============================================================

if st.session_state.simulation is None:
    st.info(
        "Configure the vehicle above and press START to begin the simulation."
    )
    st.stop()


simulation = st.session_state.simulation


@st.fragment(run_every=1.0)
def live_dashboard():
    # --------------------------------------------------------
    # THROTTLE
    # --------------------------------------------------------

    st.subheader("🎛️ Live Driving Control")

    throttle = st.slider(
        "⚡ Throttle (%)",
        min_value=0,
        max_value=100,
        value=40,
        step=1,
        key="live_throttle",
        disabled=not st.session_state.simulation_running,
    )

    if throttle <= 30:
        driving_pattern = "Eco"
        pattern_message = "🌱 Eco Driving"
    elif throttle <= 65:
        driving_pattern = "Normal"
        pattern_message = "🚗 Normal Driving"
    else:
        driving_pattern = "Aggressive"
        pattern_message = "🏎️ Aggressive Driving"

    st.caption(
        f"{pattern_message} — automatically detected from throttle."
    )

    # --------------------------------------------------------
    # ADVANCE SIMULATION
    # --------------------------------------------------------

    if st.session_state.simulation_running:
        state = simulation.step(throttle)
    else:
        state = simulation.last_state

    # --------------------------------------------------------
    # TOP METRICS
    # --------------------------------------------------------

    st.subheader("📊 Live System Results")

    r1, r2, r3, r4 = st.columns(4)

    with r1:
        st.metric("🔋 SOC", f"{state.soc_pct:.2f}%")

    with r2:
        st.metric("🚗 Speed", f"{state.speed_kmh:.1f} km/h")

    with r3:
        if state.predicted_wh_per_km is not None:
            st.metric(
                "⚡ Predicted Consumption",
                f"{state.predicted_wh_per_km:.1f} Wh/km",
            )
        else:
            st.metric(
                "⚡ Trip Consumption",
                f"{state.wh_per_km:.1f} Wh/km",
            )

    with r4:
        if state.remaining_range_km is not None:
            st.metric(
                "🛣️ Remaining Range",
                f"{state.remaining_range_km:.1f} km",
            )
        else:
            st.metric("🛣️ Remaining Range", "Waiting for data")

    # --------------------------------------------------------
    # VEHICLE / BATTERY STATUS
    # --------------------------------------------------------

    st.subheader("🚘 Vehicle & Battery Status")

    v1, v2, v3 = st.columns(3)

    with v1:
        st.write(f"**Speed:** {state.speed_kmh:.2f} km/h")
        st.write(f"**Acceleration:** {state.acceleration_mps2:.3f} m/s²")
        st.write(f"**Motor RPM:** {state.motor_rpm:.0f} RPM")
        st.write(f"**Time:** {state.time_s:.0f} s")

    with v2:
        st.write(f"**Battery Voltage:** {state.battery_voltage_v:.1f} V")
        st.write(f"**Battery Current:** {state.battery_current_a:.2f} A")
        st.write(f"**Battery Power:** {state.battery_power_kw:.2f} kW")
        st.write(f"**Battery Temperature:** {state.battery_temperature_c:.1f} °C")

    with v3:
        st.write(f"**SOC:** {state.soc_pct:.2f}%")
        st.write(f"**SOH:** {state.soh_pct:.1f}%")
        st.write(f"**Distance:** {state.distance_km:.3f} km")
        st.write(f"**Trip Wh/km:** {state.wh_per_km:.1f}")

    # --------------------------------------------------------
    # OPTIMIZATION
    # --------------------------------------------------------

    st.subheader("⚙️ Power Optimization")

    o1, o2, o3, o4 = st.columns(4)

    with o1:
        st.metric(
            "Requested Power",
            f"{state.requested_power_kw:.2f} kW",
        )

    with o2:
        st.metric(
            "Optimized Power",
            f"{state.optimized_power_kw:.2f} kW",
        )

    with o3:
        st.metric(
            "Power Limit",
            f"{state.power_limit_kw:.2f} kW",
        )

    with o4:
        st.metric(
            "Optimization Status",
            state.optimization_status,
        )

    if state.optimized_power_kw < state.requested_power_kw:
        st.warning(
            "Power delivery is being limited by the optimizer."
        )
    else:
        st.success("Power delivery is within the current limit.")

    # --------------------------------------------------------
    # REGEN
    # --------------------------------------------------------

    st.subheader("♻️ Regenerative Braking")

    g1, g2, g3 = st.columns(3)

    with g1:
        if state.regen_active:
            st.success("♻️ REGEN ACTIVE")
        else:
            st.info("Regen inactive")

    with g2:
        st.metric(
            "Regen Power",
            f"{state.regen_power_kw:.2f} kW",
        )

    with g3:
        st.metric(
            "Energy Recovered",
            f"{state.cumulative_energy_recovered_wh:.2f} Wh",
        )

    st.caption(state.regen_status)

    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    st.subheader("🔋 Energy Accounting")

    e1, e2, e3, e4 = st.columns(4)

    with e1:
        st.metric(
            "Energy Consumed",
            f"{state.cumulative_energy_consumed_wh:.2f} Wh",
        )

    with e2:
        st.metric(
            "Energy Recovered",
            f"{state.cumulative_energy_recovered_wh:.2f} Wh",
        )

    with e3:
        st.metric(
            "Net Energy",
            f"{state.cumulative_net_energy_wh:.2f} Wh",
        )

    with e4:
        st.metric(
            "Battery Power",
            f"{state.battery_power_kw:.2f} kW",
        )

    # --------------------------------------------------------
    # ML STATUS
    # --------------------------------------------------------

    st.subheader("🤖 ML Model")

    if state.ml_available:
        st.success("Random Forest energy model loaded and active.")

        m1, m2 = st.columns(2)

        with m1:
            st.metric(
                "Predicted Wh/km",
                f"{state.predicted_wh_per_km:.2f}",
            )

        with m2:
            if state.remaining_range_km is not None:
                st.metric(
                    "ML-based Remaining Range",
                    f"{state.remaining_range_km:.2f} km",
                )
    else:
        st.warning(
            "ML model file not found. The physics simulation is running, "
            "but range currently uses measured trip Wh/km as a fallback."
        )
        st.caption(
            "Place ev_energy_consumption_model.joblib beside app.py "
            "to activate the Random Forest prediction."
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status_text = (
        "🟢 RUNNING"
        if st.session_state.simulation_running
        else "⏸️ STOPPED"
    )

    st.subheader(f"System Status: {status_text}")


live_dashboard()