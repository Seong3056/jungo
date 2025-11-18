#include "lock_module.h"

bool doorLocked = false;
bool doorOpen = false;
bool ultraSentAfterClose = false;

String serialBuffer = "";

// ------------------------------------------------------
// 🔹 MATCH / NO_MATCH 처리
// ------------------------------------------------------
void handleSerialResponse() {
  if (!Serial.available()) return;

  String res = Serial.readStringUntil('\n');
  res.trim();
  if (res.length() == 0) return;

  if (res == "MATCH") {
    if (!doorOpen) {
      doorOpen = true;
      openDoor();
      showMessage("Door Open", 1000);
      showPrompt();
    }
  }
  else if (res == "NO_MATCH") {
    showMessage("ACCESS DENIED", 1000);
    showPrompt();
  }
}

// ------------------------------------------------------
// setup
// ------------------------------------------------------
void setup() {
  Serial.begin(9600);

  lcdInit();
  keypadInit();
  motorInit();
  magnetInit();
  ultrasonicInit();

  closeDoor();
  doorLocked = true;
  ultraSentAfterClose = false;
}

// ------------------------------------------------------
// loop
// ------------------------------------------------------
void loop() {

  // 0. 라즈베리 응답 처리
  handleSerialResponse();

  // 1. 문 닫힘 감지 → ULTRA 리셋
  if (isMagnetDetected()) {
    if (!doorLocked) {
      closeDoor();
      delay(50);
      lcd.clear();
      showPrompt();

      doorLocked = true;
      doorOpen = false;
      ultraSentAfterClose = false;
    }
  } else {
    doorLocked = false;
  }

  // 2. 문 닫힌 후 초음파 감지 1회만 전송
  if (doorLocked && !ultraSentAfterClose) {
    float d = getUltrasonicDistance();   // ⭐ 모듈에서 가져옴

    if (d > 5 && d < 26) {
      Serial.println("ULTRA:1");
      ultraSentAfterClose = true;  // 1회만 전송
    }
  }

  // 3. 키패드 처리
  handleKeypad();
}
