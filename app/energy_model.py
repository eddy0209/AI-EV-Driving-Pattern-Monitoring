from dataclasses import dataclass


@dataclass
class EnergyState:
    battery_power_kw: float
    battery_current_a: float
    energy_consumed_wh: float
    energy_recovered_wh: float
    net_energy_wh: float
    cumulative_energy_consumed_wh: float
    cumulative_energy_recovered_wh: float
    cumulative_net_energy_wh: float
    soc_pct: float
    distance_km: float
    wh_per_km: float


class EnergyModel:
    def __init__(
        self,
        battery_voltage_v,
        battery_capacity_ah,
        initial_soc_pct=100.0,
        battery_soh_pct=100.0,
        motor_efficiency_pct=90.0,
        auxiliary_power_w=0.0,
        timestep_s=1.0,
    ):
        self.battery_voltage_v = max(0.1, float(battery_voltage_v))
        self.battery_capacity_ah = max(0.1, float(battery_capacity_ah))
        self.soh_pct = min(100.0, max(0.0, float(battery_soh_pct)))
        self.motor_efficiency = min(
            1.0, max(0.01, float(motor_efficiency_pct) / 100.0)
        )
        self.auxiliary_power_w = max(0.0, float(auxiliary_power_w))
        self.timestep_s = max(0.01, float(timestep_s))

        self.initial_soc_pct = min(100.0, max(0.0, float(initial_soc_pct)))
        self.soc_pct = self.initial_soc_pct

        self.cumulative_energy_consumed_wh = 0.0
        self.cumulative_energy_recovered_wh = 0.0
        self.cumulative_net_energy_wh = 0.0
        self.distance_km = 0.0

    @property
    def usable_battery_energy_wh(self):
        """
        Usable energy based on nominal battery energy and SOH.

        E_usable = V * Ah * SOH
        """
        return (
            self.battery_voltage_v
            * self.battery_capacity_ah
            * self.soh_pct
            / 100.0
        )

    @property
    def available_energy_wh(self):
        """
        Energy currently available at the present SOC.
        """
        return (
            self.usable_battery_energy_wh
            * self.soc_pct
            / 100.0
        )

    def reset(self, soc_pct=None):
        """Reset trip energy counters and optionally reset SOC."""
        if soc_pct is not None:
            self.initial_soc_pct = min(
                100.0, max(0.0, float(soc_pct))
            )

        self.soc_pct = self.initial_soc_pct
        self.cumulative_energy_consumed_wh = 0.0
        self.cumulative_energy_recovered_wh = 0.0
        self.cumulative_net_energy_wh = 0.0
        self.distance_km = 0.0

    def calculate(
        self,
        motor_power_kw=0.0,
        regen_power_kw=0.0,
        speed_kmh=0.0,
        battery_voltage_v=None,
    ):
        """
        Advance the battery simulation by one timestep.

        Parameters
        ----------
        motor_power_kw:
            Positive electrical demand from the battery-side motor system.

        regen_power_kw:
            Positive magnitude of power recovered by regenerative braking.

        speed_kmh:
            Vehicle speed used to calculate distance.

        battery_voltage_v:
            Optional live battery voltage. If supplied, it is used for
            current calculation for this timestep.

        Returns
        -------
        EnergyState
        """

        voltage = (
            self.battery_voltage_v
            if battery_voltage_v is None
            else max(0.1, float(battery_voltage_v))
        )

        motor_power_kw = max(0.0, float(motor_power_kw))
        regen_power_kw = max(0.0, float(regen_power_kw))
        speed_kmh = max(0.0, float(speed_kmh))

        # Motor demand is assumed to already represent electrical input.
        # Auxiliary loads are also drawn from the battery.
        discharge_power_kw = (
            motor_power_kw
            + self.auxiliary_power_w / 1000.0
        )

        # Regen is energy entering the battery.
        net_battery_power_kw = (
            discharge_power_kw
            - regen_power_kw
        )

        # Energy for this timestep.
        net_energy_wh = (
            net_battery_power_kw
            * self.timestep_s
            / 3600.0
            * 1000.0
        )

        # Separate positive consumption and recovered energy.
        energy_consumed_wh = (
            max(0.0, discharge_power_kw)
            * self.timestep_s
            / 3600.0
            * 1000.0
        )

        energy_recovered_wh = (
            min(
                regen_power_kw,
                max(0.0, discharge_power_kw + regen_power_kw)
            )
            * self.timestep_s
            / 3600.0
            * 1000.0
        )

        # Prevent recovery from exceeding the configured maximum battery
        # capacity at the top end of SOC.
        usable_energy = self.usable_battery_energy_wh

        if usable_energy > 0:
            energy_before = (
                usable_energy
                * self.soc_pct
                / 100.0
            )

            max_chargeable_wh = max(
                0.0,
                usable_energy - energy_before
            )

            energy_recovered_wh = min(
                energy_recovered_wh,
                max_chargeable_wh
            )

        # SOC update.
        if usable_energy > 0:
            soc_delta_pct = (
                (energy_recovered_wh - energy_consumed_wh)
                / usable_energy
                * 100.0
            )
        else:
            soc_delta_pct = 0.0

        self.soc_pct = min(
            100.0,
            max(0.0, self.soc_pct + soc_delta_pct)
        )

        # Recalculate actual net energy from the accepted amounts.
        actual_net_energy_wh = (
            energy_consumed_wh
            - energy_recovered_wh
        )

        self.cumulative_energy_consumed_wh += energy_consumed_wh
        self.cumulative_energy_recovered_wh += energy_recovered_wh
        self.cumulative_net_energy_wh += actual_net_energy_wh

        # Distance travelled during this timestep.
        distance_km = (
            speed_kmh
            * self.timestep_s
            / 3600.0
        )

        self.distance_km += distance_km

        # Trip Wh/km.
        if self.distance_km > 0:
            wh_per_km = (
                self.cumulative_net_energy_wh
                / self.distance_km
            )
        else:
            wh_per_km = 0.0

        # Battery current follows the net battery power sign convention:
        # positive = discharge, negative = charging.
        battery_power_kw = (
            actual_net_energy_wh
            * 3600.0
            / self.timestep_s
            / 1000.0
        )

        battery_current_a = (
            battery_power_kw * 1000.0 / voltage
        )

        return EnergyState(
            battery_power_kw=battery_power_kw,
            battery_current_a=battery_current_a,
            energy_consumed_wh=energy_consumed_wh,
            energy_recovered_wh=energy_recovered_wh,
            net_energy_wh=actual_net_energy_wh,
            cumulative_energy_consumed_wh=(
                self.cumulative_energy_consumed_wh
            ),
            cumulative_energy_recovered_wh=(
                self.cumulative_energy_recovered_wh
            ),
            cumulative_net_energy_wh=(
                self.cumulative_net_energy_wh
            ),
            soc_pct=self.soc_pct,
            distance_km=self.distance_km,
            wh_per_km=wh_per_km,
        )


if __name__ == "__main__":
    # Standalone test.
    energy = EnergyModel(
        battery_voltage_v=48,
        battery_capacity_ah=85,
        initial_soc_pct=70,
        battery_soh_pct=95,
        auxiliary_power_w=20,
        timestep_s=1,
    )

    print("=== ENERGY MODEL TEST ===")

    for second in range(5):
        state = energy.calculate(
            motor_power_kw=2.0,
            regen_power_kw=0.0,
            speed_kmh=30,
        )

        print(
            f"{second + 1}s | "
            f"battery={state.battery_power_kw:.2f} kW | "
            f"current={state.battery_current_a:.2f} A | "
            f"SOC={state.soc_pct:.4f}% | "
            f"distance={state.distance_km:.4f} km | "
            f"Wh/km={state.wh_per_km:.2f}"
        )

    print("\n=== REGEN TEST ===")

    state = energy.calculate(
        motor_power_kw=0.0,
        regen_power_kw=1.6,
        speed_kmh=40,
    )

    print(
        f"battery={state.battery_power_kw:.2f} kW | "
        f"current={state.battery_current_a:.2f} A | "
        f"recovered={state.energy_recovered_wh:.4f} Wh | "
        f"SOC={state.soc_pct:.4f}%"
    )