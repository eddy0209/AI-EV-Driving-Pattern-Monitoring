# Optimization Logic

## Objective of Optimization

The main objective is to optimize:

* Energy Consumption
* Motor Power Usage
* Current Consumption
* Battery Efficiency

to improve EV performance and driving range.

---

## Why Optimization Is Needed

Aggressive driving causes:

* High current draw
* Rapid battery discharge
* Increased power consumption
* Reduced EV range

Therefore optimization is required to minimize unnecessary energy wastage.

---

## Optimization Strategy

The system continuously monitors:

* Throttle Input
* Speed
* Current Consumption
* Power Usage

The AI model then detects driving behaviour.

---

## Driving Pattern Classification

### Eco Driving

* Low throttle
* Smooth acceleration
* Efficient power usage

Optimization:

* Full PWM allowed
* Maximum efficiency

---

### Normal Driving

* Moderate acceleration
* Average current consumption

Optimization:

* Moderate PWM optimization
* Controlled power usage

---

### Aggressive Driving

* High throttle
* Sudden acceleration
* High current spikes

Optimization:

* PWM reduced dynamically
* Power consumption minimized
* Battery efficiency improved

---

## PWM Optimization

PWM (Pulse Width Modulation) is used to control motor power.

Example:

Normal PWM:
90%

Optimized PWM:
70%

This reduces:

* Motor power usage
* Current consumption
* Battery drain

---

## Final Optimization Result

The optimization system improves:

* Battery efficiency
* Energy management
* Driving range
* EV performance
