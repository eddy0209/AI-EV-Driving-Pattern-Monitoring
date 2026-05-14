#include <LiquidCrystal.h>


LiquidCrystal lcd(12, 11, 5, 4, 3, 2);


int potPin = A0;
int motorEnable = 9;
int motorInput1 = 8;


int throttle;
int speedValue;

float speed;
float current;
float voltage = 24.0;
float power;
float batteryCapacity = 240.0;
float estimatedRange;

void setup() {

  pinMode(motorEnable, OUTPUT);
  pinMode(motorInput1, OUTPUT);

  lcd.begin(16, 2);

  digitalWrite(motorInput1, HIGH);
}

void loop() {


  throttle = analogRead(potPin);


  speedValue = map(throttle, 0, 1023, 0, 255);


  analogWrite(motorEnable, speedValue);


  speed = map(throttle, 0, 1023, 0, 80);

  current = map(throttle, 0, 1023, 1, 15);


  power = voltage * current;


  estimatedRange = (batteryCapacity / power) * speed;


  lcd.clear();


  lcd.setCursor(0, 0);
  lcd.print("Range:");
  lcd.print(estimatedRange, 1);
  lcd.print("km");


  lcd.setCursor(0, 1);

  if(throttle < 300)
    lcd.print("Mode: ECO");

  else if(throttle < 700)
    lcd.print("Mode:NORMAL");

  else
    lcd.print("Mode:AGGRESS");

  delay(500);
}