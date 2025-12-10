#include "lock_module.h"

bool doorOpen = false;   // 문이 열렸는지
bool doorLocked = false; // 문이 잠겼는지

unsigned long lastMagCheck = 0;

void setup() {
  Serial.begin(9600);

  lcdInit();
  keypadInit();
  motorInit();
  magnetInit();
  //ultrasonicInit();

  closeDoor();
  doorOpen = false;
  doorLocked = true;

  showPrompt();
}

void loop() {

  handleKeypad();
  handleSerialResponse();

  if (millis() - lastMagCheck > 200) {
    lastMagCheck = millis();

    if (isMagnetDetected()) {
      if (!doorOpen)  return; // 이미 문이 닫힌 상태라면 아무동작 안함
      
      Serial.println("DETECT:1");
      closeDoor();
      doorOpen = false;
      doorLocked = true;
    }
  }
}

void handleSerialResponse() {
  if (!Serial.available()) return;

  String res = Serial.readStringUntil('\n');
  res.trim();
  if (res.length() == 0) return;

  if (res == "MATCH") {
    openDoor();
    doorOpen = true;
    doorLocked = false;
    showMessage("Door Open", 800);
    showPrompt();
  }
  else if (res == "NO_MATCH") {
    closeDoor();
    doorOpen = false;
    doorLocked = true;
    showMessage("ACCESS DENIED", 800);
    showPrompt();
  }
  else if (res == "OPEN") {
    openDoor();
    doorOpen = true;
    doorLocked = false;
    showMessage("Door Open", 800);
    showPrompt();
  }
  else if (res == "CLOSE") {
    closeDoor();
    doorOpen = false;
    doorLocked = true;
  }
  else if (res == "DENIED") {
    closeDoor();
    doorOpen = false;
    doorLocked = true;
    showMessage("Object Inside", 800);
    showPrompt();
  }
}
