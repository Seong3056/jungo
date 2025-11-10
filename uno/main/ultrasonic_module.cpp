#include "lock_module.h"

unsigned long lastUltraSend = 0;

void ultrasonicInit() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1;
  return (duration * 0.0343) / 2.0;
}

bool isObjectDetected(float range) {
  float d = getDistance();
  return (d > 0 && d < range);
}

void handleUltrasonic() {
  static unsigned long lastSend = 0;
  unsigned long now = millis();

  if (isObjectDetected(30.0)) {
    if (now - lastSend > 500) {  // 0.5초 간격으로 전송
      Serial.println("ULTRA:1"); // ✅ 감지 신호 전송
      lastSend = now;
    }
  }
}