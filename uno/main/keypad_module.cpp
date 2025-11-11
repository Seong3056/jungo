#include "lock_module.h"

char keys[ROWS][COLS] = {
  { '1', '2', '3', 'A' },
  { '4', '5', '6', 'B' },
  { '7', '8', '9', 'C' },
  { '*', '0', '#', 'D' }
};

// byte rowPins[ROWS] = {6, 7, 8, 9};
// byte colPins[COLS] = {2, 3, 4, 5};
byte rowPins[ROWS] = { 8, 4, 9, 5 };
byte colPins[COLS] = { 6, 2, 7, 3 };

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

String inputId = "";
String inputCode = "";
bool enteringId = true;  // 현재 상품 ID 입력 중인지 여부
const int CODE_LEN = 4;

void keypadInit() {
  keypad.setDebounceTime(20);
  keypad.setHoldTime(50);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Enter ID:");
  lcd.setCursor(0, 1);
}

void handleKeypad() {
  char key = keypad.getKey();
  if (!key) return;

  // 초기화 키: *
  if (key == '*') {
    inputId = "";
    inputCode = "";
    enteringId = true;
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Enter ID:");
    lcd.setCursor(0, 1);
    return;
  }

  // 입력 완료 키: #
  if (key == '#') {
    if (enteringId) {
      if (inputId.length() > 0) {
        enteringId = false;
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Enter Code:");
        lcd.setCursor(0, 1);
      } else {
        lcd.clear();
        lcd.print("Enter ID first");
        delay(800);
        lcd.clear();
        lcd.print("Enter ID:");
        lcd.setCursor(0, 1);
      }
    } else {
      if (inputCode.length() == CODE_LEN && inputId.length() > 0) {
        // ✅ 최종 전송
        String message = "CHECK:" + inputId + ":" + inputCode;
        Serial.println(message);
        delay(10);
        lcd.clear();
        lcd.print("Checking...");
        delay(800);

        // 초기 상태 복귀
        inputId = "";
        inputCode = "";
        enteringId = true;
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Enter ID:");
        lcd.setCursor(0, 1);
      } else {
        lcd.clear();
        lcd.print("Incomplete");
        delay(800);
        lcd.clear();
        lcd.print("Enter ID:");
        lcd.setCursor(0, 1);
      }
    }
    return;
  }

  // 숫자 입력 처리
  if (isdigit(key)) {
    if (enteringId) {
      if (inputId.length() < 8) {  // ID는 최대 8자리로 제한
        inputId += key;
        lcd.print(key);  // ID 출력
      }
    } else {
      if (inputCode.length() < CODE_LEN) {
        inputCode += key;
        lcd.print(key);  // 비밀번호 출력
      }
    }
  }
}
