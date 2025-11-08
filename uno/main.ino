#include "lock_module_setup.h"

String inputBuffer = ""; // 누른 키들을 저장하는 문자열

void setup() {
  Serial.begin(9600);
  lcdInit();
  keypadInit();
  motorInit();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Enter Code:");
  Serial.println("=== getKey() Test ===");
}

void loop() {
  char key = keypad.getKey();
  if (key) {
    Serial.print("Pressed key: ");
    Serial.println(key);

    if (key == 'A') {
      // 초기화
      inputBuffer = "";
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Enter Code:");
      lcd.setCursor(0, 1);
      lcd.print("Cleared");
      delay(500);
      lcd.setCursor(0, 1);
      lcd.print("                "); // 두 번째 줄 지우기
    } 
    else {
      // 입력 누적
      inputBuffer += key;
      lcd.setCursor(0, 1);
      lcd.print(inputBuffer);
    }
  }
}
