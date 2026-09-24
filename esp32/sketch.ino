#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

const char* SERVER_URL = "http://host.wokwi.internal:8000/";

void setup() {

    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println("================================");
    Serial.println("EV AI - ESP32 BACKEND TEST");
    Serial.println("================================");

    Serial.print("Connecting to WiFi");

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi connected!");

    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());

    Serial.println("Testing Python backend...");

    HTTPClient http;

    http.begin(SERVER_URL);

    int httpCode = http.GET();

    Serial.print("HTTP response: ");
    Serial.println(httpCode);

    if (httpCode > 0) {

        String response = http.getString();

        Serial.println("Backend response:");
        Serial.println(response);

    } else {

        Serial.print("HTTP request failed: ");
        Serial.println(http.errorToString(httpCode));

    }

    http.end();
}

void loop() {

    delay(1000);
}