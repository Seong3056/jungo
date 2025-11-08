#include "lock_module_setup.h"

String inputCode = "";
bool waitingResponse = false;

void setup() {
  Serial.begin(9600);
  lcdInit();
  keypadInit();
  motorInit();
  lcd.print("Enter Code:");
}

void loop() {
  char key = keypad.getKey();

  if (key) {
    if (key == '*') {
      inputCode = "";
      lcd.clear();
      lcd.print("Enter Code:");
    } 
    else if (key == '#') {
      if (inputCode.length() == 4) {
        Serial.println(inputCode);
        lcd.clear();
        lcd.print("Sending...");
        waitingResponse = true;
      } else {
        lcd.clear();
        lcd.print("4 digits only!");
        delay(1000);
        lcd.clear();
        lcd.print("Enter Code:");
      }
    } 
    else if (key >= '0' && key <= '9' && inputCode.length() < 4) {
      inputCode += key;
      lcd.setCursor(0, 1);
      lcd.print(inputCode);
    }
  }

  // 📥 Serial Response
  if (waitingResponse && Serial.available()) {
    String response = Serial.readStringUntil('\n');
    response.trim();

    lcd.clear();
    if (response == "MATCH") lcd.print("Access Granted");
    else lcd.print("Access Denied");

    waitingResponse = false;
    delay(2000);
    lcd.clear();
    lcd.print("Enter Code:");
    inputCode = "";
  }
}
