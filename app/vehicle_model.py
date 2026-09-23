from dataclasses import dataclass
import math


@dataclass
class VehicleState:
    speed_kmh: float
    speed_mps: float
    acceleration_mps2: float
    motor_rpm: float
    wheel_rpm: float
    traction_force_n: float
    rolling_force_n: float
    aerodynamic_force_n: float
    grade_force_n: float
    net_force_n: float
    wheel_power_kw: float


class VehicleModel:
    def __init__(
        self,
        mass_kg,
        motor_rated_power_kw,
        motor_efficiency_pct=90.0,
        wheel_radius_m=0.25,
        gear_ratio=8.0,
        rolling_resistance_coeff=0.012,
        drag_coefficient=0.30,
        frontal_area_m2=2.0,
        air_density_kg_m3=1.225,
        road_gradient_pct=0.0,
        timestep_s=1.0,
        max_speed_kmh=120.0,
    ):
        self.mass_kg = max(1.0, float(mass_kg))
        self.motor_rated_power_kw = max(0.01, float(motor_rated_power_kw))
        self.motor_efficiency = min(
            1.0, max(0.01, float(motor_efficiency_pct) / 100.0)
        )
        self.wheel_radius_m = max(0.05, float(wheel_radius_m))
        self.gear_ratio = max(0.1, float(gear_ratio))
        self.crr = max(0.0, float(rolling_resistance_coeff))
        self.cd = max(0.0, float(drag_coefficient))
        self.frontal_area_m2 = max(0.01, float(frontal_area_m2))
        self.air_density = max(0.1, float(air_density_kg_m3))
        self.road_gradient_pct = float(road_gradient_pct)
        self.timestep_s = max(0.01, float(timestep_s))
        self.max_speed_kmh = max(1.0, float(max_speed_kmh))

        self.speed_mps = 0.0

    def reset(self, speed_kmh=0.0):
        """Reset vehicle speed for a new simulation."""
        self.speed_mps = max(0.0, float(speed_kmh) / 3.6)

    def set_speed(self, speed_kmh):
        """Set the current simulated speed."""
        self.speed_mps = max(0.0, float(speed_kmh) / 3.6)

    def calculate(
        self,
        optimized_power_kw,
        road_gradient_pct=None,
        throttle_pct=0.0,
    ):
        """
        Advance the vehicle model by one timestep.

        Positive optimized_power_kw means motor drive power.
        If zero power is requested, the vehicle naturally decelerates
        from rolling resistance, aerodynamic drag and road gradient.

        Returns a VehicleState.
        """

        power_kw = max(0.0, float(optimized_power_kw))

        if road_gradient_pct is None:
            gradient_pct = self.road_gradient_pct
        else:
            gradient_pct = float(road_gradient_pct)

        # Convert percentage grade to angle.
        grade_angle = math.atan(gradient_pct / 100.0)

        v = max(0.0, self.speed_mps)

        # Forces opposing/assisting motion.
        rolling_force = (
            self.crr
            * self.mass_kg
            * 9.81
            * math.cos(grade_angle)
        )

        aerodynamic_force = (
            0.5
            * self.air_density
            * self.cd
            * self.frontal_area_m2
            * v
            * v
        )

        grade_force = (
            self.mass_kg
            * 9.81
            * math.sin(grade_angle)
        )

        # Convert motor electrical/mechanical power into wheel power.
        # Optimized power is treated as motor electrical input.
        wheel_power_w = power_kw * 1000.0 * self.motor_efficiency

        # Avoid division by zero at standstill.
        if v > 0.5:
            traction_force = wheel_power_w / v
        else:
            # At standstill, cap the force using the rated motor power.
            reference_speed = 5.0 / 3.6
            traction_force = wheel_power_w / reference_speed

        # Prevent unrealistic traction force at very low speed.
        max_force = (
            self.motor_rated_power_kw
            * 1000.0
            * self.motor_efficiency
            / (5.0 / 3.6)
        )
        traction_force = min(traction_force, max_force)

        # Net longitudinal force.
        net_force = (
            traction_force
            - rolling_force
            - aerodynamic_force
            - grade_force
        )

        acceleration = net_force / self.mass_kg

        # Integrate speed.
        new_speed = max(
            0.0,
            min(
                self.max_speed_kmh / 3.6,
                v + acceleration * self.timestep_s,
            ),
        )

        # If stopped and there is no positive drive force, don't report
        # a negative speed; acceleration is allowed to represent braking.
        actual_acceleration = (
            new_speed - v
        ) / self.timestep_s

        self.speed_mps = new_speed

        # Wheel and motor RPM.
        wheel_angular_speed_rad_s = (
            new_speed / self.wheel_radius_m
        )

        wheel_rpm = (
            wheel_angular_speed_rad_s
            * 60.0
            / (2.0 * math.pi)
        )

        motor_rpm = wheel_rpm * self.gear_ratio

        actual_wheel_power_kw = (
            traction_force * new_speed / 1000.0
        )

        return VehicleState(
            speed_kmh=new_speed * 3.6,
            speed_mps=new_speed,
            acceleration_mps2=actual_acceleration,
            motor_rpm=motor_rpm,
            wheel_rpm=wheel_rpm,
            traction_force_n=traction_force,
            rolling_force_n=rolling_force,
            aerodynamic_force_n=aerodynamic_force,
            grade_force_n=grade_force,
            net_force_n=net_force,
            wheel_power_kw=max(0.0, actual_wheel_power_kw),
        )


if __name__ == "__main__":
    # Standalone demonstration.
    vehicle = VehicleModel(
        mass_kg=500,
        motor_rated_power_kw=5,
        motor_efficiency_pct=90,
        road_gradient_pct=0,
        timestep_s=1,
    )

    print("=== Vehicle Model Test ===")

    for step in range(10):
        state = vehicle.calculate(
            optimized_power_kw=2.5,
            road_gradient_pct=0,
            throttle_pct=50,
        )

        print(
            f"t={step + 1:2d}s | "
            f"speed={state.speed_kmh:6.2f} km/h | "
            f"accel={state.acceleration_mps2:6.2f} m/s² | "
            f"RPM={state.motor_rpm:7.0f} | "
            f"wheel power={state.wheel_power_kw:5.2f} kW"
        )
