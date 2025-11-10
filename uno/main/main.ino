#include "lock_module.h"

bool doorOpen = false;
String lastMessage = "";

// ===================== LCD 안전 출력 (중복 방지) =====================
void safeShowMessage(const String &msg, int delayTime = 1000) {
  if (lastMessage != msg) {
    showMessage(msg, delayTime);
    lastMessage = msg;
  }
}

// ===================== 초기 설정 =====================
void setup() {
  Serial.begin(9600);
  lcdInit();
  keypadInit();
  motorInit();
  magnetInit();
  ultrasonicInit();   // ✅ 초음파 센서 초기화 복구

  safeShowMessage("System Ready", 1000);
  showPrompt();
  Serial.println("🔧 Arduino UNO Ready - Waiting for commands...");
}

// ===================== 라즈베리 → 아두이노 명령 처리 =====================
void handleSerialResponse() {
  if (!Serial.available()) return;

  String res = Serial.readStringUntil('\n');
  res.trim();
  if (res.length() == 0) return;

  Serial.print("📩 Received: ");
  Serial.println(res);

  if (res == "MATCH") {                     // 인증 성공 → 문 열기
    if (!doorOpen) {
      doorOpen = true;
      openDoor();
      safeShowMessage("Door Open", 1000);
      showPrompt();
    }
  }
  else if (res == "NO_MATCH") {                // 인증 실패 → 표시만
    safeShowMessage("ACCESS DENIED", 1000);
    showPrompt();
  }
  else {
    Serial.print("⚠️ Unknown command: ");
    Serial.println(res);
  }
}

// ===================== 마그네틱 센서 (문 닫힘 감지) =====================
void handleMagnet() {
  if (isMagnetDetected() && doorOpen) {
    Serial.println("CLOSE:1");      // 아두이노 → 라즈베리로 송신
    doorOpen = false;
    closeDoor();
    safeShowMessage("Door Closed", 800);
    showPrompt();
  }
}

// ===================== 메인 루프 =====================
void loop() {
  handleKeypad();
  handleSerialResponse();
  handleMagnet();
  handleUltrasonic();
  delay(100);
}
