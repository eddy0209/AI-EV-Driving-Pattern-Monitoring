#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

int potPin = A0;
int motorEnable = 9;
int motorInput1 = 8;

void setup() {
  pinMode(motorEnable, OUTPUT);
  pinMode(motorInput1, OUTPUT);

  lcd.begin(16, 2);

  digitalWrite(motorInput1, HIGH);
}

void loop() {

  int throttle = analogRead(potPin);

  int speedValue = map(throttle, 0, 1023, 0, 255);

  analogWrite(motorEnable, speedValue);

  lcd.clear();

  lcd.setCursor(0,0);
  lcd.print("Throttle:");
  lcd.print(map(throttle,0,1023,0,100));

  lcd.setCursor(0,1);

  if(throttle < 300)
    lcd.print("Mode: ECO");

  else if(throttle < 700)
    lcd.print("Mode: NORMAL");

  else
    lcd.print("Mode: AGGRESS");

  delay(300);
}