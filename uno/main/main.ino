#include "lock_module_setup.h"

String inputBuffer = "";
String enteredId = "";
String enteredCode = "";

bool waitingResponse = false;
bool enteringId = true;

bool lastMagnet = false;
bool currentMagnet = false;

unsigned long lastInputTime = 0;
const unsigned long INPUT_TIMEOUT = 30000; // 30초 입력 제한

void setup() {
  Serial.begin(9600);
  lcdInit();
  keypadInit();
  motorInit();

  pinMode(MAGNET_PIN, INPUT);   // ✅ 마그네틱 센서 핀 초기화

  lcd.clear();
  lcd.print("Enter ID:");
  lastInputTime = millis();
}

void resetToEnterId() {
  inputBuffer = "";
  enteredId = "";
  enteredCode = "";
  enteringId = true;
  waitingResponse = false;
  lcd.clear();
  lcd.print("Enter ID:");
  lastInputTime = millis();
}

void loop() {
  char key = keypad.getKey();

  // 🔹 마그네틱 센서 상태 읽기
  currentMagnet = digitalRead(MAGNET_PIN);

  // 🔹 센서 상태 변화 시 LCD에 표시
  if (currentMagnet != lastMagnet) {
    lastMagnet = currentMagnet;
    lcd.clear();
    if (currentMagnet == LOW) {         // 자석 감지 (문 닫힘)
      lcd.print("Magnet Detected");
    } else {                            // 자석 없음 (문 열림)
      lcd.print("Magnet Removed");
    }
    delay(800);
    lcd.clear();
    lcd.print("Enter ID:");
  }

  // 🔹 입력 타임아웃 처리
  if (!waitingResponse && (millis() - lastInputTime > INPUT_TIMEOUT)) {
    lcd.clear();
    lcd.print("Timeout");
    delay(1000);
    resetToEnterId();
    return;
  }

  // 🔹 키 입력 처리
  if (key) {
    lastInputTime = millis();

    if (key == '*') { // 전체 초기화
      resetToEnterId();
      return;
    }

    if (key == '#') {
      if (enteringId) {
        if (inputBuffer.length() > 0) {
          enteredId = inputBuffer;
          inputBuffer = "";
          enteringId = false;
          lcd.clear();
          lcd.print("Enter Code:");
        } else {
          lcd.clear();
          lcd.print("Invalid ID");
          delay(800);
          resetToEnterId();
        }
      } else {
        if (inputBuffer.length() == 4) {
          enteredCode = inputBuffer;
          lcd.clear();
          lcd.print("Sending...");
          waitingResponse = true;

          // 🔹 Raspberry Pi로 전송 (형식: CHECK:<id>:<code>)
          String msg = "CHECK:" + enteredId + ":" + enteredCode + "\n";
          Serial.print(msg);
        } else {
          lcd.clear();
          lcd.print("4 digits only!");
          delay(1000);
          lcd.clear();
          lcd.print("Enter Code:");
          inputBuffer = "";
        }
      }
    }

    // 🔹 숫자 입력 처리
    else if (key >= '0' && key <= '9') {
      if (inputBuffer.length() < 10) {
        inputBuffer += key;
        lcd.setCursor(0, 1);
        lcd.print(inputBuffer);
      }
    }
  }

  // 📥 Raspberry Pi 응답 처리
  if (waitingResponse && Serial.available()) {
    String response = Serial.readStringUntil('\n');
    response.trim();

    lcd.clear();
    if (response == "MATCH") {
      lcd.print("Access Granted");
      //motorUnlock();  // ✅ 모터 동작 (문 열기)
    } else if (response == "NO_MATCH") {
      lcd.print("Access Denied");
    } else if (response == "NO_LISTING" || response == "NO_SUCH_ID") {
      lcd.print("No such ID found");
    } else {
      lcd.print("Error");
      lcd.setCursor(0, 1);
      lcd.print(response);
    }

    waitingResponse = false;
    delay(2000);
    resetToEnterId();
  }
}
