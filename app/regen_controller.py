from dataclasses import dataclass


@dataclass
class RegenResult:
    regen_power_kw: float
    regen_energy_wh: float
    battery_charge_power_kw: float
    regen_active: bool
    status: str


class RegenController:
    """
    Explainable regenerative-braking controller.

    Sign convention:
        Positive battery power/current -> battery discharging
        Negative battery power/current -> battery charging

    Therefore regen_power_kw is returned as a positive magnitude,
    while battery_charge_power_kw is returned as a negative battery
    power value for integration with the battery model.
    """

    def __init__(
        self,
        regen_efficiency_pct=80.0,
        max_regen_power_kw=2.0,
        min_regen_speed_kmh=5.0,
        max_soc_pct=95.0,
        max_battery_temp_c=45.0,
        timestep_s=1.0,
    ):
        self.regen_efficiency_pct = float(regen_efficiency_pct)
        self.max_regen_power_kw = float(max_regen_power_kw)
        self.min_regen_speed_kmh = float(min_regen_speed_kmh)
        self.max_soc_pct = float(max_soc_pct)
        self.max_battery_temp_c = float(max_battery_temp_c)
        self.timestep_s = float(timestep_s)

    def calculate(
        self,
        speed_kmh,
        acceleration_mps2,
        vehicle_mass_kg,
        soc_pct,
        battery_temp_c=25.0,
        motor_max_regen_power_kw=None,
    ):
        """
        Calculate regenerative braking for one simulation timestep.

        Regen is enabled only when:
        - vehicle is moving above the minimum speed,
        - vehicle is decelerating (negative acceleration),
        - SOC is below the maximum regen SOC limit,
        - battery temperature is below the charging temperature limit.

        Theoretical regenerative power is based on kinetic-energy recovery:

            P = m * |a| * v * efficiency

        where:
            m = vehicle mass (kg)
            a = deceleration (m/s^2)
            v = speed (m/s)

        Returns a RegenResult.
        """

        speed_kmh = max(0.0, float(speed_kmh))
        acceleration_mps2 = float(acceleration_mps2)
        vehicle_mass_kg = max(0.0, float(vehicle_mass_kg))
        soc_pct = min(100.0, max(0.0, float(soc_pct)))
        battery_temp_c = float(battery_temp_c)

        # Basic validity checks.
        if vehicle_mass_kg <= 0:
            return self._zero_result("Invalid vehicle mass")

        if speed_kmh <= self.min_regen_speed_kmh:
            return self._zero_result("Speed too low for regen")

        if acceleration_mps2 >= 0:
            return self._zero_result("No deceleration")

        if soc_pct >= self.max_soc_pct:
            return self._zero_result("SOC too high for regen")

        if battery_temp_c >= self.max_battery_temp_c:
            return self._zero_result("Battery temperature too high")

        # Convert km/h to m/s.
        speed_mps = speed_kmh / 3.6

        # Regenerative efficiency as a fraction.
        efficiency = min(
            1.0,
            max(0.0, self.regen_efficiency_pct / 100.0)
        )

        # Mechanical power available from deceleration.
        mechanical_power_w = (
            vehicle_mass_kg
            * abs(acceleration_mps2)
            * speed_mps
        )

        # Electrical power recovered after regen losses.
        theoretical_regen_kw = (
            mechanical_power_w * efficiency / 1000.0
        )

        # Apply maximum regen power limit.
        regen_limit_kw = self.max_regen_power_kw

        if motor_max_regen_power_kw is not None:
            regen_limit_kw = min(
                regen_limit_kw,
                max(0.0, float(motor_max_regen_power_kw))
            )

        regen_power_kw = min(
            theoretical_regen_kw,
            regen_limit_kw
        )

        if regen_power_kw <= 0:
            return self._zero_result("No recoverable braking energy")

        # Energy recovered during this timestep.
        regen_energy_wh = (
            regen_power_kw * self.timestep_s / 3600.0 * 1000.0
        )

        # Negative sign means energy is flowing INTO the battery.
        battery_charge_power_kw = -regen_power_kw

        return RegenResult(
            regen_power_kw=regen_power_kw,
            regen_energy_wh=regen_energy_wh,
            battery_charge_power_kw=battery_charge_power_kw,
            regen_active=True,
            status="Regenerative braking active",
        )

    @staticmethod
    def _zero_result(status):
        return RegenResult(
            regen_power_kw=0.0,
            regen_energy_wh=0.0,
            battery_charge_power_kw=0.0,
            regen_active=False,
            status=status,
        )

    def reset(self):
        """Reset hook for future stateful regen-control logic."""
        pass


if __name__ == "__main__":
    # Simple standalone test.
    controller = RegenController(
        regen_efficiency_pct=80,
        max_regen_power_kw=2.0,
        timestep_s=1.0,
    )

    result = controller.calculate(
        speed_kmh=40,
        acceleration_mps2=-1.5,
        vehicle_mass_kg=120,
        soc_pct=60,
        battery_temp_c=30,
    )

    print("=== Regen Controller Test ===")
    print(f"Regen active:          {result.regen_active}")
    print(f"Regen power:           {result.regen_power_kw:.3f} kW")
    print(f"Energy recovered:      {result.regen_energy_wh:.4f} Wh")
    print(f"Battery charge power:  {result.battery_charge_power_kw:.3f} kW")
    print(f"Status:                {result.status}")