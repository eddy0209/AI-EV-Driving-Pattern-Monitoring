# EV System Workflow

## Project Workflow

The proposed system follows the workflow below:

Throttle Input
↓
Sensor Data Acquisition
↓
AI Driving Pattern Detection
↓
Energy Consumption Analysis
↓
PWM Optimization Logic
↓
Motor Power Control
↓
Battery Efficiency Improvement
↓
Optimized EV Range

---

## Step-by-Step Explanation

### 1. Throttle Input

The throttle potentiometer acts as the accelerator pedal of the electric vehicle. The driver input determines motor speed and power demand.

### 2. Sensor Data Acquisition

Sensors collect:

* Current Consumption
* Voltage
* Motor Speed
* Throttle Variation

The ESP32 acquires all sensor data.

### 3. AI Driving Pattern Detection

The AI system classifies driving behaviour into:

* Eco Driving
* Normal Driving
* Aggressive Driving

based on throttle and energy usage patterns.

### 4. Energy Consumption Analysis

The system calculates:

* Current Consumption
* Power Consumption
* Battery Usage

to evaluate EV efficiency.

### 5. PWM Optimization Logic

If aggressive driving is detected:

* PWM duty cycle is reduced
* Unnecessary motor power is minimized
* Current spikes are controlled

### 6. Motor Power Control

Optimized PWM signals control the motor driver and regulate motor speed efficiently.

### 7. Battery Efficiency Improvement

Controlled power usage improves:

* Battery efficiency
* Energy utilization
* EV driving range

### 8. Optimized EV Range

The final optimized system improves the effective driving range of the electric vehicle.
