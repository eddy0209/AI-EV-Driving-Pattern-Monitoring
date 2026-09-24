#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

#include <OneWire.h>
#include <DallasTemperature.h>

// ============================================================
// WIFI
// ============================================================

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// FastAPI running on your Windows PC
const char* SERVER_URL =
    "http://host.wokwi.internal:8000/sensor";

// ============================================================
// PIN DEFINITIONS
// ============================================================

#define THROTTLE_PIN 34

#define SDA_PIN 21
#define SCL_PIN 22

#define ONE_WIRE_PIN 4

#define START_BUTTON 18
#define STOP_BUTTON 19
#define RESET_BUTTON 23

#define GREEN_LED 25
#define BLUE_LED 26
#define RED_LED 27

// ============================================================
// OLED
// ============================================================

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    &Wire,
    -1
);

// ============================================================
// SENSORS
// ============================================================

Adafruit_MPU6050 mpu;

OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature temperatureSensor(&oneWire);

// ============================================================
// SIMULATION STATE
// ============================================================

bool simulationRunning = false;

bool wifiConnected = false;

float throttlePct = 0.0;

float accelerationMps2 = 0.0;
float batteryTempC = 25.0;

float speedKmh = 0.0;
float batteryVoltageV = 48.0;
float batteryCurrentA = 0.0;
float batteryPowerKw = 0.0;

float socPct = 70.0;
float sohPct = 95.0;

float optimizedPowerKw = 0.0;
float requestedPowerKw = 0.0;
float powerLimitKw = 0.0;

float distanceKm = 0.0;

float energyConsumedWh = 0.0;
float energyRecoveredWh = 0.0;

float whPerKm = 0.0;
float predictedWhPerKm = 0.0;

float remainingRangeKm = 0.0;

float regenPowerKw = 0.0;

bool regenActive = false;

String optimizationStatus = "NORMAL";

// ============================================================
// BUTTON STATES
// ============================================================

bool lastStartState = HIGH;
bool lastStopState = HIGH;
bool lastResetState = HIGH;

// ============================================================
// TIMERS
// ============================================================

unsigned long lastSensorRead = 0;
unsigned long lastBackendUpdate = 0;
unsigned long lastDisplayUpdate = 0;

const unsigned long SENSOR_INTERVAL = 200;
const unsigned long BACKEND_INTERVAL = 1000;
const unsigned long DISPLAY_INTERVAL = 250;

// ============================================================
// FUNCTION DECLARATIONS
// ============================================================

void connectWiFi();

void readSensors();

void handleButtons();

void sendToBackend();

void parseBackendResponse(String response);

float getJSONFloat(String json, String key);

bool getJSONBool(String json, String key);

String getJSONString(String json, String key);

void updateLEDs();

void updateDisplay();

void displayReady();

// ============================================================
// SETUP
// ============================================================

void setup()
{
    Serial.begin(115200);

    delay(1000);

    Serial.println();
    Serial.println("==============================");
    Serial.println("EV ESP32 SYSTEM");
    Serial.println("==============================");

    // --------------------------------------------------------
    // GPIO
    // --------------------------------------------------------

    pinMode(THROTTLE_PIN, INPUT);

    pinMode(START_BUTTON, INPUT_PULLUP);
    pinMode(STOP_BUTTON, INPUT_PULLUP);
    pinMode(RESET_BUTTON, INPUT_PULLUP);

    pinMode(GREEN_LED, OUTPUT);
    pinMode(BLUE_LED, OUTPUT);
    pinMode(RED_LED, OUTPUT);

    digitalWrite(GREEN_LED, LOW);
    digitalWrite(BLUE_LED, LOW);
    digitalWrite(RED_LED, LOW);

    // --------------------------------------------------------
    // I2C
    // --------------------------------------------------------

    Wire.begin(SDA_PIN, SCL_PIN);

    // --------------------------------------------------------
    // OLED
    // --------------------------------------------------------

    if (!display.begin(
            SSD1306_SWITCHCAPVCC,
            0x3C))
    {
        Serial.println("OLED ERROR");
    }
    else
    {
        Serial.println("OLED OK");

        display.clearDisplay();

        display.setTextSize(1);
        display.setTextColor(SSD1306_WHITE);

        display.setCursor(0, 0);
        display.println("EV SYSTEM");

        display.setCursor(0, 15);
        display.println("Initializing...");

        display.display();
    }

    // --------------------------------------------------------
    // MPU6050
    // --------------------------------------------------------

    if (!mpu.begin(0x68))
    {
        Serial.println("MPU6050 ERROR");
    }
    else
    {
        Serial.println("MPU6050 OK");

        mpu.setAccelerometerRange(
            MPU6050_RANGE_8_G);

        mpu.setGyroRange(
            MPU6050_RANGE_500_DEG);

        mpu.setFilterBandwidth(
            MPU6050_BAND_21_HZ);
    }

    // --------------------------------------------------------
    // DS18B20
    // --------------------------------------------------------

    temperatureSensor.begin();

    Serial.println("DS18B20 OK");

    // --------------------------------------------------------
    // WIFI
    // --------------------------------------------------------

    connectWiFi();

    // --------------------------------------------------------
    // READY
    // --------------------------------------------------------

    displayReady();

    Serial.println("==============================");
    Serial.println("SYSTEM READY");
    Serial.println("==============================");
}

// ============================================================
// MAIN LOOP
// ============================================================

void loop()
{
    handleButtons();

    // Read sensors
    if (millis() - lastSensorRead >= SENSOR_INTERVAL)
    {
        lastSensorRead = millis();
        readSensors();
    }

    // Send data to Python backend
    if (millis() - lastBackendUpdate >= BACKEND_INTERVAL)
    {
        lastBackendUpdate = millis();
        sendToBackend();
    }

    // Update status LEDs
    updateLEDs();

    // Update OLED
    if (millis() - lastDisplayUpdate >= DISPLAY_INTERVAL)
    {
        lastDisplayUpdate = millis();
        updateDisplay();
    }

    delay(5);
}

void connectWiFi()
{
    Serial.println();
    Serial.println("Connecting to WiFi...");

    WiFi.mode(WIFI_STA);

    WiFi.begin(
        WIFI_SSID,
        WIFI_PASSWORD);

    unsigned long startTime = millis();

    while (
        WiFi.status() != WL_CONNECTED &&
        millis() - startTime < 10000)
    {
        delay(500);

        Serial.print(".");
    }

    Serial.println();

    if (WiFi.status() == WL_CONNECTED)
    {
        wifiConnected = true;

        Serial.println("WiFi connected");

        Serial.print("ESP32 IP: ");
        Serial.println(WiFi.localIP());
    }
    else
    {
        wifiConnected = false;

        Serial.println("WiFi connection failed");
    }
}

// ============================================================
// SENSOR READING
// ============================================================

void readSensors()
{
    // --------------------------------------------------------
    // THROTTLE
    // --------------------------------------------------------

    int rawThrottle =
        analogRead(THROTTLE_PIN);

    throttlePct =
        ((float)rawThrottle / 4095.0) * 100.0;

    throttlePct =
        constrain(
            throttlePct,
            0.0,
            100.0);

    // --------------------------------------------------------
    // MPU6050
    // --------------------------------------------------------

    sensors_event_t accel;
    sensors_event_t gyro;
    sensors_event_t temp;

    mpu.getEvent(
        &accel,
        &gyro,
        &temp);

    /*
       The current circuit uses the MPU6050 X-axis
       as the longitudinal acceleration axis.
    */

    accelerationMps2 =
        accel.acceleration.x;

    // Remove tiny sensor noise

    if (fabs(accelerationMps2) < 0.08)
    {
        accelerationMps2 = 0.0;
    }

    // --------------------------------------------------------
    // DS18B20
    // --------------------------------------------------------

    temperatureSensor.requestTemperatures();

    float measuredTemp =
        temperatureSensor.getTempCByIndex(0);

    if (
        measuredTemp != DEVICE_DISCONNECTED_C &&
        measuredTemp > -55.0 &&
        measuredTemp < 125.0)
    {
        batteryTempC = measuredTemp;
    }

    // --------------------------------------------------------
    // DEBUG
    // --------------------------------------------------------

    Serial.print("Throttle: ");
    Serial.print(throttlePct, 1);

    Serial.print("% | Accel: ");
    Serial.print(accelerationMps2, 2);

    Serial.print(" m/s2 | Temp: ");
    Serial.print(batteryTempC, 1);

    Serial.println(" C");
}

// ============================================================
// BUTTON HANDLING
// ============================================================

void handleButtons()
{
    bool startState =
        digitalRead(START_BUTTON);

    bool stopState =
        digitalRead(STOP_BUTTON);

    bool resetState =
        digitalRead(RESET_BUTTON);

    // --------------------------------------------------------
    // START
    // --------------------------------------------------------

    if (
        lastStartState == HIGH &&
        startState == LOW)
    {
        simulationRunning = true;

        Serial.println(">>> START");

        delay(100);
    }

    // --------------------------------------------------------
    // STOP
    // --------------------------------------------------------

    if (
        lastStopState == HIGH &&
        stopState == LOW)
    {
        simulationRunning = false;

        Serial.println(">>> STOP");

        delay(100);
    }

    // --------------------------------------------------------
    // RESET
    // --------------------------------------------------------

    if (
        lastResetState == HIGH &&
        resetState == LOW)
    {
        simulationRunning = false;

        throttlePct = 0.0;

        speedKmh = 0.0;
        batteryCurrentA = 0.0;
        batteryPowerKw = 0.0;

        optimizedPowerKw = 0.0;
        requestedPowerKw = 0.0;

        regenPowerKw = 0.0;

        regenActive = false;

        Serial.println(">>> RESET");

        delay(100);
    }

    lastStartState = startState;
    lastStopState = stopState;
    lastResetState = resetState;
}

// ============================================================
// SEND DATA TO FASTAPI
// ============================================================

void sendToBackend()
{
    if (WiFi.status() != WL_CONNECTED)
    {
        wifiConnected = false;

        connectWiFi();

        return;
    }

    wifiConnected = true;

    HTTPClient http;

    http.setTimeout(3000);

    http.begin(SERVER_URL);

    http.addHeader(
        "Content-Type",
        "application/json");

    // --------------------------------------------------------
    // CREATE JSON
    // --------------------------------------------------------

    String json = "{";

    json += "\"throttle_pct\":";
    json += String(throttlePct, 2);

    json += ",";

    json += "\"acceleration_mps2\":";
    json += String(accelerationMps2, 3);

    json += ",";

    json += "\"battery_temp_c\":";
    json += String(batteryTempC, 2);

    json += ",";

    json += "\"battery_voltage_v\":";
    json += String(batteryVoltageV, 2);

    json += ",";

    json += "\"soc_pct\":";
    json += String(socPct, 2);

    json += ",";

    json += "\"soh_pct\":";
    json += String(sohPct, 2);

    json += ",";

    json += "\"speed_kmh\":";
    json += String(speedKmh, 2);

    json += ",";

    json += "\"simulation_running\":";

    if (simulationRunning)
    {
        json += "true";
    }
    else
    {
        json += "false";
    }

    json += "}";

    // --------------------------------------------------------
    // SEND
    // --------------------------------------------------------

    Serial.println();
    Serial.println("Sending to backend:");
    Serial.println(json);

    int httpCode =
        http.POST(json);

    if (httpCode > 0)
    {
        Serial.print("HTTP Response: ");
        Serial.println(httpCode);

        if (httpCode == HTTP_CODE_OK)
        {
            String response =
                http.getString();

            Serial.println("Backend response:");
            Serial.println(response);

            parseBackendResponse(response);
        }
    }
    else
    {
        Serial.print("HTTP ERROR: ");
        Serial.println(
            http.errorToString(httpCode));
    }

    http.end();
}

// ============================================================
// BACKEND RESPONSE PARSER
// ============================================================

void parseBackendResponse(String response)
{
    optimizedPowerKw =
        getJSONFloat(
            response,
            "optimized_power_kw");

    requestedPowerKw =
        getJSONFloat(
            response,
            "requested_power_kw");

    powerLimitKw =
        getJSONFloat(
            response,
            "power_limit_kw");

    speedKmh =
        getJSONFloat(
            response,
            "speed_kmh");

    accelerationMps2 =
        getJSONFloat(
            response,
            "acceleration_mps2");

    batteryVoltageV =
        getJSONFloat(
            response,
            "battery_voltage_v");

    batteryCurrentA =
        getJSONFloat(
            response,
            "battery_current_a");

    batteryPowerKw =
        getJSONFloat(
            response,
            "battery_power_kw");

    batteryTempC =
        getJSONFloat(
            response,
            "battery_temp_c");

    socPct =
        getJSONFloat(
            response,
            "soc_pct");

    sohPct =
        getJSONFloat(
            response,
            "soh_pct");

    distanceKm =
        getJSONFloat(
            response,
            "distance_km");

    energyConsumedWh =
        getJSONFloat(
            response,
            "energy_consumed_wh");

    energyRecoveredWh =
        getJSONFloat(
            response,
            "energy_recovered_wh");

    whPerKm =
        getJSONFloat(
            response,
            "wh_per_km");

    predictedWhPerKm =
        getJSONFloat(
            response,
            "predicted_wh_per_km");

    remainingRangeKm =
        getJSONFloat(
            response,
            "remaining_range_km");

    regenPowerKw =
        getJSONFloat(
            response,
            "regen_power_kw");

    regenActive =
        getJSONBool(
            response,
            "regen_active");

    optimizationStatus =
        getJSONString(
            response,
            "optimization_status");

    // --------------------------------------------------------
    // PRINT IMPORTANT RESULTS
    // --------------------------------------------------------

    Serial.println();
    Serial.println("========== EV STATE ==========");

    Serial.print("Speed: ");
    Serial.print(speedKmh, 1);
    Serial.println(" km/h");

    Serial.print("Throttle: ");
    Serial.print(throttlePct, 1);
    Serial.println(" %");

    Serial.print("Motor Power: ");
    Serial.print(optimizedPowerKw, 2);
    Serial.println(" kW");

    Serial.print("Battery Power: ");
    Serial.print(batteryPowerKw, 2);
    Serial.println(" kW");

    Serial.print("SOC: ");
    Serial.print(socPct, 2);
    Serial.println(" %");

    Serial.print("Battery Temp: ");
    Serial.print(batteryTempC, 1);
    Serial.println(" C");

    Serial.print("Wh/km: ");
    Serial.print(whPerKm, 1);

    Serial.println();

    Serial.print("Predicted Wh/km: ");
    Serial.print(predictedWhPerKm, 1);

    Serial.println();

    Serial.print("Remaining Range: ");
    Serial.print(remainingRangeKm, 1);
    Serial.println(" km");

    Serial.print("Regen: ");

    if (regenActive)
    {
        Serial.print("ACTIVE ");

        Serial.print(regenPowerKw, 2);

        Serial.println(" kW");
    }
    else
    {
        Serial.println("OFF");
    }

    Serial.print("Optimization: ");
    Serial.println(optimizationStatus);

    Serial.println("==============================");
}

// ============================================================
// JSON FLOAT
// ============================================================

float getJSONFloat(
    String json,
    String key)
{
    String searchKey =
        "\"" + key + "\":";

    int start =
        json.indexOf(searchKey);

    if (start < 0)
    {
        return 0.0;
    }

    start += searchKey.length();

    int comma =
        json.indexOf(",", start);

    int brace =
        json.indexOf("}", start);

    int end = -1;

    if (comma >= 0 && brace >= 0)
    {
        end = min(comma, brace);
    }
    else if (comma >= 0)
    {
        end = comma;
    }
    else if (brace >= 0)
    {
        end = brace;
    }
    else
    {
        end = json.length();
    }

    String value =
        json.substring(start, end);

    value.trim();

    return value.toFloat();
}

// ============================================================
// JSON BOOLEAN
// ============================================================

bool getJSONBool(
    String json,
    String key)
{
    String searchKey =
        "\"" + key + "\":";

    int start =
        json.indexOf(searchKey);

    if (start < 0)
    {
        return false;
    }

    start += searchKey.length();

    String value =
        json.substring(start, start + 5);

    value.trim();

    return value.startsWith("true");
}

// ============================================================
// JSON STRING
// ============================================================

String getJSONString(
    String json,
    String key)
{
    String searchKey =
        "\"" + key + "\":\"";

    int start =
        json.indexOf(searchKey);

    if (start < 0)
    {
        return "NORMAL";
    }

    start += searchKey.length();

    int end =
        json.indexOf("\"", start);

    if (end < 0)
    {
        return "NORMAL";
    }

    return json.substring(
        start,
        end);
}

// ============================================================
// LED STATUS
// ============================================================

void updateLEDs()
{
    digitalWrite(
        GREEN_LED,
        LOW);

    digitalWrite(
        BLUE_LED,
        LOW);

    digitalWrite(
        RED_LED,
        LOW);

    // RED = stopped

    if (!simulationRunning)
    {
        digitalWrite(
            RED_LED,
            HIGH);

        return;
    }

    // BLUE = regenerative braking

    if (regenActive)
    {
        digitalWrite(
            BLUE_LED,
            HIGH);

        return;
    }

    // GREEN = normal driving

    digitalWrite(
        GREEN_LED,
        HIGH);
}

// ============================================================
// OLED
// ============================================================

void updateDisplay()
{
    display.clearDisplay();

    display.setTextSize(1);
    display.setTextColor(
        SSD1306_WHITE);

    // --------------------------------------------------------
    // STATUS
    // --------------------------------------------------------

    display.setCursor(0, 0);

    if (!simulationRunning)
    {
        display.print("STOP");
    }
    else if (regenActive)
    {
        display.print("REGEN");
    }
    else
    {
        display.print("RUN");
    }

    display.setCursor(70, 0);

    display.print("SOC:");

    display.print(
        socPct,
        0);

    display.print("%");

    // --------------------------------------------------------
    // SPEED
    // --------------------------------------------------------

    display.setCursor(0, 13);

    display.print("SPD:");

    display.print(
        speedKmh,
        1);

    display.print("km/h");

    // --------------------------------------------------------
    // THROTTLE
    // --------------------------------------------------------

    display.setCursor(0, 26);

    display.print("THR:");

    display.print(
        throttlePct,
        0);

    display.print("%");

    // --------------------------------------------------------
    // POWER
    // --------------------------------------------------------

    display.setCursor(65, 26);

    display.print("P:");

    display.print(
        batteryPowerKw,
        1);

    display.print("kW");

    // --------------------------------------------------------
    // TEMPERATURE
    // --------------------------------------------------------

    display.setCursor(0, 39);

    display.print("T:");

    display.print(
        batteryTempC,
        1);

    display.print("C");

    // --------------------------------------------------------
    // RANGE
    // --------------------------------------------------------

    display.setCursor(65, 39);

    display.print("R:");

    display.print(
        remainingRangeKm,
        1);

    display.print("km");

    // --------------------------------------------------------
    // OPTIMIZATION
    // --------------------------------------------------------

    display.setCursor(0, 52);

    if (optimizationStatus.length() > 20)
    {
        display.print(
            optimizationStatus.substring(
                0,
                20));
    }
    else
    {
        display.print(
            optimizationStatus);
    }

    display.display();
}

// ============================================================
// READY SCREEN
// ============================================================

void displayReady()
{
    display.clearDisplay();

    display.setTextSize(1);
    display.setTextColor(
        SSD1306_WHITE);

    display.setCursor(0, 0);
    display.println("EV SYSTEM");

    display.setCursor(0, 15);
    display.println("READY");

    display.setCursor(0, 30);

    if (wifiConnected)
    {
        display.println("WiFi: CONNECTED");
    }
    else
    {
        display.println("WiFi: OFFLINE");
    }

    display.display();
}