from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from app.optimizer import EVPowerOptimizer, OptimizerConfig
from app.regen_controller import RegenController
from app.vehicle_model import VehicleModel
from app.energy_model import EnergyModel
from app.ml_model import EVEnergyMLModel
from app.range_model import RangeModel


@dataclass
class EVSimulationConfig:
    # Battery
    battery_voltage_v: float = 48.0
    battery_capacity_ah: float = 85.0
    initial_soc_pct: float = 70.0
    battery_soh_pct: float = 95.0
    initial_battery_temp_c: float = 25.0

    # Motor
    motor_rated_power_kw: float = 5.0
    motor_efficiency_pct: float = 90.0

    # Vehicle
    vehicle_mass_kg: float = 500.0
    wheel_radius_m: float = 0.25
    gear_ratio: float = 8.0

    # Road
    road_gradient_pct: float = 0.0

    # Regen
    regen_efficiency_pct: float = 70.0
    max_regen_power_kw: float = 2.0

    # Simulation
    timestep_s: float = 1.0
    auxiliary_power_w: float = 20.0
    range_reserve_soc_pct: float = 5.0

    # Optimizer
    optimization_enabled: bool = True
    max_power_ramp_kw_per_step: float = 0.20


@dataclass
class EVSimulationState:
    time_s: float
    throttle_pct: float

    speed_kmh: float
    acceleration_mps2: float
    motor_rpm: float

    battery_voltage_v: float
    battery_current_a: float
    battery_power_kw: float
    battery_temperature_c: float

    soc_pct: float
    soh_pct: float

    requested_power_kw: float
    optimized_power_kw: float
    power_limit_kw: float
    optimization_status: str

    regen_active: bool
    regen_power_kw: float
    energy_recovered_wh: float
    cumulative_energy_recovered_wh: float

    energy_consumed_wh: float
    cumulative_energy_consumed_wh: float
    net_energy_wh: float
    cumulative_net_energy_wh: float

    distance_km: float
    wh_per_km: float

    predicted_wh_per_km: Optional[float]
    remaining_range_km: Optional[float]
    ml_available: bool

    regen_status: str


class EVSimulation:
    def __init__(
        self,
        config: Optional[EVSimulationConfig] = None,
        model_path=None,
    ):
        self.config = config or EVSimulationConfig()

        self.optimizer = EVPowerOptimizer(
            OptimizerConfig(
                motor_rated_power_kw=self.config.motor_rated_power_kw,
                motor_efficiency=(
                    self.config.motor_efficiency_pct / 100.0
                ),
                max_motor_power_kw=self.config.motor_rated_power_kw,
                max_power_ramp_kw_per_step=(
                    self.config.max_power_ramp_kw_per_step
                ),
                max_regen_power_kw=self.config.max_regen_power_kw,
            )
        )

        self.vehicle = VehicleModel(
            mass_kg=self.config.vehicle_mass_kg,
            motor_rated_power_kw=self.config.motor_rated_power_kw,
            motor_efficiency_pct=self.config.motor_efficiency_pct,
            wheel_radius_m=self.config.wheel_radius_m,
            gear_ratio=self.config.gear_ratio,
            road_gradient_pct=self.config.road_gradient_pct,
            timestep_s=self.config.timestep_s,
        )

        self.regen = RegenController(
            regen_efficiency_pct=self.config.regen_efficiency_pct,
            max_regen_power_kw=self.config.max_regen_power_kw,
            timestep_s=self.config.timestep_s,
        )

        self.energy = EnergyModel(
            battery_voltage_v=self.config.battery_voltage_v,
            battery_capacity_ah=self.config.battery_capacity_ah,
            initial_soc_pct=self.config.initial_soc_pct,
            battery_soh_pct=self.config.battery_soh_pct,
            motor_efficiency_pct=self.config.motor_efficiency_pct,
            auxiliary_power_w=self.config.auxiliary_power_w,
            timestep_s=self.config.timestep_s,
        )

        self.range_model = RangeModel(
            reserve_soc_pct=self.config.range_reserve_soc_pct
        )

        # ML is optional during development so the physics simulator can
        # still be tested when the .joblib file has not been copied yet.
        self.ml_model = None
        self.ml_available = False

        try:
            self.ml_model = EVEnergyMLModel(model_path)
            self.ml_available = True
        except Exception:
            self.ml_model = None
            self.ml_available = False

        self.running = False
        self.time_s = 0.0
        self.throttle_pct = 0.0
        self.battery_temperature_c = (
            self.config.initial_battery_temp_c
        )

        self.last_state = self._build_state(
            requested_power_kw=0.0,
            optimized_power_kw=0.0,
            power_limit_kw=self.config.motor_rated_power_kw,
            optimization_status="READY",
            regen_active=False,
            regen_power_kw=0.0,
            energy_recovered_wh=0.0,
            regen_status="Ready",
            energy_consumed_wh=0.0,
            net_energy_wh=0.0,
            predicted_wh_per_km=None,
            remaining_range_km=None,
        )

    def start(self):
        """Start/resume the simulation without resetting SOC."""
        self.running = True

    def stop(self):
        """Pause the simulation without resetting its state."""
        self.running = False

    def reset(self):
        """Reset the trip and restore the configured initial SOC."""
        self.running = False
        self.time_s = 0.0
        self.throttle_pct = 0.0
        self.battery_temperature_c = (
            self.config.initial_battery_temp_c
        )

        self.optimizer.reset()
        self.vehicle.reset(0.0)
        self.energy.reset(self.config.initial_soc_pct)
        self.regen.reset()

        self.last_state = self._build_state(
            requested_power_kw=0.0,
            optimized_power_kw=0.0,
            power_limit_kw=self.config.motor_rated_power_kw,
            optimization_status="READY",
            regen_active=False,
            regen_power_kw=0.0,
            energy_recovered_wh=0.0,
            regen_status="Ready",
            energy_consumed_wh=0.0,
            net_energy_wh=0.0,
            predicted_wh_per_km=None,
            remaining_range_km=None,
        )

    def set_road_gradient(self, road_gradient_pct):
        """Change road gradient for the next simulation steps."""
        self.config.road_gradient_pct = float(road_gradient_pct)
        self.vehicle.road_gradient_pct = float(road_gradient_pct)

    def step(self, throttle_pct, force=False):
        """
        Advance one simulation timestep.

        If the simulation is stopped, no physical state changes unless
        force=True. This lets a UI display the current state without
        accidentally consuming battery energy.
        """
        if not self.running and not force:
            return self.last_state

        self.throttle_pct = max(
            0.0,
            min(100.0, float(throttle_pct))
        )

        # 1. Optimize driver power request.
        optimization = self.optimizer.step(
            throttle_pct=self.throttle_pct,
            speed_kmh=self.vehicle.speed_mps * 3.6,
            acceleration_mps2=0.0,
            soc_percent=self.energy.soc_pct,
            battery_temp_c=self.battery_temperature_c,
            optimization_enabled=self.config.optimization_enabled,
        )

        # 2. Vehicle dynamics.
        vehicle_state = self.vehicle.calculate(
            optimized_power_kw=optimization.optimized_power_kw,
            road_gradient_pct=self.config.road_gradient_pct,
            throttle_pct=self.throttle_pct,
        )

        # 3. Estimate battery temperature for the next control step.
        self._update_battery_temperature(
            battery_power_kw=(
                optimization.optimized_power_kw
            ),
            regen_power_kw=0.0,
        )

        # 4. Regen uses actual speed/deceleration.
        regen_result = self.regen.calculate(
            speed_kmh=vehicle_state.speed_kmh,
            acceleration_mps2=vehicle_state.acceleration_mps2,
            vehicle_mass_kg=self.config.vehicle_mass_kg,
            soc_pct=self.energy.soc_pct,
            battery_temp_c=self.battery_temperature_c,
            motor_max_regen_power_kw=self.config.max_regen_power_kw,
        )

        # 5. Battery energy/SOC.
        energy_state = self.energy.calculate(
            motor_power_kw=optimization.optimized_power_kw,
            regen_power_kw=regen_result.regen_power_kw,
            speed_kmh=vehicle_state.speed_kmh,
            battery_voltage_v=self.config.battery_voltage_v,
        )

        # 6. ML prediction.
        predicted_wh_per_km = None

        if self.ml_available:
            try:
                prediction = self.ml_model.predict(
                    battery_nominal_v=self.config.battery_voltage_v,
                    battery_capacity_ah=self.config.battery_capacity_ah,
                    soc_pct=energy_state.soc_pct,
                    soh_pct=self.config.battery_soh_pct,
                    battery_temperature_c=self.battery_temperature_c,
                    motor_rated_power_kw=(
                        self.config.motor_rated_power_kw
                    ),
                    motor_efficiency_pct=(
                        self.config.motor_efficiency_pct
                    ),
                    total_mass_kg=self.config.vehicle_mass_kg,
                    vehicle_speed_kmh=vehicle_state.speed_kmh,
                    acceleration_mps2=(
                        vehicle_state.acceleration_mps2
                    ),
                    throttle_pct=self.throttle_pct,
                    road_gradient_pct=(
                        self.config.road_gradient_pct
                    ),
                    regen_efficiency_pct=(
                        self.config.regen_efficiency_pct
                    ),
                )

                predicted_wh_per_km = (
                    prediction.predicted_wh_per_km
                )
            except Exception:
                predicted_wh_per_km = None

        # Use trip measured Wh/km as a display fallback before the ML
        # model is available. This is not presented as an ML prediction.
        range_wh_per_km = predicted_wh_per_km

        if range_wh_per_km is None and energy_state.distance_km > 0:
            range_wh_per_km = max(
                1.0,
                energy_state.wh_per_km
            )

        remaining_range_km = None

        if range_wh_per_km is not None:
            range_result = self.range_model.calculate(
                battery_voltage_v=self.config.battery_voltage_v,
                battery_capacity_ah=(
                    self.config.battery_capacity_ah
                ),
                soc_pct=energy_state.soc_pct,
                soh_pct=self.config.battery_soh_pct,
                predicted_wh_per_km=range_wh_per_km,
            )
            remaining_range_km = (
                range_result.remaining_range_km
            )

        self.time_s += self.config.timestep_s

        self.last_state = self._build_state(
            requested_power_kw=optimization.requested_power_kw,
            optimized_power_kw=optimization.optimized_power_kw,
            power_limit_kw=optimization.power_limit_kw,
            optimization_status=optimization.status,
            regen_active=regen_result.regen_active,
            regen_power_kw=regen_result.regen_power_kw,
            energy_recovered_wh=energy_state.energy_recovered_wh,
            regen_status=regen_result.status,
            energy_consumed_wh=energy_state.energy_consumed_wh,
            net_energy_wh=energy_state.net_energy_wh,
            predicted_wh_per_km=predicted_wh_per_km,
            remaining_range_km=remaining_range_km,
            vehicle_state=vehicle_state,
            energy_state=energy_state,
        )

        return self.last_state

    def _update_battery_temperature(
        self,
        battery_power_kw,
        regen_power_kw,
    ):
        """
        Small thermal state approximation for the prototype.

        Temperature changes slowly; it is intentionally not treated as
        another user-controlled input during the simulation.
        """
        net_power = abs(
            float(battery_power_kw)
            - float(regen_power_kw)
        )

        # Heating is proportional to power; cooling returns temperature
        # slowly toward ambient.
        ambient = 25.0
        heating = net_power * 0.025
        cooling = (self.battery_temperature_c - ambient) * 0.02

        self.battery_temperature_c += (
            heating - cooling
        )

        self.battery_temperature_c = max(
            15.0,
            min(60.0, self.battery_temperature_c)
        )

    def _build_state(
        self,
        requested_power_kw,
        optimized_power_kw,
        power_limit_kw,
        optimization_status,
        regen_active,
        regen_power_kw,
        energy_recovered_wh,
        regen_status,
        energy_consumed_wh,
        net_energy_wh,
        predicted_wh_per_km,
        remaining_range_km,
        vehicle_state=None,
        energy_state=None,
    ):
        speed_kmh = (
            vehicle_state.speed_kmh
            if vehicle_state is not None
            else self.vehicle.speed_mps * 3.6
        )
        acceleration_mps2 = (
            vehicle_state.acceleration_mps2
            if vehicle_state is not None
            else 0.0
        )
        motor_rpm = (
            vehicle_state.motor_rpm
            if vehicle_state is not None
            else 0.0
        )
        battery_current_a = (
            energy_state.battery_current_a
            if energy_state is not None
            else 0.0
        )
        battery_power_kw = (
            energy_state.battery_power_kw
            if energy_state is not None
            else 0.0
        )

        return EVSimulationState(
            time_s=self.time_s,
            throttle_pct=self.throttle_pct,
            speed_kmh=speed_kmh,
            acceleration_mps2=acceleration_mps2,
            motor_rpm=motor_rpm,
            battery_voltage_v=self.config.battery_voltage_v,
            battery_current_a=battery_current_a,
            battery_power_kw=battery_power_kw,
            battery_temperature_c=self.battery_temperature_c,
            soc_pct=self.energy.soc_pct,
            soh_pct=self.config.battery_soh_pct,
            requested_power_kw=requested_power_kw,
            optimized_power_kw=optimized_power_kw,
            power_limit_kw=power_limit_kw,
            optimization_status=optimization_status,
            regen_active=regen_active,
            regen_power_kw=regen_power_kw,
            energy_recovered_wh=energy_recovered_wh,
            cumulative_energy_recovered_wh=(
                self.energy.cumulative_energy_recovered_wh
            ),
            energy_consumed_wh=energy_consumed_wh,
            cumulative_energy_consumed_wh=(
                self.energy.cumulative_energy_consumed_wh
            ),
            net_energy_wh=net_energy_wh,
            cumulative_net_energy_wh=(
                self.energy.cumulative_net_energy_wh
            ),
            distance_km=self.energy.distance_km,
            wh_per_km=(
                self.energy.cumulative_net_energy_wh
                / self.energy.distance_km
                if self.energy.distance_km > 0
                else 0.0
            ),
            predicted_wh_per_km=predicted_wh_per_km,
            remaining_range_km=remaining_range_km,
            ml_available=self.ml_available,
            regen_status=regen_status,
        )

    def state_dict(self):
        """Return the current state as a normal dictionary for Streamlit/API."""
        return asdict(self.last_state)


def run_demo():
    """
    Terminal demo.

    This demonstrates a drive -> high throttle -> coast/deceleration
    sequence. The ML model is optional; if it is not present, measured
    trip Wh/km is used only as a temporary range-estimation fallback.
    """

    config = EVSimulationConfig(
        battery_voltage_v=48,
        battery_capacity_ah=85,
        initial_soc_pct=70,
        battery_soh_pct=95,
        motor_rated_power_kw=5,
        motor_efficiency_pct=90,
        vehicle_mass_kg=500,
        road_gradient_pct=0,
        regen_efficiency_pct=70,
        max_regen_power_kw=2,
        timestep_s=1,
        max_power_ramp_kw_per_step=0.5,
    )

    simulation = EVSimulation(config)

    print("=== INTEGRATED EV SIMULATION ===")
    print(
        f"ML model available: "
        f"{simulation.ml_available}"
    )

    simulation.start()

    # Accelerate.
    for throttle in [20, 40, 60, 80, 80, 80, 60, 40]:
        state = simulation.step(throttle)
        print_state(state)

    # Release throttle. The vehicle coasts/decelerates and can trigger
    # regenerative braking once acceleration becomes negative.
    for _ in range(8):
        state = simulation.step(0)
        print_state(state)

    simulation.stop()

    print("\n=== FINAL ===")
    print(
        f"SOC: {simulation.last_state.soc_pct:.3f}%"
    )
    print(
        f"Distance: {simulation.last_state.distance_km:.3f} km"
    )
    print(
        f"Energy consumed: "
        f"{simulation.last_state.cumulative_energy_consumed_wh:.3f} Wh"
    )
    print(
        f"Energy recovered: "
        f"{simulation.last_state.cumulative_energy_recovered_wh:.3f} Wh"
    )
    print(
        f"Net energy: "
        f"{simulation.last_state.cumulative_net_energy_wh:.3f} Wh"
    )
    if simulation.last_state.predicted_wh_per_km is not None:
        print(
            f"Predicted Wh/km: "
            f"{simulation.last_state.predicted_wh_per_km:.2f}"
        )
    if simulation.last_state.remaining_range_km is not None:
        print(
            f"Remaining range: "
            f"{simulation.last_state.remaining_range_km:.2f} km"
        )


def print_state(state):
    print(
        f"t={state.time_s:4.0f}s | "
        f"thr={state.throttle_pct:3.0f}% | "
        f"speed={state.speed_kmh:6.2f} km/h | "
        f"acc={state.acceleration_mps2:6.2f} m/s² | "
        f"SOC={state.soc_pct:6.2f}% | "
        f"power={state.battery_power_kw:6.2f} kW | "
        f"regen={state.regen_power_kw:5.2f} kW"
    )


if __name__ == "__main__":
    run_demo()