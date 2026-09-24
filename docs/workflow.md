EV System Workflow

Project: Driving Pattern Monitoring and Range Optimization System for Electric Vehicles




Table of Contents

Overview

System Architecture

1. Vehicle Configuration

2. Start Simulation

3. Throttle Input

4. Optimization

5. Vehicle Dynamics

6. Regenerative Braking

7. Battery Energy Model

8. SOC Update

9. Distance and Wh/km

10. ML Energy Prediction

11. Remaining Range

12. Live Dashboard

13. Stop and Reset

Per-Step Simulation Loop

Module Responsibilities

Data Flow

Overview

The project simulates and monitors the energy behavior of an electric vehicle while applying power optimization and regenerative braking.

The driver primarily controls:

Throttle = 0–100%

The rest of the vehicle state is calculated by the simulation.

The workflow combines:

Vehicle dynamics

Motor-power optimization

Regenerative braking

Battery energy modeling

SOC tracking

Machine-learning-based Wh/km prediction

Remaining-range calculation

Live Streamlit visualization

System Architecture

flowchart TD
    A[Streamlit Frontend<br/>app.py] --> B[Simulation Controller<br/>main.py]

    B --> C[Power Optimizer<br/>optimizer.py]
    C --> D[Vehicle Dynamics<br/>vehicle_model.py]
    D --> E[Regen Controller<br/>regen_controller.py]
    E --> F[Energy Model<br/>energy_model.py]

    F --> G[ML Model<br/>ml_model.py]
    G --> H[Range Model<br/>range_model.py]

    H --> I[Live Dashboard<br/>Speed / SOC / Wh/km / Range]

    F --> I
    D --> I
    C --> I
    E --> I

1. Vehicle Configuration

Before starting the simulation, the user enters the vehicle and battery configuration.

Battery Parameters

Parameter

Unit

Battery nominal voltage

V

Battery capacity

Ah

Initial SOC

%

Battery SOH

%

Motor Parameters

Parameter

Unit

Motor rated power

kW

Motor efficiency

%

Vehicle Parameters

Parameter

Unit

Total vehicle mass

kg

Road gradient

%

Regenerative Braking

Parameter

Unit

Regen efficiency

%

Maximum regen power

kW

Advanced Settings

Range reserve SOC

Optimization ON/OFF

These parameters initialize EVSimulationConfig.

2. Start Simulation

When the user presses START:

flowchart LR
    A[Vehicle Configuration] --> B[Create Simulation]
    B --> C[Initialize State]
    C --> D[Start Live Simulation]

The initial SOC is retained and the trip state begins from the configured starting condition.

While the simulation is running, the vehicle configuration is locked.

3. Throttle Input

The main driver-controlled input during the simulation is:

Throttle = 0–100%

The throttle is continuously passed into the simulation step.

flowchart LR
    A[Driver] --> B[Throttle 0-100%]
    B --> C[EVSimulation.step()]

4. Optimization

The throttle is passed to the power optimizer.

Throttle
   ↓
Requested Motor Power
   ↓
Power Limits
   ↓
Optimized Motor Power

The optimizer considers:

Motor power limit

Battery SOC

Battery temperature

Power ramp limit

High-throttle eco limit

Output:

optimized_power_kw

This value is sent to the vehicle model.

5. Vehicle Dynamics

The vehicle model calculates the physical response of the vehicle.

Calculated Values

Vehicle speed

Acceleration

Motor RPM

Wheel RPM

Traction force

Rolling resistance

Aerodynamic drag

Road-grade force

Net force

Wheel power

Main Forces

The vehicle model considers:

flowchart TD
    A[Motor Power] --> B[Traction Force]

    B --> F[Net Force]
    C[Rolling Resistance] --> F
    D[Aerodynamic Drag] --> F
    E[Road Grade Force] --> F

    F --> G[Acceleration]
    G --> H[Vehicle Speed]

The vehicle state is updated at every simulation timestep.

6. Regenerative Braking

The regen controller checks whether regenerative braking should be active.

Regen can operate when the required conditions are satisfied:

Vehicle is moving above the minimum regen speed.

Vehicle acceleration is negative.

Battery SOC is below the regen SOC limit.

Battery temperature is within the charging limit.

The theoretical regenerative power is calculated using:

m |a| v \eta_{regen}
]

Where:

Symbol

Meaning

(m)

Vehicle mass

(a)

Vehicle acceleration

(v)

Vehicle velocity

(\eta_{regen})

Regen efficiency

The actual regen power is limited by the configured maximum regen power.

flowchart TD
    A[Vehicle State] --> B{Negative Acceleration?}
    B -->|No| C[Regen OFF]
    B -->|Yes| D{Speed Above Minimum?}
    D -->|No| C
    D -->|Yes| E{SOC Below Limit?}
    E -->|No| C
    E -->|Yes| F{Temperature Safe?}
    F -->|No| C
    F -->|Yes| G[Calculate Regen Power]
    G --> H[Apply Regen Power Limit]
    H --> I[Battery Charging]

During regen:

Battery power < 0

represents charging.

7. Battery Energy Model

The energy model combines:

Motor electrical demand

Auxiliary electrical load

Regenerative charging

The conceptual battery-power relationship is:

Battery Power
=
Motor Electrical Power
+
Auxiliary Power
-
Recovered Regen Power

Battery current is calculated using:

[
I = rac{P}{V}
]

Energy over a timestep is:

[
E = P \Delta t
]

The implementation uses Wh and seconds consistently when performing timestep calculations.

8. SOC Update

SOC changes according to net battery energy.

Energy Consumed
       -
Energy Recovered
       =
Net Energy Used

Conceptually:

flowchart LR
    A[Motor Demand] --> C[Net Battery Energy]
    B[Regen Recovery] --> C
    C --> D[SOC Update]

Important Behavior

The simulation does not reduce SOC simply because the timer is running.

Energy must be drawn from the battery.

A small auxiliary load may create a small stationary energy consumption.

9. Distance and Wh/km

Distance is accumulated from vehicle speed over the simulation timestep.

Energy efficiency is represented by:

[
Wh/km =
rac{Energy\ Consumed}{Distance}
]

The system tracks:

Distance

Energy consumed

Energy recovered

Net energy

Trip Wh/km

When distance is zero, the system avoids treating the undefined 0 km division as a valid Wh/km value.

10. ML Energy Prediction

The ML model predicts energy consumption in:

Wh/km

It uses the current battery, motor, vehicle, road, and driving conditions.

ML Features

#

Feature

1

Battery nominal voltage

2

Battery capacity

3

Battery energy

4

SOC

5

SOH

6

Battery temperature

7

Motor rated power

8

Motor efficiency

9

Total vehicle mass

10

Vehicle speed

11

Acceleration

12

Throttle

13

Road gradient

14

Regen efficiency

The ML stage is:

flowchart LR
    A[Battery Parameters] --> D[ML Model]
    B[Vehicle Parameters] --> D
    C[Driving Conditions] --> D
    D --> E[Predicted Wh/km]

Important Design Decision

The ML model predicts:

Energy Consumption → Wh/km

It does not directly predict:

Remaining Range

Remaining range is calculated separately.

11. Remaining Range

The range model uses battery energy availability and predicted Wh/km.

Step 1 — Nominal Battery Energy

V_{nominal} 	imes Ah
]

Step 2 — Usable Energy

E_{nominal}
imes
rac{SOH}{100}
]

Step 3 — Available Energy

E_{usable}
imes
rac{SOC}{100}
]

If a reserve SOC is configured, the reserve energy is held back.

Step 4 — Remaining Range

rac{E_{available}}
{Predicted\ Wh/km}
]

Therefore:

flowchart TD
    A[Battery Voltage] --> D[Nominal Energy]
    B[Battery Capacity] --> D

    D --> E[SOH Adjustment]
    C[SOH] --> E

    E --> F[SOC Adjustment]
    G[SOC] --> F

    F --> H[Available Energy]
    I[Predicted Wh/km] --> J[Range Calculation]

    H --> J
    J --> K[Remaining Range km]

This design means that battery capacity and battery SOH directly affect the calculated remaining range.

12. Live Dashboard

The Streamlit dashboard displays the current simulation state.

Driving

Throttle

Speed

Acceleration

Motor RPM

Distance

Battery

Battery voltage

Battery current

Battery power

SOC

SOH

Battery temperature

Optimization

Requested power

Optimized power

Power limit

Optimization status

Regeneration

Regen active/inactive

Regen power

Energy recovered

Energy

Energy consumed

Energy recovered

Net energy

Wh/km

Prediction and Range

Predicted Wh/km

Remaining range

ML status

13. Stop and Reset

STOP

When STOP is pressed:

flowchart LR
    A[Running Simulation] --> B[STOP]
    B --> C[Simulation Paused]
    C --> D[Current State Preserved]

The following are preserved:

SOC

Distance

Energy

Vehicle state

Trip statistics

RESET

When RESET is pressed:

flowchart LR
    A[Current Simulation] --> B[RESET]
    B --> C[Restore Initial Configuration]
    C --> D[Restore Initial SOC]
    D --> E[Clear Trip Energy]
    E --> F[Clear Distance]
    F --> G[Unlock Configuration]

Per-Step Simulation Loop

Every live simulation timestep follows this sequence:

flowchart TD
    A[Read Throttle] --> B[Optimizer]
    B --> C[Optimized Motor Power]
    C --> D[Vehicle Model]
    D --> E[Speed / Acceleration / RPM]
    E --> F[Regen Controller]
    F --> G[Regen Power]
    G --> H[Energy Model]
    C --> H
    H --> I[SOC / Current / Battery Power]
    I --> J[Distance / Energy / Wh/km]
    J --> K[ML Model]
    K --> L[Predicted Wh/km]
    L --> M[Range Model]
    M --> N[Remaining Range]
    N --> O[Dashboard Update]
    O --> A

Module Responsibilities

Module

Responsibility

app.py

Streamlit frontend and user interaction

main.py

Simulation orchestration and state management

optimizer.py

Motor-power optimization

vehicle_model.py

Vehicle dynamics

regen_controller.py

Regenerative braking

energy_model.py

Battery power, energy, SOC and distance

ml_model.py

Wh/km prediction

range_model.py

Remaining-range calculation

Data Flow

flowchart LR
    T[Throttle] --> O[Optimizer]
    O --> P[Optimized Power]
    P --> V[Vehicle Dynamics]
    V --> S[Speed / Acceleration]
    S --> R[Regen Controller]
    R --> E[Energy Model]
    P --> E
    E --> B[Battery State]
    B --> M[ML Prediction]
    M --> W[Predicted Wh/km]
    B --> G[Range Model]
    W --> G
    G --> RR[Remaining Range]

Complete Project Structure

ev_project/
│
├── app.py
├── main.py
│
├── optimizer.py
├── vehicle_model.py
├── regen_controller.py
├── energy_model.py
├── ml_model.py
├── range_model.py
│
├── ev_energy_consumption_model.joblib
│
├── optimization_logic.md
├── workflow.md
│
└── *_test.py

Summary

The complete system follows a modular pipeline:

USER
  │
  ▼
Throttle
  │
  ▼
Optimizer
  │
  ▼
Vehicle Dynamics
  │
  ▼
Regenerative Braking
  │
  ▼
Battery Energy Model
  │
  ├──────────────► SOC
  │
  ├──────────────► Energy
  │
  └──────────────► Distance / Wh/km
                         │
                         ▼
                    ML Prediction
                         │
                         ▼
                    Predicted Wh/km
                         │
                         ▼
                    Range Model
                         │
                         ▼
                  Remaining Range

The architecture keeps optimization, vehicle physics, battery modeling, ML prediction, and range calculation separate, making the project easier to test, demonstrate, and extend to future live sensor input.