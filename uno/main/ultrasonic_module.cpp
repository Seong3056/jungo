#include "lock_module.h"

void ultrasonicInit() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

void handleUltrasonic() {
  static unsigned long lastSend = 0;
  const unsigned long cooldown = 5000; // 5초 쿨다운
  unsigned long now = millis();

  long duration;
  float distance;

  // 초음파 거리 측정
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  duration = pulseIn(ECHO_PIN, HIGH, 3000); // 30ms 타임아웃
  distance = duration * 0.034 / 2.0;         // cm 단위

  // ✅ 감지 조건 (26cm 이내)
  if (distance > 0 && distance < 26) {
    if (now - lastSend > cooldown) {
      Serial.println("ULTRA:1");  // 감지 신호 전송
      lastSend = now;
    }
  }
}
