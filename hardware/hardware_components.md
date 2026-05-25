# Hardware Components

## 1. ESP32
Used for:
- Sensor data acquisition
- PWM generation
- Embedded control

## 2. Raspberry Pi
Used for:
- AI processing
- Optimization logic
- Machine learning execution

## 3. Potentiometer
Acts as throttle input for the EV system.

## 4. L293D Motor Driver
Controls motor speed using PWM signals.

## 5. DC Motor / BLDC Motor
Simulates EV motor operation.

## 6. ACS712 Current Sensor
Measures motor current consumption.

## 7. Voltage Sensor
Monitors EV battery voltage.

## 8. Rotary Encoder
Measures motor speed and rotation.

## 9. LCD 16x2 Display
Displays:
- Driving mode
- Optimization status
- Power saving information

# Hardware Workflow

Potentiometer
↓
ESP32 / Arduino
↓
PWM Optimization
↓
Motor Driver
↓
DC Motor
↓
LCD Display
