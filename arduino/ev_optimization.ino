#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

int potPin = A0;
int motorEnable = 9;
int motorInput1 = 8;

int throttle;
int speedValue;
int optimizedPWM;

float speed;
float current;
float voltage = 24.0;
float power;
float optimizedPower;
float efficiency;

String drivingMode;
String optimizationStatus;

void setup() {

  pinMode(motorEnable, OUTPUT);
  pinMode(motorInput1, OUTPUT);

  lcd.begin(16, 2);

  digitalWrite(motorInput1, HIGH);
}

void loop() {

  throttle = analogRead(potPin);

  speedValue = map(throttle, 0, 1023, 0, 255);

  speed = map(throttle, 0, 1023, 0, 80);

  current = map(throttle, 0, 1023, 1, 15);

  power = voltage * current;

  if(throttle < 300) {

    drivingMode = "ECO";

    optimizedPWM = speedValue;

    optimizationStatus = "EFF HIGH";

    efficiency = 95;
  }

  else if(throttle < 700) {

    drivingMode = "NORMAL";

    optimizedPWM = speedValue * 0.90;

    optimizationStatus = "OPT ACTIVE";

    efficiency = 80;
  }

  else {

    drivingMode = "AGGRESSIVE";

    optimizedPWM = speedValue * 0.70;

    optimizationStatus = "PWM REDUCED";

    efficiency = 60;
  }

  analogWrite(motorEnable, optimizedPWM);

  optimizedPower = power * (optimizedPWM / 255.0);

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print(drivingMode);

  lcd.setCursor(0, 1);
  lcd.print(optimizationStatus);

  delay(500);
}