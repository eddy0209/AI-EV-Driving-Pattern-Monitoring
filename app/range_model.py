from dataclasses import dataclass


@dataclass
class RangeResult:
    nominal_battery_energy_wh: float
    usable_battery_energy_wh: float
    available_energy_wh: float
    predicted_wh_per_km: float
    remaining_range_km: float
    reserve_energy_wh: float
    range_limited_by_reserve: bool


class RangeModel:
    def __init__(self, reserve_soc_pct=0.0):
        """
        reserve_soc_pct:
            Minimum SOC the range estimate assumes will be retained.

        Example:
            reserve_soc_pct=10 means the displayed range represents
            distance available from the current SOC down to 10% SOC.
        """
        self.reserve_soc_pct = min(
            99.0,
            max(0.0, float(reserve_soc_pct))
        )

    def calculate(
        self,
        battery_voltage_v,
        battery_capacity_ah,
        soc_pct,
        soh_pct,
        predicted_wh_per_km,
    ):
        """
        Calculate remaining driving range.

        Parameters
        ----------
        battery_voltage_v:
            Battery nominal voltage in volts.

        battery_capacity_ah:
            Battery rated capacity in amp-hours.

        soc_pct:
            Current battery SOC.

        soh_pct:
            Current battery SOH.

        predicted_wh_per_km:
            Energy consumption predicted by the ML model.

        Returns
        -------
        RangeResult
        """

        voltage = max(0.0, float(battery_voltage_v))
        capacity_ah = max(0.0, float(battery_capacity_ah))

        soc = min(100.0, max(0.0, float(soc_pct)))
        soh = min(100.0, max(0.0, float(soh_pct)))

        consumption = max(0.1, float(predicted_wh_per_km))

        # Nominal battery energy.
        nominal_energy_wh = voltage * capacity_ah

        # Account for battery degradation.
        usable_energy_wh = (
            nominal_energy_wh
            * soh
            / 100.0
        )

        # Energy currently stored.
        available_energy_wh = (
            usable_energy_wh
            * soc
            / 100.0
        )

        # Energy corresponding to the reserved SOC.
        reserve_energy_wh = (
            usable_energy_wh
            * self.reserve_soc_pct
            / 100.0
        )

        # Only energy above the reserve is considered available
        # for the displayed range.
        range_energy_wh = max(
            0.0,
            available_energy_wh - reserve_energy_wh
        )

        remaining_range_km = (
            range_energy_wh / consumption
        )

        return RangeResult(
            nominal_battery_energy_wh=nominal_energy_wh,
            usable_battery_energy_wh=usable_energy_wh,
            available_energy_wh=range_energy_wh,
            predicted_wh_per_km=consumption,
            remaining_range_km=remaining_range_km,
            reserve_energy_wh=reserve_energy_wh,
            range_limited_by_reserve=(
                self.reserve_soc_pct > 0
            ),
        )


def calculate_remaining_range(
    battery_voltage_v,
    battery_capacity_ah,
    soc_pct,
    soh_pct,
    predicted_wh_per_km,
    reserve_soc_pct=0.0,
):
    """
    Convenience function for one-off range calculations.
    """
    model = RangeModel(
        reserve_soc_pct=reserve_soc_pct
    )

    return model.calculate(
        battery_voltage_v=battery_voltage_v,
        battery_capacity_ah=battery_capacity_ah,
        soc_pct=soc_pct,
        soh_pct=soh_pct,
        predicted_wh_per_km=predicted_wh_per_km,
    )


if __name__ == "__main__":
    # Standalone demonstration.
    range_model = RangeModel(reserve_soc_pct=5)

    result = range_model.calculate(
        battery_voltage_v=48,
        battery_capacity_ah=85,
        soc_pct=70,
        soh_pct=95,
        predicted_wh_per_km=120,
    )

    print("=== RANGE MODEL TEST ===")
    print(
        f"Nominal battery energy: "
        f"{result.nominal_battery_energy_wh:.1f} Wh"
    )
    print(
        f"Usable battery energy: "
        f"{result.usable_battery_energy_wh:.1f} Wh"
    )
    print(
        f"Available energy for range: "
        f"{result.available_energy_wh:.1f} Wh"
    )
    print(
        f"Predicted consumption: "
        f"{result.predicted_wh_per_km:.1f} Wh/km"
    )
    print(
        f"Remaining range: "
        f"{result.remaining_range_km:.1f} km"
    )
