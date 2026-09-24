EV Optimization Logic

1. Purpose

The optimization module controls how much motor power the EV requests and applies operating limits before the power is passed to the vehicle dynamics model.

The optimizer does not directly calculate remaining range or battery SOC. Its role is to make the requested motor power safer and more energy-aware based on throttle, SOC, battery temperature, motor limits, and ramp limits.

2. Input

The optimizer receives:

throttle_pct — driver throttle command, 0–100%

speed_kmh — current vehicle speed

acceleration_mps2 — current acceleration

soc_percent — current battery SOC

battery_temp_c — current battery temperature

optimization_enabled — whether optimization is enabled

The current speed and acceleration are available for future optimization rules and monitoring, while the main power decision is based on throttle and system limits.

3. Requested Motor Power

The throttle command is converted into requested motor power.

Throttle %
     ↓
Requested motor power

The requested power is limited by the motor's configured maximum/rated power.

Conceptually:

requested_power = throttle_fraction × motor_power_limit

where:

throttle_fraction = throttle_pct / 100

4. Power Limiting Logic

The optimizer applies several limits.

4.1 Motor Power Limit

The requested power cannot exceed the configured maximum motor power.

requested power ≤ maximum motor power

4.2 Power Ramp Limit

The power cannot change too quickly between simulation steps.

This prevents unrealistic instantaneous jumps in motor power.

previous optimized power
            ↓
      ramp limitation
            ↓
new optimized power

The default ramp limit is:

0.20 kW per simulation step

4.3 Low SOC Limiting

The optimizer reduces available motor power when the battery SOC becomes low.

SOC ≤ 20%

Maximum available power is limited to approximately:

60% of maximum motor power

SOC ≤ 10%

Maximum available power is limited further to approximately:

35% of maximum motor power

This protects the battery and allows the vehicle to continue operating at low SOC.

4.4 Battery Temperature Limiting

Motor power is also reduced when battery temperature becomes high.

Battery temperature ≥ 45°C

Maximum power is limited to approximately:

70% of maximum motor power

Battery temperature ≥ 50°C

Maximum power is limited to approximately:

40% of maximum motor power

This prevents continued high-power operation under thermal stress.

4.5 High-Throttle Eco Limiting

When throttle is very high:

Throttle ≥ 80%

the optimizer can apply an eco power cap of approximately:

70% of maximum motor power

This prevents unnecessary continuous high-power demand when optimization is enabled.

5. Optimization ON/OFF

The system supports an optimization switch.

Optimization ON

The optimizer applies:

motor power limits

SOC limits

thermal limits

power ramp limiting

high-throttle eco limiting

Optimization OFF

The requested throttle power is allowed to pass through subject to the fundamental motor power limit.

This allows the dashboard to demonstrate the difference between normal operation and optimized operation.

6. Priority of Limits

The effective power limit is the most restrictive applicable limit.

Conceptually:

Motor limit
     ↓
SOC limit
     ↓
Temperature limit
     ↓
Eco limit
     ↓
Ramp limit
     ↓
Final optimized motor power

The final optimized power must never exceed the active system limit.

7. Optimization Result

The optimizer returns:

throttle_pct

requested_power_kw

optimized_power_kw

power_limit_kw

ramp_limited

soc_limited

thermal_limited

optimization_active

status

These values are passed to the rest of the simulation and displayed on the dashboard.

8. Interaction With Other Modules

The optimizer is one stage in the complete simulation pipeline.

Throttle
   ↓
Optimizer
   ↓
Optimized Motor Power
   ↓
Vehicle Model
   ↓
Speed + Acceleration + RPM
   ↓
Regen Controller
   ↓
Energy Model
   ↓
SOC + Battery Power + Energy
   ↓
ML Model
   ↓
Predicted Wh/km
   ↓
Range Model
   ↓
Remaining Range

The optimizer therefore affects energy consumption indirectly by controlling motor power.

9. Important Design Boundary

The optimizer does not perform:

battery SOC calculation

battery current calculation

energy consumption calculation

regenerative braking calculation

ML prediction

remaining-range calculation

Those responsibilities belong to their respective modules.

This separation keeps the project modular and makes the system easier to test and explain.