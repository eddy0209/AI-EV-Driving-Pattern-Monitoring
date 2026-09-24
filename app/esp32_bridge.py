from fastapi import FastAPI
from pydantic import BaseModel

from app.main import EVSimulation, EVSimulationConfig


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="EV ESP32 Bridge",
    version="1.0"
)


# ============================================================
# ESP32 SENSOR DATA
# ============================================================

class SensorData(BaseModel):

    # Main throttle input
    throttle_pct: float = 0.0

    # Optional compatibility field
    throttle: float | None = None

    # Sensors
    acceleration_mps2: float = 0.0
    battery_temp_c: float = 25.0
    battery_voltage_v: float = 48.0
    soc_pct: float = 70.0
    soh_pct: float = 95.0
    speed_kmh: float = 0.0

    # Simulation control
    simulation_running: bool = False
    start: bool = False
    stop: bool = False
    reset: bool = False


# ============================================================
# SIMULATION CONFIGURATION
# ============================================================

config = EVSimulationConfig(
    battery_voltage_v=48.0,
    battery_capacity_ah=85.0,
    initial_soc_pct=70.0,
    battery_soh_pct=95.0,

    motor_rated_power_kw=5.0,
    motor_efficiency_pct=90.0,

    vehicle_mass_kg=500.0,

    road_gradient_pct=0.0,

    regen_efficiency_pct=70.0,
    max_regen_power_kw=2.0,

    timestep_s=1.0,

    auxiliary_power_w=20.0,

    range_reserve_soc_pct=5.0,

    optimization_enabled=True,

    max_power_ramp_kw_per_step=0.20,
)


simulation = EVSimulation(config)


# ============================================================
# SENSOR ENDPOINT
# ============================================================

@app.post("/sensor")
def receive_sensor_data(data: SensorData):

    # --------------------------------------------------------
    # Determine throttle
    # --------------------------------------------------------

    # Prefer throttle_pct.
    # If an older client sends "throttle", use that instead.
    throttle = data.throttle_pct

    if data.throttle is not None:
        throttle = data.throttle

    # Keep throttle inside valid range
    throttle = max(0.0, min(100.0, throttle))


    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    if data.reset:
        simulation.reset()


    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    if data.start or data.simulation_running:
        simulation.start()


    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    if data.stop:
        simulation.stop()


    # --------------------------------------------------------
    # Update battery temperature
    # --------------------------------------------------------

    simulation.config.initial_battery_temp_c = data.battery_temp_c


    # --------------------------------------------------------
    # Run simulation
    # --------------------------------------------------------

    state = simulation.step(
        throttle_pct=throttle,
        force=True
    )


    # --------------------------------------------------------
    # Return simulation state
    # --------------------------------------------------------

    return {

        "throttle_pct":
            throttle,

        "optimized_power_kw":
            state.optimized_power_kw,

        "requested_power_kw":
            state.requested_power_kw,

        "speed_kmh":
            state.speed_kmh,

        "acceleration_mps2":
            state.acceleration_mps2,

        "motor_rpm":
            state.motor_rpm,

        "battery_voltage_v":
            state.battery_voltage_v,

        "battery_current_a":
            state.battery_current_a,

        "battery_power_kw":
            state.battery_power_kw,

        "battery_temp_c":
            state.battery_temperature_c,

        "soc_pct":
            state.soc_pct,

        "soh_pct":
            state.soh_pct,

        "distance_km":
            state.distance_km,

        "energy_consumed_wh":
            state.energy_consumed_wh,

        "energy_recovered_wh":
            state.energy_recovered_wh,

        "wh_per_km":
            state.wh_per_km,

        "predicted_wh_per_km":
            state.predicted_wh_per_km
            if state.predicted_wh_per_km is not None
            else 0.0,

        "remaining_range_km":
            state.remaining_range_km,

        "regen_active":
            state.regen_active,

        "regen_power_kw":
            state.regen_power_kw,

        "optimization_status":
            state.optimization_status,

        "power_limit_kw":
            state.power_limit_kw,

        "status":
            state.optimization_status,
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def health():

    return {
        "status": "online",
        "system": "EV Simulation Backend"
    }