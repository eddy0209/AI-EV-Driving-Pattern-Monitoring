from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class OptimizerConfig:
    motor_rated_power_kw: float = 2.0
    motor_efficiency: float = 0.90

    # Maximum positive battery/motor power allowed by the optimizer.
    max_motor_power_kw: float = 2.0

    # Maximum change in commanded motor power per control step.
    # Example: 0.20 kW per 0.1 s control step.
    max_power_ramp_kw_per_step: float = 0.20

    # Eco strategy: at high throttle, cap positive power at this fraction
    # of the configured maximum. The optimizer can be disabled.
    eco_power_limit_fraction: float = 0.70

    # Battery protection limits.
    low_soc_percent: float = 20.0
    critical_soc_percent: float = 10.0
    high_battery_temp_c: float = 45.0
    critical_battery_temp_c: float = 50.0

    # Regen controller uses this later; included here so the optimizer
    # exposes a single vehicle configuration.
    max_regen_power_kw: float = 1.0


@dataclass
class OptimizationResult:
    throttle_pct: float
    requested_power_kw: float
    optimized_power_kw: float
    power_limit_kw: float
    ramp_limited: bool
    soc_limited: bool
    thermal_limited: bool
    optimization_active: bool
    status: str


class EVPowerOptimizer:
    def __init__(self, config: OptimizerConfig | None = None):
        self.config = config or OptimizerConfig()
        self.previous_power_kw = 0.0

    def reset(self) -> None:
        """Reset the internal ramp state, normally when START is pressed."""
        self.previous_power_kw = 0.0

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    def _power_limit(
        self,
        throttle_pct: float,
        soc_percent: float,
        battery_temp_c: float,
        optimization_enabled: bool,
    ) -> tuple[float, bool, bool, bool, str]:
        """
        Determine the maximum positive motor power permitted at this instant.
        """
        cfg = self.config
        limit = min(cfg.motor_rated_power_kw, cfg.max_motor_power_kw)

        soc_limited = False
        thermal_limited = False
        status = "NORMAL"

        if not optimization_enabled:
            return limit, False, False, False, "OPTIMIZATION_OFF"

        # Low SOC: progressively reduce available power.
        if soc_percent <= cfg.critical_soc_percent:
            limit *= 0.35
            soc_limited = True
            status = "CRITICAL_SOC_LIMIT"
        elif soc_percent <= cfg.low_soc_percent:
            limit *= 0.60
            soc_limited = True
            status = "LOW_SOC_LIMIT"

        # High battery temperature: reduce power.
        if battery_temp_c >= cfg.critical_battery_temp_c:
            limit *= 0.40
            thermal_limited = True
            status = "CRITICAL_TEMP_LIMIT"
        elif battery_temp_c >= cfg.high_battery_temp_c:
            limit *= 0.70
            thermal_limited = True
            status = "HIGH_TEMP_LIMIT"

        # Optional eco cap at high throttle. This is deliberately simple
        # and can later be replaced by an ML/model-predictive strategy.
        if throttle_pct >= 80.0:
            limit = min(limit, cfg.motor_rated_power_kw *
                        cfg.eco_power_limit_fraction)
            status = "ECO_POWER_LIMIT" if status == "NORMAL" else status

        return max(0.0, limit), soc_limited, thermal_limited, True, status

    def step(
        self,
        throttle_pct: float,
        speed_kmh: float,
        acceleration_mps2: float,
        soc_percent: float,
        battery_temp_c: float,
        optimization_enabled: bool = True,
    ) -> OptimizationResult:
        """
        Run one optimizer control step.

        throttle_pct:
            Driver accelerator request, 0..100%.

        speed_kmh / acceleration_mps2:
            Current vehicle state. These are exposed for future extensions
            such as slope-aware torque control; the first version uses them
            for state interpretation but does not invent a braking command.

        soc_percent / battery_temp_c:
            Battery state used for conservative power limiting.

        Returns:
            OptimizationResult containing requested and optimized power.
        """
        cfg = self.config

        throttle_pct = self._clamp(float(throttle_pct), 0.0, 100.0)
        soc_percent = self._clamp(float(soc_percent), 0.0, 100.0)

        # Driver-requested positive motor power.
        requested_power_kw = (
            throttle_pct / 100.0 * cfg.motor_rated_power_kw
        )

        if not optimization_enabled:
            # No optimization: deliver requested power, bounded only by the
            # physical configured motor rating.
            optimized_power_kw = min(
                requested_power_kw,
                cfg.motor_rated_power_kw,
                cfg.max_motor_power_kw,
            )
            ramp_limited = False
            power_limit_kw = min(
                cfg.motor_rated_power_kw,
                cfg.max_motor_power_kw,
            )
            status = "OPTIMIZATION_OFF"
            soc_limited = False
            thermal_limited = False
            optimization_active = False

        else:
            (
                power_limit_kw,
                soc_limited,
                thermal_limited,
                optimization_active,
                status,
            ) = self._power_limit(
                throttle_pct,
                soc_percent,
                battery_temp_c,
                optimization_enabled=True,
            )

            # --------------------------------------------------------
            # ZERO THROTTLE
            # --------------------------------------------------------
            # When the driver releases the accelerator, remove
            # positive motor/traction power immediately.
            #
            # This allows the vehicle model to decelerate naturally,
            # which can then trigger regenerative braking.
            if throttle_pct <= 0.0:

                optimized_power_kw = 0.0
                ramp_limited = False

            else:

                # ----------------------------------------------------
                # NORMAL POSITIVE POWER CONTROL
                # ----------------------------------------------------

                target_power_kw = min(
                    requested_power_kw,
                    power_limit_kw
                )

                # Ramp limiter prevents sudden increases/decreases
                # during normal positive throttle operation.
                max_step = max(
                    0.0,
                    cfg.max_power_ramp_kw_per_step
                )

                upper = self.previous_power_kw + max_step
                lower = max(
                    0.0,
                    self.previous_power_kw - max_step
                )

                optimized_power_kw = self._clamp(
                    target_power_kw,
                    lower,
                    upper
                )

                optimized_power_kw = min(
                    optimized_power_kw,
                    power_limit_kw
                )

                ramp_limited = (
                        abs(optimized_power_kw - target_power_kw)
                        > 1e-9
                )

                if ramp_limited and status == "NORMAL":
                    status = "POWER_RAMP_LIMIT"

        self.previous_power_kw = optimized_power_kw

        return OptimizationResult(
            throttle_pct=throttle_pct,
            requested_power_kw=round(requested_power_kw, 4),
            optimized_power_kw=round(optimized_power_kw, 4),
            power_limit_kw=round(power_limit_kw, 4),
            ramp_limited=ramp_limited,
            soc_limited=soc_limited,
            thermal_limited=thermal_limited,
            optimization_active=optimization_active,
            status=status,
        )

    def optimize(self, **kwargs) -> Dict:
        """Dictionary-returning convenience wrapper for APIs/frontend code."""
        return asdict(self.step(**kwargs))


if __name__ == "__main__":
    # Quick demonstration of the optimizer behavior.
    optimizer = EVPowerOptimizer(
        OptimizerConfig(
            motor_rated_power_kw=2.0,
            max_motor_power_kw=2.0,
            max_power_ramp_kw_per_step=0.20,
            eco_power_limit_fraction=0.70,
        )
    )

    print("Throttle ramp: 0% -> 100%")
    for throttle in [0, 20, 40, 60, 80, 100, 100, 100]:
        result = optimizer.step(
            throttle_pct=throttle,
            speed_kmh=20.0,
            acceleration_mps2=1.0,
            soc_percent=75.0,
            battery_temp_c=30.0,
            optimization_enabled=True,
        )
        print(result)

    print("\nLow-SOC test")
    optimizer.reset()
    result = optimizer.step(
        throttle_pct=100,
        speed_kmh=20.0,
        acceleration_mps2=1.0,
        soc_percent=15.0,
        battery_temp_c=30.0,
        optimization_enabled=True,
    )
    print(result)

    print("\nHigh-temperature test")
    optimizer.reset()
    result = optimizer.step(
        throttle_pct=100,
        speed_kmh=20.0,
        acceleration_mps2=1.0,
        soc_percent=75.0,
        battery_temp_c=48.0,
        optimization_enabled=True,
    )
    print(result)
