#include "lock_module.h"

bool doorLocked = false;
bool doorOpen = false;   // 🔹 문이 열렸는지 상태 저장

void setup() {
  Serial.begin(9600);

  lcdInit();
  keypadInit();
  motorInit();
  magnetInit();
  ultrasonicInit();

  closeDoor();   // 시작 시 문 잠금
  doorLocked = true;
}

// ===============================================
// 🔹 라즈베리 → 아두이노 직렬 통신 처리
//    MATCH → 문 열기
//    NO_MATCH → 접근 거부 메시지
// ===============================================
void handleSerialResponse() {
  if (!Serial.available()) return;

  String res = Serial.readStringUntil('\n');
  res.trim();
  if (res.length() == 0) return;

  Serial.print("📩 Received: ");
  Serial.println(res);

  if (res == "MATCH") {             // 인증 성공 → 문 열기
    if (!doorOpen) {
      doorOpen = true;
      openDoor();
      showMessage("Door Open", 1000);
      showPrompt();
    }
  }
  else if (res == "NO_MATCH") {     // 인증 실패
    showMessage("ACCESS DENIED", 1000);
    showPrompt();
  }
  else {
    Serial.print("⚠️ Unknown command: ");
    Serial.println(res);
  }
}

void loop() {

  // ======================================
  // 🔹 0. 라즈베리 신호 처리 (MATCH/NO_MATCH)
  // ======================================
  handleSerialResponse();

  // ======================================
  // 🔹 1. 마그네틱 센서 감지 → 문 잠금
  // ======================================
  if (isMagnetDetected()) {
    if (!doorLocked) {        // 문 열렸는데 자석 감지 → 문 닫힘
      closeDoor();
      doorLocked = true;
      doorOpen = false;       // 문 닫혔으므로 열림 상태 false
    }
  } else {
    doorLocked = false;       // 문 열림 상태
  }

  // ======================================
  // 🔹 2. 문이 잠긴 동안 초음파 감지
  // ======================================
  if (doorLocked) {
    handleUltrasonic();       // 26cm 변화 감지 → ULTRA:1 전송
  }

  // ======================================
  // 🔹 3. 키패드 처리
  // ======================================
  handleKeypad();
}
