#include "lock_module.h"

bool doorLocked = false;
bool doorOpen = false;
bool detectAfterClose = true;

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
      detectAfterClose = false;
      showMessage("Door Open", 1000);
      showPrompt();
      
    }
  }
  else if (res == "NO_MATCH") {
    showMessage("ACCESS DENIED", 1000);
    showPrompt();
  }
  else if (res == "OPEN"){
    detectAfterClose = true;
    openDoor();
    showMessage("Door Open", 1000);
    showPrompt();
    
  }
  else if (res == "DENIED"){
    showMessage("Object Inside", 1000);
    showPrompt();
  }
  else if (res == "CLOSE"){
    closeDoor();
    detectAfterClose = true;
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
  detectAfterClose = true;
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
      Serial.println("DETECT:1");
      closeDoor();
      delay(50);
      lcd.clear();
      showPrompt();

      doorLocked = true;
      doorOpen = false;
//      ultraSentAfterClose = false;
      detectAfterClose = false;
    }
  } else {
    doorLocked = false;
    detectAfterClose = true;
  }



  // 3. 키패드 처리
  handleKeypad();  
}
